from app.models import EvidenceSignal

SIGNATURE_TERMS = [
    b'"AIGC"',
    b'"aigc"',
    b'"aigc_info"',
    b"GB 45438",
    b"GB45438",
    b"AI_GENERATED",
]


def inspect_gb45438(image_bytes: bytes) -> EvidenceSignal:
    matches = [term.decode("utf-8", errors="ignore") for term in SIGNATURE_TERMS if term in image_bytes]

    return EvidenceSignal(
        detected=bool(matches),
        status="detected" if matches else "absent",
        summary=(
            "Possible GB 45438/AIGC byte-level marker was found."
            if matches
            else "No GB 45438/AIGC byte-level marker was found by v0 scan."
        ),
        details={"matched_terms": matches},
    )

