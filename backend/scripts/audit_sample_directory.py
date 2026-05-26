import argparse
import json
import mimetypes
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a directory of user-supplied TrustPic samples.")
    parser.add_argument("sample_dir", help="Directory containing real image samples.")
    parser.add_argument("--json-output", help="Optional JSON output path.")
    parser.add_argument("--markdown-output", help="Optional Markdown output path.")
    args = parser.parse_args()

    sample_dir = Path(args.sample_dir)
    results = [analyze_path(path) for path in sorted(iter_image_paths(sample_dir))]
    payload = {"sample_dir": str(sample_dir), "results": results}

    if args.json_output:
        Path(args.json_output).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.markdown_output:
        Path(args.markdown_output).write_text(render_markdown(results), encoding="utf-8")

    print(json.dumps(payload, indent=2))


def iter_image_paths(sample_dir: Path):
    for path in sample_dir.iterdir():
        if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
            yield path


def analyze_path(path: Path) -> dict:
    client = TestClient(app)
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    with path.open("rb") as image_file:
        response = client.post(
            "/api/v1/analyze",
            files={"file": (path.name, image_file, content_type)},
        )

    payload = response.json()
    signals = payload.get("signals", {}) if isinstance(payload, dict) else {}
    return {
        "file": path.name,
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
        summary["local_anomaly_detected"] = details.get("local_anomaly_detected")
        summary["local_anomaly_count"] = details.get("local_anomaly_count")
        summary["local_anomaly_ratio"] = details.get("local_anomaly_ratio")
    return summary


def render_markdown(results: list[dict]) -> str:
    lines = [
        "# TrustPic Real Sample Audit",
        "",
        "| file | verdict | C2PA | GB45438 | EXIF fields | ELA | ELA mean | local anomalies |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for item in results:
        lines.append(
            "| "
            f"`{item['file']}` | "
            f"{item['verdict']} | "
            f"{item['c2pa'].get('status')} | "
            f"{item['gb45438'].get('status')} | "
            f"{item['exif'].get('field_count')} | "
            f"{item['ela'].get('status')} | "
            f"{item['ela'].get('mean_error')} | "
            f"{item['ela'].get('local_anomaly_count')} |"
        )
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
