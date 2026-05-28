const DEFAULT_API_BASE = "http://127.0.0.1:8000";

const COPY = {
  "zh-CN": {
    subtitle: "右键图片证据报告",
    primaryHint: "在网页图片上右键，选择“用 TrustPic 分析这张图片”。如果是单独打开的图片页面，选择“用 TrustPic 分析当前图片页面”。",
    analyzeUrl: "分析",
    urlPlaceholder: "图片 URL",
    source: "图片来源",
    conclusion: "结论",
    aiEvidence: "AI 相关证据",
    coreEvidence: "核心证据",
    heatmap: "局部差异热图",
    notes: "报告怎么读",
    expand: "展开解释",
    means: "能说明什么",
    doesNotMean: "不能说明什么",
    waiting: "等待右键图片，或粘贴图片 URL。",
    loading: "分析中...",
    fetching: "正在读取图片 URL...",
    noUrl: "请输入图片 URL。",
    urlNotImage: "这个 URL 没有返回可分析的图片。",
    requestFailed: "分析失败",
  },
  "en-US": {
    subtitle: "Right-click image evidence report",
    primaryHint: "Right-click an image and choose Analyze image with TrustPic. If the image is open as its own page, choose Analyze current image page with TrustPic.",
    analyzeUrl: "Analyze",
    urlPlaceholder: "Image URL",
    source: "Image source",
    conclusion: "Conclusion",
    aiEvidence: "AI-related evidence",
    coreEvidence: "Core evidence",
    heatmap: "Local difference heatmap",
    notes: "How to read this report",
    expand: "Expand explanation",
    means: "What it can show",
    doesNotMean: "What it cannot show",
    waiting: "Right-click an image, or paste an image URL.",
    loading: "Analyzing...",
    fetching: "Fetching image URL...",
    noUrl: "Enter an image URL.",
    urlNotImage: "This URL did not return an analyzable image.",
    requestFailed: "Analysis failed",
  },
};

const state = {
  apiBase: DEFAULT_API_BASE,
  locale: browserLocale(),
};

const elements = {
  apiBase: document.getElementById("apiBase"),
  imageUrl: document.getElementById("imageUrl"),
  urlButton: document.getElementById("urlButton"),
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
  heatmapSection: document.getElementById("heatmapSection"),
  heatmap: document.getElementById("heatmap"),
  limits: document.getElementById("limits"),
  template: document.getElementById("evidenceTemplate"),
};

document.addEventListener("DOMContentLoaded", init);

async function init() {
  const saved = await chrome.storage.local.get(["activeAnalysis", "apiBase", "lastError", "lastReport", "lastSourceUrl"]);
  state.apiBase = normalizeApiBase(saved.apiBase || DEFAULT_API_BASE);

  elements.apiBase.value = state.apiBase;
  elements.imageUrl.value = saved.lastSourceUrl || "";

  applyCopy();
  bindEvents();
  renderStoredState(saved);
}

function bindEvents() {
  elements.apiBase.addEventListener("change", async () => {
    state.apiBase = normalizeApiBase(elements.apiBase.value || DEFAULT_API_BASE);
    elements.apiBase.value = state.apiBase;
    await chrome.storage.local.set({ apiBase: state.apiBase });
  });

  elements.urlButton.addEventListener("click", analyzeImageUrl);

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
  document.getElementById("primaryHint").textContent = copy.primaryHint;
  document.getElementById("urlButton").textContent = copy.analyzeUrl;
  document.getElementById("imageUrl").placeholder = copy.urlPlaceholder;
  document.getElementById("sourceLabel").textContent = copy.source;
  document.getElementById("conclusionLabel").textContent = copy.conclusion;
  document.getElementById("aiAlertLabel").textContent = copy.aiEvidence;
  document.getElementById("coreEvidenceLabel").textContent = copy.coreEvidence;
  document.getElementById("heatmapLabel").textContent = copy.heatmap;
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

async function analyzeImageUrl() {
  const copy = COPY[state.locale];
  const sourceUrl = elements.imageUrl.value.trim();
  if (!sourceUrl) {
    showNotice(copy.noUrl);
    return;
  }

  await chrome.storage.local.set({
    activeAnalysis: {
      status: "running",
      sourceUrl,
      startedAt: Date.now(),
    },
    lastReport: null,
    lastError: null,
    lastSourceUrl: sourceUrl,
  });
  renderSource(sourceUrl);

  try {
    showNotice(copy.fetching);
    const report = await analyzeUrlInSidePanel(sourceUrl);
    await chrome.storage.local.set({
      activeAnalysis: {
        status: "complete",
        sourceUrl,
        completedAt: Date.now(),
      },
      lastReport: report,
      lastSourceUrl: sourceUrl,
      lastAnalyzedAt: Date.now(),
      lastError: null,
    });
  } catch (error) {
    await chrome.storage.local.set({
      activeAnalysis: {
        status: "error",
        sourceUrl,
        completedAt: Date.now(),
      },
      lastError: error instanceof Error ? error.message : copy.requestFailed,
    });
  }
}

async function analyzeUrlInSidePanel(sourceUrl) {
  const response = await fetch(sourceUrl, {
    credentials: "include",
    cache: "no-store",
  });
  if (!response.ok) throw new Error(`Image request failed with ${response.status}`);

  const sourceBlob = await response.blob();
  const contentType = supportedImageType(sourceBlob.type, sourceUrl);
  if (!contentType) throw new Error(COPY[state.locale].urlNotImage);

  const imageBlob = sourceBlob.type === contentType ? sourceBlob : sourceBlob.slice(0, sourceBlob.size, contentType);
  const formData = new FormData();
  formData.append("file", imageBlob, filenameFromUrl(sourceUrl, contentType));

  const apiResponse = await fetch(analyzeEndpoint(), {
    method: "POST",
    body: formData,
  });
  if (!apiResponse.ok) {
    const payload = await apiResponse.json().catch(() => null);
    throw new Error(payload?.detail || `${COPY[state.locale].requestFailed}: ${apiResponse.status}`);
  }
  return apiResponse.json();
}

function renderSource(sourceUrl) {
  elements.sourceSection.hidden = false;
  elements.sourceLink.href = sourceUrl;
  elements.sourceLink.textContent = sourceUrl;
  elements.imageUrl.value = sourceUrl;
}

function renderReport(report) {
  elements.report.hidden = false;
  elements.confidenceValue.textContent = report.interpretation.confidence_label;
  elements.conclusionText.textContent = report.interpretation.conclusion;

  const evidence = report.interpretation.evidence_chain || [];
  renderAiAlert(evidence);
  renderEvidence(evidence.filter((item) => item.key !== "ela"));
  renderHeatmap(report.assets?.ela_heatmap_data_url);
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

function renderEvidence(evidence) {
  elements.evidenceList.replaceChildren();
  for (const item of evidence) {
    const node = elements.template.content.firstElementChild.cloneNode(true);
    node.classList.add(`evidence-${item.key}`);
    node.querySelector("h3").textContent = item.title;
    node.querySelector(".summary").textContent = item.summary;
    const status = node.querySelector(".status");
    status.textContent = item.status_label;
    status.classList.add(statusClass(item.status_label));
    node.querySelector(".expand-label").textContent = COPY[state.locale].expand;
    node.querySelector(".means-label").textContent = COPY[state.locale].means;
    node.querySelector(".does-not-label").textContent = COPY[state.locale].doesNotMean;
    node.querySelector(".means").textContent = item.means;
    node.querySelector(".does-not").textContent = item.does_not_mean;
    elements.evidenceList.append(node);
  }
}

function renderHeatmap(dataUrl) {
  if (!dataUrl) {
    elements.heatmapSection.hidden = true;
    return;
  }
  elements.heatmapSection.hidden = false;
  elements.heatmap.src = dataUrl;
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

function analyzeEndpoint() {
  return `${state.apiBase}/api/v1/analyze?locale=${encodeURIComponent(state.locale)}`;
}

function normalizeApiBase(value) {
  return String(value || DEFAULT_API_BASE).replace(/\/+$/, "");
}

function browserLocale() {
  const language = chrome.i18n?.getUILanguage?.() || navigator.language || "zh-CN";
  return language.toLowerCase().startsWith("zh") ? "zh-CN" : "en-US";
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
