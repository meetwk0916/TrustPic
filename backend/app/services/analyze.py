from io import BytesIO

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from app.models import AnalyzeResponse, ReportAssets, ReportSignals
from app.services.c2pa_signal import inspect_c2pa
from app.services.ela import inspect_ela
from app.services.exif import inspect_exif
from app.services.gb45438 import inspect_gb45438

MAX_UPLOAD_BYTES = 15 * 1024 * 1024
MAX_PIXELS = 40_000_000
SUPPORTED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


class AnalyzeError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message


async def analyze_upload(file: UploadFile) -> AnalyzeResponse:
    if file.content_type not in SUPPORTED_MIME_TYPES:
        raise AnalyzeError(415, "Unsupported file type. Use JPG, PNG, or WebP.")

    image_bytes = await file.read()
    if not image_bytes:
        raise AnalyzeError(400, "No file content received.")
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise AnalyzeError(413, "File is too large. Maximum size is 15 MB.")

    image = _load_image(image_bytes)
    width, height = image.size
    if width * height > MAX_PIXELS:
        raise AnalyzeError(413, "Image dimensions are too large for v0 analysis.")

    c2pa = inspect_c2pa(image_bytes, file.content_type or "")
    gb45438 = inspect_gb45438(image_bytes)
    exif = inspect_exif(image)
    ela, heatmap_data_url = inspect_ela(image)

    signals = ReportSignals(c2pa=c2pa, gb45438=gb45438, exif=exif, ela=ela)
    verdict, summary, recommendation = _build_verdict(signals)

    limitations = [
        "No supported signal found does not prove the image is authentic.",
        "ELA can suggest compression or edit irregularities, but it does not prove AI generation.",
        "C2PA and metadata can be stripped by screenshots, re-encoding, or platform forwarding.",
        "TrustPic v0 does not run deep-learning AI detector models or SynthID detection.",
    ]

    return AnalyzeResponse(
        verdict=verdict,
        summary=summary,
        signals=signals,
        limitations=limitations,
        recommendation=recommendation,
        assets=ReportAssets(ela_heatmap_data_url=heatmap_data_url),
    )


def _load_image(image_bytes: bytes) -> Image.Image:
    try:
        image = Image.open(BytesIO(image_bytes))
        image.load()
        return image
    except (UnidentifiedImageError, OSError) as exc:
        raise AnalyzeError(400, "Uploaded file could not be decoded as an image.") from exc


def _build_verdict(signals: ReportSignals) -> tuple[str, str, str]:
    if signals.c2pa.detected or signals.gb45438.detected:
        return (
            "supported_signal_detected",
            "Supported provenance or AI-generation metadata was detected.",
            "Review the detected provenance signal and source details before sharing.",
        )

    if signals.ela.detected:
        return (
            "review_recommended",
            "ELA found compression irregularities that may deserve review.",
            "Compare the heatmap with the original image and verify the image context from another source.",
        )

    return (
        "no_supported_signal_found",
        "No supported AI provenance signal or strong ELA irregularity was found.",
        "Treat this as inconclusive, not as proof that the image is real.",
    )

