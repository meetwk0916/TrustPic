// Minimal EXIF reader, ported to mirror PIL Image.getexif() over the IFD0 block.
// Reads top-level IFD0 tags (the same set PIL exposes by iterating getexif()),
// from JPEG APP1 "Exif\0\0", PNG "eXIf", or WebP "EXIF" containers.

const TIFF_TAG_NAMES = {
  256: "ImageWidth",
  257: "ImageLength",
  258: "BitsPerSample",
  259: "Compression",
  262: "PhotometricInterpretation",
  270: "ImageDescription",
  271: "Make",
  272: "Model",
  273: "StripOffsets",
  274: "Orientation",
  277: "SamplesPerPixel",
  278: "RowsPerStrip",
  279: "StripByteCounts",
  282: "XResolution",
  283: "YResolution",
  284: "PlanarConfiguration",
  296: "ResolutionUnit",
  301: "TransferFunction",
  305: "Software",
  306: "DateTime",
  315: "Artist",
  318: "WhitePoint",
  319: "PrimaryChromaticities",
  513: "JPEGInterchangeFormat",
  514: "JPEGInterchangeFormatLength",
  529: "YCbCrCoefficients",
  530: "YCbCrSubSampling",
  531: "YCbCrPositioning",
  532: "ReferenceBlackWhite",
  700: "XMLPacket",
  33432: "Copyright",
  33434: "ExposureTime",
  33437: "FNumber",
  34665: "ExifOffset",
  34850: "ExposureProgram",
  34853: "GPSInfo",
  34855: "ISOSpeedRatings",
  36864: "ExifVersion",
  36867: "DateTimeOriginal",
  36868: "DateTimeDigitized",
  37377: "ShutterSpeedValue",
  37378: "ApertureValue",
  37380: "ExposureBiasValue",
  37383: "MeteringMode",
  37385: "Flash",
  37386: "FocalLength",
  37500: "MakerNote",
  37510: "UserComment",
  40961: "ColorSpace",
  41986: "ExposureMode",
  41987: "WhiteBalance",
  41990: "SceneCaptureType",
  42035: "LensMake",
  42036: "LensModel",
};

const TYPE_SIZES = { 1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 6: 1, 7: 1, 8: 2, 9: 4, 10: 8, 11: 4, 12: 8 };

const latin1 = new TextDecoder("latin1");

export function inspectExif(bytes, contentType) {
  const tiff = locateTiff(bytes, contentType);
  const fields = tiff ? readIfd0(tiff.view, tiff.offset, tiff.little) : {};
  const fieldCount = Object.keys(fields).length;

  if (fieldCount === 0) {
    return {
      checked: true,
      detected: false,
      status: "absent",
      summary: "No EXIF metadata was found.",
      details: { field_count: 0 },
    };
  }

  return {
    checked: true,
    detected: true,
    status: "present",
    summary: `EXIF metadata is present with ${fieldCount} fields.`,
    details: { field_count: fieldCount, fields },
  };
}

function locateTiff(bytes, contentType) {
  const type = String(contentType || "").toLowerCase();
  if (type.includes("png") || isPng(bytes)) {
    return locateFromPng(bytes);
  }
  if (type.includes("webp") || isWebp(bytes)) {
    return locateFromWebp(bytes);
  }
  return locateFromJpeg(bytes);
}

function isPng(bytes) {
  return bytes.length > 8 && bytes[0] === 0x89 && bytes[1] === 0x50 && bytes[2] === 0x4e && bytes[3] === 0x47;
}

function isWebp(bytes) {
  return (
    bytes.length > 12 &&
    bytes[0] === 0x52 &&
    bytes[1] === 0x49 &&
    bytes[2] === 0x46 &&
    bytes[3] === 0x46 &&
    bytes[8] === 0x57 &&
    bytes[9] === 0x45 &&
    bytes[10] === 0x42 &&
    bytes[11] === 0x50
  );
}

function locateFromJpeg(bytes) {
  if (bytes.length < 4 || bytes[0] !== 0xff || bytes[1] !== 0xd8) {
    return null;
  }
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  let offset = 2;
  while (offset + 4 <= bytes.length) {
    if (view.getUint8(offset) !== 0xff) {
      offset += 1;
      continue;
    }
    const marker = view.getUint8(offset + 1);
    if (marker === 0xd9 || marker === 0xda) {
      break;
    }
    if (marker === 0xff) {
      offset += 1;
      continue;
    }
    const segLength = view.getUint16(offset + 2, false);
    if (segLength < 2) {
      break;
    }
    const dataStart = offset + 4;
    if (marker === 0xe1 && dataStart + 6 <= bytes.length) {
      const header = latin1.decode(bytes.subarray(dataStart, dataStart + 6));
      if (header === "Exif\u0000\u0000") {
        return tiffFrom(bytes, dataStart + 6);
      }
    }
    offset += 2 + segLength;
  }
  return null;
}

function locateFromPng(bytes) {
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  let offset = 8;
  while (offset + 8 <= bytes.length) {
    const length = view.getUint32(offset, false);
    const type = latin1.decode(bytes.subarray(offset + 4, offset + 8));
    const dataStart = offset + 8;
    if (type === "eXIf") {
      return tiffFrom(bytes, dataStart);
    }
    if (type === "IEND") {
      break;
    }
    offset = dataStart + length + 4;
  }
  return null;
}

function locateFromWebp(bytes) {
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  let offset = 12;
  while (offset + 8 <= bytes.length) {
    const fourcc = latin1.decode(bytes.subarray(offset, offset + 4));
    const size = view.getUint32(offset + 4, true);
    let dataStart = offset + 8;
    if (fourcc === "EXIF") {
      if (latin1.decode(bytes.subarray(dataStart, dataStart + 6)) === "Exif\u0000\u0000") {
        dataStart += 6;
      }
      return tiffFrom(bytes, dataStart);
    }
    offset = dataStart + size + (size % 2);
  }
  return null;
}

function tiffFrom(bytes, tiffStart) {
  if (tiffStart + 8 > bytes.length) {
    return null;
  }
  const byteOrder = latin1.decode(bytes.subarray(tiffStart, tiffStart + 2));
  const little = byteOrder === "II";
  if (!little && byteOrder !== "MM") {
    return null;
  }
  const view = new DataView(bytes.buffer, bytes.byteOffset + tiffStart, bytes.byteLength - tiffStart);
  const magic = view.getUint16(2, little);
  if (magic !== 42) {
    return null;
  }
  const ifdOffset = view.getUint32(4, little);
  return { view, offset: ifdOffset, little };
}

function readIfd0(view, ifdOffset, little) {
  const fields = {};
  if (ifdOffset + 2 > view.byteLength) {
    return fields;
  }
  const count = view.getUint16(ifdOffset, little);
  let entry = ifdOffset + 2;
  for (let i = 0; i < count; i += 1) {
    if (entry + 12 > view.byteLength) {
      break;
    }
    const tag = view.getUint16(entry, little);
    const type = view.getUint16(entry + 2, little);
    const valueCount = view.getUint32(entry + 4, little);
    const name = TIFF_TAG_NAMES[tag] || String(tag);
    const value = readValue(view, entry + 8, type, valueCount, little);
    if (value !== undefined) {
      fields[name] = formatValue(value).slice(0, 200);
    }
    entry += 12;
  }
  return fields;
}

function readValue(view, valueFieldOffset, type, valueCount, little) {
  const unitSize = TYPE_SIZES[type];
  if (!unitSize) {
    return undefined;
  }
  const totalBytes = unitSize * valueCount;
  let dataOffset = valueFieldOffset;
  if (totalBytes > 4) {
    dataOffset = view.getUint32(valueFieldOffset, little);
  }
  if (dataOffset + totalBytes > view.byteLength) {
    return undefined;
  }

  if (type === 2) {
    return readAscii(view, dataOffset, valueCount);
  }
  if (type === 7 || type === 1 || type === 6) {
    return { bytes: valueCount };
  }

  const values = [];
  for (let i = 0; i < valueCount; i += 1) {
    values.push(readNumeric(view, dataOffset + i * unitSize, type, little));
  }
  return values.length === 1 ? values[0] : values;
}

function readAscii(view, offset, count) {
  const chars = [];
  for (let i = 0; i < count; i += 1) {
    const code = view.getUint8(offset + i);
    if (code === 0) {
      break;
    }
    chars.push(code);
  }
  return latin1.decode(new Uint8Array(chars));
}

function readNumeric(view, offset, type, little) {
  switch (type) {
    case 3:
      return view.getUint16(offset, little);
    case 4:
      return view.getUint32(offset, little);
    case 8:
      return view.getInt16(offset, little);
    case 9:
      return view.getInt32(offset, little);
    case 11:
      return view.getFloat32(offset, little);
    case 12:
      return view.getFloat64(offset, little);
    case 5: {
      const num = view.getUint32(offset, little);
      const den = view.getUint32(offset + 4, little);
      return den === 0 ? 0 : num / den;
    }
    case 10: {
      const num = view.getInt32(offset, little);
      const den = view.getInt32(offset + 4, little);
      return den === 0 ? 0 : num / den;
    }
    default:
      return 0;
  }
}

function formatValue(value) {
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "number") {
    return String(value);
  }
  if (value && typeof value === "object" && "bytes" in value) {
    return `<${value.bytes} bytes>`;
  }
  if (Array.isArray(value)) {
    return `(${value.join(", ")})`;
  }
  return String(value);
}
