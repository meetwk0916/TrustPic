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

## Public Dataset Audit

For public AIGC datasets, prefer raw/original-file variants that preserve source metadata. Avoid WebP-compressed or re-encoded classification mirrors when the goal is EXIF, C2PA, GB 45438, or ELA validation.

Local raw dataset directory:

```bash
cd backend
.venv/bin/python scripts/audit_public_dataset.py local /private/tmp/aigc-artifacts-raw \
  --max-per-label 25 \
  --json-output /private/tmp/trustpic-public-dataset-audit.json \
  --markdown-output /private/tmp/trustpic-public-dataset-audit.md
```

The local auditor scans recursively and infers labels from parent directory names by default, for example `real/*.jpg` and `fake/*.png`. WebP is skipped by default for provenance-focused audits; pass `--include-webp` only when the dataset's native source files are WebP.

Hugging Face dataset split:

```bash
cd backend
.venv/bin/python -m pip install -e '.[dev,datasets]'
.venv/bin/python scripts/audit_public_dataset.py hf DATASET_NAME \
  --split train \
  --image-column image \
  --label-column label \
  --source-column source \
  --streaming \
  --max-per-label 25 \
  --json-output /private/tmp/trustpic-hf-audit.json \
  --markdown-output /private/tmp/trustpic-hf-audit.md
```

The Hugging Face path casts the image column with `decode=False` so TrustPic analyzes the original bytes or cached raw file path instead of a Pillow-resaved image.
If `label_column` or `source_column` uses Hugging Face `ClassLabel`, the audit converts numeric IDs into their label names before grouping.

## Multi-Source Audit Suite

Use the suite runner when comparing multiple public data sources in one report:

```bash
cd backend
.venv/bin/python scripts/audit_dataset_suite.py ../docs/public-dataset-suite.example.json \
  --min-confidence-level medium \
  --min-confidence-score 0.6 \
  --require-completed-sources 3 \
  --json-output /private/tmp/trustpic-dataset-suite.json \
  --markdown-output /private/tmp/trustpic-dataset-suite.md
```

The example config expects locally downloaded raw datasets under `/private/tmp/trustpic-datasets/`:

- `AIGC-Artifacts-Raw`
- `DND-Dataset`
- `Real-World-AIGC`

Keep those directories outside git. If a dataset is available through Hugging Face and keeps raw image bytes, replace a local source with:

```json
{
  "name": "DATASET_NAME",
  "mode": "hf",
  "dataset": "ORG_OR_USER/DATASET_NAME",
  "split": "train",
  "image_column": "image",
  "label_column": "label",
  "source_column": "source",
  "streaming": true,
  "max_per_label": 25
}
```

The suite report includes per-source confidence and combined confidence. The score measures audit readiness, not whether an image is real or AI-generated. It combines:

- analyzer success rate
- sample count
- label coverage
- labeled sample rate
- observed provenance, EXIF, and ELA signal coverage

Treat `high` as enough evidence to calibrate thresholds and compare source groups. Treat `low` or `insufficient` as a prompt to add samples, labels, or metadata-preserving sources before drawing conclusions.

The suite config and CLI can both define a gate:

- `min_confidence_level`: required combined confidence level.
- `min_confidence_score`: required combined confidence score.
- `require_completed_sources`: minimum number of sources that must complete.
- `min_alignment_rate`: required match rate for configured label expectations.

If the gate fails, `audit_dataset_suite.py` exits with status code `1` after writing the JSON/Markdown report.

Each source can define optional `expectations` keyed by dataset label. Supported checks:

- `verdict`: one allowed verdict or a list of allowed verdicts.
- `c2pa_status`: one allowed C2PA status or a list of statuses.
- `gb45438_status`: one allowed GB 45438 status or a list of statuses.
- `ela_status`: one allowed ELA status or a list of statuses.
- `exif_detected`: boolean EXIF presence expectation.

Expectation alignment is a dataset-audit consistency check, not proof that TrustPic is an AI detector. For raw public datasets where provenance may have been stripped, use broad verdict expectations first, then tighten them after inspecting aggregate results.

If Hugging Face network access is unstable, download or mount the raw dataset files locally and use `mode: "local"` in the suite config. Local mode is the preferred path for large datasets and for preserving file-level provenance evidence.

## Acceptance Notes

After auditing a real sample set, record only non-sensitive findings in project docs:

- sample category
- source/tool/device, if shareable
- expected signal
- actual TrustPic result
- any mismatch or limitation

Keep originals outside git unless the licensing and privacy status is clear.
