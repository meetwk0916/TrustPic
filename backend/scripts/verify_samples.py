import argparse
import json
import mimetypes
import sys
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

EXPECTED_RESULTS = {
    "plain.png": {
        "status_code": 200,
        "verdict": "no_supported_signal_found",
        "c2pa_detected": False,
        "gb45438_detected": False,
        "exif_detected": False,
        "ela_status": "low_signal",
        "has_ela_heatmap": True,
    },
    "marked-aigc.png": {
        "status_code": 200,
        "verdict": "supported_signal_detected",
        "c2pa_detected": False,
        "gb45438_detected": True,
        "exif_detected": False,
        "ela_status": "low_signal",
        "has_ela_heatmap": True,
    },
    "camera-exif.jpg": {
        "status_code": 200,
        "c2pa_detected": False,
        "gb45438_detected": False,
        "exif_detected": True,
        "ela_status": "low_signal",
        "has_ela_heatmap": True,
    },
    "metadata-stripped.jpg": {
        "status_code": 200,
        "c2pa_detected": False,
        "gb45438_detected": False,
        "exif_detected": False,
        "ela_status": "low_signal",
        "has_ela_heatmap": True,
    },
    "edited-compressed.jpg": {
        "status_code": 200,
        "c2pa_detected": False,
        "gb45438_detected": False,
        "exif_detected": False,
        "ela_status": "low_signal",
        "has_ela_heatmap": True,
    },
    "ela-review-compressed.jpg": {
        "status_code": 200,
        "verdict": "review_recommended",
        "c2pa_detected": False,
        "gb45438_detected": False,
        "exif_detected": False,
        "ela_status": "review",
        "has_ela_heatmap": True,
    },
    "c2pa-attacks-C.jpg": {
        "status_code": 200,
        "verdict": "supported_signal_detected",
        "c2pa_detected": True,
        "c2pa_validation_state": "Valid",
        "gb45438_detected": False,
        "has_ela_heatmap": True,
    },
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
    failures = validate_results(results)
    print(json.dumps({"output_dir": str(output_dir), "results": results, "failures": failures}, indent=2))
    if failures:
        sys.exit(1)


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
    exif = signals.get("exif", {}) if isinstance(signals, dict) else {}
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
        "exif_detected": exif.get("detected"),
        "exif_field_count": exif.get("details", {}).get("field_count")
        if isinstance(exif.get("details"), dict)
        else None,
        "ela_status": ela.get("status"),
        "ela_mean_error": ela.get("details", {}).get("mean_error")
        if isinstance(ela.get("details"), dict)
        else None,
        "has_ela_heatmap": bool(payload.get("assets", {}).get("ela_heatmap_data_url"))
        if isinstance(payload, dict)
        else False,
    }


def validate_results(results: list[dict]) -> list[str]:
    failures = []
    for result in results:
        expected = EXPECTED_RESULTS.get(result["file"], {})
        for key, expected_value in expected.items():
            if result.get(key) != expected_value:
                failures.append(
                    f"{result['file']}: expected {key}={expected_value!r}, got {result.get(key)!r}"
                )
    return failures


if __name__ == "__main__":
    main()
