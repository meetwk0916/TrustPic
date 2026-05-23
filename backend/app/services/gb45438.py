import re
from html import unescape

from app.models import EvidenceSignal

TC260_AIGC_NAMESPACE = "http://www.tc260.org.cn/ns/AIGC/1.0/"
TC260_FIELDS = [
    "Label",
    "ContentProducer",
    "ProduceID",
    "ReservedCode1",
    "ContentPropagator",
    "PropagateID",
    "ReservedCode2",
]
SIGNATURE_TERMS = [
    b'"AIGC"',
    b'"aigc"',
    b'"aigc_info"',
    b"GB 45438",
    b"GB45438",
    b"AI_GENERATED",
    TC260_AIGC_NAMESPACE.encode("utf-8"),
]


def inspect_gb45438(image_bytes: bytes) -> EvidenceSignal:
    text = image_bytes.decode("utf-8", errors="ignore")
    matched_terms = [term.decode("utf-8", errors="ignore") for term in SIGNATURE_TERMS if term in image_bytes]
    xmp_fields = _extract_tc260_xmp_fields(text)
    detected = bool(matched_terms or xmp_fields)

    return EvidenceSignal(
        detected=detected,
        status="detected" if detected else "absent",
        summary=(
            "Possible GB 45438/AIGC metadata or byte-level marker was found."
            if detected
            else "No GB 45438/AIGC metadata or byte-level marker was found by v0 scan."
        ),
        details={
            "matched_terms": matched_terms,
            "tc260_namespace_detected": TC260_AIGC_NAMESPACE in text,
            "xmp_fields": xmp_fields,
            "scan_mode": "tc260_xmp_and_byte_markers",
        },
    )


def _extract_tc260_xmp_fields(text: str) -> dict[str, str]:
    fields = {}
    for field in TC260_FIELDS:
        value = _extract_xml_value(text, field)
        if value:
            fields[field] = value
    return fields


def _extract_xml_value(text: str, local_name: str) -> str | None:
    # Handles both prefixed tags like <AIGC:Label> and default namespace tags like <Label>.
    pattern = rf"<(?:[A-Za-z0-9_.-]+:)?{re.escape(local_name)}\b[^>]*>(.*?)</(?:[A-Za-z0-9_.-]+:)?{re.escape(local_name)}>"
    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    return unescape(re.sub(r"\s+", " ", match.group(1)).strip())[:300]
