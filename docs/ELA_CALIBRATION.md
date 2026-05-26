# ELA Calibration

TrustPic v0 uses ELA as a local-difference review signal, not as proof of AI generation or tampering.

Current heuristic:

- JPEG recompression quality: `90`
- Heatmap amplification: `15`
- Tile size: `32`
- Local tile minimum error: `28.0`
- Local tile ratio threshold: `2.5x` the tile mean error
- Review rule: at least `2` anomalous tiles, with anomalous tiles covering no more than `25%` of analyzed tiles

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
| concentrated local high-frequency JPEG | `review` |

The v0 release coverage suite produced this snapshot:

```bash
cd backend
.venv/bin/python scripts/audit_dataset_suite.py ../docs/public-dataset-v0-release.example.json \
  --json-output /private/tmp/trustpic-v0-release-suite.json \
  --markdown-output /private/tmp/trustpic-v0-release-suite.md
```

Result: 54 samples, 5 completed sources, gate `passed`, combined confidence `high` (`0.9`), expectation alignment `1.0`, and ELA review rate `0.2593`.

Important calibration observations:

- Public EXIF JPEG samples had high global `mean_error` values (`37.53` and `50.11`) but stayed `low_signal` because no concentrated local anomaly was detected.
- The generated metadata-stripped JPEG stayed `low_signal`.
- The generated concentrated local-difference fixture returned `review`.
- Public remote benchmark samples can trigger local-difference review, but those datasets are not forensic ground truth for editing. Treat them as distribution checks, not proof of tampering accuracy.

## Interpretation

ELA highlights recompression differences. TrustPic v0 ignores global compression as a user-facing signal and only marks ELA as `review` when a small set of tiles stands out from the overall image. This can be useful as a local-difference clue, but it is sensitive to texture, format, save quality, and editing workflow. A local ELA signal does not prove AI generation, P图, or malicious tampering, and a low ELA signal does not prove authenticity.

## Remaining Calibration Work

Before treating the threshold as product-grade, collect real product-flow samples and record:

- original camera photos with varied texture and lighting
- platform-compressed or platform-forwarded images
- known edits saved through common editing tools
- screenshots and recompressed images from mobile apps
- AI-generated images exported by common generators

Then compare local tile distributions and update both thresholds and UI language if needed.
