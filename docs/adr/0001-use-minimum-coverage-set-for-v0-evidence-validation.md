# Use Minimum Coverage Set For v0 Evidence Validation

TrustPic v0 validates an evidence-reporting product, not a universal AI-vs-real detector, so the first dataset plan uses a minimum coverage set instead of an exhaustive benchmark suite. This means prioritizing distinct evidence coverage across remote extraction, C2PA, GB 45438/TC260, EXIF, ELA review, metadata-stripped samples, confidence gates, and report generation before adding large or redundant AI-image benchmarks such as GenImage, ScaleDF, or InfImagine.

**Consequences**

- `AIGC-Detection-Benchmark` is enough for the first remote extraction smoke path once it proves label/source normalization and gated reports.
- `DataSeeds DSD` and C2PA-specific samples have higher first-phase value than additional real/fake classification datasets.
- Large benchmark sources are deferred until the evidence matrix is covered by distinct source types.
