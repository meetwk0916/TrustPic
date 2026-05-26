from app.models import EvidenceSignal, ReportSignals
from app.services.interpretation import build_interpretation


def _signal(status: str = "absent", detected: bool = False, details: dict | None = None) -> EvidenceSignal:
    return EvidenceSignal(status=status, detected=detected, details=details or {}, summary="")


def test_openai_c2pa_source_record_becomes_ai_source_conclusion() -> None:
    signals = ReportSignals(
        gb45438=_signal(details={"matched_terms": []}),
        ela=_signal(status="ok", details={"mean_error": 0.4}),
        c2pa=_signal(
            status="detected",
            detected=True,
            details={
                "signature_issuer": "OpenAI",
                "signature_common_name": "OpenAI Image Signing",
                "validation_state": "Valid",
                "ai_related": True,
            },
        ),
        exif=_signal(),
    )

    interpretation = build_interpretation(signals)

    assert interpretation.confidence_label == "强"
    assert interpretation.conclusion == "图片来源记录显示这张图与 AI 生成来源有关。"
    assert interpretation.evidence_chain[0].title == "AI 生成标记"
    assert interpretation.evidence_chain[0].status_label == "未发现"
    assert "来源记录里有 AI 相关证据" in interpretation.evidence_chain[0].summary
    source_record = interpretation.evidence_chain[2]
    assert source_record.title == "图片来源记录"
    assert source_record.status_label == "支持证据"
    assert source_record.summary == "发现可验证的 AI 相关图片来源记录。"
    assert "OpenAI" in source_record.means


def test_notebooklm_google_c2pa_source_record_becomes_ai_source_conclusion() -> None:
    signals = ReportSignals(
        gb45438=_signal(details={"matched_terms": []}),
        ela=_signal(status="ok", details={"mean_error": 0.4}),
        c2pa=_signal(
            status="detected",
            detected=True,
            details={
                "signature_issuer": "Google Trust Services",
                "signature_common_name": "NotebookLM",
                "claim_generator": "NotebookLM Video Overview",
                "validation_state": "Valid",
                "ai_related": True,
            },
        ),
        exif=_signal(),
    )

    interpretation = build_interpretation(signals)

    assert interpretation.confidence_label == "强"
    assert interpretation.conclusion == "图片来源记录显示这张图与 AI 生成来源有关。"
    source_record = interpretation.evidence_chain[2]
    assert source_record.status_label == "支持证据"
    assert source_record.summary == "发现可验证的 AI 相关图片来源记录。"
    assert "Google Trust Services" in source_record.means


def test_google_c2pa_without_ai_product_name_stays_attention_level() -> None:
    signals = ReportSignals(
        gb45438=_signal(details={"matched_terms": []}),
        ela=_signal(status="ok", details={"mean_error": 0.4}),
        c2pa=_signal(
            status="detected",
            detected=True,
            details={
                "signature_issuer": "Google Trust Services",
                "signature_common_name": "Google",
                "validation_state": "Valid",
                "ai_related": False,
            },
        ),
        exif=_signal(),
    )

    interpretation = build_interpretation(signals)

    assert interpretation.confidence_label == "强"
    assert interpretation.conclusion == "发现这张图带有可验证的来源记录。"
    source_record = interpretation.evidence_chain[2]
    assert source_record.status_label == "需留意"
    assert source_record.summary == "发现 Google 图片来源记录，但没有看到明确的 AI 产品名。"
