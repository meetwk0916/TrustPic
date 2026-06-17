// Live-browser smoke test: loads the unpacked extension in real Chrome and runs
// the full analyzeImage() pipeline (incl. the Canvas ELA path) in the extension origin.
// Run: node extension/test/smoke.mjs
import path from "node:path";
import http from "node:http";
import { fileURLToPath } from "node:url";
import { existsSync, readFileSync } from "node:fs";
import puppeteer from "puppeteer-core";

const here = path.dirname(fileURLToPath(import.meta.url));
const extDir = path.resolve(here, "..");

const MIME = {
  ".html": "text/html",
  ".js": "text/javascript",
  ".mjs": "text/javascript",
  ".json": "application/json",
  ".css": "text/css",
};

function startServer(root) {
  const server = http.createServer((req, res) => {
    const urlPath = decodeURIComponent(req.url.split("?")[0]);
    const filePath = path.join(root, urlPath);
    if (!filePath.startsWith(root) || !existsSync(filePath)) {
      res.writeHead(404);
      res.end("not found");
      return;
    }
    const ext = path.extname(filePath);
    res.writeHead(200, { "Content-Type": MIME[ext] || "application/octet-stream" });
    res.end(readFileSync(filePath));
  });
  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => resolve(server));
  });
}

function findChrome() {
  const env = process.env;
  const candidates = [
    path.join(env.LOCALAPPDATA || "", "Google/Chrome/Application/chrome.exe"),
    path.join(env.PROGRAMFILES || "", "Google/Chrome/Application/chrome.exe"),
    path.join(env["PROGRAMFILES(X86)"] || "", "Google/Chrome/Application/chrome.exe"),
    path.join(env["PROGRAMFILES(X86)"] || "", "Microsoft/Edge/Application/msedge.exe"),
    path.join(env.PROGRAMFILES || "", "Microsoft/Edge/Application/msedge.exe"),
  ];
  return candidates.find((p) => p && existsSync(p));
}

let passed = 0;
let failed = 0;
function check(name, cond, extra) {
  if (cond) {
    passed += 1;
    console.log("ok   -", name);
  } else {
    failed += 1;
    console.log("FAIL -", name, extra != null ? JSON.stringify(extra) : "");
  }
}

const chromePath = findChrome();
if (!chromePath) {
  console.error("No Chrome/Edge binary found.");
  process.exit(2);
}

const browser = await puppeteer.launch({
  executablePath: chromePath,
  headless: "new",
  args: ["--no-first-run", "--no-default-browser-check"],
});

const server = await startServer(extDir);
const port = server.address().port;
const base = `http://127.0.0.1:${port}`;

try {
  const page = await browser.newPage();
  page.on("console", (m) => {
    if (m.type() === "error") console.log("   [page error]", m.text());
  });
  page.on("pageerror", (e) => console.log("   [pageerror]", e.message));

  const resp = await page.goto(`${base}/test/_harness.html`, { waitUntil: "domcontentloaded" });
  check("harness page loads", resp && resp.ok(), { status: resp && resp.status() });

  // Run the whole pipeline inside the extension page (real Chromium Canvas APIs).
  const results = await page.evaluate(async (origin) => {
    const mod = await import(`${origin}/analysis/analyze.js`);
    const { analyzeImage } = mod;

    const enc = (s) => new TextEncoder().encode(s);
    function concat(...parts) {
      const total = parts.reduce((n, p) => n + p.length, 0);
      const out = new Uint8Array(total);
      let off = 0;
      for (const p of parts) {
        out.set(p, off);
        off += p.length;
      }
      return out;
    }

    async function canvasBytes(type, draw, quality) {
      const c = document.createElement("canvas");
      c.width = 160;
      c.height = 160;
      const ctx = c.getContext("2d");
      draw(ctx, c);
      const blob = await new Promise((r) => c.toBlob(r, type, quality));
      return new Uint8Array(await blob.arrayBuffer());
    }

    // Build an EXIF APP1 segment (IFD0 Make/Model) and splice it after a real JPEG's SOI.
    function buildExifApp1(make, model) {
      const makeBytes = enc(make + "\u0000");
      const modelBytes = enc(model + "\u0000");
      const ifdStart = 8;
      const entryCount = 2;
      const dataStart = ifdStart + 2 + entryCount * 12 + 4;
      const makeOffset = dataStart;
      const modelOffset = dataStart + makeBytes.length;
      const tiffLen = modelOffset + modelBytes.length;
      const tiff = new Uint8Array(tiffLen);
      const view = new DataView(tiff.buffer);
      tiff[0] = 0x49;
      tiff[1] = 0x49;
      view.setUint16(2, 42, true);
      view.setUint32(4, ifdStart, true);
      view.setUint16(ifdStart, entryCount, true);
      let e = ifdStart + 2;
      view.setUint16(e, 271, true);
      view.setUint16(e + 2, 2, true);
      view.setUint32(e + 4, makeBytes.length, true);
      view.setUint32(e + 8, makeOffset, true);
      e += 12;
      view.setUint16(e, 272, true);
      view.setUint16(e + 2, 2, true);
      view.setUint32(e + 4, modelBytes.length, true);
      view.setUint32(e + 8, modelOffset, true);
      view.setUint32(ifdStart + 2 + entryCount * 12, 0, true);
      tiff.set(makeBytes, makeOffset);
      tiff.set(modelBytes, modelOffset);
      const exifHeader = enc("Exif\u0000\u0000");
      const app1Len = 2 + exifHeader.length + tiff.length;
      const app1Header = new Uint8Array(4);
      const av = new DataView(app1Header.buffer);
      av.setUint8(0, 0xff);
      av.setUint8(1, 0xe1);
      av.setUint16(2, app1Len, false);
      return concat(app1Header, exifHeader, tiff);
    }

    const out = {};

    // 1) Clean solid PNG -> no supported signal.
    const cleanPng = await canvasBytes("image/png", (ctx) => {
      ctx.fillStyle = "#8899aa";
      ctx.fillRect(0, 0, 160, 160);
    });
    out.clean = await analyzeImage(cleanPng, "image/png", "zh-CN");

    // 2) Real PNG + appended GB45438 AI marker bytes (still decodes).
    const gbBytes = concat(cleanPng, enc('\n"AI_GENERATED"\n'));
    out.gb = await analyzeImage(gbBytes, "image/png", "zh-CN");

    // 3) Real JPEG + appended heuristic C2PA AI manifest bytes.
    const photoJpeg = await canvasBytes(
      "image/jpeg",
      (ctx) => {
        const g = ctx.createLinearGradient(0, 0, 160, 160);
        g.addColorStop(0, "#203040");
        g.addColorStop(1, "#d0c0a0");
        ctx.fillStyle = g;
        ctx.fillRect(0, 0, 160, 160);
        ctx.fillStyle = "#ff3300";
        ctx.fillRect(40, 40, 30, 30);
      },
      0.92,
    );
    const c2paBytes = concat(photoJpeg, enc("....jumb....c2pa.assertions....OpenAI DALL-E...."));
    out.c2pa = await analyzeImage(c2paBytes, "image/jpeg", "zh-CN");

    // 4) Real JPEG with spliced EXIF Make/Model APP1.
    const app1 = buildExifApp1("TrustPic Camera", "V0 EXIF Sample");
    const exifJpeg = concat(photoJpeg.slice(0, 2), app1, photoJpeg.slice(2));
    out.exif = await analyzeImage(exifJpeg, "image/jpeg", "zh-CN");

    // 5) English locale on clean image (locale toggle path).
    out.cleanEn = await analyzeImage(cleanPng, "image/png", "en-US");

    // Trim heatmap data urls to a boolean + length to keep payload small.
    for (const k of Object.keys(out)) {
      const url = out[k]?.assets?.ela_heatmap_data_url;
      out[k]._heatmapOk = typeof url === "string" && url.startsWith("data:image/");
      out[k]._heatmapLen = typeof url === "string" ? url.length : 0;
      if (out[k].assets) delete out[k].assets.ela_heatmap_data_url;
    }
    return out;
  }, base);

  // Clean PNG
  check("clean PNG: verdict no_supported_signal_found", results.clean.verdict === "no_supported_signal_found", results.clean.verdict);
  check("clean PNG: ELA produced a heatmap data URL", results.clean._heatmapOk && results.clean._heatmapLen > 100, results.clean._heatmapLen);
  check("clean PNG: report has interpretation + limitations", Boolean(results.clean.interpretation) && Array.isArray(results.clean.limitations) && results.clean.limitations.length === 4);

  // GB45438
  check("GB45438 marker: verdict supported_signal_detected", results.gb.verdict === "supported_signal_detected", results.gb.verdict);
  check("GB45438 marker: gb45438 signal detected", results.gb.signals.gb45438.detected === true);
  check("GB45438 marker: zh conclusion mentions AI marker", typeof results.gb.interpretation.conclusion === "string" && results.gb.interpretation.conclusion.includes("AI"), results.gb.interpretation.conclusion);

  // C2PA
  check("C2PA manifest: c2pa signal detected", results.c2pa.signals.c2pa.detected === true);
  check("C2PA manifest: ai_related true, validation_state null", results.c2pa.signals.c2pa.details.ai_related === true && results.c2pa.signals.c2pa.details.validation_state === null);
  check("C2PA manifest: verdict supported_signal_detected", results.c2pa.verdict === "supported_signal_detected", results.c2pa.verdict);

  // EXIF
  check("EXIF JPEG: exif detected with Make/Model", results.exif.signals.exif.detected === true && results.exif.signals.exif.details.fields.Make === "TrustPic Camera" && results.exif.signals.exif.details.fields.Model === "V0 EXIF Sample", results.exif.signals.exif.details);
  check("EXIF JPEG: ELA heatmap produced", results.exif._heatmapOk);

  // Locale
  check("English locale: confidence_label is Limited", results.cleanEn.interpretation.confidence_label === "Limited", results.cleanEn.interpretation.confidence_label);
  check("English locale: conclusion is English", typeof results.cleanEn.interpretation.conclusion === "string" && /No readable/.test(results.cleanEn.interpretation.conclusion), results.cleanEn.interpretation.conclusion);

  console.log(`\n${passed} passed, ${failed} failed.`);
  process.exitCode = failed === 0 ? 0 : 1;
} finally {
  await browser.close();
  server.close();
}
