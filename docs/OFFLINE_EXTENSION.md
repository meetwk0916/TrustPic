# TrustPic Offline Extension (self-contained, no backend)

Last aligned: 2026-06-17

## Goal

Run the full TrustPic v0 evidence pipeline entirely inside the Chrome extension,
with no cloud backend and no network call other than fetching the selected image
itself. The extension can be loaded unpacked (or zipped for the store) and works
on its own.

## Architecture

- `service-worker.js`: registers the right-click context menu, opens the Side
  Panel, and records the requested image URL in `chrome.storage.local`. It does
  not call any API.
- `sidepanel.js` (ES module): owns the analysis. On a new request it fetches the
  image bytes, runs the local pipeline, builds the bilingual report, and renders
  it. Locale switches re-run the pipeline locally.
- `analysis/`: pure-JS port of the backend evidence modules.
  - `gb45438.js`: GB 45438 / TC260 byte-marker and XMP scan.
  - `exif.js`: minimal TIFF/IFD0 EXIF reader (JPEG APP1, PNG `eXIf`, WebP `EXIF`).
  - `ela.js`: Canvas-based ELA (re-encode JPEG q=90, amplified diff, tile-level
    local-difference analysis, heatmap data URL).
  - `c2pa.js`: heuristic C2PA reader. Detects a C2PA/JUMBF manifest, extracts
    best-effort source strings, and flags AI-related terms. It does **not**
    cryptographically verify the signature, so `validation_state` is always
    unknown in offline mode.
  - `interpretation.js`: faithful port of the bilingual interpretation layer.
  - `analyze.js`: orchestrator producing the same report shape as the backend
    `AnalyzeResponse`.
  - `run.js`: fetch image + run `analyze` for the Side Panel.

## C2PA fidelity note

Offline mode reports C2PA presence and readable source/AI clues, but cannot
return a `Valid` signature state. A detected manifest therefore surfaces as
"needs attention" rather than a verified source. This is intentional and honest:
the extension only claims what it can actually read without a backend toolkit.

## Build / deploy

No build step. Load `extension/` unpacked, or run `extension/package.sh` to
produce the store ZIP.
