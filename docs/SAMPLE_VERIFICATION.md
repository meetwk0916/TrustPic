# Sample Verification

Use this note to verify that the local v0 can process representative files before calling the feature usable.

## Generate Local Samples

```bash
cd backend
.venv/bin/python scripts/generate_sample_images.py /private/tmp/trustpic-samples
```

Generated samples:

- `plain.png`: simple PNG without expected provenance metadata.
- `marked-aigc.png`: PNG bytes with an appended `AI_GENERATED` marker for the GB 45438/AIGC byte-scan path.
- `edited-compressed.jpg`: compressed JPEG with local shape edits for ELA smoke review.

These are smoke samples, not forensic ground truth. A real C2PA sample is still needed before v0 can claim C2PA sample coverage.

## Backend Smoke

Start the backend:

```bash
cd backend
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In another terminal:

```bash
curl --noproxy '*' -sS -F file=@/private/tmp/trustpic-samples/plain.png \
  http://127.0.0.1:8000/api/v1/analyze

curl --noproxy '*' -sS -F file=@/private/tmp/trustpic-samples/marked-aigc.png \
  http://127.0.0.1:8000/api/v1/analyze

curl --noproxy '*' -sS -F file=@/private/tmp/trustpic-samples/edited-compressed.jpg \
  http://127.0.0.1:8000/api/v1/analyze
```

Expected smoke outcomes:

- `plain.png` returns `success` with all signal sections present.
- `marked-aigc.png` returns `supported_signal_detected` and `signals.gb45438.detected: true`.
- `edited-compressed.jpg` returns `success` with an ELA heatmap data URL.

## Web Smoke

Start the frontend:

```bash
cd web
npm run dev
```

Open `http://127.0.0.1:5173/`, upload the generated samples, and verify:

- the selected image preview renders
- file name, type, and size render under the preview
- verdict, evidence summaries, details, recommendation, limitations, and ELA heatmap render without layout overlap
- failed uploads show a controlled error message

## Still Missing Real Samples

Before v0 is complete, add or document real representative samples for:

- camera image with EXIF
- metadata-stripped image from a common platform flow
- C2PA image with a readable manifest
- edited/recompressed image with a known edit history
