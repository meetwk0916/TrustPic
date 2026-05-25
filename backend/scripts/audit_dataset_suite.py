import argparse
import json
from pathlib import Path
from typing import Any

try:
    from audit_public_dataset import (
        audit_samples,
        compute_confidence,
        iter_huggingface_rows_samples,
        iter_huggingface_samples,
        iter_local_samples,
        summarize_results,
    )
except ImportError:
    from scripts.audit_public_dataset import (
        audit_samples,
        compute_confidence,
        iter_huggingface_rows_samples,
        iter_huggingface_samples,
        iter_local_samples,
        summarize_results,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a multi-source TrustPic dataset audit suite and aggregate confidence metrics."
    )
    parser.add_argument("config", help="JSON suite config describing local and Hugging Face sources.")
    parser.add_argument("--json-output", help="Optional JSON output path.")
    parser.add_argument("--markdown-output", help="Optional Markdown output path.")
    parser.add_argument(
        "--min-confidence-level",
        choices=["insufficient", "low", "medium", "high"],
        help="Fail with exit code 1 unless combined confidence reaches this level.",
    )
    parser.add_argument(
        "--min-confidence-score",
        type=float,
        help="Fail with exit code 1 unless combined confidence reaches this score.",
    )
    parser.add_argument(
        "--require-completed-sources",
        type=int,
        help="Fail with exit code 1 unless at least this many sources complete.",
    )
    parser.add_argument(
        "--min-alignment-rate",
        type=float,
        help="Fail with exit code 1 unless configured label expectations meet this combined alignment rate.",
    )
    args = parser.parse_args()

    payload = run_suite(load_config(Path(args.config)))
    if cli_gate_requested(args):
        payload["gate"] = evaluate_gate(
            payload,
            min_confidence_level=args.min_confidence_level,
            min_confidence_score=args.min_confidence_score,
            require_completed_sources=args.require_completed_sources,
            min_alignment_rate=args.min_alignment_rate,
        )

    if args.json_output:
        Path(args.json_output).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.markdown_output:
        Path(args.markdown_output).write_text(render_suite_markdown(payload), encoding="utf-8")

    print(json.dumps(payload, indent=2))
    if payload["gate"]["status"] == "failed":
        raise SystemExit(1)


def cli_gate_requested(args: argparse.Namespace) -> bool:
    return any(
        value is not None
        for value in (
            args.min_confidence_level,
            args.min_confidence_score,
            args.require_completed_sources,
            args.min_alignment_rate,
        )
    )


def load_config(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON suite config {path}: {exc}") from exc


def run_suite(config: dict) -> dict:
    sources = config.get("sources")
    if not isinstance(sources, list) or not sources:
        raise SystemExit("Suite config must include a non-empty 'sources' list.")

    source_payloads = [run_source(source, defaults=config.get("defaults", {})) for source in sources]
    completed = [payload for payload in source_payloads if payload.get("status") == "completed"]
    skipped = [payload for payload in source_payloads if payload.get("status") == "skipped"]
    failed = [payload for payload in source_payloads if payload.get("status") == "failed"]
    combined_results = []
    for payload in completed:
        combined_results.extend(payload["results"])

    combined_summary = summarize_results(combined_results)
    combined_expectation_summary = combine_expectation_summaries(completed)
    payload = {
        "suite": config.get("suite", "trustpic-dataset-suite"),
        "metadata_policy": config.get("metadata_policy", "prefer_raw_original_files"),
        "source_count": len(source_payloads),
        "completed_source_count": len(completed),
        "skipped_source_count": len(skipped),
        "failed_source_count": len(failed),
        "total_samples": len(combined_results),
        "combined_summary": combined_summary,
        "combined_expectation_summary": combined_expectation_summary,
        "confidence": compute_confidence(combined_results, combined_summary),
        "sources": source_payloads,
    }
    gate_config = config.get("gate", {}) if isinstance(config.get("gate", {}), dict) else {}
    payload["gate"] = evaluate_gate(
        payload,
        min_confidence_level=gate_config.get("min_confidence_level"),
        min_confidence_score=gate_config.get("min_confidence_score"),
        require_completed_sources=gate_config.get("require_completed_sources"),
        min_alignment_rate=gate_config.get("min_alignment_rate"),
    )
    return payload


def evaluate_gate(
    payload: dict,
    *,
    min_confidence_level: str | None = None,
    min_confidence_score: float | None = None,
    require_completed_sources: int | None = None,
    min_alignment_rate: float | None = None,
) -> dict:
    failures = []
    confidence = payload.get("confidence", {})

    if min_confidence_level and confidence_level_rank(confidence.get("level")) < confidence_level_rank(min_confidence_level):
        failures.append(
            f"Combined confidence level {confidence.get('level')} is below required level {min_confidence_level}."
        )
    if min_confidence_score is not None and float(confidence.get("score", 0.0)) < float(min_confidence_score):
        failures.append(
            f"Combined confidence score {confidence.get('score')} is below required score {min_confidence_score}."
        )
    if require_completed_sources is not None and payload.get("completed_source_count", 0) < int(require_completed_sources):
        failures.append(
            f"Completed source count {payload.get('completed_source_count', 0)} is below required count {require_completed_sources}."
        )
    if min_alignment_rate is not None:
        alignment = payload.get("combined_expectation_summary", {}).get("alignment_rate")
        if alignment is None:
            failures.append("No configured label expectations were available for alignment gate.")
        elif float(alignment) < float(min_alignment_rate):
            failures.append(f"Combined alignment rate {alignment} is below required rate {min_alignment_rate}.")
    if payload.get("failed_source_count", 0) > 0:
        failures.append(f"{payload['failed_source_count']} source(s) failed.")

    return {
        "status": "failed" if failures else "passed",
        "failures": failures,
        "requirements": {
            "min_confidence_level": min_confidence_level,
            "min_confidence_score": min_confidence_score,
            "require_completed_sources": require_completed_sources,
            "min_alignment_rate": min_alignment_rate,
        },
    }


def confidence_level_rank(level: str | None) -> int:
    order = {"insufficient": 0, "low": 1, "medium": 2, "high": 3}
    return order.get(level or "insufficient", 0)


def combine_expectation_summaries(source_payloads: list[dict]) -> dict:
    checked = 0
    matched = 0
    mismatches = []
    configured_sources = 0
    for source in source_payloads:
        summary = source.get("expectation_summary", {})
        if not summary.get("configured"):
            continue
        configured_sources += 1
        checked += summary.get("checked", 0)
        matched += summary.get("matched", 0)
        for mismatch in summary.get("mismatches", []):
            mismatches.append({"source": source.get("name"), **mismatch})

    return {
        "configured": configured_sources > 0,
        "configured_source_count": configured_sources,
        "checked": checked,
        "matched": matched,
        "mismatched": checked - matched,
        "alignment_rate": round(matched / checked, 4) if checked else None,
        "mismatches": mismatches,
    }


def run_source(source: dict, *, defaults: dict) -> dict:
    if source.get("enabled", True) is False:
        return skipped_source(source, "Source disabled in suite config.")

    mode = source.get("mode")
    try:
        if mode == "local":
            return run_local_source(source, defaults=defaults)
        if mode == "hf":
            return run_huggingface_source(source, defaults=defaults)
        if mode == "hf_rows":
            return run_huggingface_rows_source(source, defaults=defaults)
    except SystemExit as exc:
        if source.get("allow_missing", defaults.get("allow_missing", False)):
            return skipped_source(source, str(exc))
        return failed_source(source, str(exc))

    return failed_source(source, f"Unsupported source mode: {mode}")


def run_local_source(source: dict, *, defaults: dict) -> dict:
    sample_root = Path(required_value(source, "path"))
    samples = iter_local_samples(
        sample_root,
        include_webp=bool(source.get("include_webp", defaults.get("include_webp", False))),
        label_from=source.get("label_from", defaults.get("label_from", "parent")),
        max_samples=int_or_none(source.get("max_samples", defaults.get("max_samples"))),
        max_per_label=int_or_none(source.get("max_per_label", defaults.get("max_per_label"))),
    )
    payload = audit_samples(samples, dataset=str(sample_root), mode="local")
    return with_source_metadata(payload, source)


def run_huggingface_source(source: dict, *, defaults: dict) -> dict:
    samples = iter_huggingface_samples(
        dataset_name=required_value(source, "dataset"),
        config=source.get("config"),
        split=source.get("split", defaults.get("split", "train")),
        image_column=source.get("image_column", defaults.get("image_column", "image")),
        label_column=source.get("label_column", defaults.get("label_column", "label")),
        source_column=source.get("source_column", defaults.get("source_column")),
        streaming=bool(source.get("streaming", defaults.get("streaming", False))),
        max_samples=int_or_none(source.get("max_samples", defaults.get("max_samples"))),
        max_per_label=int_or_none(source.get("max_per_label", defaults.get("max_per_label"))),
    )
    payload = audit_samples(samples, dataset=source["dataset"], mode="huggingface")
    return with_source_metadata(payload, source)


def run_huggingface_rows_source(source: dict, *, defaults: dict) -> dict:
    samples = iter_huggingface_rows_samples(
        dataset_name=required_value(source, "dataset"),
        config=source.get("config", defaults.get("config", "default")),
        split=source.get("split", defaults.get("split", "train")),
        image_column=source.get("image_column", defaults.get("image_column", "image")),
        label_column=source.get("label_column", defaults.get("label_column", "label")),
        source_column=source.get("source_column", defaults.get("source_column")),
        offset=int(source.get("offset", defaults.get("offset", 0))),
        max_samples=int_or_none(source.get("max_samples", defaults.get("max_samples"))),
        max_per_label=int_or_none(source.get("max_per_label", defaults.get("max_per_label"))),
    )
    payload = audit_samples(samples, dataset=source["dataset"], mode="huggingface_rows")
    return with_source_metadata(payload, source)


def with_source_metadata(payload: dict, source: dict) -> dict:
    source_name = source.get("name") or payload["dataset"]
    expectations = source.get("expectations", {})
    expectation_summary = evaluate_expectations(payload["results"], expectations)
    for item in payload["results"]:
        item["dataset_source"] = source_name
        item["expectation"] = evaluate_sample_expectation(item, expectations)
    return {
        "status": "completed",
        "name": source_name,
        "mode": payload["mode"],
        "dataset": payload["dataset"],
        "metadata_policy": source.get("metadata_policy", "raw_or_original_files_required"),
        "total": payload["total"],
        "summary": payload["summary"],
        "expectation_summary": expectation_summary,
        "confidence": payload["confidence"],
        "results": payload["results"],
    }


def evaluate_expectations(results: list[dict], expectations: dict | None) -> dict:
    if not isinstance(expectations, dict) or not expectations:
        return {
            "configured": False,
            "checked": 0,
            "matched": 0,
            "mismatched": 0,
            "alignment_rate": None,
            "mismatches": [],
        }

    checked = 0
    matched = 0
    mismatches = []
    for item in results:
        expectation = evaluate_sample_expectation(item, expectations)
        if not expectation["configured"]:
            continue
        checked += 1
        if expectation["matched"]:
            matched += 1
        else:
            mismatches.append(
                {
                    "sample_id": item.get("sample_id"),
                    "file": item.get("file"),
                    "label": item.get("label"),
                    "failures": expectation["failures"],
                }
            )

    return {
        "configured": True,
        "checked": checked,
        "matched": matched,
        "mismatched": checked - matched,
        "alignment_rate": round(matched / checked, 4) if checked else None,
        "mismatches": mismatches,
    }


def evaluate_sample_expectation(item: dict, expectations: dict | None) -> dict:
    if not isinstance(expectations, dict) or not expectations:
        return {"configured": False, "matched": None, "failures": []}

    expectation = expectations.get(item.get("label")) or expectations.get("*")
    if not isinstance(expectation, dict):
        return {"configured": False, "matched": None, "failures": []}

    failures = []
    check_allowed("verdict", item.get("verdict"), expectation, failures)
    check_allowed("c2pa_status", item["c2pa"].get("status"), expectation, failures)
    check_allowed("gb45438_status", item["gb45438"].get("status"), expectation, failures)
    check_allowed("ela_status", item["ela"].get("status"), expectation, failures)
    if "exif_detected" in expectation and bool(item["exif"].get("detected")) != bool(expectation["exif_detected"]):
        failures.append(
            f"exif_detected={item['exif'].get('detected')} not equal expected {expectation['exif_detected']}"
        )
    return {"configured": True, "matched": not failures, "failures": failures}


def check_allowed(field_name: str, actual: object, expectation: dict, failures: list[str]) -> None:
    allowed = expectation.get(field_name)
    if allowed is None:
        return
    allowed_values = allowed if isinstance(allowed, list) else [allowed]
    if actual not in allowed_values:
        failures.append(f"{field_name}={actual} not in expected {allowed_values}")


def skipped_source(source: dict, reason: str) -> dict:
    return source_status_payload(source, "skipped", reason)


def failed_source(source: dict, reason: str) -> dict:
    return source_status_payload(source, "failed", reason)


def source_status_payload(source: dict, status: str, reason: str) -> dict:
    return {
        "status": status,
        "name": source.get("name") or source.get("dataset") or source.get("path") or "unnamed-source",
        "mode": source.get("mode"),
        "dataset": source.get("dataset") or source.get("path"),
        "reason": reason,
        "total": 0,
        "summary": {"by_label": {}, "by_source": {}},
        "expectation_summary": {
            "configured": False,
            "checked": 0,
            "matched": 0,
            "mismatched": 0,
            "alignment_rate": None,
            "mismatches": [],
        },
        "confidence": compute_confidence([], {"by_label": {}, "by_source": {}}),
        "results": [],
    }


def required_value(source: dict, key: str) -> str:
    value = source.get(key)
    if not value:
        raise SystemExit(f"Source '{source.get('name', 'unnamed-source')}' is missing required key: {key}")
    return str(value)


def int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def render_suite_markdown(payload: dict) -> str:
    lines = [
        "# TrustPic Dataset Audit Suite",
        "",
        f"- Suite: `{payload['suite']}`",
        f"- Metadata policy: `{payload['metadata_policy']}`",
        f"- Sources: {payload['completed_source_count']} completed, "
        f"{payload['skipped_source_count']} skipped, {payload['failed_source_count']} failed",
        f"- Total samples: {payload['total_samples']}",
        f"- Combined confidence: `{payload['confidence']['level']}` ({payload['confidence']['score']})",
        f"- Combined alignment: {payload['combined_expectation_summary']['alignment_rate']}",
        f"- Gate: `{payload.get('gate', {}).get('status', 'not_configured')}`",
        "",
        "## Source Summary",
        "",
        "| source | status | mode | samples | confidence | reason |",
        "|---|---|---|---:|---|---|",
    ]
    for source in payload["sources"]:
        confidence = source.get("confidence", {})
        lines.append(
            "| "
            f"`{source['name']}` | "
            f"{source['status']} | "
            f"{source.get('mode') or ''} | "
            f"{source.get('total', 0)} | "
            f"{confidence.get('level')} ({confidence.get('score')}) | "
            f"{source.get('reason', '')} |"
        )

    lines.extend(
        [
            "",
            "## Expectation Alignment",
            "",
            "| metric | value |",
            "|---|---:|",
        ]
    )
    for metric, value in payload["combined_expectation_summary"].items():
        if metric == "mismatches":
            continue
        lines.append(f"| `{metric}` | {value} |")

    lines.extend(
        [
            "",
            "## Combined Confidence",
            "",
            "| metric | value |",
            "|---|---:|",
        ]
    )
    for metric, value in payload["confidence"]["metrics"].items():
        lines.append(f"| `{metric}` | {value} |")

    lines.extend(["", "Reasons:", ""])
    for reason in payload["confidence"]["reasons"]:
        lines.append(f"- {reason}")

    if payload.get("gate", {}).get("failures"):
        lines.extend(["", "Gate failures:", ""])
        for failure in payload["gate"]["failures"]:
            lines.append(f"- {failure}")

    lines.extend(
        [
            "",
            "## Combined Label Summary",
            "",
            "| label | count | verdicts | C2PA statuses | GB45438 statuses | EXIF present | ELA review |",
            "|---|---:|---|---|---|---:|---:|",
        ]
    )
    for label, summary in sorted(payload["combined_summary"]["by_label"].items()):
        lines.append(
            "| "
            f"`{label}` | "
            f"{summary['count']} | "
            f"{format_counts(summary['verdicts'])} | "
            f"{format_counts(summary['c2pa_statuses'])} | "
            f"{format_counts(summary['gb45438_statuses'])} | "
            f"{summary['exif_present']} | "
            f"{summary['ela_review']} |"
        )

    lines.append("")
    return "\n".join(lines)


def format_counts(counts: dict) -> str:
    return ", ".join(f"{key}: {value}" for key, value in sorted(counts.items(), key=lambda item: str(item[0])))


if __name__ == "__main__":
    main()
