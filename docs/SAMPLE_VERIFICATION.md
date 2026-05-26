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
- `gb45438-xmp.png`: PNG bytes with a TC260 AIGC XMP packet using the `http://www.tc260.org.cn/ns/AIGC/1.0/` namespace.
- `camera-exif.jpg`: JPEG with generated camera-like EXIF fields.
- `metadata-stripped.jpg`: same generated scene re-saved without EXIF.
- `edited-compressed.jpg`: compressed JPEG with local shape edits for heatmap smoke review.
- `ela-review-compressed.jpg`: JPEG with a concentrated high-frequency local region expected to trip the v0 local-difference review signal.

These are smoke samples, not forensic ground truth. A production C2PA sample from a real tool or device is still needed before v0 can claim production C2PA sample coverage.

## Automated Verification

Run generated samples only:

```bash
cd backend
.venv/bin/python scripts/verify_samples.py --output-dir /private/tmp/trustpic-samples
```

Run generated samples plus a public C2PA sample:

```bash
cd backend
.venv/bin/python scripts/verify_samples.py --download-public --output-dir /private/tmp/trustpic-samples
```

The verification script exits non-zero if expected outcomes fail.

The public C2PA sample currently used is `sample/C.jpg` from `contentauth/c2pa-attacks`.
That repository describes `sample/C.jpg` as an example image with attached Content Credentials.
It is a test/security sample with a test certificate, not a real camera-authenticity sample.

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
- `gb45438-xmp.png` returns `supported_signal_detected`, `signals.gb45438.details.tc260_namespace_detected: true`, and `signals.gb45438.details.xmp_fields.Label: "AIGC"`.
- `camera-exif.jpg` returns `success` and `signals.exif.detected: true`.
- `metadata-stripped.jpg` returns `success` and `signals.exif.detected: false`.
- `edited-compressed.jpg` returns `success` with an ELA heatmap data URL.
- `ela-review-compressed.jpg` returns `review_recommended`, `signals.ela.status: "review"`, and `signals.ela.details.local_anomaly_detected: true`.
- `c2pa-attacks-C.jpg`, when downloaded, returns `supported_signal_detected`, `signals.c2pa.detected: true`, and `signals.c2pa.details.validation_state: "Valid"`.

## Web Smoke

Start the frontend:

```bash
cd web
npm run dev
```

Open `http://127.0.0.1:5173/`, upload the generated samples, and verify:

- the selected image preview renders
- file name, type, and size render under the preview
- conclusion, confidence, evidence summaries, foldable details, boundary notes, and local-difference heatmap render without layout overlap
- failed uploads show a controlled error message

## Still Missing Real Samples

Before v0 is complete, add or document real representative samples for:

- camera image with EXIF
- metadata-stripped image from a common platform flow
- production C2PA image with a readable manifest from a real tool or device
- edited/recompressed image with a known edit history
