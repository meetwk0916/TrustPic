# TrustPic Chrome Extension

Last aligned: 2026-05-28

The Chrome extension is a self-use right-click client for the existing TrustPic API. It does not run evidence analysis locally. It fetches the selected page image, sends it to `POST /api/v1/analyze`, and renders the returned `interpretation` report in Chrome Side Panel.

## Current Shape

- Manifest V3 unpacked extension under `extension/`.
- Right-click image analysis:
  - right-click an image element on a page or standalone image page
  - choose `用 TrustPic 分析图片` on Chinese Chrome, or `Analyze image with TrustPic` on other Chrome UI languages
  - the extension opens Chrome Side Panel immediately, fetches the image bytes, calls the configured API, and updates the report in the side panel
  - the TrustPic menu is registered only for Chrome's native image context, so blank-area right-clicks do not show it
- Side Panel supports:
  - API base URL setting
  - language selected automatically from the browser UI language
  - conclusion, confidence, AI evidence alert, core evidence, local difference analysis, boundary notes, and heatmap display
  - expandable evidence explanations and technical details, aligned with the Web report structure
  - image URL fallback when right-click extraction is not available

## Run The API

Start the backend first:

```bash
cd backend
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The side panel defaults to:

```text
http://127.0.0.1:8000
```

You can change the API field in the side panel for a deployed backend.

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

For a direct image URL fallback:

1. Paste a direct JPG, PNG, or WebP URL into the side panel.
2. Click analyze.

## Boundaries

- The extension does not persist uploaded originals.
- The extension stores `apiBase`, the latest image URL, latest analysis status, and the latest returned report in Chrome local storage.
- The extension locale follows the browser UI language: Chinese browser UI uses `zh-CN`; other languages use `en-US`.
- URL analysis depends on Chrome extension host permissions and whether the URL returns image bytes.
- Authenticated, canvas-rendered, blob, or dynamically generated images may not be recoverable as original files through the extension.
- Right-click analysis usually sees the clicked element's image URL, not necessarily the publisher's original file.
- Background-image, canvas-rendered, or custom viewers that do not expose a native image context may need the direct URL fallback or Web app upload path.
- For provenance-sensitive checks, compare right-click results with a locally saved original file in the Web app when available.
