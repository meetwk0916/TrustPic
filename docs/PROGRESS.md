# TrustPic Progress

Last aligned: 2026-05-23

## Current State

TrustPic is at a runnable v0 prototype checkpoint.

The current implementation includes:

- Backend FastAPI service with `GET /api/v1/health` and `POST /api/v1/analyze`.
- Single-image upload validation for JPG, PNG, and WebP MIME types.
- Evidence modules for C2PA read attempts, GB 45438/AIGC byte-marker scan, EXIF summary, and ELA heatmap generation.
- Evidence-first report contract with verdict, summary, signals, limitations, recommendation, and `assets.ela_heatmap_data_url`.
- React + Vite Web UI for selecting an image, previewing it, showing file metadata, calling the backend, and displaying the report, signal details, and ELA heatmap.
- Local sample-image generator for repeatable smoke checks.
- CodeGraph index initialized for the project.
- Git repository initialized and pushed to `origin/main`.

## Verified Locally

Validated on 2026-05-23:

```bash
cd backend
.venv/bin/python -m pytest
```

Result: `3 passed`.

Validated again after negative-path coverage was added:

```bash
cd backend
.venv/bin/python -m pytest
```

Result: `8 passed`.

Validated again after public C2PA sample verification and C2PA false-positive coverage were added:

```bash
cd backend
.venv/bin/python -m pytest
```

Result: `9 passed`.

Validated again after representative EXIF, metadata-stripped, and ELA review coverage were added:

```bash
cd backend
.venv/bin/python -m pytest
```

Result: `11 passed`.

```bash
cd web
npm run build
```

Result: TypeScript build and Vite production build passed.

Manual smoke checks also passed:

- Backend `GET /api/v1/health` returned `{"status":"ok"}`.
- Frontend dev server returned HTTP 200 at `http://127.0.0.1:5173/`.
- A temporary PNG upload to `POST /api/v1/analyze` returned a complete `success` report with all four signal sections.
- Generated smoke samples are documented in `docs/SAMPLE_VERIFICATION.md`.
- Generated `plain.png`, `marked-aigc.png`, `camera-exif.jpg`, `metadata-stripped.jpg`, `edited-compressed.jpg`, and `ela-review-compressed.jpg` were uploaded through `scripts/verify_samples.py`; all matched expected outcomes.
- `scripts/verify_samples.py --download-public` verified public `contentauth/c2pa-attacks` sample `C.jpg` with `c2pa_status: detected` and `c2pa_validation_state: Valid`.

## Git And Index

- Remote: `https://github.com/meetwk0916/TrustPic`
- Branch: `main`
- Initial commit: `dfb0104 Initial TrustPic v0 prototype`
- CodeGraph status: up to date, 16 indexed code files, 125 nodes, 203 edges.

## Not Blocked By API Quota

The current v0 does not depend on OpenAI API quota or commercial detector APIs.

Deferred quota/API-dependent directions remain:

- OpenAI Verify automation.
- SynthID direct detection.
- Commercial third-party detector API fallback.
- Chrome extension integration.

## Remaining Work To Finish v0

The v0 goal is not complete until the success criteria in `docs/V0_GOALS.md` are verified against representative samples.

Highest-priority gaps:

- Add real user-supplied or production-source sample records for:
  - camera image with EXIF, beyond generated EXIF
  - metadata-stripped image from an actual platform flow
  - production C2PA sample from a real tool or device
  - edited or recompressed image with a known real edit history
- Decide whether the GB 45438 scanner stays as a byte-marker v0 scan or moves to a known implementation.
- Calibrate or document the ELA threshold with sample images instead of relying only on the current heuristic.
- Confirm C2PA behavior with a production C2PA image sample, not only a public test/security sample.

## Next Recommended Step

Start with backend confidence before expanding product surface:

1. Add real user-supplied sample evidence for EXIF, platform-stripped metadata, production C2PA, and known edit-history files.
2. Re-run backend tests and frontend build.
3. Commit the v0 real-sample verification results.
