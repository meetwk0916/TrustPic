# TrustPic Context

TrustPic is an evidence-first image reporting context. Its language distinguishes supported evidence signals from general AI-image detection claims.

## Language

**Evidence Report**:
A single-image report that states which supported provenance, metadata, and review signals were found or absent. It does not prove an image is real, fake, authentic, or AI-generated.
_Avoid_: AI detector result, authenticity proof, real/fake judgment

**Supported Signal**:
A signal TrustPic v0 knows how to inspect and describe, currently provenance metadata, EXIF metadata, GB 45438/TC260 AIGC markers, and ELA review indicators. A missing supported signal is evidence of absence only for that signal, not proof of authenticity.
_Avoid_: truth signal, proof, probability

**Full-Scenario Full-Chain Coverage**:
Coverage of the TrustPic v0 evidence matrix and validation flow: C2PA, GB 45438/TC260, EXIF, ELA, metadata-stripped files, remote dataset extraction, label normalization, confidence gating, and report generation. It does not mean connecting every available AI-vs-real benchmark.
_Avoid_: all AI detector benchmarks, universal fake-image coverage

**Remote Extraction Smoke Source**:
A dataset source used to prove TrustPic can fetch remote samples, normalize labels and sources, analyze images, and produce gated reports. It may be unsuitable for metadata calibration if it does not preserve C2PA, EXIF, or GB 45438 evidence.
_Avoid_: calibration source, provenance source

**Metadata Calibration Source**:
A sample source whose files preserve metadata needed to calibrate or verify supported signals such as C2PA, EXIF, or GB 45438/TC260 fields. It must be treated separately from real/fake classification benchmarks.
_Avoid_: benchmark source, detector training set

**Minimum Coverage Set**:
The smallest source set that covers TrustPic v0's evidence matrix and validation flow without duplicating low-value AI-vs-real benchmarks. The first phase set is one remote extraction smoke source, one extra generator benchmark, one EXIF photography source, C2PA positive or attack samples, one C2PA batch candidate, and the existing GB 45438/TC260 fixture.
_Avoid_: exhaustive benchmark suite, every public fake-image dataset

**C2PA Required Source**:
A stable Content Credentials sample source that TrustPic treats as required for v0 C2PA coverage. The first required C2PA source is `contentauth/c2pa-attacks`; broader Hugging Face C2PA datasets are candidates until their structure and metadata preservation are verified.
_Avoid_: any dataset that mentions C2PA, unverified C2PA benchmark

**GB45438 Fixture**:
A controlled sample file that contains TC260 AIGC namespace or marker evidence for TrustPic's conservative GB 45438 scan. In the first phase, a synthetic fixture is enough to prove scanner and report behavior; real domestic source files become metadata calibration sources when available.
_Avoid_: GB45438 certification, complete national-standard compliance sample

**EXIF Required Source**:
A real photography source with preserved technical EXIF metadata, used to verify TrustPic's metadata reporting beyond generated fixtures. The first-phase candidate is DataSeeds DSD because it explicitly targets photographic images with technical metadata.
_Avoid_: generated EXIF fixture, metadata-free photo benchmark

**ELA Review Smoke**:
A small validation set that checks whether ELA metrics and heatmaps are produced and reported cautiously for edited or recompressed files. It is not a tampering benchmark and does not prove manipulation.
_Avoid_: forensic tampering evaluation, manipulation proof

## Example Dialogue

Dev: "Can we use an AI-vs-real benchmark as full coverage?"

Domain expert: "Only as a remote extraction smoke source. Full-scenario full-chain coverage also needs metadata calibration sources for C2PA, EXIF, GB 45438/TC260, and ELA."

Dev: "Should we add GenImage, ScaleDF, and InfImagine now?"

Domain expert: "Not in the first phase. The minimum coverage set is enough until the evidence matrix is covered by distinct source types."

Dev: "If a sample has no C2PA or EXIF, can the report say it is fake or real?"

Domain expert: "No. The evidence report can say no supported provenance or metadata signal was found, then list limitations and recommend review."
