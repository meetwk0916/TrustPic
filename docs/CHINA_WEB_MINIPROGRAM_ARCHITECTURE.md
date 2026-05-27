# TrustPic China Web + Mini Program Architecture

Last aligned: 2026-05-27

This document keeps the domestic product path explicit. Overseas v0 deployment is for fast public testing; the domestic version should preserve a Web + WeChat Mini Program architecture that shares the same backend report contract.

## Product Shape

- Web: public H5/Web app for desktop and mobile browsers.
- Mini Program: WeChat Mini Program client for image selection, upload, and report rendering.
- Backend: one FastAPI evidence API shared by both clients.
- Report contract: `backend/app/models.py` remains the durable boundary. Web and Mini Program should render the same `interpretation` object.

## Recommended Domestic Stack

Use Tencent CloudBase first unless there is a clear reason to split vendors:

- Web hosting: CloudBase static website hosting or COS + CDN.
- API hosting: CloudBase Run / cloud hosting with the existing backend container.
- Optional storage later: CloudBase cloud storage or COS for short-lived derived assets only.
- Optional database later: CloudBase database or TencentDB/Postgres for report metadata only.
- Mini Program: native WeChat Mini Program or Taro React.

CloudBase is the preferred first domestic target because it is designed for Mini Program, Web, backend compute, storage, database, and static hosting in one platform.

## Runtime Architecture

```text
User
  |
  | Web browser
  v
CloudBase static hosting / CDN
  |
  | HTTPS POST /api/v1/analyze
  v
CloudBase Run container
  |
  | in-request image analysis only
  v
FastAPI TrustPic backend

User
  |
  | WeChat Mini Program
  v
wx.uploadFile / HTTPS
  |
  v
Same FastAPI TrustPic backend
```

Do not fork the evidence engine for Mini Program. The Mini Program should only:

- choose or capture an image
- upload the image to `POST /api/v1/analyze`
- render conclusion, confidence, evidence chain, foldable details, and heatmap
- show the same boundary wording as Web

## Backend Config

The current backend container path can be reused:

- `backend/Dockerfile`
- `/api/v1/health`
- `/api/v1/analyze`

Domestic environment variables:

```bash
TRUSTPIC_ALLOWED_ORIGINS=https://trustpic.example.cn,https://www.trustpic.example.cn
TRUSTPIC_MAX_UPLOAD_MB=15
TRUSTPIC_MAX_PIXELS=40000000
```

If Mini Program uploads hit the API directly, configure the Mini Program request/upload legal domain to the API domain and keep it HTTPS.

## Domain Plan

Recommended:

- `trustpic.example.cn`: Web app.
- `api.trustpic.example.cn`: shared API.

Domestic production traffic should assume:

- ICP filing may be required for custom mainland China domains.
- WeChat Mini Program requires configured legal request/upload domains.
- HTTPS is required.
- CDN, API, and Mini Program domains should be planned before public review.

## Storage Policy

v0 domestic version should keep the same privacy posture as overseas v0:

- Do not persist uploaded originals.
- Do not log image bytes, base64 heatmaps, or full private EXIF.
- Return the heatmap inline for v0.
- Add object storage only when derived assets must be saved or shared.

When storage is added, prefer:

- short-lived object keys
- lifecycle expiration
- separated original and derived asset buckets
- no public-read original image bucket

## Mini Program Client Choice

Start with one of two paths:

### Native WeChat Mini Program

Use if the first domestic release should optimize for WeChat review, upload APIs, platform UI conventions, and low runtime risk.

Pros:

- closest to WeChat platform behavior
- fewer cross-compile surprises
- easier to reason about upload and domain restrictions

Cons:

- Web and Mini Program UI code diverge
- report components need to be implemented twice

### Taro React

Use if Web + Mini Program UI reuse becomes more important.

Pros:

- React-like development
- possible sharing of report rendering logic
- easier for future H5/Mini Program alignment

Cons:

- Mini Program constraints still need explicit testing
- cross-platform abstractions can obscure platform-specific upload behavior

Recommended first domestic implementation: native Mini Program shell that consumes the existing API. Revisit Taro only after the report UI stabilizes further.

## Release Sequence

1. Keep Web v0 stable on the shared API contract.
2. Deploy backend container to domestic cloud hosting.
3. Deploy Web to domestic static hosting/CDN.
4. Configure API CORS and Mini Program legal domains.
5. Build Mini Program upload/report shell against `/api/v1/analyze`.
6. Run the same real sample suite against domestic deployment.
7. Add persistence only if users need saved report history.

## Not In First Domestic Release

- user accounts
- report history
- paid plan
- batch analysis
- persistent original image storage
- GPU model inference
- separate Mini Program evidence engine
