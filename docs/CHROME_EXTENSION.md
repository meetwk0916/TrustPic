# TrustPic Chrome Extension

Last aligned: 2026-05-29

The Chrome extension has one purpose: right-click one image in Chrome and generate a TrustPic evidence report for that selected image. It runs the full evidence analysis **locally in the browser** — it fetches the selected image, inspects it on-device (C2PA, GB 45438/TC260, EXIF, ELA), and renders the `interpretation` report in Chrome Side Panel. No backend server is required and the image bytes never leave the browser.

## Current Shape

- Manifest V3 unpacked extension under `extension/`.
- Right-click image analysis:
  - right-click an image element on a page or standalone image page
  - choose `用 TrustPic 分析图片` on Chinese Chrome, or `Analyze image with TrustPic` on other Chrome UI languages
  - the extension opens Chrome Side Panel immediately, fetches the image bytes, analyzes them locally in the browser, and updates the report in the side panel
  - the TrustPic menu is registered only for Chrome's native image context, so blank-area right-clicks do not show it
- Side Panel supports:
  - language selected automatically from the browser UI language, with a manual Chinese/English switch in the panel header
  - conclusion, confidence, AI evidence alert, core evidence, local difference analysis, boundary notes, and heatmap display
  - expandable evidence explanations and technical details, aligned with the Web report structure
- All analysis runs on-device; the extension does not call any backend API and does not send the image anywhere.

## Architecture

All evidence analysis runs inside the extension. There is no API to run.

- `service-worker.js` registers the right-click menu, opens the Side Panel, and records the selected image URL.
- `sidepanel.js` (ES module) fetches the image, runs the local pipeline in `analysis/`, and renders the report.
- `analysis/` contains buildless JS ports of the evidence modules: `c2pa.js`, `gb45438.js`, `exif.js`, `ela.js`, `interpretation.js`, plus the `analyze.js` orchestrator and `run.js` fetch helper.

The optional FastAPI backend in `backend/` still powers the Web app, but the extension no longer depends on it. See [offline extension notes](OFFLINE_EXTENSION.md).

C2PA note: offline mode detects and reads a C2PA/JUMBF manifest and flags AI-related terms, but it cannot cryptographically verify the signature, so a detected manifest is reported as "needs attention" rather than a verified source.

## Load In Chrome

1. Open `chrome://extensions`.
2. Enable Developer mode.
3. Click `Load unpacked`.
4. Select the repository `extension/` directory.
5. Pin TrustPic from the extensions menu.

## Use

For a page image:

1. Right-click an image on a page.
2. Choose the TrustPic image analysis menu item.
3. The extension opens Chrome Side Panel when the analysis starts and updates it with the result.

For an image opened as its own browser tab:

1. Right-click the image itself.
2. Choose the same TrustPic image analysis menu item.

For unsupported image viewers:

1. Use the Web app upload path.
2. Or open the direct JPG, PNG, or WebP file URL and right-click the image.

## Boundaries

- The extension does not persist uploaded originals.
- The extension stores the latest image URL, latest analysis status, and the latest returned report in Chrome local storage.
- The extension locale defaults from the browser UI language, then can be switched manually. The selected locale is stored locally and reused for later right-click analyses.
- URL analysis depends on Chrome extension host permissions and whether the URL returns image bytes.
- Authenticated, canvas-rendered, blob, or dynamically generated images may not be recoverable as original files through the extension.
- Right-click analysis usually sees the clicked element's image URL, not necessarily the publisher's original file.
- Background-image, canvas-rendered, or custom viewers that do not expose a native image context may need the Web app upload path.
- For provenance-sensitive checks, compare right-click results with a locally saved original file in the Web app when available.

## Package For Chrome Web Store

```bash
sh extension/package.sh
```

The package is written to the repository root as `trustpic-chrome-<version>.zip`. The ZIP root contains `manifest.json`, which is required for Chrome Web Store upload.
