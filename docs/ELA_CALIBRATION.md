# ELA Calibration

TrustPic v0 uses ELA as a review signal, not as proof of AI generation or tampering.

Current heuristic:

- JPEG recompression quality: `90`
- Heatmap amplification: `15`
- Review threshold: mean error greater than `12.0`

Run the local calibration snapshot:

```bash
cd backend
.venv/bin/python scripts/calibrate_ela.py \
  --generate \
  --sample-dir /private/tmp/trustpic-samples \
  --json-output /private/tmp/trustpic-ela-calibration.json \
  --markdown-output /private/tmp/trustpic-ela-calibration.md
```

The generated sample set currently produces:

| sample type | expected ELA status |
|---|---|
| flat PNG without provenance metadata | `low_signal` |
| GB 45438/AIGC marker PNG | `low_signal` |
| generated camera-like EXIF JPEG | `low_signal` |
| generated metadata-stripped JPEG | `low_signal` |
| simple edited/compressed JPEG | `low_signal` |
| high-frequency low-quality JPEG | `review` |

## Interpretation

ELA highlights compression differences. It can be useful for review, but it is sensitive to texture, format, save quality, and editing workflow. A high ELA score does not prove AI generation, and a low ELA score does not prove authenticity.

## Remaining Calibration Work

Before treating the threshold as product-grade, collect real samples and record:

- original camera photos with varied texture and lighting
- platform-compressed or platform-forwarded images
- known edits saved through common editing tools
- screenshots and recompressed images from mobile apps
- AI-generated images exported by common generators

Then compare distributions around the `12.0` threshold and update both the threshold and UI language if needed.
