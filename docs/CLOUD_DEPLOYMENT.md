# TrustPic Overseas Cloud Deployment

Last aligned: 2026-05-28

This is the recommended v0 overseas deployment shape. TrustPic v0 analyzes one uploaded image in request scope and does not persist originals, reports, users, or jobs.

## Recommended Stack

- Web: Cloudflare Pages.
- API: containerized FastAPI service.
  - Recommended first deployment: Render Web Service or Fly.io container app behind `api.trustpic.example.com`.
  - Cloudflare-only path: Cloudflare Containers fronted by a Worker, once we are ready to operate that beta-style path.
- Database: none for v0.
- Object storage: none for v0.
- Queue/Redis: none for v0.
- GPU: none for v0.

## Why The API Is Not A Plain Worker

Cloudflare Pages is a good fit for the React/Vite Web app. The API is different: TrustPic depends on Python image-processing libraries such as Pillow and `c2pa-python`, and it performs request-time image decoding plus ELA. Plain Workers, including Python Workers, are not the conservative v0 target for this workload because native/package/runtime compatibility is the main deployment risk.

Use the existing Docker backend first. If we want an all-Cloudflare stack later, move that Docker image into Cloudflare Containers instead of rewriting the evidence engine for Workers.

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
- Node version: `22` via `web/.node-version`.

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

Cloudflare DNS:

- `trustpic.example.com`: attach as the custom domain on the Pages project.
- `api.trustpic.example.com`: CNAME to the backend host if using Render/Fly, or route to the Worker if using Cloudflare Containers.

After the frontend domain is final, update the backend:

```bash
TRUSTPIC_ALLOWED_ORIGINS=https://trustpic.example.com,https://www.trustpic.example.com
```

After the backend domain is final, update Pages:

```bash
VITE_API_BASE=https://api.trustpic.example.com
```

Then redeploy both sides.

## Edge And API Limits

Set these limits at the hosting or reverse-proxy layer:

- Maximum request body: 15 MB.
- Request timeout: 30-60 seconds.
- Basic rate limit: 10-30 analyze requests per IP per minute.

Do not log image bytes, base64 heatmaps, or full private EXIF fields in production logs.

## Cloudflare Settings

Recommended first pass:

- Turn on HTTPS redirects for the zone.
- Add a WAF/rate limiting rule for `POST /api/v1/analyze`.
- Start with 10 requests per IP per minute if the demo is public.
- Keep Cloudflare cache disabled for `/api/*`.
- Do not cache uploaded image requests or API responses.

The Web app can be cached normally as static assets. `web/public/_headers` adds conservative browser security headers to Pages output.

## Deployment Order

1. Deploy backend container and verify:

```bash
curl https://api.trustpic.example.com/api/v1/health
```

2. Set backend `TRUSTPIC_ALLOWED_ORIGINS` to the Cloudflare Pages preview URL while testing.
3. Create Cloudflare Pages project from `web`.
4. Set Pages `VITE_API_BASE` to the backend URL and `VITE_DEFAULT_LOCALE=en-US`.
5. Deploy Pages and test a real image upload.
6. Attach final custom domains.
7. Replace preview origins in `TRUSTPIC_ALLOWED_ORIGINS` with the final domain list.
8. Re-test Web upload, Chrome extension API base, and `/api/v1/health`.

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
