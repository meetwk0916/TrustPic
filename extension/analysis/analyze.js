// Local analysis orchestrator, ported from backend app/services/analyze.py.

import { inspectC2pa } from "./c2pa.js";
import { inspectGb45438 } from "./gb45438.js";
import { inspectExif } from "./exif.js";
import { inspectEla } from "./ela.js";
import { buildInterpretation } from "./interpretation.js";

const MAX_UPLOAD_BYTES = 15 * 1024 * 1024;
const MAX_PIXELS = 40000000;
const SUPPORTED_MIME_TYPES = new Set(["image/jpeg", "image/png", "image/webp"]);

const LIMITATIONS = [
  "No supported signal found does not prove the image is authentic.",
  "ELA can suggest compression or edit irregularities, but it does not prove AI generation.",
  "C2PA and metadata can be stripped by screenshots, re-encoding, or platform forwarding.",
  "TrustPic v0 does not run deep-learning AI detector models or SynthID detection.",
];

export class AnalyzeError extends Error {
  constructor(message) {
    super(message);
    this.name = "AnalyzeError";
  }
}

export async function analyzeImage(bytes, contentType, locale = "zh-CN") {
  if (!SUPPORTED_MIME_TYPES.has(contentType)) {
    throw new AnalyzeError("Unsupported file type. Use JPG, PNG, or WebP.");
  }
  if (!bytes || bytes.length === 0) {
    throw new AnalyzeError("No file content received.");
  }
  if (bytes.length > MAX_UPLOAD_BYTES) {
    throw new AnalyzeError("File is too large. Maximum size is 15 MB.");
  }

  const bitmap = await decodeImage(bytes, contentType);
  try {
    if (bitmap.width * bitmap.height > MAX_PIXELS) {
      throw new AnalyzeError("Image dimensions are too large for v0 analysis.");
    }

    const c2pa = inspectC2pa(bytes);
    const gb45438 = inspectGb45438(bytes);
    const exif = inspectExif(bytes, contentType);
    const { signal: ela, heatmapDataUrl } = await inspectEla(bitmap);

    const signals = { c2pa, gb45438, exif, ela };
    const { verdict, summary, recommendation } = buildVerdict(signals);
    const interpretation = buildInterpretation(signals, locale);

    return {
      status: "success",
      verdict,
      summary,
      signals,
      interpretation,
      limitations: LIMITATIONS,
      recommendation,
      assets: { ela_heatmap_data_url: heatmapDataUrl },
    };
  } finally {
    bitmap.close?.();
  }
}

async function decodeImage(bytes, contentType) {
  try {
    const blob = new Blob([bytes], { type: contentType });
    return await createImageBitmap(blob);
  } catch {
    throw new AnalyzeError("Uploaded file could not be decoded as an image.");
  }
}

function buildVerdict(signals) {
  if (signals.c2pa.detected || signals.gb45438.detected) {
    return {
      verdict: "supported_signal_detected",
      summary: "Supported provenance or AI-generation metadata was detected.",
      recommendation: "Review the detected provenance signal and source details before sharing.",
    };
  }
  if (signals.ela.detected) {
    return {
      verdict: "review_recommended",
      summary: "ELA found a concentrated local difference pattern that may deserve review.",
      recommendation: "Compare the local difference heatmap with the original image context.",
    };
  }
  return {
    verdict: "no_supported_signal_found",
    summary: "No supported AI provenance signal or concentrated local difference pattern was found.",
    recommendation: "Treat this as inconclusive, not as proof that the image is real.",
  };
}
