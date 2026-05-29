# TrustPic Technical Stack

## Decision Summary

Use an API-first architecture:

- Backend: Python + FastAPI.
- Evidence engine: Python libraries around C2PA, image metadata, and ELA.
- Web v0 frontend: React + Vite.
- Future Mini Program frontend: Taro React or native WeChat Mini Program, consuming the same backend API.
- Shared contract: OpenAPI schema and generated or hand-maintained TypeScript types for the report JSON.
- Domestic product path: Web + WeChat Mini Program should stay first-class; see `docs/CHINA_WEB_MINIPROGRAM_ARCHITECTURE.md`.

This keeps v0 small while avoiding a rewrite of the core detection logic when Web and Mini Program clients diverge.

## Why Not One Frontend Codebase First?

Taro can target both H5 and WeChat Mini Program, but it imposes Mini Program constraints on the Web UI from day one. TrustPic v0 needs a fast, inspectable Web tool first. The UI surface is small enough that a later Mini Program client can reuse the API contract instead of sharing every component.

If Mini Program becomes the primary distribution channel earlier than expected, start with a native WeChat Mini Program shell that consumes the same API. Revisit Taro only if UI sharing becomes more valuable than platform-specific simplicity.

## Backend

### Stack

- Python 3.11 or 3.12.
- FastAPI for HTTP API and OpenAPI generation.
- Uvicorn for local serving.
- Pydantic for response models.
- Pillow for image loading, EXIF, format handling, and ELA.
- `c2pa-python` for C2PA reads.
- Optional later: OpenCV only if Pillow ELA is insufficient.

### Backend Responsibilities

- Validate file type, size, and image dimensions.
- Read the uploaded image in request scope only.
- Run v0 evidence checks:
  - C2PA
  - GB 45438 signal scan
  - EXIF summary
  - ELA metric and heatmap
- Return evidence-first JSON.
- Build localized user-facing `interpretation` text from the same evidence signals. v0 supports `locale=zh-CN` and `locale=en-US`.
- Serve generated heatmap as an in-memory response or short-lived derived asset.

### Backend Non-Goals For v0

- No GPU inference.
- No queue system.
- No user database.
- No object storage.
- No commercial detector APIs.

## Frontend

### Web v0

Use React + Vite + TypeScript.

Reasoning:

- Small app, no SEO or server-rendering need.
- Faster local startup than a full Next.js app.
- Easy upload/report UI.
- TypeScript types can mirror the backend report schema.
- Keeps frontend deployment simple.

### Future WeChat Mini Program

Preferred first domestic path: native WeChat Mini Program shell if we want lower platform risk for upload, domain, and review behavior.

Fallback path: Taro React if Web + Mini Program report UI reuse becomes the stronger priority.

Mini Program should not run the evidence engine locally. It should:

- choose or capture an image
- call `POST /api/v1/analyze`
- render the same report contract
- display derived heatmap if returned

## API Contract

The backend API is the durable boundary between clients.

Initial endpoints:

- `GET /api/v1/health`
- `POST /api/v1/analyze`

`POST /api/v1/analyze` accepts an optional `locale` query parameter. The backend falls back to Chinese for unsupported locales. The evidence schema stays the same; only user-facing labels, conclusions, evidence explanations, and boundary notes are localized.

Possible later endpoint:

- `GET /api/v1/reports/{report_id}` only if we deliberately add persistence.

The API should avoid Web-only assumptions so the Mini Program can consume it later.

## Repository Shape

Recommended v0 layout:

```text
TrustPic/
  backend/
    app/
      main.py
      models.py
      services/
        analyze.py
        c2pa.py
        gb45438.py
        exif.py
        ela.py
    tests/
    pyproject.toml
  web/
    src/
    package.json
  docs/
```

## Validation Plan

Backend:

- Unit-test each signal module with small fixtures.
- API-test `POST /api/v1/analyze` with valid, invalid, and oversized files.
- Snapshot-test response shape enough to protect the Mini Program contract.

Frontend:

- Manual local upload smoke test for v0.
- Later add Playwright once UI behavior stabilizes.

## Open Technical Questions

- Which exact C2PA sample files should be used as fixtures?
- Whether `c2pa-python` installs cleanly on the target deployment Python and platform.
- Whether GB 45438 scanning should start as simple byte/metadata detection or use a known open implementation.
- Whether heatmaps should be returned inline as base64 for v0 or exposed as a derived response endpoint.
- Whether v0 deploy target is local-only, a single VPS, or Cloudflare-fronted public demo. Decision: overseas v0 should use Cloudflare Pages for Web and a Railway container backend; see `docs/CLOUD_DEPLOYMENT.md`.
- Which domestic deployment path should preserve Web + Mini Program. Decision: keep a shared FastAPI API, deploy Web on domestic static hosting/CDN, deploy the backend container on CloudBase Run or equivalent, and build the Mini Program as an API-consuming client; see `docs/CHINA_WEB_MINIPROGRAM_ARCHITECTURE.md`.

## Current v0 Detection Notes

- GB 45438 starts as a conservative TC260 AIGC XMP namespace and byte-marker scanner. It checks for the `http://www.tc260.org.cn/ns/AIGC/1.0/` namespace, core TC260-style fields, and basic AIGC/GB marker terms.
- ELA starts as a heuristic review signal with a documented calibration script. It is not treated as proof of AI generation or tampering.
- Real sample audits should be run from local directories outside git using `backend/scripts/audit_sample_directory.py`.
