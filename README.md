# TrustPic

TrustPic is a single-image evidence report tool for AI provenance and image integrity signals.

The v0 goal is not to prove whether every image is real or AI-generated. The v0 goal is to produce a usable, transparent report from supported evidence: C2PA, GB 45438 metadata/signals, EXIF, and ELA.

## Current Planning Docs

- [NotebookLM source](docs/notebooklm-ai-image-detection-spec-prototype.md)
- [v0 goals](docs/V0_GOALS.md)
- [technical stack](docs/TECH_STACK.md)
- [current progress](docs/PROGRESS.md)
- [v0 release checklist](docs/V0_RELEASE_CHECKLIST.md)
- [sample verification](docs/SAMPLE_VERIFICATION.md)
- [ELA calibration](docs/ELA_CALIBRATION.md)
- [real sample intake](docs/REAL_SAMPLE_INTAKE.md)
- [v0 real sample suite](docs/V0_REAL_SAMPLE_SUITE.md)
- [report interpretation guide](docs/REPORT_INTERPRETATION_GUIDE.md)
- [overseas cloud deployment](docs/CLOUD_DEPLOYMENT.md)
- [China Web + Mini Program architecture](docs/CHINA_WEB_MINIPROGRAM_ARCHITECTURE.md)
- [Chrome extension](docs/CHROME_EXTENSION.md)
- [Chrome Web Store notes](docs/CHROME_EXTENSION_STORE.md)
- [public dataset suite example](docs/public-dataset-suite.example.json)
- [first-phase minimum coverage suite](docs/public-dataset-first-phase.example.json)
- [v0 release coverage suite](docs/public-dataset-v0-release.example.json)
- [public dataset remote catalog example](docs/public-dataset-remote-catalog.example.json)

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

Chrome extension:

```bash
# Store build uses https://trustpic-production.up.railway.app by default.
# For local development, start the backend first, then load extension/ as an unpacked extension in Chrome.
# Right-click a page image and choose "Analyze image with TrustPic".
cd backend
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Chrome Web Store package and privacy policy:

```bash
sh extension/package.sh
# Privacy policy is published with the Web app at /privacy.html.
```

## v0 API

- `GET /api/v1/health`
- `POST /api/v1/analyze`

`POST /api/v1/analyze` accepts one `multipart/form-data` file field named `file`.
It also accepts optional `locale=zh-CN` or `locale=en-US` to localize the user-facing report interpretation.
