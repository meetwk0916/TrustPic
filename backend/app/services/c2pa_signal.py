import json
from io import BytesIO

from app.models import EvidenceSignal


def inspect_c2pa(image_bytes: bytes, content_type: str) -> EvidenceSignal:
    try:
        import c2pa  # type: ignore
    except Exception:
        return EvidenceSignal(
            checked=False,
            status="unavailable",
            summary="c2pa-python is not installed or could not be imported.",
        )

    try:
        with c2pa.Reader(content_type, BytesIO(image_bytes)) as reader:
            manifest_json = reader.json()
    except Exception as exc:
        return EvidenceSignal(
            status="absent",
            summary="No readable C2PA manifest was found.",
            details={"reason": exc.__class__.__name__},
        )

    try:
        manifest = json.loads(manifest_json)
    except json.JSONDecodeError:
        manifest = {"raw": manifest_json}

    manifest_text = json.dumps(manifest, ensure_ascii=False).lower()
    ai_terms = ["ai", "aigc", "generated", "openai", "dall", "imagen", "midjourney"]
    is_ai_related = any(term in manifest_text for term in ai_terms)

    return EvidenceSignal(
        detected=is_ai_related,
        status="detected" if is_ai_related else "present",
        summary=(
            "C2PA manifest contains AI-related provenance terms."
            if is_ai_related
            else "C2PA manifest is present, but no AI-related term was detected by v0 rules."
        ),
        details={
            "active_manifest": manifest.get("active_manifest"),
            "manifest_count": len(manifest.get("manifests", {})) if isinstance(manifest, dict) else None,
        },
    )
