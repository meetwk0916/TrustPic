# TrustPic v0 Goals

## Starting Assumptions

- TrustPic should start as a usable single-image tool, not a broad platform.
- The first valuable output is an evidence report, not a binary "real/fake" verdict.
- Future product forms include Web and WeChat Mini Program, so v0 must expose a stable API and report schema.
- We should avoid depending on closed or unavailable detector APIs for v0.

## Product Positioning

TrustPic v0 is a privacy-conscious image evidence reporter.

It accepts one image and returns:

- What supported provenance signals were found.
- What supported provenance signals were absent.
- Whether the file has basic metadata and EXIF signals.
- Whether ELA suggests local compression or edit irregularities.
- A cautious verdict with limitations.
- A machine-readable JSON report.

TrustPic v0 must not claim:

- It can prove an image is real.
- It can detect all AI-generated images.
- Absence of C2PA, GB 45438, EXIF, or ELA signals means an image is authentic.
- ELA alone proves AI generation.

## v0 Scope

### Included

- Single image upload.
- Supported formats: JPG, JPEG, PNG, WebP.
- Backend API endpoint: `POST /api/v1/analyze`.
- Report JSON response with stable top-level fields.
- C2PA read/verification attempt.
- GB 45438 file metadata or byte-signal scan attempt.
- EXIF extraction summary.
- ELA image generation and metrics.
- Web UI that can upload one image and display the report.
- Local run command documented in the repository.

### Deferred

- SSP or other deep-learning AI detector models.
- SynthID direct detection.
- OpenAI Verify automation.
- Chrome extension.
- WeChat Mini Program release.
- User accounts.
- Persistent image storage.
- Batch processing.
- Legal/forensic certificate generation.

## Report Contract

The v0 report should use evidence-first language:

```json
{
  "status": "success",
  "verdict": "supported_signal_detected | review_recommended | no_supported_signal_found | unsupported",
  "summary": "Human-readable explanation",
  "signals": {
    "c2pa": {},
    "gb45438": {},
    "exif": {},
    "ela": {}
  },
  "limitations": [],
  "recommendation": "Human-readable next step",
  "assets": {
    "ela_heatmap_url": null
  }
}
```

## Success Criteria

v0 is done when:

- A developer can run backend and frontend locally from documented commands.
- A user can upload one image through the Web UI.
- The UI shows the original image, evidence sections, verdict, limitations, and ELA heatmap when available.
- The API returns structured JSON that a future Mini Program can consume without special casing the Web UI.
- Invalid file type and oversized file cases return controlled errors.
- At least four sample paths are manually verified:
  - normal camera image with EXIF
  - image with stripped metadata
  - image with C2PA metadata, if a sample is available
  - edited/compressed image that produces an ELA heatmap

## v0 Non-Negotiables

- Do not persist uploaded original images.
- Do not present `Pass` as "true image".
- Do not call model-derived scores "probability" unless calibrated by a labeled evaluation set.
- Keep the API stable before building Mini Program UI.

