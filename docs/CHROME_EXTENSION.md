# TrustPic Chrome Extension

Last aligned: 2026-05-28

The Chrome extension is a self-use right-click client for the existing TrustPic API. It does not run evidence analysis locally. It fetches the selected page image, sends it to `POST /api/v1/analyze`, and renders the returned `interpretation` report in Chrome Side Panel.

## Current Shape

- Manifest V3 unpacked extension under `extension/`.
- Right-click image analysis:
  - right-click an image
  - choose `Analyze image with TrustPic`
  - the extension opens Chrome Side Panel, fetches the image bytes, calls the configured API, and updates the report in the side panel
- Side Panel supports:
  - API base URL setting
  - language selected automatically from the browser UI language
  - conclusion, confidence, AI evidence alert, core evidence, boundary notes, and heatmap display
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
2. Choose `Analyze image with TrustPic`.
3. The extension opens Chrome Side Panel when the analysis starts and updates it with the result.

For a direct image URL fallback:

1. Paste a direct JPG, PNG, or WebP URL into the side panel.
2. Click analyze.

## Boundaries

- The extension does not persist uploaded originals.
- The extension stores `apiBase`, the latest image URL, latest analysis status, and the latest returned report in Chrome local storage.
- The extension locale follows the browser UI language: Chinese browser UI uses `zh-CN`; other languages use `en-US`.
- URL analysis depends on Chrome extension host permissions and whether the URL returns image bytes.
- Authenticated, canvas-rendered, blob, or dynamically generated images may not be recoverable as original files through the extension.
- Right-click analysis usually sees the image URL currently used by the page, not necessarily the publisher's original file.
- For provenance-sensitive checks, compare right-click results with a locally saved original file in the Web app when available.
