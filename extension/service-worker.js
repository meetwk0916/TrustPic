const MENU_ID = "trustpic-analyze-image";
const DEFAULT_API_BASE = "http://127.0.0.1:8000";

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: MENU_ID,
    title: "Analyze image with TrustPic",
    contexts: ["image"],
  });
});

chrome.contextMenus.onClicked.addListener(async (info) => {
  if (info.menuItemId !== MENU_ID || !info.srcUrl) return;

  const sourceUrl = info.srcUrl;
  await chrome.storage.local.set({
    activeAnalysis: {
      status: "running",
      sourceUrl,
      startedAt: Date.now(),
    },
    lastError: null,
  });

  chrome.action.setBadgeText({ text: "..." });
  chrome.action.setBadgeBackgroundColor({ color: "#d97706" });

  await chrome.windows.create({
    url: chrome.runtime.getURL("popup.html"),
    type: "popup",
    width: 460,
    height: 720,
  });

  try {
    const settings = await chrome.storage.local.get(["apiBase", "locale"]);
    const report = await analyzeImageUrl({
      sourceUrl,
      apiBase: settings.apiBase || DEFAULT_API_BASE,
      locale: settings.locale || "zh-CN",
    });

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
    chrome.action.setBadgeText({ text: "" });
  } catch (error) {
    await chrome.storage.local.set({
      activeAnalysis: {
        status: "error",
        sourceUrl,
        completedAt: Date.now(),
      },
      lastError: error instanceof Error ? error.message : "Analysis failed",
    });
    chrome.action.setBadgeText({ text: "!" });
    chrome.action.setBadgeBackgroundColor({ color: "#dc2626" });
  }
});

async function analyzeImageUrl({ sourceUrl, apiBase, locale }) {
  const imageResponse = await fetch(sourceUrl, {
    credentials: "include",
    cache: "no-store",
  });
  if (!imageResponse.ok) {
    throw new Error(`Image request failed with ${imageResponse.status}`);
  }

  const sourceBlob = await imageResponse.blob();
  const contentType = supportedImageType(sourceBlob.type, sourceUrl);
  if (!contentType) {
    throw new Error("This image format is not supported. Use JPG, PNG, or WebP.");
  }

  const imageBlob = sourceBlob.type === contentType ? sourceBlob : sourceBlob.slice(0, sourceBlob.size, contentType);
  const formData = new FormData();
  formData.append("file", imageBlob, filenameFromUrl(sourceUrl, contentType));

  const response = await fetch(analyzeEndpoint(apiBase, locale), {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail || `TrustPic API failed with ${response.status}`);
  }
  return response.json();
}

function analyzeEndpoint(apiBase, locale) {
  const base = String(apiBase || DEFAULT_API_BASE).replace(/\/+$/, "");
  return `${base}/api/v1/analyze?locale=${encodeURIComponent(locale || "zh-CN")}`;
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
