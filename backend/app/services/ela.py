import base64
from io import BytesIO

from PIL import Image, ImageChops, ImageEnhance, ImageStat

from app.models import EvidenceSignal

JPEG_QUALITY = 90
AMPLIFICATION = 15
REVIEW_THRESHOLD = 12.0


def inspect_ela(image: Image.Image) -> tuple[EvidenceSignal, str | None]:
    rgb = image.convert("RGB")
    buffer = BytesIO()
    rgb.save(buffer, "JPEG", quality=JPEG_QUALITY)
    buffer.seek(0)

    compressed = Image.open(buffer).convert("RGB")
    diff = ImageChops.difference(rgb, compressed)
    enhanced = ImageEnhance.Brightness(diff).enhance(AMPLIFICATION)
    mean_error = sum(ImageStat.Stat(enhanced).mean) / 3
    detected = mean_error > REVIEW_THRESHOLD

    out = BytesIO()
    enhanced.save(out, format="JPEG", quality=90)
    data_url = "data:image/jpeg;base64," + base64.b64encode(out.getvalue()).decode("ascii")

    return (
        EvidenceSignal(
            detected=detected,
            status="review" if detected else "low_signal",
            summary=(
                "ELA mean error is above the v0 review threshold."
                if detected
                else "ELA mean error is below the v0 review threshold."
            ),
            details={
                "mean_error": round(mean_error, 2),
                "review_threshold": REVIEW_THRESHOLD,
                "jpeg_quality": JPEG_QUALITY,
                "amplification": AMPLIFICATION,
            },
        ),
        data_url,
    )

