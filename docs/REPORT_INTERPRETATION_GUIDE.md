# TrustPic Report Interpretation Guide

Last aligned: 2026-05-27

This guide defines how TrustPic v0 explains a single-image report to users.

TrustPic v0 reports what the current file evidence supports. It does not claim that a picture is real, fake, authentic, AI-generated, or tampered with when the supported evidence is absent.

## Output Structure

The user-facing report is ordered by the questions users most often bring to the product:

1. Conclusion
2. Confidence
3. Evidence chain
4. Foldable evidence explanations
5. Boundary notes

The report does not include next-step advice. The product should help users read the evidence, not push them into a review workflow.

## Confidence

Confidence means: how strongly the current evidence chain supports this report conclusion.

It is not a probability that the image is real, fake, AI-generated, or edited.

Supported labels:

- `强`: a strong supported signal exists, such as an AI-generation marker, or a valid source record without local-difference evidence.
- `较强`: a source record exists but needs attention, or the file has relatively rich photo/edit metadata without stronger signals.
- `中等`: the main evidence is a local-difference clue, sparse metadata, or another moderate signal.
- `有限`: supported signals are absent or too weak to support more than a limited conclusion.

English UI labels map to the same internal confidence semantics:

- `Strong`
- `Fairly strong`
- `Moderate`
- `Limited`

Unsupported or failed analysis should be treated as an abnormal state, not downgraded into `有限`.

## Evidence Chain Order

The evidence chain must use this order:

1. `AI 生成标记`
2. `局部差异线索`
3. `图片来源记录`
4. `拍摄/编辑信息`

### AI 生成标记

This covers GB 45438/TC260/AIGC markers that TrustPic v0 can identify.

This section does not cover every possible AI-related provenance record. For example, an OpenAI signer found in `图片来源记录` is AI-related source evidence, but it is not a GB 45438/TC260 marker.

If detected:

- Status: `支持证据`
- User meaning: the file contains an AI-generation related marker that v0 recognizes.
- Boundary: this does not prove every part of the image is AI-generated, and it does not prove the marker came from an authoritative platform.

If absent:

- Status: `未发现`
- User meaning: the supported marker scan found no recognized AI-generation marker.
- Boundary: this does not prove the image is not AI-generated. Many platforms strip or never write this metadata. It also does not cancel out AI-related source evidence found in the source record.

### 局部差异线索

This covers tile-level ELA local-difference evidence. Global compression, platform recompression, screenshots, and ordinary re-saving are common file-flow behavior and should not be elevated into a user-facing warning by themselves.

If detected:

- Status: `需留意`
- User meaning: a small set of image regions stands out from the overall recompression pattern.
- Boundary: this is only a local-difference clue. It can be caused by texture, overlays, editing workflow, or recompression. It cannot alone prove tampering, P图, or AI generation.

If absent:

- Status: `未发现`
- User meaning: TrustPic did not find a concentrated local ELA anomaly.
- Boundary: this does not prove the image was never edited. It also does not treat ordinary compression as important evidence.

### 图片来源记录

This covers C2PA-style provenance data, but the UI should use the human-readable phrase `图片来源记录`.

This section also carries the file-originality reading. Keep the title as `图片来源记录`; do not add a separate top-level module unless the product later adds dedicated screenshot or screen-photo detection.

Supported file-originality labels:

- `原始性较强`: the current file has a valid source record or rich photo/save metadata.
- `原始性有限`: the current file has incomplete source evidence, partial metadata, or no readable source/EXIF evidence.
- `疑似二次采集`: reserved for future screenshot, platform re-encode, or screen-photo signals. Do not emit this label until the evidence module actually supports it.
- `无法判断`: the source-record check did not complete.

If detected and valid:

- Status: `支持证据`
- User meaning: the file contains a readable source record, and the signature validation state is valid.
- File originality: usually `原始性较强`.
- Boundary: this does not guarantee the image content is true, complete, or shown in its original context.

If the source record includes AI-related provenance, such as OpenAI, the user-facing summary should say that this is an AI-related source record.

For Google-family records:

- `Gemini`, `NotebookLM`, `Imagen`, `SynthID`, or `Nano Banana` in the source record should be treated as AI-related source evidence.
- `Google` as the only signer/source name is not enough to claim AI generation, because Google can sign non-AI provenance records too. In that case the report should say that a Google source record was found, but the AI product name was not explicit.

If detected but incomplete or abnormal:

- Status: `需留意`
- User meaning: a source record exists, but the validation state is incomplete, unknown, or abnormal.
- File originality: usually `原始性有限`.
- Boundary: this does not prove the picture is fake, and it does not make the record automatically trustworthy.

If absent:

- Status: `未发现`
- User meaning: TrustPic v0 did not find a readable source record.
- File originality: usually `原始性有限`; rich EXIF may raise the originality reading, but does not create source provenance.
- Boundary: this is common and does not mean the image is AI-generated, edited, or authentic. Screenshots, forwarding, platform downloads, re-encoding, and secondary saves can all lose source records.

### 拍摄/编辑信息

This covers EXIF metadata.

If detected:

- Status: `支持证据`
- User meaning: the file contains photo or edit metadata, such as camera, software, capture parameters, or save information.
- Boundary: EXIF can be modified or removed. It cannot alone prove authenticity or exclude later editing.

If absent:

- Status: `未发现`
- User meaning: no EXIF metadata was found.
- Boundary: screenshots, forwarded images, and compressed platform images often have no EXIF.

## Evidence Status Labels

- `支持证据`: this evidence supports a concrete report statement.
- `需留意`: this evidence is meaningful, but should not be read as direct proof.
- `未发现`: this evidence was checked and not found.
- `无法分析`: TrustPic did not complete this evidence check.

English UI labels map to the same status semantics:

- `Supporting evidence`
- `Needs attention`
- `Not found`
- `Not analyzed`

## Possible Conclusions

TrustPic v0 chooses the conclusion by evidence priority, not by a generic verdict label.

1. If an AI-generation marker is detected:
   `发现这张图带有 AI 生成相关标记。`

2. If no GB 45438/TC260 marker is detected, but the source record is AI-related:
   `图片来源记录指向 AI 生成来源。`

3. If no AI marker or AI-related source record is detected, but local ELA difference is detected:
   `发现局部区域存在差异集中线索。`

4. If no AI marker, AI-related source record, or ELA finding is detected, but a valid source record is detected:
   `发现这张图带有可验证的来源记录。`

5. If a source record is detected but validation is incomplete or abnormal:
   `发现图片来源记录，但验证状态需要留意。`

6. If only photo/edit metadata is detected:
   `发现这张图包含拍摄或保存信息，但没有发现 AI 相关来源或标记。`

7. If no supported evidence is detected:
   `没有发现 TrustPic v0 能读取的 AI 来源、AI 标记或局部差异线索。`

## UI Requirements

- Show conclusion and confidence before technical signal names.
- Show the evidence chain in the fixed order above.
- Each evidence item must expose foldable explanations:
  - `能说明什么`
  - `不能说明什么`
  - technical details, if present
- Avoid treating missing metadata as proof of authenticity.
- Avoid presenting ELA as a direct tampering detector.
- Avoid using `内容凭证` as the primary user-facing phrase.
- Keep bilingual output generated by the backend `interpretation` object. The Web UI only chooses the locale and renders the returned report.
