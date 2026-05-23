from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from app.services import analyze as analyze_service
from app.main import app

client = TestClient(app)


def _png_bytes(size: tuple[int, int] = (64, 64)) -> bytes:
    image = Image.new("RGB", size, color=(120, 40, 80))
    out = BytesIO()
    image.save(out, format="PNG")
    return out.getvalue()


def test_health() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_png_returns_report_shape() -> None:
    response = client.post(
        "/api/v1/analyze",
        files={"file": ("sample.png", _png_bytes(), "image/png")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["verdict"] in {
        "supported_signal_detected",
        "review_recommended",
        "no_supported_signal_found",
        "unsupported",
    }
    assert set(payload["signals"]) == {"c2pa", "gb45438", "exif", "ela"}
    assert payload["assets"]["ela_heatmap_data_url"].startswith("data:image/jpeg;base64,")


def test_rejects_unsupported_file_type() -> None:
    response = client.post(
        "/api/v1/analyze",
        files={"file": ("sample.txt", b"not an image", "text/plain")},
    )

    assert response.status_code == 415


def test_rejects_empty_image_content() -> None:
    response = client.post(
        "/api/v1/analyze",
        files={"file": ("empty.png", b"", "image/png")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "No file content received."


def test_rejects_undecodable_image_bytes() -> None:
    response = client.post(
        "/api/v1/analyze",
        files={"file": ("broken.png", b"not actually a png", "image/png")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded file could not be decoded as an image."


def test_rejects_oversized_upload(monkeypatch) -> None:
    monkeypatch.setattr(analyze_service, "MAX_UPLOAD_BYTES", 4)

    response = client.post(
        "/api/v1/analyze",
        files={"file": ("sample.png", _png_bytes(), "image/png")},
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "File is too large. Maximum size is 15 MB."


def test_rejects_oversized_dimensions(monkeypatch) -> None:
    monkeypatch.setattr(analyze_service, "MAX_PIXELS", 16)

    response = client.post(
        "/api/v1/analyze",
        files={"file": ("sample.png", _png_bytes(size=(8, 8)), "image/png")},
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "Image dimensions are too large for v0 analysis."


def test_gb45438_marker_changes_verdict_to_supported_signal() -> None:
    response = client.post(
        "/api/v1/analyze",
        files={"file": ("marked.png", _png_bytes() + b'\n"AI_GENERATED"\n', "image/png")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["verdict"] == "supported_signal_detected"
    assert payload["signals"]["gb45438"]["detected"] is True
    assert payload["signals"]["gb45438"]["details"]["matched_terms"] == ["AI_GENERATED"]
