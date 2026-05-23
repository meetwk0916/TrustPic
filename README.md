# TrustPic

TrustPic is a single-image evidence report tool for AI provenance and image integrity signals.

The v0 goal is not to prove whether every image is real or AI-generated. The v0 goal is to produce a usable, transparent report from supported evidence: C2PA, GB 45438 metadata/signals, EXIF, and ELA.

## Current Planning Docs

- [NotebookLM source](docs/notebooklm-ai-image-detection-spec-prototype.md)
- [v0 goals](docs/V0_GOALS.md)
- [technical stack](docs/TECH_STACK.md)

## Local Development

Backend:

```bash
cd backend
python3.11 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Web:

```bash
cd web
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

## v0 API

- `GET /api/v1/health`
- `POST /api/v1/analyze`

`POST /api/v1/analyze` accepts one `multipart/form-data` file field named `file`.
