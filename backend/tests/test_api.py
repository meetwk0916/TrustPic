from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from app.services import analyze as analyze_service
from app.main import app

client = TestClient(app)


def _png_bytes(size: tuple[int, int] = (64, 64)) -> bytes:
    image = Image.new("RGB", size, color=(120, 40, 80))
    out = BytesIO()
    image.save(out, format="PNG")
    return out.getvalue()


def _jpeg_with_exif_bytes() -> bytes:
    image = Image.new("RGB", (80, 80), color=(96, 132, 166))
    exif = Image.Exif()
    exif[271] = "TrustPic Camera"
    exif[272] = "V0 EXIF Sample"
    out = BytesIO()
    image.save(out, format="JPEG", quality=92, exif=exif)
    return out.getvalue()


def _ela_review_jpeg_bytes() -> bytes:
    image = Image.new("RGB", (160, 120), color=(128, 128, 128))
    draw = ImageDraw.Draw(image)
    for x in range(48, 112, 2):
        color = (20, 20, 20) if x % 4 == 0 else (235, 235, 235)
        draw.rectangle((x, 32, x + 1, 96), fill=color)
    for y in range(32, 96, 4):
        draw.line((48, y, 111, y), fill=(230, 40, 40), width=1)
    out = BytesIO()
    image.save(out, format="JPEG", quality=35)
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
    assert payload["interpretation"]["confidence_label"] == "有限"
    assert payload["interpretation"]["conclusion"] == "没有发现 TrustPic v0 能读取的 AI 来源、AI 标记或局部差异线索。"
    assert [item["title"] for item in payload["interpretation"]["evidence_chain"]] == [
        "AI 生成标记",
        "局部差异线索",
        "图片来源记录",
        "拍摄/编辑信息",
    ]
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
    assert payload["interpretation"]["confidence_label"] == "强"
    assert payload["interpretation"]["conclusion"] == "发现这张图带有 AI 生成相关标记。"
    assert payload["interpretation"]["evidence_chain"][0]["title"] == "AI 生成标记"
    assert payload["interpretation"]["evidence_chain"][0]["status_label"] == "支持证据"


def test_gb45438_tc260_xmp_fields_change_verdict_to_supported_signal() -> None:
    xmp_packet = b"""
<x:xmpmeta xmlns:x="adobe:ns:meta/">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description xmlns:AIGC="http://www.tc260.org.cn/ns/AIGC/1.0/">
      <AIGC:Label>AIGC</AIGC:Label>
      <AIGC:ContentProducer>TrustPic Sample Generator</AIGC:ContentProducer>
      <AIGC:ProduceID>sample-produce-id</AIGC:ProduceID>
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>
"""
    response = client.post(
        "/api/v1/analyze",
        files={"file": ("gb-xmp.png", _png_bytes() + xmp_packet, "image/png")},
    )

    assert response.status_code == 200
    payload = response.json()
    gb45438 = payload["signals"]["gb45438"]
    assert payload["verdict"] == "supported_signal_detected"
    assert gb45438["detected"] is True
    assert gb45438["details"]["tc260_namespace_detected"] is True
    assert gb45438["details"]["xmp_fields"]["Label"] == "AIGC"
    assert gb45438["details"]["xmp_fields"]["ContentProducer"] == "TrustPic Sample Generator"


def test_exif_jpeg_reports_metadata_fields() -> None:
    response = client.post(
        "/api/v1/analyze",
        files={"file": ("camera.jpg", _jpeg_with_exif_bytes(), "image/jpeg")},
    )

    assert response.status_code == 200
    payload = response.json()
    exif = payload["signals"]["exif"]
    assert exif["detected"] is True
    assert exif["status"] == "present"
    assert exif["details"]["fields"]["Make"] == "TrustPic Camera"
    assert exif["details"]["fields"]["Model"] == "V0 EXIF Sample"
    assert payload["interpretation"]["confidence_label"] == "中等"
    assert payload["interpretation"]["conclusion"] == "发现这张图包含拍摄或保存信息，但没有发现 AI 相关来源或标记。"
    exif_evidence = payload["interpretation"]["evidence_chain"][3]
    assert exif_evidence["title"] == "拍摄/编辑信息"
    assert exif_evidence["status_label"] == "支持证据"


def test_high_error_jpeg_returns_review_recommended() -> None:
    response = client.post(
        "/api/v1/analyze",
        files={"file": ("ela-review.jpg", _ela_review_jpeg_bytes(), "image/jpeg")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["verdict"] == "review_recommended"
    assert payload["signals"]["ela"]["detected"] is True
    assert payload["signals"]["ela"]["status"] == "review"
    assert payload["signals"]["ela"]["details"]["local_anomaly_detected"] is True
    assert payload["signals"]["ela"]["details"]["local_anomaly_count"] >= 2
    assert payload["interpretation"]["confidence_label"] == "中等"
    assert payload["interpretation"]["conclusion"] == "发现局部区域存在差异集中线索。"
    ela_evidence = payload["interpretation"]["evidence_chain"][1]
    assert ela_evidence["title"] == "局部差异线索"
    assert ela_evidence["status_label"] == "需留意"
