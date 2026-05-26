import base64
from io import BytesIO
from statistics import mean, pstdev

from PIL import Image, ImageChops, ImageEnhance, ImageStat

from app.models import EvidenceSignal

JPEG_QUALITY = 90
AMPLIFICATION = 15
TILE_SIZE = 32
LOCAL_TILE_MIN_ERROR = 28.0
LOCAL_RATIO_THRESHOLD = 2.5
LOCAL_MIN_TILE_COUNT = 2


def inspect_ela(image: Image.Image) -> tuple[EvidenceSignal, str | None]:
    rgb = image.convert("RGB")
    buffer = BytesIO()
    rgb.save(buffer, "JPEG", quality=JPEG_QUALITY)
    buffer.seek(0)

    compressed = Image.open(buffer).convert("RGB")
    diff = ImageChops.difference(rgb, compressed)
    enhanced = ImageEnhance.Brightness(diff).enhance(AMPLIFICATION)
    mean_error = sum(ImageStat.Stat(enhanced).mean) / 3
    local_analysis = analyze_local_differences(enhanced)
    detected = local_analysis["local_anomaly_detected"]

    out = BytesIO()
    enhanced.save(out, format="JPEG", quality=90)
    data_url = "data:image/jpeg;base64," + base64.b64encode(out.getvalue()).decode("ascii")

    return (
        EvidenceSignal(
            detected=detected,
            status="review" if detected else "low_signal",
            summary=(
                "ELA found a concentrated local difference pattern."
                if detected
                else "ELA did not find a concentrated local difference pattern."
            ),
            details={
                "mean_error": round(mean_error, 2),
                "jpeg_quality": JPEG_QUALITY,
                "amplification": AMPLIFICATION,
                **local_analysis,
            },
        ),
        data_url,
    )


def analyze_local_differences(image: Image.Image) -> dict:
    grayscale = image.convert("L")
    width, height = grayscale.size
    tiles = []

    for top in range(0, height, TILE_SIZE):
        for left in range(0, width, TILE_SIZE):
            right = min(left + TILE_SIZE, width)
            bottom = min(top + TILE_SIZE, height)
            if right - left < TILE_SIZE // 2 or bottom - top < TILE_SIZE // 2:
                continue
            crop = grayscale.crop((left, top, right, bottom))
            tile_error = ImageStat.Stat(crop).mean[0]
            tiles.append(
                {
                    "x": left,
                    "y": top,
                    "width": right - left,
                    "height": bottom - top,
                    "mean_error": tile_error,
                }
            )

    if not tiles:
        return {
            "tile_size": TILE_SIZE,
            "tile_count": 0,
            "local_anomaly_detected": False,
            "local_anomaly_count": 0,
            "local_anomaly_ratio": 0.0,
            "local_threshold": LOCAL_TILE_MIN_ERROR,
            "top_tiles": [],
        }

    tile_errors = [tile["mean_error"] for tile in tiles]
    average_error = mean(tile_errors)
    spread = pstdev(tile_errors) if len(tile_errors) > 1 else 0.0
    ratio_threshold = average_error * LOCAL_RATIO_THRESHOLD
    local_threshold = max(LOCAL_TILE_MIN_ERROR, ratio_threshold)
    anomaly_tiles = [tile for tile in tiles if tile["mean_error"] >= local_threshold]
    anomaly_ratio = len(anomaly_tiles) / len(tiles)
    local_anomaly_detected = len(anomaly_tiles) >= LOCAL_MIN_TILE_COUNT and anomaly_ratio <= 0.25

    top_tiles = sorted(tiles, key=lambda item: item["mean_error"], reverse=True)[:5]
    return {
        "tile_size": TILE_SIZE,
        "tile_count": len(tiles),
        "tile_mean_error": round(average_error, 2),
        "tile_error_stddev": round(spread, 2),
        "local_threshold": round(local_threshold, 2),
        "local_anomaly_detected": local_anomaly_detected,
        "local_anomaly_count": len(anomaly_tiles),
        "local_anomaly_ratio": round(anomaly_ratio, 4),
        "local_anomaly_tiles": [serialize_tile(tile) for tile in anomaly_tiles[:12]],
        "top_tiles": [serialize_tile(tile) for tile in top_tiles],
    }


def serialize_tile(tile: dict) -> dict:
    return {
        "x": tile["x"],
        "y": tile["y"],
        "width": tile["width"],
        "height": tile["height"],
        "mean_error": round(tile["mean_error"], 2),
    }
