import argparse
import json
import mimetypes
from pathlib import Path
from urllib.request import urlretrieve

from fastapi.testclient import TestClient

from app.main import app
from generate_sample_images import generate_samples

PUBLIC_C2PA_SAMPLES = {
    "c2pa-attacks-C.jpg": {
        "url": "https://raw.githubusercontent.com/contentauth/c2pa-attacks/main/sample/C.jpg",
        "source": "contentauth/c2pa-attacks sample/C.jpg",
        "note": "Public Content Credentials test image with a self-signed/untrusted test certificate.",
    }
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify TrustPic v0 against local smoke samples.")
    parser.add_argument(
        "--output-dir",
        default="/private/tmp/trustpic-samples",
        help="Directory for generated and downloaded samples.",
    )
    parser.add_argument(
        "--download-public",
        action="store_true",
        help="Download public C2PA samples before verification.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    sample_paths = generate_samples(output_dir)

    if args.download_public:
        sample_paths.extend(download_public_samples(output_dir))

    results = [verify_sample(path) for path in sample_paths]
    print(json.dumps({"output_dir": str(output_dir), "results": results}, indent=2))


def download_public_samples(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    downloaded = []
    for filename, metadata in PUBLIC_C2PA_SAMPLES.items():
        target = output_dir / filename
        urlretrieve(metadata["url"], target)
        downloaded.append(target)
    return downloaded


def verify_sample(path: Path) -> dict:
    client = TestClient(app)
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    with path.open("rb") as image_file:
        response = client.post(
            "/api/v1/analyze",
            files={"file": (path.name, image_file, content_type)},
        )

    payload = response.json()
    signals = payload.get("signals", {}) if isinstance(payload, dict) else {}
    c2pa = signals.get("c2pa", {}) if isinstance(signals, dict) else {}
    gb45438 = signals.get("gb45438", {}) if isinstance(signals, dict) else {}
    ela = signals.get("ela", {}) if isinstance(signals, dict) else {}

    return {
        "file": path.name,
        "source": PUBLIC_C2PA_SAMPLES.get(path.name, {}).get("source", "local generated sample"),
        "status_code": response.status_code,
        "verdict": payload.get("verdict") if isinstance(payload, dict) else None,
        "c2pa_status": c2pa.get("status"),
        "c2pa_detected": c2pa.get("detected"),
        "c2pa_validation_state": c2pa.get("details", {}).get("validation_state")
        if isinstance(c2pa.get("details"), dict)
        else None,
        "gb45438_detected": gb45438.get("detected"),
        "ela_status": ela.get("status"),
        "has_ela_heatmap": bool(payload.get("assets", {}).get("ela_heatmap_data_url"))
        if isinstance(payload, dict)
        else False,
    }


if __name__ == "__main__":
    main()
