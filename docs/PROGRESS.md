# TrustPic Progress

Last aligned: 2026-05-25

## Current State

TrustPic is at a runnable v0 prototype checkpoint.

The current implementation includes:

- Backend FastAPI service with `GET /api/v1/health` and `POST /api/v1/analyze`.
- Single-image upload validation for JPG, PNG, and WebP MIME types.
- Evidence modules for C2PA read attempts, GB 45438/AIGC byte-marker scan, EXIF summary, and ELA heatmap generation.
- Evidence-first report contract with verdict, summary, signals, limitations, recommendation, and `assets.ela_heatmap_data_url`.
- React + Vite Web UI for selecting an image, previewing it, showing file metadata, calling the backend, and displaying the report, signal details, and ELA heatmap.
- Local sample-image generator for repeatable smoke checks.
- Strict generated/public sample verifier, ELA calibration script, real-sample directory audit script, public dataset audit script, multi-source dataset suite runner, and auto validation window.
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
- `gb45438-xmp.png` verifies TC260 AIGC XMP namespace and field extraction.
- `scripts/calibrate_ela.py` exports generated-sample ELA metrics to JSON and Markdown.
- `scripts/audit_sample_directory.py` audits arbitrary user-supplied sample directories into JSON and Markdown summaries.
- `scripts/audit_public_dataset.py` audits recursive local raw dataset directories and optional Hugging Face dataset splits into grouped JSON and Markdown summaries with audit-confidence metrics.
- `scripts/audit_dataset_suite.py` runs multiple dataset sources from one JSON config, reports combined confidence and label-expectation alignment, and can fail with a non-zero exit code when confidence/source-count/alignment gates are not met.

Validated on 2026-05-24 after public dataset audit support was added:

```bash
cd backend
.venv/bin/python -m pytest
```

Result: `17 passed`.

Validated again after multi-source suite and confidence metrics were added:

```bash
cd backend
.venv/bin/python -m pytest
```

Result: `20 passed`.

Validated again after Hugging Face ClassLabel normalization and SOCKS proxy support for optional dataset dependencies were added:

```bash
cd backend
.venv/bin/python -m pytest
```

Result: `21 passed`.

Validated again after suite confidence gates were added:

```bash
cd backend
.venv/bin/python -m pytest
```

Result: `23 passed`.

Validated again after label-expectation alignment checks were added:

```bash
cd backend
.venv/bin/python -m pytest
```

Result: `27 passed`.

```bash
cd backend
.venv/bin/python scripts/audit_public_dataset.py local /private/tmp/trustpic-public-audit-smoke --max-samples 3 \
  --json-output /private/tmp/trustpic-public-audit-smoke.json \
  --markdown-output /private/tmp/trustpic-public-audit-smoke.md
```

Result: 3 generated samples audited successfully, with grouped verdict, C2PA, GB 45438, EXIF, and ELA summaries.

```bash
cd backend
.venv/bin/python scripts/audit_dataset_suite.py ../docs/public-dataset-suite.example.json \
  --json-output /private/tmp/trustpic-dataset-suite-smoke.json \
  --markdown-output /private/tmp/trustpic-dataset-suite-smoke.md
```

Result: 3 local dataset sources completed successfully in smoke mode, with 6 generated samples, 0 skipped sources, 0 failed sources, and combined confidence `medium` (`0.73`). The low sample count warning is expected for smoke data.

Gated suite pass:

```bash
cd backend
.venv/bin/python scripts/audit_dataset_suite.py ../docs/public-dataset-suite.example.json \
  --min-confidence-level medium \
  --min-confidence-score 0.6 \
  --require-completed-sources 3 \
  --json-output /private/tmp/trustpic-dataset-suite-gated.json \
  --markdown-output /private/tmp/trustpic-dataset-suite-gated.md
```

Result: exit code `0`, gate status `passed`, expectation alignment `1.0`.

Gated suite failure check:

```bash
cd backend
.venv/bin/python scripts/audit_dataset_suite.py ../docs/public-dataset-suite.example.json \
  --min-confidence-level high \
  --min-confidence-score 0.9 \
  --require-completed-sources 3 \
  --json-output /private/tmp/trustpic-dataset-suite-gate-fail.json \
  --markdown-output /private/tmp/trustpic-dataset-suite-gate-fail.md
```

Result: exit code `1`, gate status `failed`, with failures for confidence level and score.

Optional Hugging Face dependencies were installed with:

```bash
cd backend
.venv/bin/python -m pip install -e '.[dev,datasets]'
```

Result: `datasets`, `huggingface-hub`, `pyarrow`, and `socksio` installed successfully in the backend venv.

Validated on 2026-05-25 after the auto validation window was added:

```bash
cd backend
.venv/bin/python -m pytest
```

Result: `32 passed`.

Validated again after Hugging Face datasets-server row extraction was added:

```bash
cd backend
.venv/bin/python -m pytest
```

Result: `35 passed`.

```bash
cd backend
.venv/bin/python scripts/audit_dataset_window.py \
  --root /private/tmp/trustpic-datasets \
  --config-output /private/tmp/trustpic-auto-window-config.json \
  --json-output /private/tmp/trustpic-auto-window.json \
  --markdown-output /private/tmp/trustpic-auto-window.md
```

Result: local discovery found 3 known sources (`AIGC-Artifacts-Raw`, `DND-Dataset`, and `Real-World-AIGC`), completed 6 generated smoke samples, produced combined confidence `medium` (`0.73`), expectation alignment `1.0`, and gate status `passed`.

Validated remote Hugging Face row extraction with `TheKernel01/AIGC-Detection-Benchmark`:

```bash
cd backend
.venv/bin/python scripts/audit_dataset_window.py \
  --remote-only \
  --remote-catalog /private/tmp/trustpic-aigc-detection-benchmark-catalog.json \
  --require-completed-sources 1 \
  --min-confidence-level low \
  --min-confidence-score 0.3 \
  --json-output /private/tmp/trustpic-aigc-detection-benchmark-window.json \
  --markdown-output /private/tmp/trustpic-aigc-detection-benchmark-window.md
```

Result: datasets-server row extraction completed 6 remote samples, labels normalized to `real` and `fake`, generator/source values included `Real`, `ADM`, `BigGAN`, and `CycleGAN`, analyzer success rate `1.0`, combined confidence `medium` (`0.755`), expectation alignment `1.0`, and gate status `passed`. This source is suitable for remote extraction smoke checks, but the first sample set had no C2PA, GB 45438, or EXIF signals, so it is not enough for metadata calibration.

```bash
cd web
npm run build
```

Result: TypeScript build and Vite production build passed.

```bash
git diff --check
```

Result: no whitespace errors.

## Git And Index

- Remote: `https://github.com/meetwk0916/TrustPic`
- Branch: `main`
- Initial commit: `dfb0104 Initial TrustPic v0 prototype`
- CodeGraph status: up to date after dataset audit additions.

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

- Replace smoke data with real metadata-preserving public dataset subsets, such as raw AIGC artifact files, DND-Dataset, or Real-World-AIGC variants that keep original source files.
- Use the verified `AIGC-Detection-Benchmark` `hf_rows` entry for remote extraction smoke only; continue looking for raw/original dataset IDs for metadata calibration.
- Enable remaining placeholder `docs/public-dataset-remote-catalog.example.json` entries only after replacing Hugging Face IDs with verified raw/original dataset IDs and column names.
- Add real user-supplied or production-source sample records for:
  - camera image with EXIF, beyond generated EXIF
  - metadata-stripped image from an actual platform flow
  - production C2PA sample from a real tool or device
  - edited or recompressed image with a known real edit history
- Decide whether the upgraded GB 45438 scanner should remain a v0 TC260 XMP/marker scanner or move to a known implementation.
- Calibrate ELA threshold with real user/production samples instead of generated samples only.
- Confirm C2PA behavior with a production C2PA image sample, not only a public test/security sample.

## Next Recommended Step

Start with backend confidence before expanding product surface:

1. Download or mount the real raw datasets under `/private/tmp/trustpic-datasets/`, or enable verified Hugging Face raw dataset entries in `docs/public-dataset-remote-catalog.example.json`.
2. Run `scripts/audit_dataset_window.py` to auto-discover available local or remote sources and generate the gated validation report.
3. Re-run backend tests and frontend build.
4. Commit the v0 real-sample verification results.
