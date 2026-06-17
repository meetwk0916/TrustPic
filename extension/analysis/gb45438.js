// GB 45438 / TC260 AIGC marker scan, ported from backend app/services/gb45438.py.

const TC260_AIGC_NAMESPACE = "http://www.tc260.org.cn/ns/AIGC/1.0/";

const TC260_FIELDS = [
  "Label",
  "ContentProducer",
  "ProduceID",
  "ReservedCode1",
  "ContentPropagator",
  "PropagateID",
  "ReservedCode2",
];

const SIGNATURE_TERMS = [
  '"AIGC"',
  '"aigc"',
  '"aigc_info"',
  "GB 45438",
  "GB45438",
  "AI_GENERATED",
  TC260_AIGC_NAMESPACE,
];

const latin1 = new TextDecoder("latin1");
const utf8 = new TextDecoder("utf-8", { fatal: false, ignoreBOM: true });

export function inspectGb45438(bytes) {
  const byteText = latin1.decode(bytes);
  const xmpText = utf8.decode(bytes);

  const matchedTerms = SIGNATURE_TERMS.filter((term) => byteText.includes(term));
  const xmpFields = extractTc260XmpFields(xmpText);
  const detected = matchedTerms.length > 0 || Object.keys(xmpFields).length > 0;

  return {
    checked: true,
    detected,
    status: detected ? "detected" : "absent",
    summary: detected
      ? "Possible GB 45438/AIGC metadata or byte-level marker was found."
      : "No GB 45438/AIGC metadata or byte-level marker was found by v0 scan.",
    details: {
      matched_terms: matchedTerms,
      tc260_namespace_detected: byteText.includes(TC260_AIGC_NAMESPACE),
      xmp_fields: xmpFields,
      scan_mode: "tc260_xmp_and_byte_markers",
    },
  };
}

function extractTc260XmpFields(text) {
  const fields = {};
  for (const field of TC260_FIELDS) {
    const value = extractXmlValue(text, field);
    if (value) {
      fields[field] = value;
    }
  }
  return fields;
}

function extractXmlValue(text, localName) {
  const escaped = localName.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const pattern = new RegExp(
    `<(?:[A-Za-z0-9_.-]+:)?${escaped}\\b[^>]*>([\\s\\S]*?)</(?:[A-Za-z0-9_.-]+:)?${escaped}>`,
    "i",
  );
  const match = pattern.exec(text);
  if (!match) {
    return null;
  }
  const collapsed = match[1].replace(/\s+/g, " ").trim();
  return decodeEntities(collapsed).slice(0, 300);
}

function decodeEntities(value) {
  return value
    .replace(/&#x([0-9a-fA-F]+);/g, (_, hex) => safeCodePoint(parseInt(hex, 16)))
    .replace(/&#(\d+);/g, (_, dec) => safeCodePoint(parseInt(dec, 10)))
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&amp;/g, "&");
}

function safeCodePoint(code) {
  if (!Number.isFinite(code) || code < 0 || code > 0x10ffff) {
    return "";
  }
  try {
    return String.fromCodePoint(code);
  } catch {
    return "";
  }
}
