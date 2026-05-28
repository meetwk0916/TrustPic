# TrustPic v0 Release Checklist

Last aligned: 2026-05-28

## Status

v0 is runnable and usable as a single-image evidence report prototype. The current release gate passes for generated/public coverage, but real product-flow samples are still missing.

## Completed

- Backend API: `GET /api/v1/health`, `POST /api/v1/analyze`.
- Web UI: upload, preview, conclusion, confidence, AI alert, core evidence, local-difference module, report-reading notes, dark mode, and Chinese/English switching.
- Report contract: `interpretation` is the user-facing contract.
- Bilingual report interpretation: `POST /api/v1/analyze` accepts `locale=zh-CN` or `locale=en-US`; unsupported locales fall back to Chinese.
- AI evidence:
  - GB45438/TC260/AIGC metadata and byte marker scan.
  - C2PA source record parsing.
  - AI-related C2PA source interpretation for OpenAI/DALL-E and explicit Google AI records such as Gemini, NotebookLM, Imagen, SynthID, and Nano Banana.
- Metadata evidence: EXIF summary.
- File-originality reading: `图片来源记录` summary/details include `原始性较强`, `原始性有限`, or `无法判断` without adding a separate warning module.
- Local-difference evidence: tile-level ELA heatmap and local anomaly metrics.
- Dataset tooling:
  - generated sample verifier.
  - real sample manifest auditor.
  - public dataset auditor.
  - multi-source dataset suite runner.
  - release coverage suite with a 50+ sample gate.

## Latest Validation

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
cd backend
.venv/bin/python scripts/prepare_first_phase_fixtures.py
.venv/bin/python scripts/audit_dataset_suite.py ../docs/public-dataset-v0-release.example.json \
  --json-output /private/tmp/trustpic-v0-release-suite.json \
  --markdown-output /private/tmp/trustpic-v0-release-suite.md
```

Result: 5 completed sources, 0 skipped, 0 failed, 54 samples, gate `passed`, combined confidence `high` (`0.9`), expectation alignment `1.0`.

```bash
cd backend
.venv/bin/python scripts/audit_v0_real_sample_manifest.py ../docs/v0-real-sample-manifest.example.json \
  --allow-missing \
  --json-output /private/tmp/trustpic-real-v0-dry-run.json \
  --markdown-output /private/tmp/trustpic-real-v0-dry-run.md
```

Result: script works; all 7 required real sample slots are missing in the example manifest.

## Release Blockers

- Add real OpenAI/ChatGPT original image with preserved source record.
- Add real NotebookLM/Gemini/Imagen original and re-encoded/screenshot pair.
- Add real domestic GB45438/TC260 original export when available.
- Add real camera EXIF image from the target user flow.
- Add real platform-stripped image from a common sharing/downloading flow.
- Add known local edit/composite sample for local-difference calibration.

## Deferred Beyond v0

- Direct SynthID detection.
- OpenAI Verify automation.
- Deep-learning visual AI detector models.
- Browser extension.
- WeChat Mini Program release.
- Persistent image storage, user accounts, and batch processing.
