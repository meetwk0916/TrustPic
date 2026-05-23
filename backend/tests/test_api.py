from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app

client = TestClient(app)


def _png_bytes() -> bytes:
    image = Image.new("RGB", (64, 64), color=(120, 40, 80))
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

