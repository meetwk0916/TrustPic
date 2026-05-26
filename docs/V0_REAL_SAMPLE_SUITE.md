# TrustPic v0 Real Sample Suite

Last aligned: 2026-05-26

This suite is for real files kept outside git. It checks whether TrustPic v0 behaves correctly on product-relevant originals and common transformed copies.

## Required Slots

- `openai_c2pa_original`: OpenAI/ChatGPT generated image with original C2PA/source record.
- `google_ai_original`: NotebookLM/Gemini/Imagen original export when available.
- `google_ai_reencoded`: NotebookLM/Gemini/Imagen screenshot or re-encoded copy.
- `domestic_gb45438_original`: domestic AIGC export with GB45438/TC260 metadata when available.
- `camera_exif_original`: normal camera or phone photo with EXIF.
- `platform_stripped`: common platform-forwarded or downloaded image with stripped metadata.
- `known_local_edit`: known local edit or composite for local-difference ELA calibration.

## Run

Copy `docs/v0-real-sample-manifest.example.json` to a private path, update the file paths, and run:

```bash
cd backend
.venv/bin/python scripts/audit_v0_real_sample_manifest.py /private/tmp/trustpic-real-v0/manifest.json \
  --json-output /private/tmp/trustpic-real-v0/audit.json \
  --markdown-output /private/tmp/trustpic-real-v0/audit.md
```

For a dry run before all files exist:

```bash
cd backend
.venv/bin/python scripts/audit_v0_real_sample_manifest.py ../docs/v0-real-sample-manifest.example.json \
  --allow-missing \
  --json-output /private/tmp/trustpic-real-v0-dry-run.json \
  --markdown-output /private/tmp/trustpic-real-v0-dry-run.md
```

The script exits non-zero when required files are missing unless `--allow-missing` is used.

## Expected Use

This suite is not a benchmark. It is a v0 boundary check:

- Original AI exports should surface readable source records or AI markers when the provider embeds them.
- Screenshot, platform-forwarded, or re-encoded copies may lose source records and should not be treated as authentic.
- Domestic samples should be used to validate real GB45438/TC260 metadata, replacing generated fixtures when available.
- Local-difference ELA should stay a clue only, not a tampering verdict.
