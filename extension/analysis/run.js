// Fetch a selected image and run the local TrustPic analysis pipeline.

import { analyzeImage, AnalyzeError } from "./analyze.js";

export async function runAnalysis(sourceUrl, locale) {
  const imageResponse = await fetch(sourceUrl, { credentials: "include", cache: "no-store" });
  if (!imageResponse.ok) {
    throw new Error(`Image request failed with ${imageResponse.status}`);
  }

  const sourceBlob = await imageResponse.blob();
  const contentType = supportedImageType(sourceBlob.type, sourceUrl);
  if (!contentType) {
    throw new Error("This image format is not supported. Use JPG, PNG, or WebP.");
  }

  const bytes = new Uint8Array(await sourceBlob.arrayBuffer());
  try {
    return await analyzeImage(bytes, contentType, locale);
  } catch (error) {
    if (error instanceof AnalyzeError) {
      throw new Error(error.message);
    }
    throw error;
  }
}

export function supportedImageType(contentType, url) {
  const normalized = String(contentType || "").split(";")[0].trim().toLowerCase();
  if (["image/jpeg", "image/png", "image/webp"].includes(normalized)) {
    return normalized;
  }

  const lowerUrl = String(url || "").split("?")[0].toLowerCase();
  if (lowerUrl.startsWith("data:image/jpeg") || lowerUrl.startsWith("data:image/jpg")) return "image/jpeg";
  if (lowerUrl.startsWith("data:image/png")) return "image/png";
  if (lowerUrl.startsWith("data:image/webp")) return "image/webp";
  if (lowerUrl.endsWith(".jpg") || lowerUrl.endsWith(".jpeg")) return "image/jpeg";
  if (lowerUrl.endsWith(".png")) return "image/png";
  if (lowerUrl.endsWith(".webp")) return "image/webp";
  return null;
}
