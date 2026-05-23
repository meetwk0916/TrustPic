# Real Sample Intake

Use this workflow when collecting real user-supplied or production-source samples.

## Sample Set

Create a local directory outside the repository, for example:

```bash
mkdir -p /private/tmp/trustpic-real-samples
```

Recommended files:

- `camera-exif-*.jpg`: original camera image with EXIF.
- `platform-stripped-*.jpg`: same or similar image after upload/download from a real platform flow.
- `production-c2pa-*.jpg`: image exported by a production C2PA-capable tool or device.
- `known-edit-*.jpg`: image with known edit history and save/export steps.

Do not commit real user images into the repository unless they are explicitly cleared for redistribution.

## Audit Command

```bash
cd backend
.venv/bin/python scripts/audit_sample_directory.py /private/tmp/trustpic-real-samples \
  --json-output /private/tmp/trustpic-real-sample-audit.json \
  --markdown-output /private/tmp/trustpic-real-sample-audit.md
```

The audit produces a compact per-file summary:

- report verdict
- C2PA status and validation state
- GB 45438/TC260 XMP detection
- EXIF field count
- ELA status and mean error

## Acceptance Notes

After auditing a real sample set, record only non-sensitive findings in project docs:

- sample category
- source/tool/device, if shareable
- expected signal
- actual TrustPic result
- any mismatch or limitation

Keep originals outside git unless the licensing and privacy status is clear.
