// Parity harness for the buildless analysis modules (run with: node parity-test.mjs)
import assert from "node:assert";
import { inspectGb45438 } from "../analysis/gb45438.js";
import { inspectExif } from "../analysis/exif.js";
import { inspectC2pa } from "../analysis/c2pa.js";
import { buildInterpretation } from "../analysis/interpretation.js";
import { analyzeLocalDifferences } from "../analysis/ela.js";

let passed = 0;
function check(name, fn) {
  fn();
  passed += 1;
  console.log("ok   -", name);
}

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

function buildExifJpeg(make, model) {
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
  const soi = new Uint8Array([0xff, 0xd8]);
  const eoi = new Uint8Array([0xff, 0xd9]);
  return concat(soi, app1Header, exifHeader, tiff, eoi);
}

check("gb45438 detects AI_GENERATED marker", () => {
  const out = inspectGb45438(concat(enc("PNGDATA"), enc('\n"AI_GENERATED"\n')));
  assert.strictEqual(out.detected, true);
  assert.deepStrictEqual(out.details.matched_terms, ["AI_GENERATED"]);
});

check("gb45438 extracts TC260 XMP fields", () => {
  const xmp = `
<x:xmpmeta xmlns:x="adobe:ns:meta/">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description xmlns:AIGC="http://www.tc260.org.cn/ns/AIGC/1.0/">
      <AIGC:Label>AIGC</AIGC:Label>
      <AIGC:ContentProducer>TrustPic Sample Generator</AIGC:ContentProducer>
      <AIGC:ProduceID>sample-produce-id</AIGC:ProduceID>
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>`;
  const out = inspectGb45438(concat(enc("PNGDATA"), enc(xmp)));
  assert.strictEqual(out.detected, true);
  assert.strictEqual(out.details.tc260_namespace_detected, true);
  assert.strictEqual(out.details.xmp_fields.Label, "AIGC");
  assert.strictEqual(out.details.xmp_fields.ContentProducer, "TrustPic Sample Generator");
});

check("gb45438 absent on clean bytes", () => {
  const out = inspectGb45438(enc("just some pixels"));
  assert.strictEqual(out.detected, false);
  assert.strictEqual(out.status, "absent");
});

check("exif parses Make/Model from JPEG APP1", () => {
  const bytes = buildExifJpeg("TrustPic Camera", "V0 EXIF Sample");
  const out = inspectExif(bytes, "image/jpeg");
  assert.strictEqual(out.detected, true);
  assert.strictEqual(out.status, "present");
  assert.strictEqual(out.details.fields.Make, "TrustPic Camera");
  assert.strictEqual(out.details.fields.Model, "V0 EXIF Sample");
  assert.strictEqual(out.details.field_count, 2);
});

check("exif absent on PNG without eXIf", () => {
  const png = new Uint8Array([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0, 0, 0, 0]);
  const out = inspectExif(png, "image/png");
  assert.strictEqual(out.detected, false);
});

check("c2pa detects AI-related manifest", () => {
  const out = inspectC2pa(enc("....jumb....c2pa.assertions....OpenAI DALL-E...."));
  assert.strictEqual(out.detected, true);
  assert.strictEqual(out.details.ai_related, true);
  assert.strictEqual(out.details.validation_state, null);
  assert.ok(out.details.assertion_labels.includes("c2pa.assertions"));
});

check("c2pa absent on plain bytes", () => {
  const out = inspectC2pa(enc("plain image bytes with no provenance"));
  assert.strictEqual(out.detected, false);
  assert.strictEqual(out.status, "absent");
});

const elaLow = { checked: true, detected: false, status: "low_signal", summary: "", details: { mean_error: 1.2, local_anomaly_count: 0, local_anomaly_ratio: 0 } };
const absent = (status) => ({ checked: true, detected: false, status, summary: "", details: {} });

check("interpretation: no-signal PNG (zh)", () => {
  const signals = {
    c2pa: { checked: true, detected: false, status: "absent", summary: "", details: { reason: "NoReadableManifest" } },
    gb45438: { checked: true, detected: false, status: "absent", summary: "", details: { matched_terms: [], xmp_fields: {} } },
    exif: { checked: true, detected: false, status: "absent", summary: "", details: { field_count: 0 } },
    ela: elaLow,
  };
  const r = buildInterpretation(signals, "zh-CN");
  assert.strictEqual(r.confidence_label, "有限");
  assert.strictEqual(r.conclusion, "没有发现 TrustPic v0 能读取的 AI 来源、AI 标记或局部差异线索。");
  assert.deepStrictEqual(r.evidence_chain.map((i) => i.title), ["AI 生成标记", "局部差异线索", "图片来源记录", "拍摄/编辑信息"]);
  assert.strictEqual(r.evidence_chain[2].details.originality_label, "原始性有限");
});

check("interpretation: no-signal PNG (en)", () => {
  const signals = {
    c2pa: absent("absent"),
    gb45438: { checked: true, detected: false, status: "absent", summary: "", details: { matched_terms: [], xmp_fields: {} } },
    exif: { checked: true, detected: false, status: "absent", summary: "", details: { field_count: 0 } },
    ela: elaLow,
  };
  const r = buildInterpretation(signals, "en-US");
  assert.strictEqual(r.confidence_label, "Limited");
  assert.strictEqual(r.conclusion, "No readable AI source, AI marker, or local-difference clue was found by TrustPic v0.");
  assert.deepStrictEqual(r.evidence_chain.map((i) => i.title), ["AI marker", "Local difference clues", "Source record", "Photo/save metadata"]);
  assert.strictEqual(r.evidence_chain[2].status_label, "Not found");
  assert.strictEqual(r.evidence_chain[2].details.originality_label, "Limited originality evidence");
});

check("interpretation: gb45438 marker (zh)", () => {
  const signals = {
    c2pa: absent("absent"),
    gb45438: { checked: true, detected: true, status: "detected", summary: "", details: { matched_terms: ["AI_GENERATED"], xmp_fields: {} } },
    exif: { checked: true, detected: false, status: "absent", summary: "", details: { field_count: 0 } },
    ela: elaLow,
  };
  const r = buildInterpretation(signals, "zh-CN");
  assert.strictEqual(r.confidence_label, "强");
  assert.strictEqual(r.conclusion, "发现这张图带有 AI 生成相关标记。");
  assert.strictEqual(r.evidence_chain[0].title, "AI 生成标记");
  assert.strictEqual(r.evidence_chain[0].status_label, "支持证据");
});

check("interpretation: capture EXIF (zh)", () => {
  const signals = {
    c2pa: absent("absent"),
    gb45438: { checked: true, detected: false, status: "absent", summary: "", details: { matched_terms: [], xmp_fields: {} } },
    exif: { checked: true, detected: true, status: "present", summary: "", details: { field_count: 2, fields: { Make: "TrustPic Camera", Model: "V0 EXIF Sample" } } },
    ela: elaLow,
  };
  const r = buildInterpretation(signals, "zh-CN");
  assert.strictEqual(r.confidence_label, "中等");
  assert.strictEqual(r.conclusion, "发现这张图包含相机拍摄相关信息，但没有发现 AI 相关来源或标记。");
  assert.strictEqual(r.evidence_chain[3].title, "拍摄/编辑信息");
  assert.strictEqual(r.evidence_chain[3].status_label, "支持证据");
  assert.ok(["原始性有限", "原始性较强"].includes(r.evidence_chain[2].details.originality_label));
});

check("interpretation: ela review (zh)", () => {
  const signals = {
    c2pa: absent("absent"),
    gb45438: { checked: true, detected: false, status: "absent", summary: "", details: { matched_terms: [], xmp_fields: {} } },
    exif: { checked: true, detected: false, status: "absent", summary: "", details: { field_count: 0 } },
    ela: { checked: true, detected: true, status: "review", summary: "", details: { mean_error: 12.3, local_anomaly_count: 3, local_anomaly_ratio: 0.1 } },
  };
  const r = buildInterpretation(signals, "zh-CN");
  assert.strictEqual(r.confidence_label, "中等");
  assert.strictEqual(r.conclusion, "发现局部区域存在差异集中线索。");
  assert.strictEqual(r.evidence_chain[1].title, "局部差异线索");
  assert.strictEqual(r.evidence_chain[1].status_label, "需留意");
});

check("interpretation: AI-related c2pa drives AI source (zh)", () => {
  const signals = {
    c2pa: { checked: true, detected: true, status: "detected", summary: "", details: { ai_related: true, validation_state: null, claim_generator: "openai/1.0" } },
    gb45438: { checked: true, detected: false, status: "absent", summary: "", details: { matched_terms: [], xmp_fields: {} } },
    exif: { checked: true, detected: false, status: "absent", summary: "", details: { field_count: 0 } },
    ela: elaLow,
  };
  const r = buildInterpretation(signals, "zh-CN");
  assert.strictEqual(r.conclusion, "图片来源记录指向 AI 生成来源。");
  assert.strictEqual(r.confidence_label, "较强");
  assert.strictEqual(r.evidence_chain[2].status_label, "需留意");
});

check("ela: uniform gray => no anomaly", () => {
  const w = 128, h = 128;
  const gray = new Uint8Array(w * h).fill(10);
  const a = analyzeLocalDifferences(gray, w, h);
  assert.strictEqual(a.tile_count, 16);
  assert.strictEqual(a.local_anomaly_detected, false);
  assert.strictEqual(a.local_anomaly_count, 0);
});

check("ela: two bright tiles => anomaly detected", () => {
  const w = 128, h = 128;
  const gray = new Uint8Array(w * h).fill(5);
  for (const [tx, ty] of [[0, 0], [1, 0]]) {
    for (let y = ty * 32; y < ty * 32 + 32; y += 1) {
      for (let x = tx * 32; x < tx * 32 + 32; x += 1) {
        gray[y * w + x] = 200;
      }
    }
  }
  const a = analyzeLocalDifferences(gray, w, h);
  assert.strictEqual(a.local_anomaly_count, 2);
  assert.strictEqual(a.local_anomaly_detected, true);
});

console.log(`\n${passed} checks passed.`);
