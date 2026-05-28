const MENU_ID = "trustpic-analyze-image";
const DEFAULT_API_BASE = "http://127.0.0.1:8000";
const contextTargets = new Map();

installContextMenus();

chrome.runtime.onInstalled.addListener(() => {
  installContextMenus();
  if (chrome.sidePanel?.setPanelBehavior) {
    chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => {});
  }
});

chrome.runtime.onStartup.addListener(() => {
  installContextMenus();
});

chrome.contextMenus.onShown.addListener((info, tab) => {
  updateContextMenu(Boolean(sourceUrlFromContext(info, tab)));
});

chrome.contextMenus.onHidden.addListener(() => {
  updateContextMenu(false);
});

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId !== MENU_ID) return;

  openReportPanel(tab);

  const sourceUrl = sourceUrlFromContext(info, tab);
  if (!sourceUrl) return;
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

  chrome.action.setBadgeText({ text: "..." });
  chrome.action.setBadgeBackgroundColor({ color: "#d97706" });

  try {
    const settings = await chrome.storage.local.get(["apiBase"]);
    const report = await analyzeImageUrl({
      sourceUrl,
      apiBase: settings.apiBase || DEFAULT_API_BASE,
      locale: browserLocale(),
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

chrome.runtime.onMessage.addListener((message, sender) => {
  if (message?.type !== "trustpic-context-target") return;

  const tabId = sender.tab?.id;
  if (!tabId) return;

  const imageUrl = normalizedContextImageUrl(message.imageUrl);
  contextTargets.set(tabId, {
    imageUrl,
    pageUrl: message.pageUrl || sender.tab?.url || "",
    at: Date.now(),
  });
  updateContextMenu(Boolean(imageUrl));
});

function installContextMenus() {
  const copy = menuCopy();
  chrome.contextMenus.removeAll(() => {
    chrome.contextMenus.create({
      id: MENU_ID,
      title: copy.analyze,
      contexts: ["all"],
      visible: false,
    });
  });
}

function updateContextMenu(visible) {
  chrome.contextMenus.update(
    MENU_ID,
    {
      title: menuCopy().analyze,
      visible,
    },
    () => {
      if (chrome.runtime.lastError) return;
      chrome.contextMenus.refresh?.();
    },
  );
}

function openReportPanel(tab) {
  if (!chrome.sidePanel?.open) return;

  if (tab?.id) {
    chrome.sidePanel.open({ tabId: tab.id }).catch((error) => {
      if (tab?.windowId) {
        chrome.sidePanel.open({ windowId: tab.windowId }).catch(() => {});
      }
      chrome.storage.local.set({
        lastError: error instanceof Error ? error.message : "Could not open TrustPic side panel.",
      });
    });
    return;
  }

  if (tab?.windowId) {
    chrome.sidePanel.open({ windowId: tab.windowId }).catch((error) => {
      chrome.storage.local.set({
        lastError: error instanceof Error ? error.message : "Could not open TrustPic side panel.",
      });
    });
  }
}

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

function sourceUrlFromContext(info, tab) {
  if (info.srcUrl) return info.srcUrl;

  const target = tab?.id ? contextTargets.get(tab.id) : null;
  if (target?.imageUrl && Date.now() - target.at < 5000) {
    return target.imageUrl;
  }

  return null;
}

function normalizedContextImageUrl(value) {
  if (!value) return null;
  const text = String(value);
  if (text.startsWith("http://") || text.startsWith("https://") || text.startsWith("data:image/")) return text;
  return null;
}

function browserLocale() {
  const languages = [chrome.i18n?.getUILanguage?.(), navigator.language].filter(Boolean);
  return languages.some((language) => String(language).toLowerCase().startsWith("zh")) ? "zh-CN" : "en-US";
}

function menuCopy() {
  if (browserLocale() === "zh-CN") {
    return {
      analyze: "用 TrustPic 分析图片",
    };
  }
  return {
    analyze: "Analyze image with TrustPic",
  };
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
