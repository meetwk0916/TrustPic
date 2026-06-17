// Canvas-based Error Level Analysis, ported from backend app/services/ela.py.

const JPEG_QUALITY = 0.9;
const AMPLIFICATION = 15;
const TILE_SIZE = 32;
const LOCAL_TILE_MIN_ERROR = 28.0;
const LOCAL_RATIO_THRESHOLD = 2.5;
const LOCAL_MIN_TILE_COUNT = 2;

export async function inspectEla(bitmap) {
  const width = bitmap.width;
  const height = bitmap.height;

  const canvas = new OffscreenCanvas(width, height);
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  ctx.drawImage(bitmap, 0, 0);
  const original = ctx.getImageData(0, 0, width, height).data;

  const recompressedBlob = await canvas.convertToBlob({ type: "image/jpeg", quality: JPEG_QUALITY });
  const recompressedBitmap = await createImageBitmap(recompressedBlob);
  ctx.drawImage(recompressedBitmap, 0, 0);
  recompressedBitmap.close?.();
  const compressed = ctx.getImageData(0, 0, width, height).data;

  const pixelCount = width * height;
  const enhanced = new Uint8ClampedArray(pixelCount * 4);
  const gray = new Uint8Array(pixelCount);
  let sumAll = 0;

  for (let i = 0; i < pixelCount; i += 1) {
    const p = i * 4;
    const er = clamp255(Math.abs(original[p] - compressed[p]) * AMPLIFICATION);
    const eg = clamp255(Math.abs(original[p + 1] - compressed[p + 1]) * AMPLIFICATION);
    const eb = clamp255(Math.abs(original[p + 2] - compressed[p + 2]) * AMPLIFICATION);
    enhanced[p] = er;
    enhanced[p + 1] = eg;
    enhanced[p + 2] = eb;
    enhanced[p + 3] = 255;
    sumAll += er + eg + eb;
    gray[i] = (er * 19595 + eg * 38470 + eb * 7471 + 32768) >> 16;
  }

  const meanError = round2(sumAll / (pixelCount * 3));
  const localAnalysis = analyzeLocalDifferences(gray, width, height);
  const detected = localAnalysis.local_anomaly_detected;

  const heatmapDataUrl = await heatmapToDataUrl(enhanced, width, height);

  return {
    signal: {
      checked: true,
      detected,
      status: detected ? "review" : "low_signal",
      summary: detected
        ? "ELA found a concentrated local difference pattern."
        : "ELA did not find a concentrated local difference pattern.",
      details: {
        mean_error: meanError,
        jpeg_quality: 90,
        amplification: AMPLIFICATION,
        ...localAnalysis,
      },
    },
    heatmapDataUrl,
  };
}

export function analyzeLocalDifferences(gray, width, height) {
  const tiles = [];
  for (let top = 0; top < height; top += TILE_SIZE) {
    for (let left = 0; left < width; left += TILE_SIZE) {
      const right = Math.min(left + TILE_SIZE, width);
      const bottom = Math.min(top + TILE_SIZE, height);
      if (right - left < TILE_SIZE / 2 || bottom - top < TILE_SIZE / 2) {
        continue;
      }
      let sum = 0;
      for (let y = top; y < bottom; y += 1) {
        const rowStart = y * width;
        for (let x = left; x < right; x += 1) {
          sum += gray[rowStart + x];
        }
      }
      const area = (right - left) * (bottom - top);
      tiles.push({ x: left, y: top, width: right - left, height: bottom - top, mean_error: sum / area });
    }
  }

  if (tiles.length === 0) {
    return {
      tile_size: TILE_SIZE,
      tile_count: 0,
      local_anomaly_detected: false,
      local_anomaly_count: 0,
      local_anomaly_ratio: 0.0,
      local_threshold: LOCAL_TILE_MIN_ERROR,
      top_tiles: [],
    };
  }

  const errors = tiles.map((tile) => tile.mean_error);
  const averageError = mean(errors);
  const spread = errors.length > 1 ? pstdev(errors, averageError) : 0.0;
  const ratioThreshold = averageError * LOCAL_RATIO_THRESHOLD;
  const localThreshold = Math.max(LOCAL_TILE_MIN_ERROR, ratioThreshold);
  const anomalyTiles = tiles.filter((tile) => tile.mean_error >= localThreshold);
  const anomalyRatio = anomalyTiles.length / tiles.length;
  const localAnomalyDetected = anomalyTiles.length >= LOCAL_MIN_TILE_COUNT && anomalyRatio <= 0.25;

  const topTiles = [...tiles].sort((a, b) => b.mean_error - a.mean_error).slice(0, 5);

  return {
    tile_size: TILE_SIZE,
    tile_count: tiles.length,
    tile_mean_error: round2(averageError),
    tile_error_stddev: round2(spread),
    local_threshold: round2(localThreshold),
    local_anomaly_detected: localAnomalyDetected,
    local_anomaly_count: anomalyTiles.length,
    local_anomaly_ratio: round4(anomalyRatio),
    local_anomaly_tiles: anomalyTiles.slice(0, 12).map(serializeTile),
    top_tiles: topTiles.map(serializeTile),
  };
}

function serializeTile(tile) {
  return {
    x: tile.x,
    y: tile.y,
    width: tile.width,
    height: tile.height,
    mean_error: round2(tile.mean_error),
  };
}

async function heatmapToDataUrl(enhanced, width, height) {
  const canvas = new OffscreenCanvas(width, height);
  const ctx = canvas.getContext("2d");
  ctx.putImageData(new ImageData(enhanced, width, height), 0, 0);
  const blob = await canvas.convertToBlob({ type: "image/jpeg", quality: JPEG_QUALITY });
  return blobToDataUrl(blob);
}

function blobToDataUrl(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(reader.error || new Error("Failed to read heatmap blob."));
    reader.readAsDataURL(blob);
  });
}

function clamp255(value) {
  return value > 255 ? 255 : value;
}

function mean(values) {
  let sum = 0;
  for (const value of values) {
    sum += value;
  }
  return sum / values.length;
}

function pstdev(values, average) {
  let sum = 0;
  for (const value of values) {
    const diff = value - average;
    sum += diff * diff;
  }
  return Math.sqrt(sum / values.length);
}

function round2(value) {
  return Math.round(value * 100) / 100;
}

function round4(value) {
  return Math.round(value * 10000) / 10000;
}
