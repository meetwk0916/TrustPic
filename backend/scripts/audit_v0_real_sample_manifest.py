import argparse
import json
import mimetypes
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


REQUIRED_SLOT_IDS = {
    "openai_c2pa_original",
    "google_ai_original",
    "google_ai_reencoded",
    "domestic_gb45438_original",
    "camera_exif_original",
    "platform_stripped",
    "known_local_edit",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit TrustPic v0 real-sample manifest slots.")
    parser.add_argument("manifest", help="JSON manifest describing real v0 samples.")
    parser.add_argument("--json-output", help="Optional JSON output path.")
    parser.add_argument("--markdown-output", help="Optional Markdown output path.")
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Exit 0 even if required sample files are missing.",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    payload = audit_manifest(load_manifest(manifest_path), base_dir=manifest_path.parent)

    if args.json_output:
        Path(args.json_output).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.markdown_output:
        Path(args.markdown_output).write_text(render_markdown(payload), encoding="utf-8")

    print(json.dumps(payload, indent=2, ensure_ascii=False))
    if payload["missing_required_count"] and not args.allow_missing:
        raise SystemExit(1)


def load_manifest(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON manifest {path}: {exc}") from exc


def audit_manifest(manifest: dict, *, base_dir: Path) -> dict:
    samples = manifest.get("samples")
    if not isinstance(samples, list):
        raise SystemExit("Manifest must include a 'samples' list.")

    results = [audit_slot(slot, base_dir=base_dir) for slot in samples if isinstance(slot, dict)]
    missing_required = [item for item in results if item["required"] and item["status"] == "missing"]
    present = [item for item in results if item["status"] == "audited"]
    configured_slot_ids = {str(item.get("slot_id")) for item in results}
    missing_slot_ids = sorted(REQUIRED_SLOT_IDS - configured_slot_ids)

    return {
        "suite": manifest.get("suite", "trustpic-v0-real-sample-suite"),
        "sample_count": len(results),
        "audited_count": len(present),
        "missing_required_count": len(missing_required) + len(missing_slot_ids),
        "missing_required_slots": [item["slot_id"] for item in missing_required] + missing_slot_ids,
        "results": results,
    }


def audit_slot(slot: dict, *, base_dir: Path) -> dict:
    slot_id = str(slot.get("slot_id", "unnamed_slot"))
    path_value = slot.get("path")
    required = bool(slot.get("required", True))
    if not path_value:
        return missing_slot(slot, slot_id=slot_id, required=required, reason="No path configured.")

    path = Path(path_value)
    if not path.is_absolute():
        path = base_dir / path
    if not path.exists():
        return missing_slot(slot, slot_id=slot_id, required=required, reason=f"File not found: {path}")

    client = TestClient(app)
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    with path.open("rb") as image_file:
        response = client.post("/api/v1/analyze", files={"file": (path.name, image_file, content_type)})

    payload = response.json()
    interpretation = payload.get("interpretation", {}) if isinstance(payload, dict) else {}
    signals = payload.get("signals", {}) if isinstance(payload, dict) else {}
    return {
        "slot_id": slot_id,
        "label": slot.get("label"),
        "required": required,
        "status": "audited",
        "path": str(path),
        "status_code": response.status_code,
        "verdict": payload.get("verdict") if isinstance(payload, dict) else None,
        "confidence_label": interpretation.get("confidence_label"),
        "conclusion": interpretation.get("conclusion"),
        "signals": {
            "c2pa": summarize_signal(signals, "c2pa"),
            "gb45438": summarize_signal(signals, "gb45438"),
            "exif": summarize_signal(signals, "exif"),
            "ela": summarize_signal(signals, "ela"),
        },
    }


def missing_slot(slot: dict, *, slot_id: str, required: bool, reason: str) -> dict:
    return {
        "slot_id": slot_id,
        "label": slot.get("label"),
        "required": required,
        "status": "missing",
        "path": slot.get("path"),
        "reason": reason,
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
        summary["signature_common_name"] = details.get("signature_common_name")
        summary["claim_generator"] = details.get("claim_generator")
        summary["ai_related"] = details.get("ai_related")
    if name == "gb45438" and isinstance(details, dict):
        summary["tc260_namespace_detected"] = details.get("tc260_namespace_detected")
        summary["xmp_fields"] = details.get("xmp_fields")
        summary["matched_terms"] = details.get("matched_terms")
    if name == "exif" and isinstance(details, dict):
        summary["field_count"] = details.get("field_count")
    if name == "ela" and isinstance(details, dict):
        summary["local_anomaly_detected"] = details.get("local_anomaly_detected")
        summary["local_anomaly_count"] = details.get("local_anomaly_count")
        summary["local_anomaly_ratio"] = details.get("local_anomaly_ratio")
    return summary


def render_markdown(payload: dict) -> str:
    lines = [
        "# TrustPic v0 Real Sample Manifest Audit",
        "",
        f"- Suite: `{payload['suite']}`",
        f"- Audited slots: {payload['audited_count']}/{payload['sample_count']}",
        f"- Missing required slots: {payload['missing_required_count']}",
        "",
        "| slot | status | label | confidence | conclusion | C2PA | GB45438 | EXIF fields | local diff |",
        "|---|---|---|---|---|---|---|---:|---|",
    ]
    for item in payload["results"]:
        signals = item.get("signals", {})
        lines.append(
            "| "
            f"`{item['slot_id']}` | "
            f"{item['status']} | "
            f"{item.get('label') or ''} | "
            f"{item.get('confidence_label') or ''} | "
            f"{item.get('conclusion') or item.get('reason') or ''} | "
            f"{signals.get('c2pa', {}).get('status', '')} | "
            f"{signals.get('gb45438', {}).get('status', '')} | "
            f"{signals.get('exif', {}).get('field_count', '')} | "
            f"{signals.get('ela', {}).get('local_anomaly_count', '')} |"
        )
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
