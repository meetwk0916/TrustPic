from pathlib import Path
from sys import argv

from PIL import Image, ImageDraw


def generate_samples(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    sample_paths = []

    plain = Image.new("RGB", (320, 220), color=(116, 74, 146))
    plain_path = output_dir / "plain.png"
    plain.save(plain_path, format="PNG")
    sample_paths.append(plain_path)

    marked_path = output_dir / "marked-aigc.png"
    marked_path.write_bytes(plain_path.read_bytes() + b'\n"AI_GENERATED"\n')
    sample_paths.append(marked_path)

    xmp_packet = b"""
<x:xmpmeta xmlns:x="adobe:ns:meta/">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description xmlns:AIGC="http://www.tc260.org.cn/ns/AIGC/1.0/">
      <AIGC:Label>AIGC</AIGC:Label>
      <AIGC:ContentProducer>TrustPic Sample Generator</AIGC:ContentProducer>
      <AIGC:ProduceID>trustpic-sample-produce-id</AIGC:ProduceID>
      <AIGC:ContentPropagator>TrustPic</AIGC:ContentPropagator>
      <AIGC:PropagateID>trustpic-sample-propagate-id</AIGC:PropagateID>
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>
"""
    gb_xmp_path = output_dir / "gb45438-xmp.png"
    gb_xmp_path.write_bytes(plain_path.read_bytes() + xmp_packet)
    sample_paths.append(gb_xmp_path)

    camera_exif = Image.new("RGB", (320, 220), color=(96, 132, 166))
    draw = ImageDraw.Draw(camera_exif)
    draw.rectangle((48, 42, 272, 178), fill=(235, 238, 231))
    draw.ellipse((118, 68, 202, 152), fill=(35, 95, 130))
    exif = Image.Exif()
    exif[271] = "TrustPic Camera"
    exif[272] = "V0 EXIF Sample"
    exif[305] = "TrustPic sample generator"
    exif_path = output_dir / "camera-exif.jpg"
    camera_exif.save(exif_path, format="JPEG", quality=92, exif=exif)
    sample_paths.append(exif_path)

    stripped_path = output_dir / "metadata-stripped.jpg"
    Image.open(exif_path).convert("RGB").save(stripped_path, format="JPEG", quality=92)
    sample_paths.append(stripped_path)

    edited = Image.new("RGB", (320, 220), color=(232, 235, 228))
    draw = ImageDraw.Draw(edited)
    draw.rectangle((36, 30, 284, 188), fill=(120, 40, 80))
    draw.ellipse((112, 54, 206, 148), fill=(245, 205, 72))
    edited_path = output_dir / "edited-compressed.jpg"
    edited.save(edited_path, format="JPEG", quality=62)
    sample_paths.append(edited_path)

    ela_review = Image.new("RGB", (320, 220), color=(128, 128, 128))
    draw = ImageDraw.Draw(ela_review)
    for x in range(112, 208, 2):
        color = (20, 20, 20) if x % 4 == 0 else (235, 235, 235)
        draw.rectangle((x, 58, x + 1, 154), fill=color)
    for y in range(58, 154, 4):
        draw.line((112, y, 207, y), fill=(230, 40, 40), width=1)
    ela_review_path = output_dir / "ela-review-compressed.jpg"
    ela_review.save(ela_review_path, format="JPEG", quality=35)
    sample_paths.append(ela_review_path)

    return sample_paths


def main() -> None:
    output_dir = Path(argv[1]) if len(argv) > 1 else Path("/private/tmp/trustpic-samples")
    generate_samples(output_dir)

    print(f"Wrote sample images to {output_dir}")


if __name__ == "__main__":
    main()
