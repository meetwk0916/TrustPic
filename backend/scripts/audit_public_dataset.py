import argparse
import json
import mimetypes
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from fastapi.testclient import TestClient

from app.main import app


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
WEBP_EXTENSION = ".webp"


@dataclass(frozen=True)
class DatasetSample:
    sample_id: str
    file_name: str
    label: str | None
    source: str | None
    relative_path: str | None = None
    path: Path | None = None
    image_bytes: bytes | None = None
    content_type: str | None = None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit metadata-preserving public image datasets with the TrustPic analyzer."
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    local_parser = subparsers.add_parser("local", help="Audit a local dataset directory recursively.")
    add_common_args(local_parser)
    local_parser.add_argument("sample_root", help="Directory containing raw dataset image files.")
    local_parser.add_argument(
        "--label-from",
        choices=["parent", "grandparent", "none"],
        default="parent",
        help="How to infer labels from the local directory layout.",
    )
    local_parser.add_argument(
        "--include-webp",
        action="store_true",
        help="Include WebP files. Omit this for provenance-focused audits of raw JPEG/PNG sources.",
    )

    hf_parser = subparsers.add_parser("hf", help="Audit a Hugging Face dataset split.")
    add_common_args(hf_parser)
    hf_parser.add_argument("dataset", help="Hugging Face dataset name, for example org/name.")
    hf_parser.add_argument("--config", help="Optional Hugging Face dataset config name.")
    hf_parser.add_argument("--split", default="train", help="Dataset split to audit.")
    hf_parser.add_argument("--image-column", default="image", help="Column containing image files.")
    hf_parser.add_argument("--label-column", default="label", help="Optional label column.")
    hf_parser.add_argument("--source-column", help="Optional source/generator column.")
    hf_parser.add_argument(
        "--streaming",
        action="store_true",
        help="Stream the dataset instead of downloading the full split first.",
    )

    args = parser.parse_args()

    if args.mode == "local":
        samples = iter_local_samples(
            Path(args.sample_root),
            include_webp=args.include_webp,
            label_from=args.label_from,
            max_samples=args.max_samples,
            max_per_label=args.max_per_label,
        )
        payload = audit_samples(samples, dataset=args.sample_root, mode="local")
    else:
        samples = iter_huggingface_samples(
            dataset_name=args.dataset,
            config=args.config,
            split=args.split,
            image_column=args.image_column,
            label_column=args.label_column,
            source_column=args.source_column,
            streaming=args.streaming,
            max_samples=args.max_samples,
            max_per_label=args.max_per_label,
        )
        payload = audit_samples(samples, dataset=args.dataset, mode="huggingface")

    if args.json_output:
        Path(args.json_output).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.markdown_output:
        Path(args.markdown_output).write_text(render_markdown(payload), encoding="utf-8")

    print(json.dumps(payload, indent=2))


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--max-samples", type=int, help="Maximum number of samples to audit.")
    parser.add_argument("--max-per-label", type=int, help="Maximum number of samples per label.")
    parser.add_argument("--json-output", help="Optional JSON output path.")
    parser.add_argument("--markdown-output", help="Optional Markdown output path.")


def iter_local_samples(
    sample_root: Path,
    *,
    include_webp: bool = False,
    label_from: str = "parent",
    max_samples: int | None = None,
    max_per_label: int | None = None,
) -> list[DatasetSample]:
    if not sample_root.exists():
        raise SystemExit(f"Sample root does not exist: {sample_root}")
    if not sample_root.is_dir():
        raise SystemExit(f"Sample root is not a directory: {sample_root}")

    counters: dict[str, int] = defaultdict(int)
    samples: list[DatasetSample] = []
    for path in sorted(sample_root.rglob("*")):
        if not path.is_file() or not is_supported_image(path, include_webp=include_webp):
            continue

        label = infer_label(path, sample_root, label_from)
        counter_key = label or "unlabeled"
        if max_per_label is not None and counters[counter_key] >= max_per_label:
            continue

        relative_path = path.relative_to(sample_root).as_posix()
        samples.append(
            DatasetSample(
                sample_id=relative_path,
                file_name=path.name,
                label=label,
                source=infer_source(path, sample_root),
                relative_path=relative_path,
                path=path,
                content_type=mimetypes.guess_type(path.name)[0],
            )
        )
        counters[counter_key] += 1

        if max_samples is not None and len(samples) >= max_samples:
            break
    return samples


def is_supported_image(path: Path, *, include_webp: bool) -> bool:
    extensions = IMAGE_EXTENSIONS | ({WEBP_EXTENSION} if include_webp else set())
    return path.suffix.lower() in extensions


def infer_label(path: Path, sample_root: Path, label_from: str) -> str | None:
    if label_from == "none":
        return None

    relative_parts = path.relative_to(sample_root).parts
    if label_from == "parent" and len(relative_parts) >= 2:
        return relative_parts[-2]
    if label_from == "grandparent" and len(relative_parts) >= 3:
        return relative_parts[-3]
    return None


def infer_source(path: Path, sample_root: Path) -> str | None:
    relative_parent = path.parent.relative_to(sample_root).as_posix()
    return None if relative_parent == "." else relative_parent


def iter_huggingface_samples(
    *,
    dataset_name: str,
    config: str | None,
    split: str,
    image_column: str,
    label_column: str | None,
    source_column: str | None,
    streaming: bool,
    max_samples: int | None,
    max_per_label: int | None,
) -> list[DatasetSample]:
    try:
        from datasets import Image as HfImage
        from datasets import load_dataset
    except ImportError as exc:
        raise SystemExit(
            "Hugging Face audit requires the optional datasets package. "
            "Install it with: cd backend && .venv/bin/python -m pip install -e '.[dev,datasets]'"
        ) from exc

    load_kwargs = {"split": split, "streaming": streaming}
    if config:
        dataset = load_dataset(dataset_name, config, **load_kwargs)
    else:
        dataset = load_dataset(dataset_name, **load_kwargs)

    try:
        dataset = dataset.cast_column(image_column, HfImage(decode=False))
    except Exception as exc:
        raise SystemExit(f"Could not read image column '{image_column}' as raw images: {exc}") from exc

    counters: dict[str, int] = defaultdict(int)
    samples: list[DatasetSample] = []
    features = getattr(dataset, "features", {}) or {}
    for index, row in enumerate(dataset):
        label = normalize_hf_value(row, label_column, features) if label_column else None
        counter_key = label or "unlabeled"
        if max_per_label is not None and counters[counter_key] >= max_per_label:
            continue

        image_value = row.get(image_column)
        sample = sample_from_hf_row(
            image_value,
            sample_id=str(index),
            label=label,
            source=normalize_hf_value(row, source_column, features) if source_column else None,
        )
        samples.append(sample)
        counters[counter_key] += 1

        if max_samples is not None and len(samples) >= max_samples:
            break
    return samples


def sample_from_hf_row(
    image_value: object,
    *,
    sample_id: str,
    label: str | None,
    source: str | None,
) -> DatasetSample:
    if not isinstance(image_value, dict):
        raise SystemExit("Image column did not return raw file metadata. Use a datasets.Image column.")

    raw_path = image_value.get("path")
    image_bytes = image_value.get("bytes")
    path = Path(raw_path) if isinstance(raw_path, str) and raw_path else None
    file_name = path.name if path else f"hf-{sample_id}.image"
    content_type = mimetypes.guess_type(file_name)[0]

    if isinstance(image_bytes, bytes):
        return DatasetSample(
            sample_id=sample_id,
            file_name=file_name,
            label=label,
            source=source,
            path=None,
            image_bytes=image_bytes,
            content_type=content_type or guess_content_type(file_name, image_bytes),
        )
    if path and path.exists():
        return DatasetSample(
            sample_id=sample_id,
            file_name=file_name,
            label=label,
            source=source,
            path=path,
            image_bytes=None,
            content_type=content_type,
        )

    raise SystemExit(f"Sample {sample_id} has no accessible raw image bytes or file path.")


def normalize_value(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def normalize_hf_value(row: dict, column: str | None, features: dict) -> str | None:
    if not column:
        return None
    value = row.get(column)
    feature = features.get(column) if isinstance(features, dict) else None
    if value is None:
        return None
    if hasattr(feature, "int2str") and isinstance(value, int):
        return str(feature.int2str(value))
    return normalize_value(value)


def audit_samples(samples: Iterable[DatasetSample], *, dataset: str, mode: str) -> dict:
    client = TestClient(app)
    results = [analyze_sample(client, sample) for sample in samples]
    summary = summarize_results(results)
    return {
        "dataset": dataset,
        "mode": mode,
        "total": len(results),
        "summary": summary,
        "confidence": compute_confidence(results, summary),
        "results": results,
    }


def analyze_sample(client: TestClient, sample: DatasetSample) -> dict:
    content_type = sample.content_type or guess_content_type(sample.file_name, sample.image_bytes)
    if sample.image_bytes is not None:
        response = client.post(
            "/api/v1/analyze",
            files={"file": (sample.file_name, sample.image_bytes, content_type)},
        )
    elif sample.path is not None:
        with sample.path.open("rb") as image_file:
            response = client.post(
                "/api/v1/analyze",
                files={"file": (sample.file_name, image_file, content_type)},
            )
    else:
        raise ValueError(f"Sample {sample.sample_id} has no bytes or path.")

    payload = response.json()
    signals = payload.get("signals", {}) if isinstance(payload, dict) else {}
    return {
        "sample_id": sample.sample_id,
        "file": sample.file_name,
        "relative_path": sample.relative_path,
        "label": sample.label,
        "source": sample.source,
        "status_code": response.status_code,
        "verdict": payload.get("verdict") if isinstance(payload, dict) else None,
        "summary": payload.get("summary") if isinstance(payload, dict) else None,
        "c2pa": summarize_signal(signals, "c2pa"),
        "gb45438": summarize_signal(signals, "gb45438"),
        "exif": summarize_signal(signals, "exif"),
        "ela": summarize_signal(signals, "ela"),
    }


def summarize_signal(signals: dict, name: str) -> dict:
    signal = signals.get(name, {}) if isinstance(signals, dict) else {}
    details = signal.get("details", {}) if isinstance(signal, dict) else {}
    summary = {
        "detected": signal.get("detected"),
        "status": signal.get("status"),
    }
    if name == "c2pa" and isinstance(details, dict):
        summary["validation_state"] = details.get("validation_state")
        summary["signature_issuer"] = details.get("signature_issuer")
    if name == "gb45438" and isinstance(details, dict):
        summary["tc260_namespace_detected"] = details.get("tc260_namespace_detected")
        summary["xmp_fields"] = details.get("xmp_fields")
    if name == "exif" and isinstance(details, dict):
        summary["field_count"] = details.get("field_count")
    if name == "ela" and isinstance(details, dict):
        summary["mean_error"] = details.get("mean_error")
        summary["review_threshold"] = details.get("review_threshold")
    return summary


def guess_content_type(file_name: str, image_bytes: bytes | None = None) -> str:
    content_type = mimetypes.guess_type(file_name)[0]
    if content_type:
        return content_type
    if image_bytes:
        if image_bytes.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        if image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP":
            return "image/webp"
    return "application/octet-stream"


def summarize_results(results: list[dict]) -> dict:
    by_label: dict[str, dict] = {}
    by_source: dict[str, dict] = {}
    for item in results:
        add_group_item(by_label, item.get("label") or "unlabeled", item)
        add_group_item(by_source, item.get("source") or "unknown", item)
    return {"by_label": by_label, "by_source": by_source}


def compute_confidence(results: list[dict], summary: dict) -> dict:
    total = len(results)
    if total == 0:
        return {
            "level": "insufficient",
            "score": 0.0,
            "reasons": ["No samples were audited."],
            "metrics": empty_confidence_metrics(),
        }

    success_count = sum(1 for item in results if item.get("status_code") == 200)
    labeled_count = sum(1 for item in results if item.get("label"))
    exif_count = sum(1 for item in results if item["exif"].get("detected"))
    c2pa_count = sum(1 for item in results if item["c2pa"].get("detected"))
    gb45438_count = sum(1 for item in results if item["gb45438"].get("detected"))
    ela_review_count = sum(1 for item in results if item["ela"].get("status") == "review")
    label_count = len(summary.get("by_label", {}))

    success_rate = success_count / total
    labeled_rate = labeled_count / total
    provenance_signal_rate = (c2pa_count + gb45438_count) / total
    metadata_signal_rate = exif_count / total
    ela_review_rate = ela_review_count / total
    label_coverage_rate = min(label_count / 2, 1.0)
    sample_size_score = min(total / 50, 1.0)

    metrics = {
        "success_rate": round(success_rate, 4),
        "labeled_rate": round(labeled_rate, 4),
        "label_count": label_count,
        "label_coverage_rate": round(label_coverage_rate, 4),
        "sample_size_score": round(sample_size_score, 4),
        "provenance_signal_rate": round(provenance_signal_rate, 4),
        "metadata_signal_rate": round(metadata_signal_rate, 4),
        "ela_review_rate": round(ela_review_rate, 4),
    }

    score = (
        success_rate * 0.35
        + sample_size_score * 0.25
        + label_coverage_rate * 0.15
        + labeled_rate * 0.10
        + min(provenance_signal_rate + metadata_signal_rate + ela_review_rate, 1.0) * 0.15
    )
    score = round(score, 4)

    reasons = confidence_reasons(total=total, metrics=metrics)
    return {
        "level": confidence_level(score, metrics),
        "score": score,
        "reasons": reasons,
        "metrics": metrics,
    }


def empty_confidence_metrics() -> dict:
    return {
        "success_rate": 0.0,
        "labeled_rate": 0.0,
        "label_count": 0,
        "label_coverage_rate": 0.0,
        "sample_size_score": 0.0,
        "provenance_signal_rate": 0.0,
        "metadata_signal_rate": 0.0,
        "ela_review_rate": 0.0,
    }


def confidence_level(score: float, metrics: dict) -> str:
    if metrics["success_rate"] < 0.95 or metrics["label_count"] == 0:
        return "low"
    if score >= 0.75 and metrics["label_count"] >= 2 and metrics["sample_size_score"] >= 0.5:
        return "high"
    if score >= 0.45:
        return "medium"
    return "low"


def confidence_reasons(*, total: int, metrics: dict) -> list[str]:
    reasons = []
    if metrics["success_rate"] < 1:
        reasons.append("Some samples failed API analysis.")
    if total < 50:
        reasons.append("Sample count is below the recommended 50-image calibration floor.")
    if metrics["label_count"] < 2:
        reasons.append("Fewer than two labels were present; label-level comparison is weak.")
    if metrics["provenance_signal_rate"] == 0 and metrics["metadata_signal_rate"] == 0:
        reasons.append("No provenance or EXIF metadata signals were observed.")
    if not reasons:
        reasons.append("Sample size, label coverage, and analyzer success rate are suitable for calibration.")
    return reasons


def add_group_item(groups: dict[str, dict], key: str, item: dict) -> None:
    group = groups.setdefault(
        key,
        {
            "count": 0,
            "verdicts": defaultdict(int),
            "c2pa_statuses": defaultdict(int),
            "gb45438_statuses": defaultdict(int),
            "exif_present": 0,
            "ela_review": 0,
        },
    )
    group["count"] += 1
    group["verdicts"][item.get("verdict")] += 1
    group["c2pa_statuses"][item["c2pa"].get("status")] += 1
    group["gb45438_statuses"][item["gb45438"].get("status")] += 1
    if item["exif"].get("detected"):
        group["exif_present"] += 1
    if item["ela"].get("status") == "review":
        group["ela_review"] += 1


def render_markdown(payload: dict) -> str:
    lines = [
        "# TrustPic Public Dataset Audit",
        "",
        f"- Dataset: `{payload['dataset']}`",
        f"- Mode: `{payload['mode']}`",
        f"- Total samples: {payload['total']}",
        f"- Confidence: `{payload['confidence']['level']}` ({payload['confidence']['score']})",
        "",
        "## Confidence",
        "",
        "| metric | value |",
        "|---|---:|",
    ]
    for metric, value in payload["confidence"]["metrics"].items():
        lines.append(f"| `{metric}` | {value} |")
    lines.extend(
        [
            "",
            "Reasons:",
            "",
        ]
    )
    for reason in payload["confidence"]["reasons"]:
        lines.append(f"- {reason}")
    lines.extend(
        [
            "",
        "## Label Summary",
        "",
        "| label | count | verdicts | C2PA statuses | GB45438 statuses | EXIF present | ELA review |",
        "|---|---:|---|---|---|---:|---:|",
        ]
    )
    for label, summary in sorted(payload["summary"]["by_label"].items()):
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

    lines.extend(
        [
            "",
            "## Samples",
            "",
            "| file | label | source | verdict | C2PA | GB45438 | EXIF fields | ELA | ELA mean |",
            "|---|---|---|---|---|---|---:|---|---:|",
        ]
    )
    for item in payload["results"]:
        lines.append(
            "| "
            f"`{item['file']}` | "
            f"{item.get('label') or ''} | "
            f"{item.get('source') or ''} | "
            f"{item.get('verdict') or ''} | "
            f"{item['c2pa'].get('status')} | "
            f"{item['gb45438'].get('status')} | "
            f"{item['exif'].get('field_count')} | "
            f"{item['ela'].get('status')} | "
            f"{item['ela'].get('mean_error')} |"
        )
    lines.append("")
    return "\n".join(lines)


def format_counts(counts: dict) -> str:
    return ", ".join(f"{key}: {value}" for key, value in sorted(counts.items(), key=lambda item: str(item[0])))


if __name__ == "__main__":
    main()
