document.addEventListener(
  "contextmenu",
  (event) => {
    try {
      const pending = chrome.runtime.sendMessage({
        type: "trustpic-context-target",
        imageUrl: imageUrlFromTarget(event.target),
        pageUrl: location.href,
      });
      pending?.catch?.(() => {});
    } catch {
      // Ignore pages where extension messaging is unavailable.
    }
  },
  true,
);

function imageUrlFromTarget(target) {
  if (!(target instanceof Element)) return null;

  const image = target.closest("img");
  if (image instanceof HTMLImageElement) {
    return absoluteUrl(image.currentSrc || image.src);
  }

  if (target instanceof SVGImageElement) {
    return absoluteUrl(target.href?.baseVal);
  }

  return backgroundImageUrl(target);
}

function backgroundImageUrl(element) {
  const value = window.getComputedStyle(element).backgroundImage;
  if (!value || value === "none") return null;

  const match = value.match(/url\((["']?)(.*?)\1\)/);
  if (!match?.[2]) return null;
  return absoluteUrl(match[2]);
}

function absoluteUrl(value) {
  if (!value) return null;
  try {
    return new URL(value, location.href).href;
  } catch {
    return null;
  }
}
