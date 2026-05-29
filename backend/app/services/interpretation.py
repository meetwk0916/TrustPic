from typing import Literal

from app.models import EvidenceSignal, InterpretationEvidence, ReportInterpretation, ReportSignals


Locale = Literal["zh-CN", "en-US"]

SUPPORTED_LOCALES = {"zh-CN", "en-US"}

COPY = {
    "zh-CN": {
        "confidence": {
            "strong": "强",
            "fairly_strong": "较强",
            "moderate": "中等",
            "limited": "有限",
        },
        "status": {
            "support": "支持证据",
            "warning": "需留意",
            "not_found": "未发现",
            "unavailable": "无法分析",
        },
        "titles": {
            "ai_marker": "AI 生成标记",
            "ela": "局部差异线索",
            "source_record": "图片来源记录",
            "photo_metadata": "拍摄/编辑信息",
        },
        "conclusions": {
            "ai_marker": "发现这张图带有 AI 生成相关标记。",
            "ai_source": "图片来源记录指向 AI 生成来源。",
            "ela": "发现局部区域存在差异集中线索。",
            "valid_source": "发现这张图带有可验证的来源记录。",
            "source_attention": "发现图片来源记录，但验证状态需要留意。",
            "exif": "发现这张图包含相机拍摄相关信息，但没有发现 AI 相关来源或标记。",
            "none": "没有发现 TrustPic v0 能读取的 AI 来源、AI 标记或局部差异线索。",
        },
        "limits": [
            "没有发现可读证据，不等于图片一定不是 AI 生成。",
            "局部差异只是线索，不能单独证明图片被篡改、P 图或 AI 生成。",
            "来源记录能说明文件里带有可验证信息，但不等于图片内容一定真实或上下文完整。",
        ],
        "ai_marker": {
            "unchecked_summary": "这次没有完成 AI 生成标记检查。",
            "unchecked_means": "TrustPic 没有得到这一项证据。",
            "unchecked_does_not": "这不代表图片没有 AI 生成标记。",
            "detected_summary": "发现 AI 生成相关标记。",
            "detected_means": "文件里包含 TrustPic v0 可识别的 AI 生成标记：{field_names}。",
            "detected_does_not": "这不说明图片的每个局部都由 AI 生成，也不说明标记一定来自权威平台。",
            "source_summary": "没有发现国内显式 AI 标记；但来源记录已经指向 AI 生成来源。",
            "source_means": "这一项只看 GB 45438/TC260 或通用 AIGC 标记；OpenAI、Gemini、NotebookLM 这类来源记录会在图片来源记录里展示。",
            "source_does_not": "这不代表没有 AI 证据；对这张图，应把图片来源记录作为主要 AI 相关证据。",
            "absent_summary": "没有发现 TrustPic v0 可识别的 AI 生成标记。",
            "absent_means": "文件里没有检测到当前支持的 GB 45438/TC260 或 AIGC 标记。",
            "absent_does_not": "这不代表图片一定不是 AI 生成；很多平台会移除或不写入这类标记。",
            "field_fallback": "文件标记",
        },
        "ela": {
            "unchecked_summary": "这次没有完成局部差异检查。",
            "unchecked_means": "TrustPic 没有得到这一项证据。",
            "unchecked_does_not": "这不代表图片没有局部编辑或异常差异。",
            "detected_summary": "发现局部区域的差异更集中。",
            "detected_means": "ELA tile 分析发现 {anomaly_count} 个局部异常块，占比 {anomaly_ratio}，全图 mean error 为 {mean_error}。这些区域和全图整体压缩响应不太一致。",
            "detected_does_not": "这只是局部差异线索，不能单独证明图片被篡改、P 图或由 AI 生成。",
            "absent_summary": "没有发现局部差异集中线索。",
            "absent_means": "没有发现少量区域明显偏离整体压缩模式；全图 mean error 为 {mean_error}。",
            "absent_does_not": "截图、平台转码和整体压缩都很常见；没有局部差异线索，也不代表图片一定没有被编辑。",
        },
        "source": {
            "unchecked_summary": "这次没有完成图片来源记录检查。",
            "unchecked_means": "TrustPic 没有得到这一项证据。{originality_sentence}",
            "unchecked_does_not": "这不代表图片没有来源记录，也不代表当前文件一定是原始文件。",
            "ai_valid_summary": "发现可验证的 AI 相关来源记录。",
            "ai_valid_means": "文件里有可读取、签名有效的来源记录，且来源指向 AI 相关工具或签发方{source_text}。{originality_sentence}",
            "ai_valid_does_not": "这不说明图片的每个局部都由 AI 生成，也不保证图片内容一定真实、完整或没有被断章取义。",
            "ai_attention_summary": "发现 AI 相关来源记录，但验证状态不完整或异常。",
            "ai_attention_means": "文件里有 AI 相关来源线索，但签名验证状态为 {validation_state}{source_text}。{originality_sentence}",
            "ai_attention_does_not": "这不代表来源记录一定可信，也不等于图片内容一定造假。",
            "google_summary": "发现 Google 图片来源记录，但没有看到明确的 AI 产品名。",
            "google_means": "文件里有 Google 相关来源记录，验证状态为 {validation_state}{source_text}。{originality_sentence}",
            "google_does_not": "这不能单独说明图片由 NotebookLM、Gemini 或 Imagen 生成；需要看到更具体的产品名、生成工具或水印证据。",
            "valid_summary": "发现可验证的图片来源记录。",
            "valid_means": "文件里包含可读取的来源记录，签名验证状态为 Valid{issuer_text}。{originality_sentence}",
            "valid_does_not": "这不保证图片内容一定真实，也不保证图片没有被断章取义。",
            "attention_summary": "发现图片来源记录，但验证状态不完整或异常。",
            "attention_means": "文件里有来源记录，验证状态为 {validation_state}。{originality_sentence}",
            "attention_does_not": "这不代表图片一定造假，也不代表来源记录一定可信。",
            "absent_summary": "没有发现可读取的图片来源记录。",
            "absent_means": "文件里没有检测到 TrustPic v0 可读取的 C2PA 来源记录。{originality_sentence}",
            "absent_does_not": "这种情况很常见，尤其是截图、转发或平台下载后的图片；它不代表图片真实，也不代表图片一定是 AI 生成或被篡改。",
            "source_text": "，来源线索包括 {source_name}",
            "issuer_text": "，签发方为 {issuer}",
            "unknown_state": "未知",
        },
        "photo_metadata": {
            "unchecked_summary": "这次没有完成拍摄/编辑信息检查。",
            "unchecked_means": "TrustPic 没有得到这一项证据。",
            "unchecked_does_not": "这不代表图片没有元数据。",
            "capture_summary": "发现 {field_count} 项元数据，其中包含相机拍摄相关字段。",
            "capture_means": "文件里包含相机或拍摄参数字段，例如设备型号、拍摄时间、镜头或曝光信息。这更像是拍摄链路留下的信息。",
            "capture_does_not": "EXIF 可以被修改、复制或移除；它不能单独证明图片真实，也不能排除后期处理。",
            "software_summary": "只发现软件保存或文件结构类信息，未发现相机拍摄字段。",
            "software_means": "这类字段说明文件可能被某个软件保存、导出或处理过。例如 Software=Picasa 指向保存/处理软件，不说明图片由拍摄设备直接生成。",
            "software_does_not": "这不是相机拍摄证据，也不能单独说明图片真实、AI 生成或被篡改。",
            "absent_summary": "没有发现可读的拍摄或保存元数据。",
            "absent_means": "文件里没有检测到 TrustPic v0 可读取的 EXIF 元数据。",
            "absent_does_not": "很多截图、平台转发图或压缩图都没有 EXIF；这不代表图片一定可疑。",
        },
        "originality": {
            "unknown": "无法判断",
            "strong": "原始性较强",
            "limited": "原始性有限",
            "unchecked_reason": "图片来源记录检查未完成",
            "valid_c2pa_reason": "文件带有可读取且签名有效的来源记录",
            "invalid_c2pa_reason": "文件带有来源记录，但签名验证状态不完整或异常",
            "rich_exif_reason": "文件保留了较多相机拍摄相关信息",
            "partial_exif_reason": "文件保留了部分相机拍摄相关信息，但没有可读取的来源记录",
            "absent_reason": "没有可读取的来源记录或 EXIF；截图、转发、转码或二次保存都可能造成这种结果",
            "summary": "当前文件{label}。",
            "sentence": "当前文件原始性判断：{label}。",
            "sentence_with_reasons": "当前文件原始性判断：{label}，因为{reasons}。",
            "reason_joiner": "；",
        },
    },
    "en-US": {
        "confidence": {
            "strong": "Strong",
            "fairly_strong": "Fairly strong",
            "moderate": "Moderate",
            "limited": "Limited",
        },
        "status": {
            "support": "Supporting evidence",
            "warning": "Needs attention",
            "not_found": "Not found",
            "unavailable": "Not analyzed",
        },
        "titles": {
            "ai_marker": "AI marker",
            "ela": "Local difference clues",
            "source_record": "Source record",
            "photo_metadata": "Photo/save metadata",
        },
        "conclusions": {
            "ai_marker": "This file contains an AI-generation related marker.",
            "ai_source": "The source record points to an AI generation source.",
            "ela": "Local areas show concentrated difference clues.",
            "valid_source": "This file contains a verifiable source record.",
            "source_attention": "A source record was found, but its validation state needs attention.",
            "exif": "This file contains camera-capture related metadata, but no AI-related source or marker was found.",
            "none": "No readable AI source, AI marker, or local-difference clue was found by TrustPic v0.",
        },
        "limits": [
            "Not finding readable evidence does not prove the image is not AI-generated.",
            "Local differences are clues only; they cannot prove manipulation, editing, or AI generation on their own.",
            "A source record can show verifiable file information, but it does not prove the image content is true or complete.",
        ],
        "ai_marker": {
            "unchecked_summary": "The AI marker check did not complete.",
            "unchecked_means": "TrustPic did not get evidence for this item.",
            "unchecked_does_not": "This does not mean the image has no AI marker.",
            "detected_summary": "An AI-generation related marker was found.",
            "detected_means": "The file contains an AI marker TrustPic v0 can read: {field_names}.",
            "detected_does_not": "This does not prove every part of the image was AI-generated, or that the marker came from an authoritative platform.",
            "source_summary": "No explicit domestic AI marker was found, but the source record points to an AI generation source.",
            "source_means": "This item only checks GB 45438/TC260 or general AIGC markers. OpenAI, Gemini, and NotebookLM source records are shown under Source record.",
            "source_does_not": "This does not remove the AI-related source evidence. For this file, the Source record is the main AI-related evidence.",
            "absent_summary": "No AI marker recognized by TrustPic v0 was found.",
            "absent_means": "The file does not contain a supported GB 45438/TC260 or AIGC marker that TrustPic v0 can read.",
            "absent_does_not": "This does not prove the image is not AI-generated. Many platforms remove or never write this metadata.",
            "field_fallback": "file marker",
        },
        "ela": {
            "unchecked_summary": "The local difference check did not complete.",
            "unchecked_means": "TrustPic did not get evidence for this item.",
            "unchecked_does_not": "This does not mean the image has no local edits or unusual differences.",
            "detected_summary": "Some local areas show more concentrated differences.",
            "detected_means": "ELA tile analysis found {anomaly_count} local anomaly blocks, ratio {anomaly_ratio}, with full-image mean error {mean_error}. These areas respond differently from the overall compression pattern.",
            "detected_does_not": "This is only a local-difference clue. It cannot prove manipulation, editing, or AI generation on its own.",
            "absent_summary": "No concentrated local-difference clue was found.",
            "absent_means": "TrustPic did not find a small set of areas that clearly deviates from the overall compression pattern; full-image mean error is {mean_error}.",
            "absent_does_not": "Screenshots, platform transcoding, and general compression are common. No local-difference clue does not prove the image was never edited.",
        },
        "source": {
            "unchecked_summary": "The source record check did not complete.",
            "unchecked_means": "TrustPic did not get evidence for this item. {originality_sentence}",
            "unchecked_does_not": "This does not mean the image has no source record, and it does not prove the current file is original.",
            "ai_valid_summary": "A verifiable AI-related source record was found.",
            "ai_valid_means": "The file contains a readable, validly signed source record that points to an AI-related tool or issuer{source_text}. {originality_sentence}",
            "ai_valid_does_not": "This does not prove every part of the image was AI-generated, or that the content is true, complete, or shown in full context.",
            "ai_attention_summary": "An AI-related source record was found, but its validation state is incomplete or unusual.",
            "ai_attention_means": "The file contains AI-related source evidence, but the signature validation state is {validation_state}{source_text}. {originality_sentence}",
            "ai_attention_does_not": "This does not make the source record automatically trustworthy, and it does not prove the image content is fake.",
            "google_summary": "A Google source record was found, but no explicit AI product name was visible.",
            "google_means": "The file contains a Google-related source record, validation state {validation_state}{source_text}. {originality_sentence}",
            "google_does_not": "This alone does not show the image was generated by NotebookLM, Gemini, or Imagen. A specific product name, generation tool, or watermark evidence is needed.",
            "valid_summary": "A verifiable source record was found.",
            "valid_means": "The file contains a readable source record with Valid signature state{issuer_text}. {originality_sentence}",
            "valid_does_not": "This does not prove the image content is true, or that it has not been taken out of context.",
            "attention_summary": "A source record was found, but its validation state is incomplete or unusual.",
            "attention_means": "The file contains a source record, validation state {validation_state}. {originality_sentence}",
            "attention_does_not": "This does not prove the image is fake, and it does not make the source record automatically trustworthy.",
            "absent_summary": "No readable source record was found.",
            "absent_means": "TrustPic v0 did not detect a readable C2PA source record in the file. {originality_sentence}",
            "absent_does_not": "This is common, especially for screenshots, forwarded images, or platform downloads. It does not prove the image is authentic, AI-generated, or manipulated.",
            "source_text": ", with source clue {source_name}",
            "issuer_text": ", issuer {issuer}",
            "unknown_state": "unknown",
        },
        "photo_metadata": {
            "unchecked_summary": "The photo/save metadata check did not complete.",
            "unchecked_means": "TrustPic did not get evidence for this item.",
            "unchecked_does_not": "This does not mean the image has no metadata.",
            "capture_summary": "Found {field_count} metadata fields, including camera-capture related fields.",
            "capture_means": "The file contains camera or capture-setting fields, such as device model, capture time, lens, or exposure information. These are more consistent with capture-chain metadata.",
            "capture_does_not": "EXIF can be modified, copied, or removed. It cannot prove authenticity or rule out later editing on its own.",
            "software_summary": "Only software-save or file-structure metadata was found; no camera-capture field was found.",
            "software_means": "These fields suggest the file may have been saved, exported, or processed by software. For example, Software=Picasa points to save/processing software, not direct camera capture.",
            "software_does_not": "This is not camera-capture evidence, and it does not prove authenticity, AI generation, or manipulation on its own.",
            "absent_summary": "No readable photo or save metadata was found.",
            "absent_means": "The file does not contain EXIF metadata TrustPic v0 can read.",
            "absent_does_not": "Many screenshots, forwarded images, and compressed platform images have no EXIF. This does not make the image automatically suspicious.",
        },
        "originality": {
            "unknown": "Originality unknown",
            "strong": "Strong originality evidence",
            "limited": "Limited originality evidence",
            "unchecked_reason": "the source record check did not complete",
            "valid_c2pa_reason": "the file has a readable source record with a valid signature",
            "invalid_c2pa_reason": "the file has a source record, but the signature validation state is incomplete or unusual",
            "rich_exif_reason": "the file retains relatively rich camera-capture related metadata",
            "partial_exif_reason": "the file retains some camera-capture related metadata, but no readable source record",
            "absent_reason": "no readable source record or EXIF was found; screenshots, forwarding, transcoding, or secondary saves can cause this",
            "summary": " Current file: {label}.",
            "sentence": "File originality reading: {label}.",
            "sentence_with_reasons": "File originality reading: {label}, because {reasons}.",
            "reason_joiner": "; ",
        },
    },
}


def locale_copy(locale: str) -> dict:
    return COPY[locale] if locale in SUPPORTED_LOCALES else COPY["zh-CN"]


def build_interpretation(signals: ReportSignals, locale: str = "zh-CN") -> ReportInterpretation:
    copy = locale_copy(locale)
    return ReportInterpretation(
        confidence_label=confidence_label(signals, copy),
        conclusion=human_conclusion(signals, copy),
        evidence_chain=[
            ai_marker_evidence(signals.gb45438, copy, signals.c2pa),
            ela_evidence(signals.ela, copy),
            source_record_evidence(signals.c2pa, copy, signals.exif),
            photo_metadata_evidence(signals.exif, copy),
        ],
        limits=copy["limits"],
    )


def human_conclusion(signals: ReportSignals, copy: dict) -> str:
    conclusions = copy["conclusions"]
    if signals.gb45438.detected:
        return conclusions["ai_marker"]
    if ai_related_source_record(signals.c2pa):
        return conclusions["ai_source"]
    if signals.ela.detected:
        return conclusions["ela"]
    if signals.c2pa.detected:
        if c2pa_validation_state(signals.c2pa) == "Valid":
            return conclusions["valid_source"]
        return conclusions["source_attention"]
    if capture_exif(signals.exif):
        return conclusions["exif"]
    return conclusions["none"]


def confidence_label(signals: ReportSignals, copy: dict) -> str:
    confidence = copy["confidence"]
    if signals.gb45438.detected:
        return confidence["strong"]
    if ai_related_source_record(signals.c2pa) and c2pa_validation_state(signals.c2pa) == "Valid":
        return confidence["strong"]
    if ai_related_source_record(signals.c2pa):
        return confidence["fairly_strong"]
    if signals.c2pa.detected and c2pa_validation_state(signals.c2pa) == "Valid" and not signals.ela.detected:
        return confidence["strong"]
    if signals.c2pa.detected:
        return confidence["fairly_strong"]
    if signals.ela.detected:
        return confidence["moderate"]
    if rich_exif(signals.exif):
        return confidence["fairly_strong"]
    if capture_exif(signals.exif):
        return confidence["moderate"]
    return confidence["limited"]


def ai_marker_evidence(signal: EvidenceSignal, copy: dict, c2pa_signal: EvidenceSignal | None = None) -> InterpretationEvidence:
    text = copy["ai_marker"]
    if not signal.checked:
        return InterpretationEvidence(
            key="gb45438",
            title=copy["titles"]["ai_marker"],
            status_label=copy["status"]["unavailable"],
            summary=text["unchecked_summary"],
            means=text["unchecked_means"],
            does_not_mean=text["unchecked_does_not"],
            details=signal.details,
        )
    if signal.detected:
        fields = signal.details.get("xmp_fields", {}) if isinstance(signal.details, dict) else {}
        field_names = ", ".join(sorted(fields.keys())) if isinstance(fields, dict) and fields else text["field_fallback"]
        return InterpretationEvidence(
            key="gb45438",
            title=copy["titles"]["ai_marker"],
            status_label=copy["status"]["support"],
            summary=text["detected_summary"],
            means=text["detected_means"].format(field_names=field_names),
            does_not_mean=text["detected_does_not"],
            details=signal.details,
        )
    if c2pa_signal is not None and ai_related_source_record(c2pa_signal):
        return InterpretationEvidence(
            key="gb45438",
            title=copy["titles"]["ai_marker"],
            status_label=copy["status"]["not_found"],
            summary=text["source_summary"],
            means=text["source_means"],
            does_not_mean=text["source_does_not"],
            details=signal.details,
        )
    return InterpretationEvidence(
        key="gb45438",
        title=copy["titles"]["ai_marker"],
        status_label=copy["status"]["not_found"],
        summary=text["absent_summary"],
        means=text["absent_means"],
        does_not_mean=text["absent_does_not"],
        details=signal.details,
    )


def ela_evidence(signal: EvidenceSignal, copy: dict) -> InterpretationEvidence:
    text = copy["ela"]
    mean_error = signal.details.get("mean_error") if isinstance(signal.details, dict) else None
    anomaly_count = signal.details.get("local_anomaly_count") if isinstance(signal.details, dict) else None
    anomaly_ratio = signal.details.get("local_anomaly_ratio") if isinstance(signal.details, dict) else None
    if not signal.checked:
        return InterpretationEvidence(
            key="ela",
            title=copy["titles"]["ela"],
            status_label=copy["status"]["unavailable"],
            summary=text["unchecked_summary"],
            means=text["unchecked_means"],
            does_not_mean=text["unchecked_does_not"],
            details=signal.details,
        )
    if signal.detected:
        return InterpretationEvidence(
            key="ela",
            title=copy["titles"]["ela"],
            status_label=copy["status"]["warning"],
            summary=text["detected_summary"],
            means=text["detected_means"].format(
                anomaly_count=anomaly_count,
                anomaly_ratio=anomaly_ratio,
                mean_error=mean_error,
            ),
            does_not_mean=text["detected_does_not"],
            details=signal.details,
        )
    return InterpretationEvidence(
        key="ela",
        title=copy["titles"]["ela"],
        status_label=copy["status"]["not_found"],
        summary=text["absent_summary"],
        means=text["absent_means"].format(mean_error=mean_error),
        does_not_mean=text["absent_does_not"],
        details=signal.details,
    )


def source_record_evidence(signal: EvidenceSignal, copy: dict, exif_signal: EvidenceSignal | None = None) -> InterpretationEvidence:
    text = copy["source"]
    validation_state = c2pa_validation_state(signal)
    validation_text = validation_state or text["unknown_state"]
    ai_source = ai_related_source_record(signal)
    google_source = google_source_record(signal)
    source_name = source_record_name(signal)
    originality = file_originality(signal, copy, exif_signal)
    originality_text = originality_sentence(originality, copy)
    source_text = text["source_text"].format(source_name=source_name) if source_name else ""

    if not signal.checked:
        return InterpretationEvidence(
            key="c2pa",
            title=copy["titles"]["source_record"],
            status_label=copy["status"]["unavailable"],
            summary=source_record_summary(text["unchecked_summary"], originality, copy),
            means=text["unchecked_means"].format(originality_sentence=originality_text),
            does_not_mean=text["unchecked_does_not"],
            details=source_record_details(signal, originality),
        )
    if signal.detected and ai_source:
        if validation_state == "Valid":
            return InterpretationEvidence(
                key="c2pa",
                title=copy["titles"]["source_record"],
                status_label=copy["status"]["support"],
                summary=source_record_summary(text["ai_valid_summary"], originality, copy),
                means=text["ai_valid_means"].format(source_text=source_text, originality_sentence=originality_text),
                does_not_mean=text["ai_valid_does_not"],
                details=source_record_details(signal, originality),
            )
        return InterpretationEvidence(
            key="c2pa",
            title=copy["titles"]["source_record"],
            status_label=copy["status"]["warning"],
            summary=source_record_summary(text["ai_attention_summary"], originality, copy),
            means=text["ai_attention_means"].format(
                validation_state=validation_text,
                source_text=source_text,
                originality_sentence=originality_text,
            ),
            does_not_mean=text["ai_attention_does_not"],
            details=source_record_details(signal, originality),
        )
    if signal.detected and google_source:
        return InterpretationEvidence(
            key="c2pa",
            title=copy["titles"]["source_record"],
            status_label=copy["status"]["warning"],
            summary=source_record_summary(text["google_summary"], originality, copy),
            means=text["google_means"].format(
                validation_state=validation_text,
                source_text=source_text,
                originality_sentence=originality_text,
            ),
            does_not_mean=text["google_does_not"],
            details=source_record_details(signal, originality),
        )
    if signal.detected and validation_state == "Valid":
        issuer = signal.details.get("signature_issuer") if isinstance(signal.details, dict) else None
        issuer_text = text["issuer_text"].format(issuer=issuer) if issuer else ""
        return InterpretationEvidence(
            key="c2pa",
            title=copy["titles"]["source_record"],
            status_label=copy["status"]["support"],
            summary=source_record_summary(text["valid_summary"], originality, copy),
            means=text["valid_means"].format(issuer_text=issuer_text, originality_sentence=originality_text),
            does_not_mean=text["valid_does_not"],
            details=source_record_details(signal, originality),
        )
    if signal.detected:
        return InterpretationEvidence(
            key="c2pa",
            title=copy["titles"]["source_record"],
            status_label=copy["status"]["warning"],
            summary=source_record_summary(text["attention_summary"], originality, copy),
            means=text["attention_means"].format(
                validation_state=validation_text,
                originality_sentence=originality_text,
            ),
            does_not_mean=text["attention_does_not"],
            details=source_record_details(signal, originality),
        )
    return InterpretationEvidence(
        key="c2pa",
        title=copy["titles"]["source_record"],
        status_label=copy["status"]["not_found"],
        summary=source_record_summary(text["absent_summary"], originality, copy),
        means=text["absent_means"].format(originality_sentence=originality_text),
        does_not_mean=text["absent_does_not"],
        details=source_record_details(signal, originality),
    )


def photo_metadata_evidence(signal: EvidenceSignal, copy: dict) -> InterpretationEvidence:
    text = copy["photo_metadata"]
    field_count = exif_field_count(signal)
    if not signal.checked:
        return InterpretationEvidence(
            key="exif",
            title=copy["titles"]["photo_metadata"],
            status_label=copy["status"]["unavailable"],
            summary=text["unchecked_summary"],
            means=text["unchecked_means"],
            does_not_mean=text["unchecked_does_not"],
            details=signal.details,
        )
    if capture_exif(signal):
        return InterpretationEvidence(
            key="exif",
            title=copy["titles"]["photo_metadata"],
            status_label=copy["status"]["support"],
            summary=text["capture_summary"].format(field_count=field_count),
            means=text["capture_means"],
            does_not_mean=text["capture_does_not"],
            details=signal.details,
        )
    if signal.detected:
        return InterpretationEvidence(
            key="exif",
            title=copy["titles"]["photo_metadata"],
            status_label=copy["status"]["warning"],
            summary=text["software_summary"],
            means=text["software_means"],
            does_not_mean=text["software_does_not"],
            details=signal.details,
        )
    return InterpretationEvidence(
        key="exif",
        title=copy["titles"]["photo_metadata"],
        status_label=copy["status"]["not_found"],
        summary=text["absent_summary"],
        means=text["absent_means"],
        does_not_mean=text["absent_does_not"],
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


def source_record_summary(base: str, originality: dict, copy: dict) -> str:
    return f"{base}{copy['originality']['summary'].format(label=originality['label'])}"


def originality_sentence(originality: dict, copy: dict) -> str:
    reasons = originality.get("reasons") or []
    original_copy = copy["originality"]
    reason_text = original_copy["reason_joiner"].join(str(reason) for reason in reasons)
    if reason_text:
        return original_copy["sentence_with_reasons"].format(label=originality["label"], reasons=reason_text)
    return original_copy["sentence"].format(label=originality["label"])


def file_originality(c2pa_signal: EvidenceSignal, copy: dict, exif_signal: EvidenceSignal | None) -> dict:
    original_copy = copy["originality"]
    if not c2pa_signal.checked:
        return {
            "label": original_copy["unknown"],
            "reasons": [original_copy["unchecked_reason"]],
        }

    validation_state = c2pa_validation_state(c2pa_signal)
    if c2pa_signal.detected and validation_state == "Valid":
        return {
            "label": original_copy["strong"],
            "reasons": [original_copy["valid_c2pa_reason"]],
        }

    if c2pa_signal.detected:
        return {
            "label": original_copy["limited"],
            "reasons": [original_copy["invalid_c2pa_reason"]],
        }

    if exif_signal is not None and rich_exif(exif_signal):
        return {
            "label": original_copy["strong"],
            "reasons": [original_copy["rich_exif_reason"]],
        }

    if exif_signal is not None and capture_exif(exif_signal):
        return {
            "label": original_copy["limited"],
            "reasons": [original_copy["partial_exif_reason"]],
        }

    return {
        "label": original_copy["limited"],
        "reasons": [original_copy["absent_reason"]],
    }


def exif_field_count(signal: EvidenceSignal) -> int:
    if not isinstance(signal.details, dict):
        return 0
    value = signal.details.get("field_count")
    return int(value) if isinstance(value, int) else 0


def rich_exif(signal: EvidenceSignal) -> bool:
    return capture_exif(signal) and exif_field_count(signal) >= 5


def capture_exif(signal: EvidenceSignal) -> bool:
    fields = exif_fields(signal)
    if not signal.detected or not fields:
        return False

    capture_field_names = {
        "Make",
        "Model",
        "DateTimeOriginal",
        "DateTimeDigitized",
        "DateTime",
        "LensModel",
        "LensMake",
        "ExposureTime",
        "FNumber",
        "ISOSpeedRatings",
        "PhotographicSensitivity",
        "FocalLength",
        "FocalLengthIn35mmFilm",
        "ExposureProgram",
        "ExposureMode",
        "MeteringMode",
        "Flash",
        "WhiteBalance",
        "SceneCaptureType",
        "GPSInfo",
    }
    return any(name in fields for name in capture_field_names)


def exif_fields(signal: EvidenceSignal) -> dict:
    if not isinstance(signal.details, dict):
        return {}
    fields = signal.details.get("fields")
    return fields if isinstance(fields, dict) else {}
