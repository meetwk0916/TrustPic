# TrustPic Progress

Last aligned: 2026-05-29

## Current State

TrustPic is at a runnable v0 prototype checkpoint.

The current implementation includes:

- Backend FastAPI service with `GET /api/v1/health` and `POST /api/v1/analyze`.
- Single-image upload validation for JPG, PNG, and WebP MIME types.
- Evidence modules for C2PA read attempts, GB 45438/AIGC byte-marker scan, EXIF summary, and ELA heatmap generation.
- Evidence-first report contract with verdict, summary, signals, human-readable `interpretation`, limitations, recommendation, and `assets.ela_heatmap_data_url`.
- React + Vite Web UI for selecting an image, previewing it, showing file metadata, calling the backend, and displaying a user-readable conclusion, confidence label, ordered evidence chain, foldable evidence explanations, boundary notes, and ELA heatmap.
- Web UI can switch between Chinese and English. The frontend passes `locale=zh-CN` or `locale=en-US` to the backend, and the backend generates localized `interpretation` wording from the same evidence signals.
- Chrome extension client under `extension/` for one-purpose right-click image analysis in Chrome Side Panel and image URL fallback.
- Chrome Web Store upload package generation with store notes, permission justifications, remote-code declaration, and a static privacy policy page at Web path `/privacy.html`.
- AI-related C2PA source records, including OpenAI and explicit Google AI product records such as Gemini, NotebookLM, Imagen, SynthID, and Nano Banana, are interpreted as AI-related source evidence even when GB 45438/TC260 markers are absent.
- EXIF interpretation separates camera-capture metadata from software-save or file-structure metadata. Software-only fields such as `Software=Picasa`, `Orientation`, or `ExifOffset` do not count as camera-capture evidence and do not raise the main conclusion, confidence label, or file-originality reading.
- `图片来源记录` now also carries file-originality reading in its visible summary and details (`originality_label` and `originality_reasons`) without adding a separate top-level report module.
- ELA is now a tile-level local-difference signal. Ordinary global compression is ignored as a primary user-facing finding; `review` means a small set of local tiles stands out from the overall recompression pattern.
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

Validated again after URL source support and first-phase fixtures were added:

```bash
cd backend
.venv/bin/python -m pytest
```

Result: `39 passed`.

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

Validated first-phase minimum coverage suite after URL sources and local first-phase fixtures were added:

```bash
cd backend
.venv/bin/python scripts/prepare_first_phase_fixtures.py
.venv/bin/python scripts/audit_dataset_suite.py ../docs/public-dataset-first-phase.example.json \
  --json-output /private/tmp/trustpic-first-phase-suite.json \
  --markdown-output /private/tmp/trustpic-first-phase-suite.md
```

Result: 5 completed sources, 2 skipped candidate sources, 18 total samples, analyzer success rate `1.0`, combined confidence `medium` (`0.7983`), expectation alignment `1.0`, and gate status `passed`. Completed coverage included `AIGC-Detection-Benchmark`, `OpenFake`, public EXIF JPEG samples from `ianare/exif-samples`, `contentauth/c2pa-attacks`, and local TrustPic v0 fixtures for GB 45438/TC260, metadata-stripped, and ELA review smoke.

Candidate source findings:

- `DataSeeds DSD` rows expose EXIF metadata columns, but the downloaded image bytes did not retain EXIF in the smoke run, so it remains disabled as a metadata calibration source.
- `TrustMyContent/C2PA_Certified_Image_Authenticity` completed a 3-sample probe, but C2PA was absent in downloaded image bytes, so it remains disabled as a C2PA batch source.

```bash
cd web
npm run build
```

Result: TypeScript build and Vite production build passed.

Validated on 2026-05-26 after the report interpretation layer and UI were added:

```bash
cd backend
.venv/bin/python -m pytest
```

Result: `39 passed`.

```bash
cd web
npm run build
```

Result: TypeScript build and Vite production build passed.

Validated again after AI-related C2PA source records were promoted into the human-readable interpretation:

```bash
cd backend
.venv/bin/python -m pytest
```

Result: `40 passed`.

```bash
cd web
npm run build
```

Result: TypeScript build and Vite production build passed.

Validated again after Google-family AI source record handling was added:

```bash
cd backend
.venv/bin/python -m pytest
```

Result: `42 passed`.

```bash
cd web
npm run build
```

Result: TypeScript build and Vite production build passed.

Validated again after ELA was narrowed from global compression review to tile-level local-difference review:

```bash
cd backend
.venv/bin/python -m pytest
```

Result: `43 passed`.

Validated again after file-originality reading was merged into `图片来源记录`:

```bash
cd backend
.venv/bin/python -m pytest
```

Result: `46 passed`.

```bash
cd web
npm run build
```

Result: TypeScript build and Vite production build passed.

```bash
cd backend
.venv/bin/python scripts/verify_samples.py --output-dir /private/tmp/trustpic-samples-local-ela
```

Result: generated sample verification passed. Ordinary EXIF and metadata-stripped JPEG samples stayed `ela_status: low_signal`; `ela-review-compressed.jpg` returned `ela_status: review`.

```bash
cd backend
.venv/bin/python scripts/calibrate_ela.py --generate \
  --sample-dir /private/tmp/trustpic-samples-local-ela-cal \
  --json-output /private/tmp/trustpic-ela-calibration-local.json \
  --markdown-output /private/tmp/trustpic-ela-calibration-local.md
```

Result: calibration export passed with tile-level local anomaly fields.

```bash
cd web
npm run build
```

Result: TypeScript build and Vite production build passed.

Validated after the report UI was reorganized with key-signal colors, dark mode, and local-difference card/heatmap grouping:

```bash
cd web
npm run build
```

Result: TypeScript build and Vite production build passed.

Validated after `docs/V0_GOALS.md` was aligned to the current `interpretation` report contract:

```bash
cd backend
.venv/bin/python -m pytest
```

Result: `43 passed`.

```bash
cd web
npm run build
```

Result: TypeScript build and Vite production build passed.

Validated after the v0 real-sample manifest auditor and 50+ release suite gate were added:

```bash
cd backend
.venv/bin/python scripts/audit_v0_real_sample_manifest.py ../docs/v0-real-sample-manifest.example.json \
  --allow-missing \
  --json-output /private/tmp/trustpic-real-v0-dry-run.json \
  --markdown-output /private/tmp/trustpic-real-v0-dry-run.md
```

Result: dry run succeeded and reported 7 missing required real sample slots.

```bash
cd backend
.venv/bin/python scripts/prepare_first_phase_fixtures.py
.venv/bin/python scripts/audit_dataset_suite.py ../docs/public-dataset-v0-release.example.json \
  --json-output /private/tmp/trustpic-v0-release-suite.json \
  --markdown-output /private/tmp/trustpic-v0-release-suite.md
```

Result: 5 completed sources, 0 skipped, 0 failed, 54 total samples, gate `passed`, combined confidence `high` (`0.9`), expectation alignment `1.0`.

```bash
git diff --check
```

Result: no whitespace errors.

Validated after bilingual Chinese/English interpretation support was added:

```bash
cd backend
.venv/bin/python -m pytest
```

Result: `48 passed`.

```bash
cd web
npm run build
```

Result: TypeScript build and Vite production build passed.

```bash
git diff --check
```

Result: no whitespace errors.

Validated after the unpacked Chrome Side Panel extension client was added:

```bash
python3 -m json.tool extension/manifest.json
node --check extension/sidepanel.js
node --check extension/service-worker.js
```

Result: manifest JSON and extension JavaScript syntax checks passed.

```bash
cd backend
.venv/bin/python -m pytest
```

Result: `48 passed`.

```bash
cd web
npm run build
```

Result: TypeScript build and Vite production build passed.

Validated on 2026-05-29 after EXIF capture-vs-software wording, Chrome extension language switching, store package wording, and privacy policy page updates:

```bash
cd backend
.venv/bin/python -m pytest
```

Result: `51 passed`.

```bash
cd web
npm run build
```

Result: TypeScript build and Vite production build passed; `web/public/privacy.html` is copied to `dist/privacy.html`.

```bash
python3 -m json.tool extension/manifest.json
node --check extension/sidepanel.js
node --check extension/service-worker.js
sh extension/package.sh
unzip -p trustpic-chrome-0.1.0.zip manifest.json
git diff --check
```

Result: manifest JSON and extension JavaScript syntax checks passed, Chrome Web Store ZIP was regenerated, the ZIP manifest contains the single-purpose description, and no whitespace errors were found.

Validated on 2026-06-17 after the Chrome extension was made fully self-contained (no backend):

- The backend evidence pipeline was ported to buildless JS under `extension/analysis/`: `c2pa.js` (heuristic, presence + AI-term read, no signature verification), `gb45438.js`, `exif.js`, `ela.js` (Canvas/OffscreenCanvas), `interpretation.js` (full bilingual port), plus `analyze.js` and `run.js`.
- `service-worker.js` now only registers the menu, opens the Side Panel, and records the request. `sidepanel.js` is an ES module that fetches the image and runs the analysis locally. No `POST /api/v1/analyze` call remains.
- C2PA offline mode reports presence and AI-related clues but never `Valid`, so a detected manifest surfaces as "needs attention".

```bash
Get-ChildItem extension\*.js, extension\analysis\*.js | % { node --check $_.FullName }
node extension/test/analysis.test.mjs
```

Result: all extension JS files pass `node --check`; `extension/test/analysis.test.mjs` reports `15 checks passed`, covering GB 45438 marker/XMP, EXIF JPEG APP1 parsing, heuristic C2PA detection, the ELA tile math, and bilingual interpretation parity with the backend report contract.

## Git And Index

- Remote: `https://github.com/meetwk0916/TrustPic`
- Branch: `main`
- Initial commit: `dfb0104 Initial TrustPic v0 prototype`
- CodeGraph status: initialized in this repository.

## Not Blocked By API Quota

The current v0 does not depend on OpenAI API quota or commercial detector APIs.

Deferred quota/API-dependent directions remain:

- OpenAI Verify automation.
- SynthID direct detection.
- Commercial third-party detector API fallback.
- Chrome Web Store review/publication.

## Remaining Work To Finish v0

The v0 goal is not complete until the success criteria in `docs/V0_GOALS.md` are verified against representative samples.

Highest-priority gaps:

- Fill the 7 required real-sample manifest slots in `docs/V0_REAL_SAMPLE_SUITE.md`.
- Replace the generated GB 45438/TC260 fixture with a real domestic source file when a metadata-preserving public sample becomes available.
- Add real user-supplied or production-source sample records for a platform-stripped image and a known real edit/recompression flow.
- Decide whether the upgraded GB 45438 scanner should remain a v0 TC260 XMP/marker scanner or move to a known implementation.
- Calibrate ELA threshold with larger real user/production samples instead of first-phase smoke samples only.

## Next Recommended Step

Start with real product-flow samples before expanding product surface:

1. Copy `docs/v0-real-sample-manifest.example.json` to `/private/tmp/trustpic-real-v0/manifest.json`.
2. Fill the required sample files outside git.
3. Run `scripts/audit_v0_real_sample_manifest.py` without `--allow-missing`.
4. Re-run backend tests, frontend build, and the v0 release suite.
