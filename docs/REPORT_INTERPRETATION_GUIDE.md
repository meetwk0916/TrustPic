# TrustPic Report Interpretation Guide

Last aligned: 2026-05-26

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

- `强`: a strong supported signal exists, such as an AI-generation marker, or a valid source record without abnormal compression evidence.
- `较强`: a source record exists but needs attention, or the file has relatively rich photo/edit metadata without stronger signals.
- `中等`: the main evidence is compression/edit irregularity, sparse metadata, or another moderate signal.
- `有限`: supported signals are absent or too weak to support more than a limited conclusion.

Unsupported or failed analysis should be treated as an abnormal state, not downgraded into `有限`.

## Evidence Chain Order

The evidence chain must use this order:

1. `AI 生成标记`
2. `压缩/编辑痕迹`
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

### 压缩/编辑痕迹

This covers ELA compression-difference evidence.

If detected:

- Status: `需留意`
- User meaning: the file shows notable compression differences under the current ELA heuristic.
- Boundary: compression differences can come from saving, screenshots, platform forwarding, or edits. ELA alone cannot prove tampering, P图, or AI generation.

If absent:

- Status: `未发现`
- User meaning: ELA is below the current review threshold.
- Boundary: this does not prove the image was never processed.

### 图片来源记录

This covers C2PA-style provenance data, but the UI should use the human-readable phrase `图片来源记录`.

If detected and valid:

- Status: `支持证据`
- User meaning: the file contains a readable source record, and the signature validation state is valid.
- Boundary: this does not guarantee the image content is true or shown in its original context.

If the source record includes AI-related provenance, such as OpenAI, the user-facing summary should say that this is an AI-related source record.

For Google-family records:

- `Gemini`, `NotebookLM`, `Imagen`, `SynthID`, or `Nano Banana` in the source record should be treated as AI-related source evidence.
- `Google` as the only signer/source name is not enough to claim AI generation, because Google can sign non-AI provenance records too. In that case the report should say that a Google source record was found, but the AI product name was not explicit.

If detected but incomplete or abnormal:

- Status: `需留意`
- User meaning: a source record exists, but the validation state is incomplete, unknown, or abnormal.
- Boundary: this does not prove the picture is fake, and it does not make the record automatically trustworthy.

If absent:

- Status: `未发现`
- User meaning: TrustPic v0 did not find a readable source record.
- Boundary: this is common and does not mean the image is AI-generated or edited.

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

## Possible Conclusions

TrustPic v0 chooses the conclusion by evidence priority, not by a generic verdict label.

1. If an AI-generation marker is detected:
   `发现这张图带有 AI 生成相关标记。`

2. If no GB 45438/TC260 marker is detected, but the source record is AI-related:
   `图片来源记录显示这张图与 AI 生成来源有关。`

3. If no AI marker or AI-related source record is detected, but ELA is detected:
   `发现明显的压缩或编辑痕迹。`

4. If no AI marker, AI-related source record, or ELA finding is detected, but a valid source record is detected:
   `发现这张图带有可验证的来源记录。`

5. If a source record is detected but validation is incomplete or abnormal:
   `发现图片来源记录，但验证状态需要留意。`

6. If only photo/edit metadata is detected:
   `发现这张图包含拍摄或编辑信息，但没有发现 AI 生成标记。`

7. If no supported evidence is detected:
   `没有发现这张图是 AI 生成或被明显处理的证据。`

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
