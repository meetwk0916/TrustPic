# TrustPic Overseas Cloud Deployment

Last aligned: 2026-05-27

This is the recommended v0 overseas deployment shape. TrustPic v0 analyzes one uploaded image in request scope and does not persist originals, reports, users, or jobs.

## Recommended Stack

- Web: Cloudflare Pages.
- API: Render Web Service or Fly.io container app.
- Database: none for v0.
- Object storage: none for v0.
- Queue/Redis: none for v0.
- GPU: none for v0.

## Sizing

Start the backend at:

- 2 vCPU.
- 2 GB RAM minimum.
- 4 GB RAM preferred if public traffic or large images are expected.
- 1 Uvicorn worker.

Keep `workers=1` initially. Pillow image decode and ELA can create multiple in-memory image copies, so multiple workers may exhaust small instances when users upload large files.

## Backend

The backend Docker image is defined in `backend/Dockerfile`.

Runtime command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

Required environment variables:

```bash
TRUSTPIC_ALLOWED_ORIGINS=https://trustpic.example.com
TRUSTPIC_MAX_UPLOAD_MB=15
TRUSTPIC_MAX_PIXELS=40000000
```

See `backend/.env.example`.

For multiple frontend origins, use comma-separated values:

```bash
TRUSTPIC_ALLOWED_ORIGINS=https://trustpic.example.com,https://www.trustpic.example.com
```

Health check:

```text
/api/v1/health
```

## Render Setup

The repository includes `render.yaml`.

Recommended Render service:

- Type: Web Service.
- Runtime: Docker.
- Root directory: `backend`.
- Plan: Standard or equivalent 2 GB+ RAM instance.
- Health check path: `/api/v1/health`.

After the API URL is assigned, set `TRUSTPIC_ALLOWED_ORIGINS` to the final Cloudflare Pages domain or custom frontend domain.

## Cloudflare Pages Setup

Create a Pages project from the repository with:

- Root directory: `web`.
- Build command: `npm run build`.
- Build output directory: `dist`.

Set:

```bash
VITE_API_BASE=https://api.trustpic.example.com
VITE_DEFAULT_LOCALE=en-US
```

See `web/.env.example`.

Then rebuild the Pages deployment.

`VITE_DEFAULT_LOCALE=en-US` makes the overseas Web app open in English by default. Users can still switch between English and Chinese in the UI; the frontend passes `locale=en-US` or `locale=zh-CN` to `POST /api/v1/analyze`, and the backend returns localized report interpretation text from the same evidence logic.

## Domains

Recommended:

- `trustpic.example.com`: Cloudflare Pages frontend.
- `api.trustpic.example.com`: backend service.

Both must use HTTPS.

## Edge And API Limits

Set these limits at the hosting or reverse-proxy layer:

- Maximum request body: 15 MB.
- Request timeout: 30-60 seconds.
- Basic rate limit: 10-30 analyze requests per IP per minute.

Do not log image bytes, base64 heatmaps, or full private EXIF fields in production logs.

## Not Needed In v0

Do not add these until there is a product requirement:

- persistent image storage
- report history
- user accounts
- batch jobs
- async queue
- commercial detector API keys
- GPU inference

Add Postgres, object storage, and a queue only when TrustPic needs saved reports, user history, or batch analysis.
