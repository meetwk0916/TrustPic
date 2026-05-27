from app.models import EvidenceSignal, InterpretationEvidence, ReportInterpretation, ReportSignals


def build_interpretation(signals: ReportSignals) -> ReportInterpretation:
    return ReportInterpretation(
        confidence_label=confidence_label(signals),
        conclusion=human_conclusion(signals),
        evidence_chain=[
            ai_marker_evidence(signals.gb45438, signals.c2pa),
            ela_evidence(signals.ela),
            source_record_evidence(signals.c2pa, signals.exif),
            photo_metadata_evidence(signals.exif),
        ],
        limits=[
            "没有发现可读证据，不等于图片一定不是 AI 生成。",
            "局部差异只是线索，不能单独证明图片被篡改、P 图或 AI 生成。",
            "来源记录能说明文件里带有可验证信息，但不等于图片内容一定真实或上下文完整。",
        ],
    )


def human_conclusion(signals: ReportSignals) -> str:
    if signals.gb45438.detected:
        return "发现这张图带有 AI 生成相关标记。"
    if ai_related_source_record(signals.c2pa):
        return "图片来源记录指向 AI 生成来源。"
    if signals.ela.detected:
        return "发现局部区域存在差异集中线索。"
    if signals.c2pa.detected:
        if c2pa_validation_state(signals.c2pa) == "Valid":
            return "发现这张图带有可验证的来源记录。"
        return "发现图片来源记录，但验证状态需要留意。"
    if signals.exif.detected:
        return "发现这张图包含拍摄或保存信息，但没有发现 AI 相关来源或标记。"
    return "没有发现 TrustPic v0 能读取的 AI 来源、AI 标记或局部差异线索。"


def confidence_label(signals: ReportSignals) -> str:
    if signals.gb45438.detected:
        return "强"
    if ai_related_source_record(signals.c2pa) and c2pa_validation_state(signals.c2pa) == "Valid":
        return "强"
    if ai_related_source_record(signals.c2pa):
        return "较强"
    if signals.c2pa.detected and c2pa_validation_state(signals.c2pa) == "Valid" and not signals.ela.detected:
        return "强"
    if signals.c2pa.detected:
        return "较强"
    if signals.ela.detected:
        return "中等"
    if rich_exif(signals.exif):
        return "较强"
    if signals.exif.detected:
        return "中等"
    return "有限"


def ai_marker_evidence(signal: EvidenceSignal, c2pa_signal: EvidenceSignal | None = None) -> InterpretationEvidence:
    if not signal.checked:
        return InterpretationEvidence(
            key="gb45438",
            title="AI 生成标记",
            status_label="无法分析",
            summary="这次没有完成 AI 生成标记检查。",
            means="TrustPic 没有得到这一项证据。",
            does_not_mean="这不代表图片没有 AI 生成标记。",
            details=signal.details,
        )
    if signal.detected:
        fields = signal.details.get("xmp_fields", {}) if isinstance(signal.details, dict) else {}
        field_names = ", ".join(sorted(fields.keys())) if isinstance(fields, dict) and fields else "文件标记"
        return InterpretationEvidence(
            key="gb45438",
            title="AI 生成标记",
            status_label="支持证据",
            summary="发现 AI 生成相关标记。",
            means=f"文件里包含 TrustPic v0 可识别的 AI 生成标记：{field_names}。",
            does_not_mean="这不说明图片的每个局部都由 AI 生成，也不说明标记一定来自权威平台。",
            details=signal.details,
        )
    if c2pa_signal is not None and ai_related_source_record(c2pa_signal):
        return InterpretationEvidence(
            key="gb45438",
            title="AI 生成标记",
            status_label="未发现",
            summary="没有发现国内显式 AI 标记；但来源记录已经指向 AI 生成来源。",
            means="这一项只看 GB 45438/TC260 或通用 AIGC 标记；OpenAI、Gemini、NotebookLM 这类来源记录会在图片来源记录里展示。",
            does_not_mean="这不代表没有 AI 证据；对这张图，应把图片来源记录作为主要 AI 相关证据。",
            details=signal.details,
        )
    return InterpretationEvidence(
        key="gb45438",
        title="AI 生成标记",
        status_label="未发现",
        summary="没有发现 TrustPic v0 可识别的 AI 生成标记。",
        means="文件里没有检测到当前支持的 GB 45438/TC260 或 AIGC 标记。",
        does_not_mean="这不代表图片一定不是 AI 生成；很多平台会移除或不写入这类标记。",
        details=signal.details,
    )


def ela_evidence(signal: EvidenceSignal) -> InterpretationEvidence:
    mean_error = signal.details.get("mean_error") if isinstance(signal.details, dict) else None
    anomaly_count = signal.details.get("local_anomaly_count") if isinstance(signal.details, dict) else None
    anomaly_ratio = signal.details.get("local_anomaly_ratio") if isinstance(signal.details, dict) else None
    if not signal.checked:
        return InterpretationEvidence(
            key="ela",
            title="局部差异线索",
            status_label="无法分析",
            summary="这次没有完成局部差异检查。",
            means="TrustPic 没有得到这一项证据。",
            does_not_mean="这不代表图片没有局部编辑或异常差异。",
            details=signal.details,
        )
    if signal.detected:
        return InterpretationEvidence(
            key="ela",
            title="局部差异线索",
            status_label="需留意",
            summary="发现局部区域的差异更集中。",
            means=f"ELA tile 分析发现 {anomaly_count} 个局部异常块，占比 {anomaly_ratio}，全图 mean error 为 {mean_error}。这些区域和全图整体压缩响应不太一致。",
            does_not_mean="这只是局部差异线索，不能单独证明图片被篡改、P 图或由 AI 生成。",
            details=signal.details,
        )
    return InterpretationEvidence(
        key="ela",
        title="局部差异线索",
        status_label="未发现",
        summary="没有发现局部差异集中线索。",
        means=f"没有发现少量区域明显偏离整体压缩模式；全图 mean error 为 {mean_error}。",
        does_not_mean="截图、平台转码和整体压缩都很常见；没有局部差异线索，也不代表图片一定没有被编辑。",
        details=signal.details,
    )


def source_record_evidence(signal: EvidenceSignal, exif_signal: EvidenceSignal | None = None) -> InterpretationEvidence:
    validation_state = c2pa_validation_state(signal)
    ai_source = ai_related_source_record(signal)
    google_source = google_source_record(signal)
    source_name = source_record_name(signal)
    originality = file_originality(signal, exif_signal)
    if not signal.checked:
        return InterpretationEvidence(
            key="c2pa",
            title="图片来源记录",
            status_label="无法分析",
            summary=source_record_summary("这次没有完成图片来源记录检查。", originality),
            means=f"TrustPic 没有得到这一项证据。{originality_sentence(originality)}",
            does_not_mean="这不代表图片没有来源记录，也不代表当前文件一定是原始文件。",
            details=source_record_details(signal, originality),
        )
    if signal.detected and ai_source:
        source_text = f"，来源线索包括 {source_name}" if source_name else ""
        if validation_state == "Valid":
            return InterpretationEvidence(
                key="c2pa",
                title="图片来源记录",
                status_label="支持证据",
                summary=source_record_summary("发现可验证的 AI 相关来源记录。", originality),
                means=f"文件里有可读取、签名有效的来源记录，且来源指向 AI 相关工具或签发方{source_text}。{originality_sentence(originality)}",
                does_not_mean="这不说明图片的每个局部都由 AI 生成，也不保证图片内容一定真实、完整或没有被断章取义。",
                details=source_record_details(signal, originality),
            )
        return InterpretationEvidence(
            key="c2pa",
            title="图片来源记录",
            status_label="需留意",
            summary=source_record_summary("发现 AI 相关来源记录，但验证状态不完整或异常。", originality),
            means=f"文件里有 AI 相关来源线索，但签名验证状态为 {validation_state or '未知'}{source_text}。{originality_sentence(originality)}",
            does_not_mean="这不代表来源记录一定可信，也不等于图片内容一定造假。",
            details=source_record_details(signal, originality),
        )
    if signal.detected and google_source:
        source_text = f"，来源线索包括 {source_name}" if source_name else ""
        return InterpretationEvidence(
            key="c2pa",
            title="图片来源记录",
            status_label="需留意",
            summary=source_record_summary("发现 Google 图片来源记录，但没有看到明确的 AI 产品名。", originality),
            means=f"文件里有 Google 相关来源记录，验证状态为 {validation_state or '未知'}{source_text}。{originality_sentence(originality)}",
            does_not_mean="这不能单独说明图片由 NotebookLM、Gemini 或 Imagen 生成；需要看到更具体的产品名、生成工具或水印证据。",
            details=source_record_details(signal, originality),
        )
    if signal.detected and validation_state == "Valid":
        issuer = signal.details.get("signature_issuer") if isinstance(signal.details, dict) else None
        issuer_text = f"，签发方为 {issuer}" if issuer else ""
        return InterpretationEvidence(
            key="c2pa",
            title="图片来源记录",
            status_label="支持证据",
            summary=source_record_summary("发现可验证的图片来源记录。", originality),
            means=f"文件里包含可读取的来源记录，签名验证状态为 Valid{issuer_text}。{originality_sentence(originality)}",
            does_not_mean="这不保证图片内容一定真实，也不保证图片没有被断章取义。",
            details=source_record_details(signal, originality),
        )
    if signal.detected:
        return InterpretationEvidence(
            key="c2pa",
            title="图片来源记录",
            status_label="需留意",
            summary=source_record_summary("发现图片来源记录，但验证状态不完整或异常。", originality),
            means=f"文件里有来源记录，验证状态为 {validation_state or '未知'}。{originality_sentence(originality)}",
            does_not_mean="这不代表图片一定造假，也不代表来源记录一定可信。",
            details=source_record_details(signal, originality),
        )
    return InterpretationEvidence(
        key="c2pa",
        title="图片来源记录",
        status_label="未发现",
        summary=source_record_summary("没有发现可读取的图片来源记录。", originality),
        means=f"文件里没有检测到 TrustPic v0 可读取的 C2PA 来源记录。{originality_sentence(originality)}",
        does_not_mean="这种情况很常见，尤其是截图、转发或平台下载后的图片；它不代表图片真实，也不代表图片一定是 AI 生成或被篡改。",
        details=source_record_details(signal, originality),
    )


def photo_metadata_evidence(signal: EvidenceSignal) -> InterpretationEvidence:
    field_count = exif_field_count(signal)
    if not signal.checked:
        return InterpretationEvidence(
            key="exif",
            title="拍摄/编辑信息",
            status_label="无法分析",
            summary="这次没有完成拍摄/编辑信息检查。",
            means="TrustPic 没有得到这一项证据。",
            does_not_mean="这不代表图片没有元数据。",
            details=signal.details,
        )
    if signal.detected:
        return InterpretationEvidence(
            key="exif",
            title="拍摄/编辑信息",
            status_label="支持证据",
            summary=f"发现 {field_count} 项拍摄或保存信息。",
            means="文件里包含 EXIF 元数据，可能包括相机、软件、拍摄参数或保存信息。",
            does_not_mean="EXIF 可以被修改或移除；它不能单独证明图片真实，也不能排除后期处理。",
            details=signal.details,
        )
    return InterpretationEvidence(
        key="exif",
        title="拍摄/编辑信息",
        status_label="未发现",
        summary="没有发现拍摄或保存信息。",
        means="文件里没有检测到 EXIF 元数据。",
        does_not_mean="很多截图、平台转发图或压缩图都没有 EXIF；这不代表图片一定可疑。",
        details=signal.details,
    )


def c2pa_validation_state(signal: EvidenceSignal) -> str | None:
    if not isinstance(signal.details, dict):
        return None
    value = signal.details.get("validation_state")
    return str(value) if value is not None else None


def ai_related_source_record(signal: EvidenceSignal) -> bool:
    if not signal.detected or not isinstance(signal.details, dict):
        return False
    if signal.details.get("ai_related") is True:
        return True
    searchable_values = [
        signal.details.get("signature_issuer"),
        signal.details.get("signature_common_name"),
        signal.details.get("claim_generator"),
        signal.details.get("title"),
    ]
    searchable = " ".join(str(value).lower() for value in searchable_values if value)
    ai_terms = (
        "openai",
        "dall-e",
        "dalle",
        "aigc",
        "ai-generated",
        "generated by ai",
        "midjourney",
        "gemini",
        "notebooklm",
        "imagen",
        "synthid",
        "nano banana",
    )
    return any(term in searchable for term in ai_terms)


def google_source_record(signal: EvidenceSignal) -> bool:
    if not signal.detected or not isinstance(signal.details, dict):
        return False
    values = [
        signal.details.get("signature_issuer"),
        signal.details.get("signature_common_name"),
        signal.details.get("claim_generator"),
    ]
    searchable = " ".join(str(value).lower() for value in values if value)
    return "google" in searchable and not ai_related_source_record(signal)


def source_record_name(signal: EvidenceSignal) -> str | None:
    if not isinstance(signal.details, dict):
        return None
    for key in ("signature_issuer", "signature_common_name", "claim_generator"):
        value = signal.details.get(key)
        if value:
            return str(value)
    return None


def source_record_details(signal: EvidenceSignal, originality: dict) -> dict:
    details = dict(signal.details) if isinstance(signal.details, dict) else {}
    details["originality_label"] = originality["label"]
    details["originality_reasons"] = originality["reasons"]
    return details


def source_record_summary(base: str, originality: dict) -> str:
    return f"{base}当前文件{originality['label']}。"


def originality_sentence(originality: dict) -> str:
    reasons = originality.get("reasons") or []
    reason_text = "；".join(str(reason) for reason in reasons)
    if reason_text:
        return f"当前文件原始性判断：{originality['label']}，因为{reason_text}。"
    return f"当前文件原始性判断：{originality['label']}。"


def file_originality(c2pa_signal: EvidenceSignal, exif_signal: EvidenceSignal | None) -> dict:
    if not c2pa_signal.checked:
        return {
            "label": "无法判断",
            "reasons": ["图片来源记录检查未完成"],
        }

    validation_state = c2pa_validation_state(c2pa_signal)
    if c2pa_signal.detected and validation_state == "Valid":
        return {
            "label": "原始性较强",
            "reasons": ["文件带有可读取且签名有效的来源记录"],
        }

    if c2pa_signal.detected:
        return {
            "label": "原始性有限",
            "reasons": ["文件带有来源记录，但签名验证状态不完整或异常"],
        }

    if exif_signal is not None and rich_exif(exif_signal):
        return {
            "label": "原始性较强",
            "reasons": ["文件保留了较多拍摄或保存信息"],
        }

    if exif_signal is not None and exif_signal.detected:
        return {
            "label": "原始性有限",
            "reasons": ["文件保留了部分拍摄或保存信息，但没有可读取的来源记录"],
        }

    return {
        "label": "原始性有限",
        "reasons": ["没有可读取的来源记录或 EXIF；截图、转发、转码或二次保存都可能造成这种结果"],
    }


def exif_field_count(signal: EvidenceSignal) -> int:
    if not isinstance(signal.details, dict):
        return 0
    value = signal.details.get("field_count")
    return int(value) if isinstance(value, int) else 0


def rich_exif(signal: EvidenceSignal) -> bool:
    return signal.detected and exif_field_count(signal) >= 5
