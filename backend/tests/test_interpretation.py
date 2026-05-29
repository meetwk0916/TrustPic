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
    assert interpretation.conclusion == "图片来源记录指向 AI 生成来源。"
    assert interpretation.evidence_chain[0].title == "AI 生成标记"
    assert interpretation.evidence_chain[0].status_label == "未发现"
    assert "来源记录已经指向 AI 生成来源" in interpretation.evidence_chain[0].summary
    assert "图片来源记录作为主要 AI 相关证据" in interpretation.evidence_chain[0].does_not_mean
    source_record = interpretation.evidence_chain[2]
    assert source_record.title == "图片来源记录"
    assert source_record.status_label == "支持证据"
    assert source_record.summary == "发现可验证的 AI 相关来源记录。当前文件原始性较强。"
    assert "OpenAI" in source_record.means
    assert "当前文件原始性判断：原始性较强" in source_record.means
    assert source_record.details["originality_label"] == "原始性较强"


def test_openai_c2pa_source_record_can_render_english_interpretation() -> None:
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

    interpretation = build_interpretation(signals, locale="en-US")

    assert interpretation.confidence_label == "Strong"
    assert interpretation.conclusion == "The source record points to an AI generation source."
    assert interpretation.evidence_chain[0].title == "AI marker"
    assert interpretation.evidence_chain[0].status_label == "Not found"
    source_record = interpretation.evidence_chain[2]
    assert source_record.title == "Source record"
    assert source_record.status_label == "Supporting evidence"
    assert source_record.summary == "A verifiable AI-related source record was found. Current file: Strong originality evidence."
    assert "OpenAI" in source_record.means
    assert "File originality reading: Strong originality evidence" in source_record.means
    assert source_record.details["originality_label"] == "Strong originality evidence"


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
    assert interpretation.conclusion == "图片来源记录指向 AI 生成来源。"
    source_record = interpretation.evidence_chain[2]
    assert source_record.status_label == "支持证据"
    assert source_record.summary == "发现可验证的 AI 相关来源记录。当前文件原始性较强。"
    assert "Google Trust Services" in source_record.means
    assert source_record.details["originality_label"] == "原始性较强"


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
    assert source_record.summary == "发现 Google 图片来源记录，但没有看到明确的 AI 产品名。当前文件原始性较强。"
    assert source_record.title == "图片来源记录"
    assert source_record.details["originality_label"] == "原始性较强"


def test_ela_uses_local_difference_language_not_global_compression_warning() -> None:
    signals = ReportSignals(
        gb45438=_signal(details={"matched_terms": []}),
        ela=_signal(
            status="review",
            detected=True,
            details={
                "mean_error": 8.4,
                "local_anomaly_detected": True,
                "local_anomaly_count": 3,
                "local_anomaly_ratio": 0.08,
            },
        ),
        c2pa=_signal(),
        exif=_signal(),
    )

    interpretation = build_interpretation(signals)

    assert interpretation.conclusion == "发现局部区域存在差异集中线索。"
    ela_evidence = interpretation.evidence_chain[1]
    assert ela_evidence.title == "局部差异线索"
    assert ela_evidence.status_label == "需留意"
    assert "3 个局部异常块" in ela_evidence.means
    assert "不能单独证明图片被篡改、P 图或由 AI 生成" in ela_evidence.does_not_mean


def test_absent_source_record_reports_limited_originality_without_claiming_safety() -> None:
    signals = ReportSignals(
        gb45438=_signal(details={"matched_terms": []}),
        ela=_signal(status="ok", details={"mean_error": 0.4}),
        c2pa=_signal(),
        exif=_signal(),
    )

    interpretation = build_interpretation(signals)

    source_record = interpretation.evidence_chain[2]
    assert source_record.title == "图片来源记录"
    assert source_record.status_label == "未发现"
    assert source_record.summary == "没有发现可读取的图片来源记录。当前文件原始性有限。"
    assert "当前文件原始性判断：原始性有限" in source_record.means
    assert "截图、转发、转码或二次保存" in source_record.means
    assert source_record.details["originality_label"] == "原始性有限"


def test_rich_exif_can_raise_originality_when_source_record_is_absent() -> None:
    signals = ReportSignals(
        gb45438=_signal(details={"matched_terms": []}),
        ela=_signal(status="ok", details={"mean_error": 0.4}),
        c2pa=_signal(),
        exif=_signal(
            status="present",
            detected=True,
            details={
                "field_count": 6,
                "fields": {
                    "Make": "TrustPic Camera",
                    "Model": "V0",
                    "DateTimeOriginal": "2026:05:29 12:00:00",
                    "ExposureTime": "1/60",
                    "FNumber": "2.8",
                    "ISO": "100",
                },
            },
        ),
    )

    interpretation = build_interpretation(signals)

    source_record = interpretation.evidence_chain[2]
    assert source_record.title == "图片来源记录"
    assert source_record.status_label == "未发现"
    assert "当前文件原始性判断：原始性较强" in source_record.means
    assert source_record.details["originality_label"] == "原始性较强"


def test_software_only_exif_does_not_become_capture_evidence() -> None:
    signals = ReportSignals(
        gb45438=_signal(details={"matched_terms": []}),
        ela=_signal(status="ok", details={"mean_error": 0.4}),
        c2pa=_signal(),
        exif=_signal(
            status="present",
            detected=True,
            details={
                "field_count": 3,
                "fields": {
                    "ExifOffset": "58",
                    "Orientation": "1",
                    "Software": "Picasa",
                },
            },
        ),
    )

    interpretation = build_interpretation(signals)

    assert interpretation.confidence_label == "有限"
    assert interpretation.conclusion == "没有发现 TrustPic v0 能读取的 AI 来源、AI 标记或局部差异线索。"
    source_record = interpretation.evidence_chain[2]
    assert source_record.details["originality_label"] == "原始性有限"
    assert "截图、转发、转码或二次保存" in source_record.means
    exif_evidence = interpretation.evidence_chain[3]
    assert exif_evidence.title == "拍摄/编辑信息"
    assert exif_evidence.status_label == "需留意"
    assert exif_evidence.summary == "只发现软件保存或文件结构类信息，未发现相机拍摄字段。"
    assert "Software=Picasa" in exif_evidence.means


def test_software_only_exif_can_render_english_interpretation() -> None:
    signals = ReportSignals(
        gb45438=_signal(details={"matched_terms": []}),
        ela=_signal(status="ok", details={"mean_error": 0.4}),
        c2pa=_signal(),
        exif=_signal(
            status="present",
            detected=True,
            details={
                "field_count": 3,
                "fields": {
                    "ExifOffset": "58",
                    "Orientation": "1",
                    "Software": "Picasa",
                },
            },
        ),
    )

    interpretation = build_interpretation(signals, locale="en-US")

    assert interpretation.confidence_label == "Limited"
    assert interpretation.conclusion == "No readable AI source, AI marker, or local-difference clue was found by TrustPic v0."
    exif_evidence = interpretation.evidence_chain[3]
    assert exif_evidence.status_label == "Needs attention"
    assert exif_evidence.summary == "Only software-save or file-structure metadata was found; no camera-capture field was found."
    assert "Software=Picasa" in exif_evidence.means
