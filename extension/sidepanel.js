const COPY = {
  "zh-CN": {
    subtitle: "右键图片证据报告",
    source: "图片来源",
    confidence: "置信度",
    conclusion: "结论",
    aiEvidence: "AI 相关证据",
    coreEvidence: "核心证据",
    localDifference: "局部差异分析",
    heatmap: "局部差异热图",
    heatmapAlt: "ELA 热图",
    notes: "报告怎么读",
    expand: "展开解释",
    means: "能说明什么",
    doesNotMean: "不能说明什么",
    technicalDetails: "技术细节",
    waiting: "在网页图片上右键，选择“用 TrustPic 分析图片”。",
    loading: "分析中...",
    requestFailed: "分析失败",
  },
  "en-US": {
    subtitle: "Right-click image evidence report",
    source: "Image source",
    confidence: "Confidence",
    conclusion: "Conclusion",
    aiEvidence: "AI-related evidence",
    coreEvidence: "Core evidence",
    localDifference: "Local difference analysis",
    heatmap: "Local difference heatmap",
    heatmapAlt: "ELA heatmap",
    notes: "How to read this report",
    expand: "Expand explanation",
    means: "What it can show",
    doesNotMean: "What it cannot show",
    technicalDetails: "Technical details",
    waiting: "Right-click a page image and choose Analyze image with TrustPic.",
    loading: "Analyzing...",
    requestFailed: "Analysis failed",
  },
};

const state = {
  locale: browserLocale(),
};

const elements = {
  notice: document.getElementById("notice"),
  sourceSection: document.getElementById("sourceSection"),
  sourceLink: document.getElementById("sourceLink"),
  report: document.getElementById("report"),
  confidenceValue: document.getElementById("confidenceValue"),
  conclusionText: document.getElementById("conclusionText"),
  evidenceList: document.getElementById("evidenceList"),
  aiAlert: document.getElementById("aiAlert"),
  aiAlertSummary: document.getElementById("aiAlertSummary"),
  aiAlertMeans: document.getElementById("aiAlertMeans"),
  localDifferenceSection: document.getElementById("localDifferenceSection"),
  localDifferenceEvidence: document.getElementById("localDifferenceEvidence"),
  heatmapPanel: document.getElementById("heatmapPanel"),
  heatmap: document.getElementById("heatmap"),
  limits: document.getElementById("limits"),
  template: document.getElementById("evidenceTemplate"),
};

document.addEventListener("DOMContentLoaded", init);

async function init() {
  const saved = await chrome.storage.local.get(["activeAnalysis", "lastError", "lastReport", "lastSourceUrl"]);

  applyCopy();
  bindEvents();
  renderStoredState(saved);
}

function bindEvents() {
  chrome.storage.onChanged.addListener((changes, areaName) => {
    if (areaName !== "local") return;
    const next = {};
    for (const [key, change] of Object.entries(changes)) {
      next[key] = change.newValue;
    }
    renderStoredState(next);
  });
}

function applyCopy() {
  const copy = COPY[state.locale];
  document.documentElement.lang = state.locale === "en-US" ? "en" : "zh-CN";
  document.getElementById("subtitle").textContent = copy.subtitle;
  document.getElementById("sourceLabel").textContent = copy.source;
  document.getElementById("confidenceLabel").textContent = copy.confidence;
  document.getElementById("conclusionLabel").textContent = copy.conclusion;
  document.getElementById("aiAlertLabel").textContent = copy.aiEvidence;
  document.getElementById("coreEvidenceLabel").textContent = copy.coreEvidence;
  document.getElementById("localDifferenceLabel").textContent = copy.localDifference;
  document.getElementById("heatmapLabel").textContent = copy.heatmap;
  document.getElementById("heatmap").alt = copy.heatmapAlt;
  document.getElementById("notesLabel").textContent = copy.notes;
  document.getElementById("localeBadge").textContent = state.locale;
}

function renderStoredState(saved) {
  if (saved.activeAnalysis?.sourceUrl) {
    renderSource(saved.activeAnalysis.sourceUrl);
  }
  if (saved.lastSourceUrl) {
    renderSource(saved.lastSourceUrl);
  }
  if (saved.activeAnalysis?.status === "running") {
    showNotice(COPY[state.locale].loading);
  }
  if (saved.lastError) {
    showNotice(saved.lastError);
  }
  if (saved.lastReport) {
    renderReport(saved.lastReport);
    hideNotice();
  }
  if (!saved.activeAnalysis && !saved.lastError && !saved.lastReport) {
    showNotice(COPY[state.locale].waiting);
  }
}

function renderSource(sourceUrl) {
  elements.sourceSection.hidden = false;
  elements.sourceLink.href = sourceUrl;
  elements.sourceLink.textContent = sourceUrl;
}

function renderReport(report) {
  elements.report.hidden = false;
  elements.confidenceValue.textContent = report.interpretation.confidence_label;
  elements.conclusionText.textContent = report.interpretation.conclusion;

  const evidence = report.interpretation.evidence_chain || [];
  const coreEvidence = evidence.filter((item) => item.key !== "ela");
  const localDifference = evidence.find((item) => item.key === "ela") || null;
  renderAiAlert(evidence);
  renderEvidence(coreEvidence, elements.evidenceList);
  renderLocalDifference(localDifference, report.assets?.ela_heatmap_data_url);
  renderLimits(report.interpretation.limits || []);
}

function renderAiAlert(evidence) {
  const alert = aiStrongAlert(evidence);
  if (!alert) {
    elements.aiAlert.hidden = true;
    return;
  }
  elements.aiAlert.hidden = false;
  elements.aiAlertSummary.textContent = alert.summary;
  elements.aiAlertMeans.textContent = alert.means;
}

function renderEvidence(evidence, container) {
  container.replaceChildren();
  for (const item of evidence) {
    const node = elements.template.content.firstElementChild.cloneNode(true);
    node.classList.add(`evidence-${item.key}`);
    node.querySelector("h3").textContent = item.title;
    node.querySelector(".summary").textContent = item.summary;
    const status = node.querySelector(".status");
    status.textContent = item.status_label;
    status.classList.add(statusClass(item.status_label));
    status.classList.add(`signal-${item.key}`);
    node.querySelector(".expand-label").textContent = COPY[state.locale].expand;
    node.querySelector(".means-label").textContent = COPY[state.locale].means;
    node.querySelector(".does-not-label").textContent = COPY[state.locale].doesNotMean;
    node.querySelector(".means").textContent = item.means;
    node.querySelector(".does-not").textContent = item.does_not_mean;
    const technicalDetails = node.querySelector(".technical-details");
    const technicalPre = technicalDetails.querySelector("pre");
    if (item.details && Object.keys(item.details).length > 0) {
      technicalDetails.hidden = false;
      node.querySelector(".technical-label").textContent = COPY[state.locale].technicalDetails;
      technicalPre.textContent = JSON.stringify(item.details, null, 2);
    }
    container.append(node);
  }
}

function renderLocalDifference(evidence, heatmapUrl) {
  if (!evidence && !heatmapUrl) {
    elements.localDifferenceSection.hidden = true;
    return;
  }

  elements.localDifferenceSection.hidden = false;
  renderEvidence(evidence ? [evidence] : [], elements.localDifferenceEvidence);

  if (!heatmapUrl) {
    elements.heatmapPanel.hidden = true;
    elements.heatmap.removeAttribute("src");
    return;
  }
  elements.heatmapPanel.hidden = false;
  elements.heatmap.src = heatmapUrl;
}

function renderLimits(limits) {
  elements.limits.replaceChildren();
  for (const limit of limits) {
    const li = document.createElement("li");
    li.textContent = limit;
    elements.limits.append(li);
  }
}

function statusClass(status) {
  if (status === "支持证据" || status === "Supporting evidence") return "status-support";
  if (status === "需留意" || status === "Needs attention") return "status-warning";
  if (status === "无法分析" || status === "Not analyzed") return "status-unavailable";
  return "status-neutral";
}

function aiStrongAlert(evidence) {
  const marker = evidence.find((item) => item.key === "gb45438" && isSupportingEvidence(item.status_label));
  if (marker) return marker;

  const source = evidence.find((item) => item.key === "c2pa");
  if (!source) return null;
  if (source.details?.ai_related === true) return source;

  const text = [
    source.summary,
    source.means,
    source.details?.signature_issuer,
    source.details?.signature_common_name,
    source.details?.claim_generator,
    source.details?.title,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  const terms = ["openai", "dall-e", "dalle", "gemini", "notebooklm", "imagen", "synthid", "nano banana"];
  return terms.some((term) => text.includes(term)) ? source : null;
}

function isSupportingEvidence(status) {
  return status === "支持证据" || status === "Supporting evidence";
}

function showNotice(message) {
  elements.notice.textContent = message;
}

function hideNotice() {
  elements.notice.textContent = "";
}

function browserLocale() {
  const languages = [chrome.i18n?.getUILanguage?.(), navigator.language].filter(Boolean);
  return languages.some((language) => String(language).toLowerCase().startsWith("zh")) ? "zh-CN" : "en-US";
}

function supportedImageType(contentType, url) {
  const normalized = String(contentType || "").split(";")[0].trim().toLowerCase();
  if (["image/jpeg", "image/png", "image/webp"].includes(normalized)) return normalized;

  const lowerUrl = String(url || "").split("?")[0].toLowerCase();
  if (lowerUrl.startsWith("data:image/jpeg") || lowerUrl.startsWith("data:image/jpg")) return "image/jpeg";
  if (lowerUrl.startsWith("data:image/png")) return "image/png";
  if (lowerUrl.startsWith("data:image/webp")) return "image/webp";
  if (lowerUrl.endsWith(".jpg") || lowerUrl.endsWith(".jpeg")) return "image/jpeg";
  if (lowerUrl.endsWith(".png")) return "image/png";
  if (lowerUrl.endsWith(".webp")) return "image/webp";
  return null;
}

function filenameFromUrl(url, contentType) {
  const fallback = contentType.includes("png") ? "image.png" : contentType.includes("webp") ? "image.webp" : "image.jpg";
  try {
    const pathname = new URL(url).pathname;
    const segment = pathname.split("/").filter(Boolean).pop();
    return segment || fallback;
  } catch {
    return fallback;
  }
}
