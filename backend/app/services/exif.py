from PIL import ExifTags, Image

from app.models import EvidenceSignal


def inspect_exif(image: Image.Image) -> EvidenceSignal:
    exif = image.getexif()
    if not exif:
        return EvidenceSignal(
            detected=False,
            status="absent",
            summary="No EXIF metadata was found.",
            details={"field_count": 0},
        )

    fields = {}
    for tag_id, value in exif.items():
        tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
        if isinstance(value, bytes):
            value = f"<{len(value)} bytes>"
        fields[tag_name] = str(value)[:200]

    return EvidenceSignal(
        detected=True,
        status="present",
        summary=f"EXIF metadata is present with {len(fields)} fields.",
        details={"field_count": len(fields), "fields": fields},
    )
