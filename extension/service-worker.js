const MENU_ID = "trustpic-analyze-image";

syncContextMenu();

addChromeListener(chrome.runtime?.onInstalled, () => {
  syncContextMenu();
  if (chrome.sidePanel?.setPanelBehavior) {
    chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => {});
  }
});

addChromeListener(chrome.runtime?.onStartup, () => {
  syncContextMenu();
});

addChromeListener(chrome.contextMenus?.onClicked, async (info, tab) => {
  if (info.menuItemId !== MENU_ID) return;

  openReportPanel(tab);

  const sourceUrl = info.srcUrl;
  if (!sourceUrl) return;

  await chrome.storage.local.set({
    activeAnalysis: {
      status: "requested",
      sourceUrl,
      startedAt: Date.now(),
    },
    lastReport: null,
    lastError: null,
    lastSourceUrl: sourceUrl,
  });
});

addChromeListener(chrome.runtime?.onMessage, (message) => {
  if (message?.type === "trustpic-locale-changed") {
    const locale = isSupportedLocale(message.locale) ? message.locale : browserLocale();
    installContextMenus(locale);
  }
});

function addChromeListener(event, listener) {
  if (event?.addListener) {
    event.addListener(listener);
  }
}

async function syncContextMenu() {
  installContextMenus(await storedLocale());
}

function installContextMenus(locale = browserLocale()) {
  if (!chrome.contextMenus?.removeAll || !chrome.contextMenus?.create) return;

  const copy = menuCopy(locale);
  chrome.contextMenus.removeAll(() => {
    chrome.contextMenus.create({
      id: MENU_ID,
      title: copy.analyze,
      contexts: ["image"],
    });
  });
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

function browserLocale() {
  const languages = [chrome.i18n?.getUILanguage?.(), navigator.language].filter(Boolean);
  return languages.some((language) => String(language).toLowerCase().startsWith("zh")) ? "zh-CN" : "en-US";
}

async function storedLocale() {
  const settings = await chrome.storage.local.get(["locale"]);
  return isSupportedLocale(settings.locale) ? settings.locale : browserLocale();
}

function isSupportedLocale(value) {
  return value === "zh-CN" || value === "en-US";
}

function menuCopy(locale = browserLocale()) {
  if (locale === "zh-CN") {
    return {
      analyze: "用 TrustPic 分析图片",
    };
  }
  return {
    analyze: "Analyze image with TrustPic",
  };
}
