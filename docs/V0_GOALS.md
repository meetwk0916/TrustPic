# TrustPic v0 Goals

## Starting Assumptions

- TrustPic should start as a usable single-image tool, not a broad platform.
- The first valuable output is an evidence report, not a binary "real/fake" verdict.
- Future product forms include Web and WeChat Mini Program, so v0 must expose a stable API and report schema.
- We should avoid depending on closed or unavailable detector APIs for v0.

## Product Positioning

TrustPic v0 is a privacy-conscious image evidence reporter.

It accepts one image and returns:

- A human-readable conclusion grounded in supported file evidence.
- A confidence label describing how strongly the evidence chain supports the conclusion.
- What supported AI markers or AI-related source records were found.
- What supported provenance/source records were found or absent.
- Whether the file has basic metadata and EXIF signals.
- Whether tile-level ELA found a concentrated local-difference clue.
- Foldable explanations for what each evidence item can and cannot support.
- A machine-readable JSON report.

TrustPic v0 must not claim:

- It can prove an image is real.
- It can detect all AI-generated images.
- Absence of C2PA, GB 45438, EXIF, or ELA signals means an image is authentic.
- ELA alone proves AI generation.
- Local-difference clues prove tampering, P图, or malicious editing.
- A valid source record proves the image content is true or shown in its original context.

## v0 Scope

### Included

- Single image upload.
- Supported formats: JPG, JPEG, PNG, WebP.
- Backend API endpoint: `POST /api/v1/analyze`.
- Report JSON response with stable top-level fields.
- C2PA read/verification attempt.
- GB 45438 file metadata or byte-signal scan attempt.
- AI-related source-record interpretation for OpenAI/DALL-E and explicit Google AI product records such as Gemini, NotebookLM, Imagen, SynthID, and Nano Banana.
- EXIF extraction summary.
- ELA heatmap generation and tile-level local-difference metrics.
- Web UI that can upload one image and display the report.
- Web UI that highlights strong AI-related evidence, separates core evidence from local-difference analysis, and supports light/dark mode.
- Chinese and English report interpretation via `locale=zh-CN` or `locale=en-US` on `POST /api/v1/analyze`.
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

The v0 report uses evidence-first language. `interpretation` is the user-facing contract. `verdict`, `summary`, `limitations`, and `recommendation` remain in the API for compatibility and machine routing, but the Web UI should rely on `interpretation`.

```json
{
  "status": "success",
  "verdict": "supported_signal_detected | review_recommended | no_supported_signal_found | unsupported",
  "summary": "Compatibility summary",
  "signals": {
    "c2pa": {
      "checked": true,
      "detected": false,
      "status": "absent | detected | unavailable",
      "summary": "Signal-level summary",
      "details": {}
    },
    "gb45438": {
      "checked": true,
      "detected": false,
      "status": "absent | detected",
      "summary": "Signal-level summary",
      "details": {}
    },
    "exif": {
      "checked": true,
      "detected": false,
      "status": "absent | present",
      "summary": "Signal-level summary",
      "details": {}
    },
    "ela": {
      "checked": true,
      "detected": false,
      "status": "low_signal | review",
      "summary": "Signal-level summary",
      "details": {
        "mean_error": 0,
        "tile_size": 32,
        "tile_count": 0,
        "local_threshold": 28.0,
        "local_anomaly_detected": false,
        "local_anomaly_count": 0,
        "local_anomaly_ratio": 0,
        "local_anomaly_tiles": [],
        "top_tiles": []
      }
    }
  },
  "interpretation": {
    "confidence_label": "强 | 较强 | 中等 | 有限, or localized equivalents such as Strong | Fairly strong | Moderate | Limited",
    "conclusion": "Human-readable conclusion",
    "evidence_chain": [
      {
        "key": "gb45438 | ela | c2pa | exif",
        "title": "AI 生成标记 | 局部差异线索 | 图片来源记录 | 拍摄/编辑信息",
        "status_label": "支持证据 | 需留意 | 未发现 | 无法分析, or localized equivalents such as Supporting evidence | Needs attention | Not found | Not analyzed",
        "summary": "Short user-facing evidence summary",
        "means": "What this evidence can support",
        "does_not_mean": "What this evidence cannot support",
        "details": {}
      }
    ],
    "limits": [
      "没有发现可读证据，不等于图片一定不是 AI 生成。",
      "局部差异只是线索，不能单独证明图片被篡改、P 图或 AI 生成。",
      "来源记录能说明文件里带有可验证信息，但不等于图片内容一定真实或上下文完整。"
    ]
  },
  "limitations": [],
  "recommendation": "Compatibility recommendation; not shown as a primary Web UI section",
  "assets": {
    "ela_heatmap_data_url": null
  }
}
```

## User-Facing Report Rules

The Web UI should display:

- conclusion and confidence first;
- a strong `AI 相关证据` alert when GB 45438/TC260 markers or AI-related source records are present;
- core evidence cards for `AI 生成标记`, `图片来源记录`, and `拍摄/编辑信息`;
- `局部差异分析` as a separate lower-priority module together with the heatmap;
- report-reading notes as a separate bottom section, not mixed with core evidence.

The UI should not show next-step recommendations in v0.

## Success Criteria

v0 is done when:

- A developer can run backend and frontend locally from documented commands.
- A user can upload one image through the Web UI.
- The UI shows the original image, conclusion, confidence, AI evidence alert when relevant, core evidence cards, local-difference analysis, report-reading notes, and ELA heatmap when available.
- The API returns structured JSON that a future Mini Program can consume without special casing the Web UI.
- The API can return Chinese or English user-facing interpretation text from the same evidence signals.
- Invalid file type and oversized file cases return controlled errors.
- Sample verification and first-phase suite checks cover:
  - normal camera image with EXIF
  - image with stripped metadata
  - image with C2PA metadata
  - AI marker / GB 45438 or TC260 fixture
  - AI-related source-record examples when available
  - local-difference image that produces a review heatmap
  - at least one dataset-suite run with completed public or generated sources

## v0 Non-Negotiables

- Do not persist uploaded original images.
- Do not present `Pass` as "true image".
- Do not call model-derived scores "probability" unless calibrated by a labeled evaluation set.
- Do not treat ordinary compression or platform re-encoding as a primary warning.
- Do not present local-difference ELA as proof of tampering.
- Keep the API stable before building Mini Program UI.
