// Bilingual interpretation layer, ported from backend app/services/interpretation.py.

const SUPPORTED_LOCALES = new Set(["zh-CN", "en-US"]);

const COPY = {
  "zh-CN": {
    confidence: {
      strong: "强",
      fairly_strong: "较强",
      moderate: "中等",
      limited: "有限",
    },
    status: {
      support: "支持证据",
      warning: "需留意",
      not_found: "未发现",
      unavailable: "无法分析",
    },
    titles: {
      ai_marker: "AI 生成标记",
      ela: "局部差异线索",
      source_record: "图片来源记录",
      photo_metadata: "拍摄/编辑信息",
    },
    conclusions: {
      ai_marker: "发现这张图带有 AI 生成相关标记。",
      ai_source: "图片来源记录指向 AI 生成来源。",
      ela: "发现局部区域存在差异集中线索。",
      valid_source: "发现这张图带有可验证的来源记录。",
      source_attention: "发现图片来源记录，但验证状态需要留意。",
      exif: "发现这张图包含相机拍摄相关信息，但没有发现 AI 相关来源或标记。",
      none: "没有发现 TrustPic v0 能读取的 AI 来源、AI 标记或局部差异线索。",
    },
    limits: [
      "没有发现可读证据，不等于图片一定不是 AI 生成。",
      "局部差异只是线索，不能单独证明图片被篡改、P 图或 AI 生成。",
      "来源记录能说明文件里带有可验证信息，但不等于图片内容一定真实或上下文完整。",
    ],
    ai_marker: {
      unchecked_summary: "这次没有完成 AI 生成标记检查。",
      unchecked_means: "TrustPic 没有得到这一项证据。",
      unchecked_does_not: "这不代表图片没有 AI 生成标记。",
      detected_summary: "发现 AI 生成相关标记。",
      detected_means: "文件里包含 TrustPic v0 可识别的 AI 生成标记：{field_names}。",
      detected_does_not: "这不说明图片的每个局部都由 AI 生成，也不说明标记一定来自权威平台。",
      source_summary: "没有发现国内显式 AI 标记；但来源记录已经指向 AI 生成来源。",
      source_means: "这一项只看 GB 45438/TC260 或通用 AIGC 标记；OpenAI、Gemini、NotebookLM 这类来源记录会在图片来源记录里展示。",
      source_does_not: "这不代表没有 AI 证据；对这张图，应把图片来源记录作为主要 AI 相关证据。",
      absent_summary: "没有发现 TrustPic v0 可识别的 AI 生成标记。",
      absent_means: "文件里没有检测到当前支持的 GB 45438/TC260 或 AIGC 标记。",
      absent_does_not: "这不代表图片一定不是 AI 生成；很多平台会移除或不写入这类标记。",
      field_fallback: "文件标记",
    },
    ela: {
      unchecked_summary: "这次没有完成局部差异检查。",
      unchecked_means: "TrustPic 没有得到这一项证据。",
      unchecked_does_not: "这不代表图片没有局部编辑或异常差异。",
      detected_summary: "发现局部区域的差异更集中。",
      detected_means: "ELA tile 分析发现 {anomaly_count} 个局部异常块，占比 {anomaly_ratio}，全图 mean error 为 {mean_error}。这些区域和全图整体压缩响应不太一致。",
      detected_does_not: "这只是局部差异线索，不能单独证明图片被篡改、P 图或由 AI 生成。",
      absent_summary: "没有发现局部差异集中线索。",
      absent_means: "没有发现少量区域明显偏离整体压缩模式；全图 mean error 为 {mean_error}。",
      absent_does_not: "截图、平台转码和整体压缩都很常见；没有局部差异线索，也不代表图片一定没有被编辑。",
    },
    source: {
      unchecked_summary: "这次没有完成图片来源记录检查。",
      unchecked_means: "TrustPic 没有得到这一项证据。{originality_sentence}",
      unchecked_does_not: "这不代表图片没有来源记录，也不代表当前文件一定是原始文件。",
      ai_valid_summary: "发现可验证的 AI 相关来源记录。",
      ai_valid_means: "文件里有可读取、签名有效的来源记录，且来源指向 AI 相关工具或签发方{source_text}。{originality_sentence}",
      ai_valid_does_not: "这不说明图片的每个局部都由 AI 生成，也不保证图片内容一定真实、完整或没有被断章取义。",
      ai_attention_summary: "发现 AI 相关来源记录，但验证状态不完整或异常。",
      ai_attention_means: "文件里有 AI 相关来源线索，但签名验证状态为 {validation_state}{source_text}。{originality_sentence}",
      ai_attention_does_not: "这不代表来源记录一定可信，也不等于图片内容一定造假。",
      google_summary: "发现 Google 图片来源记录，但没有看到明确的 AI 产品名。",
      google_means: "文件里有 Google 相关来源记录，验证状态为 {validation_state}{source_text}。{originality_sentence}",
      google_does_not: "这不能单独说明图片由 NotebookLM、Gemini 或 Imagen 生成；需要看到更具体的产品名、生成工具或水印证据。",
      valid_summary: "发现可验证的图片来源记录。",
      valid_means: "文件里包含可读取的来源记录，签名验证状态为 Valid{issuer_text}。{originality_sentence}",
      valid_does_not: "这不保证图片内容一定真实，也不保证图片没有被断章取义。",
      attention_summary: "发现图片来源记录，但验证状态不完整或异常。",
      attention_means: "文件里有来源记录，验证状态为 {validation_state}。{originality_sentence}",
      attention_does_not: "这不代表图片一定造假，也不代表来源记录一定可信。",
      absent_summary: "没有发现可读取的图片来源记录。",
      absent_means: "文件里没有检测到 TrustPic v0 可读取的 C2PA 来源记录。{originality_sentence}",
      absent_does_not: "这种情况很常见，尤其是截图、转发或平台下载后的图片；它不代表图片真实，也不代表图片一定是 AI 生成或被篡改。",
      source_text: "，来源线索包括 {source_name}",
      issuer_text: "，签发方为 {issuer}",
      unknown_state: "未知",
    },
    photo_metadata: {
      unchecked_summary: "这次没有完成拍摄/编辑信息检查。",
      unchecked_means: "TrustPic 没有得到这一项证据。",
      unchecked_does_not: "这不代表图片没有元数据。",
      capture_summary: "发现 {field_count} 项元数据，其中包含相机拍摄相关字段。",
      capture_means: "文件里包含相机或拍摄参数字段，例如设备型号、拍摄时间、镜头或曝光信息。这更像是拍摄链路留下的信息。",
      capture_does_not: "EXIF 可以被修改、复制或移除；它不能单独证明图片真实，也不能排除后期处理。",
      software_summary: "只发现软件保存或文件结构类信息，未发现相机拍摄字段。",
      software_means: "这类字段说明文件可能被某个软件保存、导出或处理过。例如 Software=Picasa 指向保存/处理软件，不说明图片由拍摄设备直接生成。",
      software_does_not: "这不是相机拍摄证据，也不能单独说明图片真实、AI 生成或被篡改。",
      absent_summary: "没有发现可读的拍摄或保存元数据。",
      absent_means: "文件里没有检测到 TrustPic v0 可读取的 EXIF 元数据。",
      absent_does_not: "很多截图、平台转发图或压缩图都没有 EXIF；这不代表图片一定可疑。",
    },
    originality: {
      unknown: "无法判断",
      strong: "原始性较强",
      limited: "原始性有限",
      unchecked_reason: "图片来源记录检查未完成",
      valid_c2pa_reason: "文件带有可读取且签名有效的来源记录",
      invalid_c2pa_reason: "文件带有来源记录，但签名验证状态不完整或异常",
      rich_exif_reason: "文件保留了较多相机拍摄相关信息",
      partial_exif_reason: "文件保留了部分相机拍摄相关信息，但没有可读取的来源记录",
      absent_reason: "没有可读取的来源记录或 EXIF；截图、转发、转码或二次保存都可能造成这种结果",
      summary: "当前文件{label}。",
      sentence: "当前文件原始性判断：{label}。",
      sentence_with_reasons: "当前文件原始性判断：{label}，因为{reasons}。",
      reason_joiner: "；",
    },
  },
  "en-US": {
    confidence: {
      strong: "Strong",
      fairly_strong: "Fairly strong",
      moderate: "Moderate",
      limited: "Limited",
    },
    status: {
      support: "Supporting evidence",
      warning: "Needs attention",
      not_found: "Not found",
      unavailable: "Not analyzed",
    },
    titles: {
      ai_marker: "AI marker",
      ela: "Local difference clues",
      source_record: "Source record",
      photo_metadata: "Photo/save metadata",
    },
    conclusions: {
      ai_marker: "This file contains an AI-generation related marker.",
      ai_source: "The source record points to an AI generation source.",
      ela: "Local areas show concentrated difference clues.",
      valid_source: "This file contains a verifiable source record.",
      source_attention: "A source record was found, but its validation state needs attention.",
      exif: "This file contains camera-capture related metadata, but no AI-related source or marker was found.",
      none: "No readable AI source, AI marker, or local-difference clue was found by TrustPic v0.",
    },
    limits: [
      "Not finding readable evidence does not prove the image is not AI-generated.",
      "Local differences are clues only; they cannot prove manipulation, editing, or AI generation on their own.",
      "A source record can show verifiable file information, but it does not prove the image content is true or complete.",
    ],
    ai_marker: {
      unchecked_summary: "The AI marker check did not complete.",
      unchecked_means: "TrustPic did not get evidence for this item.",
      unchecked_does_not: "This does not mean the image has no AI marker.",
      detected_summary: "An AI-generation related marker was found.",
      detected_means: "The file contains an AI marker TrustPic v0 can read: {field_names}.",
      detected_does_not: "This does not prove every part of the image was AI-generated, or that the marker came from an authoritative platform.",
      source_summary: "No explicit domestic AI marker was found, but the source record points to an AI generation source.",
      source_means: "This item only checks GB 45438/TC260 or general AIGC markers. OpenAI, Gemini, and NotebookLM source records are shown under Source record.",
      source_does_not: "This does not remove the AI-related source evidence. For this file, the Source record is the main AI-related evidence.",
      absent_summary: "No AI marker recognized by TrustPic v0 was found.",
      absent_means: "The file does not contain a supported GB 45438/TC260 or AIGC marker that TrustPic v0 can read.",
      absent_does_not: "This does not prove the image is not AI-generated. Many platforms remove or never write this metadata.",
      field_fallback: "file marker",
    },
    ela: {
      unchecked_summary: "The local difference check did not complete.",
      unchecked_means: "TrustPic did not get evidence for this item.",
      unchecked_does_not: "This does not mean the image has no local edits or unusual differences.",
      detected_summary: "Some local areas show more concentrated differences.",
      detected_means: "ELA tile analysis found {anomaly_count} local anomaly blocks, ratio {anomaly_ratio}, with full-image mean error {mean_error}. These areas respond differently from the overall compression pattern.",
      detected_does_not: "This is only a local-difference clue. It cannot prove manipulation, editing, or AI generation on its own.",
      absent_summary: "No concentrated local-difference clue was found.",
      absent_means: "TrustPic did not find a small set of areas that clearly deviates from the overall compression pattern; full-image mean error is {mean_error}.",
      absent_does_not: "Screenshots, platform transcoding, and general compression are common. No local-difference clue does not prove the image was never edited.",
    },
    source: {
      unchecked_summary: "The source record check did not complete.",
      unchecked_means: "TrustPic did not get evidence for this item. {originality_sentence}",
      unchecked_does_not: "This does not mean the image has no source record, and it does not prove the current file is original.",
      ai_valid_summary: "A verifiable AI-related source record was found.",
      ai_valid_means: "The file contains a readable, validly signed source record that points to an AI-related tool or issuer{source_text}. {originality_sentence}",
      ai_valid_does_not: "This does not prove every part of the image was AI-generated, or that the content is true, complete, or shown in full context.",
      ai_attention_summary: "An AI-related source record was found, but its validation state is incomplete or unusual.",
      ai_attention_means: "The file contains AI-related source evidence, but the signature validation state is {validation_state}{source_text}. {originality_sentence}",
      ai_attention_does_not: "This does not make the source record automatically trustworthy, and it does not prove the image content is fake.",
      google_summary: "A Google source record was found, but no explicit AI product name was visible.",
      google_means: "The file contains a Google-related source record, validation state {validation_state}{source_text}. {originality_sentence}",
      google_does_not: "This alone does not show the image was generated by NotebookLM, Gemini, or Imagen. A specific product name, generation tool, or watermark evidence is needed.",
      valid_summary: "A verifiable source record was found.",
      valid_means: "The file contains a readable source record with Valid signature state{issuer_text}. {originality_sentence}",
      valid_does_not: "This does not prove the image content is true, or that it has not been taken out of context.",
      attention_summary: "A source record was found, but its validation state is incomplete or unusual.",
      attention_means: "The file contains a source record, validation state {validation_state}. {originality_sentence}",
      attention_does_not: "This does not prove the image is fake, and it does not make the source record automatically trustworthy.",
      absent_summary: "No readable source record was found.",
      absent_means: "TrustPic v0 did not detect a readable C2PA source record in the file. {originality_sentence}",
      absent_does_not: "This is common, especially for screenshots, forwarded images, or platform downloads. It does not prove the image is authentic, AI-generated, or manipulated.",
      source_text: ", with source clue {source_name}",
      issuer_text: ", issuer {issuer}",
      unknown_state: "unknown",
    },
    photo_metadata: {
      unchecked_summary: "The photo/save metadata check did not complete.",
      unchecked_means: "TrustPic did not get evidence for this item.",
      unchecked_does_not: "This does not mean the image has no metadata.",
      capture_summary: "Found {field_count} metadata fields, including camera-capture related fields.",
      capture_means: "The file contains camera or capture-setting fields, such as device model, capture time, lens, or exposure information. These are more consistent with capture-chain metadata.",
      capture_does_not: "EXIF can be modified, copied, or removed. It cannot prove authenticity or rule out later editing on its own.",
      software_summary: "Only software-save or file-structure metadata was found; no camera-capture field was found.",
      software_means: "These fields suggest the file may have been saved, exported, or processed by software. For example, Software=Picasa points to save/processing software, not direct camera capture.",
      software_does_not: "This is not camera-capture evidence, and it does not prove authenticity, AI generation, or manipulation on its own.",
      absent_summary: "No readable photo or save metadata was found.",
      absent_means: "The file does not contain EXIF metadata TrustPic v0 can read.",
      absent_does_not: "Many screenshots, forwarded images, and compressed platform images have no EXIF. This does not make the image automatically suspicious.",
    },
    originality: {
      unknown: "Originality unknown",
      strong: "Strong originality evidence",
      limited: "Limited originality evidence",
      unchecked_reason: "the source record check did not complete",
      valid_c2pa_reason: "the file has a readable source record with a valid signature",
      invalid_c2pa_reason: "the file has a source record, but the signature validation state is incomplete or unusual",
      rich_exif_reason: "the file retains relatively rich camera-capture related metadata",
      partial_exif_reason: "the file retains some camera-capture related metadata, but no readable source record",
      absent_reason: "no readable source record or EXIF was found; screenshots, forwarding, transcoding, or secondary saves can cause this",
      summary: " Current file: {label}.",
      sentence: "File originality reading: {label}.",
      sentence_with_reasons: "File originality reading: {label}, because {reasons}.",
      reason_joiner: "; ",
    },
  },
};

const CAPTURE_FIELD_NAMES = new Set([
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
]);

const AI_SOURCE_TERMS = [
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
];

function fmt(template, params) {
  return template.replace(/\{(\w+)\}/g, (whole, key) =>
    Object.prototype.hasOwnProperty.call(params, key) ? String(params[key]) : whole,
  );
}

function localeCopy(locale) {
  return SUPPORTED_LOCALES.has(locale) ? COPY[locale] : COPY["zh-CN"];
}

export function buildInterpretation(signals, locale = "zh-CN") {
  const copy = localeCopy(locale);
  return {
    confidence_label: confidenceLabel(signals, copy),
    conclusion: humanConclusion(signals, copy),
    evidence_chain: [
      aiMarkerEvidence(signals.gb45438, copy, signals.c2pa),
      elaEvidence(signals.ela, copy),
      sourceRecordEvidence(signals.c2pa, copy, signals.exif),
      photoMetadataEvidence(signals.exif, copy),
    ],
    limits: copy.limits,
  };
}

function humanConclusion(signals, copy) {
  const conclusions = copy.conclusions;
  if (signals.gb45438.detected) {
    return conclusions.ai_marker;
  }
  if (aiRelatedSourceRecord(signals.c2pa)) {
    return conclusions.ai_source;
  }
  if (signals.ela.detected) {
    return conclusions.ela;
  }
  if (signals.c2pa.detected) {
    if (c2paValidationState(signals.c2pa) === "Valid") {
      return conclusions.valid_source;
    }
    return conclusions.source_attention;
  }
  if (captureExif(signals.exif)) {
    return conclusions.exif;
  }
  return conclusions.none;
}

function confidenceLabel(signals, copy) {
  const confidence = copy.confidence;
  if (signals.gb45438.detected) {
    return confidence.strong;
  }
  if (aiRelatedSourceRecord(signals.c2pa) && c2paValidationState(signals.c2pa) === "Valid") {
    return confidence.strong;
  }
  if (aiRelatedSourceRecord(signals.c2pa)) {
    return confidence.fairly_strong;
  }
  if (signals.c2pa.detected && c2paValidationState(signals.c2pa) === "Valid" && !signals.ela.detected) {
    return confidence.strong;
  }
  if (signals.c2pa.detected) {
    return confidence.fairly_strong;
  }
  if (signals.ela.detected) {
    return confidence.moderate;
  }
  if (richExif(signals.exif)) {
    return confidence.fairly_strong;
  }
  if (captureExif(signals.exif)) {
    return confidence.moderate;
  }
  return confidence.limited;
}

function aiMarkerEvidence(signal, copy, c2paSignal) {
  const text = copy.ai_marker;
  if (!signal.checked) {
    return evidence("gb45438", copy.titles.ai_marker, copy.status.unavailable, text.unchecked_summary, text.unchecked_means, text.unchecked_does_not, signal.details);
  }
  if (signal.detected) {
    const fields = isPlainObject(signal.details) ? signal.details.xmp_fields : null;
    const fieldNames =
      isPlainObject(fields) && Object.keys(fields).length > 0
        ? Object.keys(fields).sort().join(", ")
        : text.field_fallback;
    return evidence(
      "gb45438",
      copy.titles.ai_marker,
      copy.status.support,
      text.detected_summary,
      fmt(text.detected_means, { field_names: fieldNames }),
      text.detected_does_not,
      signal.details,
    );
  }
  if (c2paSignal && aiRelatedSourceRecord(c2paSignal)) {
    return evidence("gb45438", copy.titles.ai_marker, copy.status.not_found, text.source_summary, text.source_means, text.source_does_not, signal.details);
  }
  return evidence("gb45438", copy.titles.ai_marker, copy.status.not_found, text.absent_summary, text.absent_means, text.absent_does_not, signal.details);
}

function elaEvidence(signal, copy) {
  const text = copy.ela;
  const details = isPlainObject(signal.details) ? signal.details : {};
  const meanError = details.mean_error;
  const anomalyCount = details.local_anomaly_count;
  const anomalyRatio = details.local_anomaly_ratio;
  if (!signal.checked) {
    return evidence("ela", copy.titles.ela, copy.status.unavailable, text.unchecked_summary, text.unchecked_means, text.unchecked_does_not, signal.details);
  }
  if (signal.detected) {
    return evidence(
      "ela",
      copy.titles.ela,
      copy.status.warning,
      text.detected_summary,
      fmt(text.detected_means, { anomaly_count: anomalyCount, anomaly_ratio: anomalyRatio, mean_error: meanError }),
      text.detected_does_not,
      signal.details,
    );
  }
  return evidence(
    "ela",
    copy.titles.ela,
    copy.status.not_found,
    text.absent_summary,
    fmt(text.absent_means, { mean_error: meanError }),
    text.absent_does_not,
    signal.details,
  );
}

function sourceRecordEvidence(signal, copy, exifSignal) {
  const text = copy.source;
  const validationState = c2paValidationState(signal);
  const validationText = validationState || text.unknown_state;
  const aiSource = aiRelatedSourceRecord(signal);
  const googleSource = googleSourceRecord(signal);
  const sourceName = sourceRecordName(signal);
  const originality = fileOriginality(signal, copy, exifSignal);
  const originalityText = originalitySentence(originality, copy);
  const sourceText = sourceName ? fmt(text.source_text, { source_name: sourceName }) : "";

  if (!signal.checked) {
    return evidence(
      "c2pa",
      copy.titles.source_record,
      copy.status.unavailable,
      sourceRecordSummary(text.unchecked_summary, originality, copy),
      fmt(text.unchecked_means, { originality_sentence: originalityText }),
      text.unchecked_does_not,
      sourceRecordDetails(signal, originality),
    );
  }
  if (signal.detected && aiSource) {
    if (validationState === "Valid") {
      return evidence(
        "c2pa",
        copy.titles.source_record,
        copy.status.support,
        sourceRecordSummary(text.ai_valid_summary, originality, copy),
        fmt(text.ai_valid_means, { source_text: sourceText, originality_sentence: originalityText }),
        text.ai_valid_does_not,
        sourceRecordDetails(signal, originality),
      );
    }
    return evidence(
      "c2pa",
      copy.titles.source_record,
      copy.status.warning,
      sourceRecordSummary(text.ai_attention_summary, originality, copy),
      fmt(text.ai_attention_means, { validation_state: validationText, source_text: sourceText, originality_sentence: originalityText }),
      text.ai_attention_does_not,
      sourceRecordDetails(signal, originality),
    );
  }
  if (signal.detected && googleSource) {
    return evidence(
      "c2pa",
      copy.titles.source_record,
      copy.status.warning,
      sourceRecordSummary(text.google_summary, originality, copy),
      fmt(text.google_means, { validation_state: validationText, source_text: sourceText, originality_sentence: originalityText }),
      text.google_does_not,
      sourceRecordDetails(signal, originality),
    );
  }
  if (signal.detected && validationState === "Valid") {
    const issuer = isPlainObject(signal.details) ? signal.details.signature_issuer : null;
    const issuerText = issuer ? fmt(text.issuer_text, { issuer }) : "";
    return evidence(
      "c2pa",
      copy.titles.source_record,
      copy.status.support,
      sourceRecordSummary(text.valid_summary, originality, copy),
      fmt(text.valid_means, { issuer_text: issuerText, originality_sentence: originalityText }),
      text.valid_does_not,
      sourceRecordDetails(signal, originality),
    );
  }
  if (signal.detected) {
    return evidence(
      "c2pa",
      copy.titles.source_record,
      copy.status.warning,
      sourceRecordSummary(text.attention_summary, originality, copy),
      fmt(text.attention_means, { validation_state: validationText, originality_sentence: originalityText }),
      text.attention_does_not,
      sourceRecordDetails(signal, originality),
    );
  }
  return evidence(
    "c2pa",
    copy.titles.source_record,
    copy.status.not_found,
    sourceRecordSummary(text.absent_summary, originality, copy),
    fmt(text.absent_means, { originality_sentence: originalityText }),
    text.absent_does_not,
    sourceRecordDetails(signal, originality),
  );
}

function photoMetadataEvidence(signal, copy) {
  const text = copy.photo_metadata;
  const fieldCount = exifFieldCount(signal);
  if (!signal.checked) {
    return evidence("exif", copy.titles.photo_metadata, copy.status.unavailable, text.unchecked_summary, text.unchecked_means, text.unchecked_does_not, signal.details);
  }
  if (captureExif(signal)) {
    return evidence(
      "exif",
      copy.titles.photo_metadata,
      copy.status.support,
      fmt(text.capture_summary, { field_count: fieldCount }),
      text.capture_means,
      text.capture_does_not,
      signal.details,
    );
  }
  if (signal.detected) {
    return evidence("exif", copy.titles.photo_metadata, copy.status.warning, text.software_summary, text.software_means, text.software_does_not, signal.details);
  }
  return evidence("exif", copy.titles.photo_metadata, copy.status.not_found, text.absent_summary, text.absent_means, text.absent_does_not, signal.details);
}

function evidence(key, title, statusLabel, summary, means, doesNotMean, details) {
  return {
    key,
    title,
    status_label: statusLabel,
    summary,
    means,
    does_not_mean: doesNotMean,
    details: isPlainObject(details) ? details : {},
  };
}

function c2paValidationState(signal) {
  if (!isPlainObject(signal.details)) {
    return null;
  }
  const value = signal.details.validation_state;
  return value !== null && value !== undefined ? String(value) : null;
}

function aiRelatedSourceRecord(signal) {
  if (!signal.detected || !isPlainObject(signal.details)) {
    return false;
  }
  if (signal.details.ai_related === true) {
    return true;
  }
  const searchable = [
    signal.details.signature_issuer,
    signal.details.signature_common_name,
    signal.details.claim_generator,
    signal.details.title,
  ]
    .filter(Boolean)
    .map((value) => String(value).toLowerCase())
    .join(" ");
  return AI_SOURCE_TERMS.some((term) => searchable.includes(term));
}

function googleSourceRecord(signal) {
  if (!signal.detected || !isPlainObject(signal.details)) {
    return false;
  }
  const searchable = [signal.details.signature_issuer, signal.details.signature_common_name, signal.details.claim_generator]
    .filter(Boolean)
    .map((value) => String(value).toLowerCase())
    .join(" ");
  return searchable.includes("google") && !aiRelatedSourceRecord(signal);
}

function sourceRecordName(signal) {
  if (!isPlainObject(signal.details)) {
    return null;
  }
  for (const key of ["signature_issuer", "signature_common_name", "claim_generator"]) {
    const value = signal.details[key];
    if (value) {
      return String(value);
    }
  }
  return null;
}

function sourceRecordDetails(signal, originality) {
  const details = isPlainObject(signal.details) ? { ...signal.details } : {};
  details.originality_label = originality.label;
  details.originality_reasons = originality.reasons;
  return details;
}

function sourceRecordSummary(base, originality, copy) {
  return `${base}${fmt(copy.originality.summary, { label: originality.label })}`;
}

function originalitySentence(originality, copy) {
  const reasons = originality.reasons || [];
  const originalCopy = copy.originality;
  const reasonText = reasons.map((reason) => String(reason)).join(originalCopy.reason_joiner);
  if (reasonText) {
    return fmt(originalCopy.sentence_with_reasons, { label: originality.label, reasons: reasonText });
  }
  return fmt(originalCopy.sentence, { label: originality.label });
}

function fileOriginality(c2paSignal, copy, exifSignal) {
  const originalCopy = copy.originality;
  if (!c2paSignal.checked) {
    return { label: originalCopy.unknown, reasons: [originalCopy.unchecked_reason] };
  }

  const validationState = c2paValidationState(c2paSignal);
  if (c2paSignal.detected && validationState === "Valid") {
    return { label: originalCopy.strong, reasons: [originalCopy.valid_c2pa_reason] };
  }
  if (c2paSignal.detected) {
    return { label: originalCopy.limited, reasons: [originalCopy.invalid_c2pa_reason] };
  }
  if (exifSignal && richExif(exifSignal)) {
    return { label: originalCopy.strong, reasons: [originalCopy.rich_exif_reason] };
  }
  if (exifSignal && captureExif(exifSignal)) {
    return { label: originalCopy.limited, reasons: [originalCopy.partial_exif_reason] };
  }
  return { label: originalCopy.limited, reasons: [originalCopy.absent_reason] };
}

function exifFieldCount(signal) {
  if (!isPlainObject(signal.details)) {
    return 0;
  }
  const value = signal.details.field_count;
  return Number.isInteger(value) ? value : 0;
}

function richExif(signal) {
  return captureExif(signal) && exifFieldCount(signal) >= 5;
}

function captureExif(signal) {
  const fields = exifFields(signal);
  if (!signal.detected || Object.keys(fields).length === 0) {
    return false;
  }
  return Object.keys(fields).some((name) => CAPTURE_FIELD_NAMES.has(name));
}

function exifFields(signal) {
  if (!isPlainObject(signal.details)) {
    return {};
  }
  const fields = signal.details.fields;
  return isPlainObject(fields) ? fields : {};
}

function isPlainObject(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}
