from pathlib import Path
from sys import argv

from PIL import Image, ImageDraw


def generate_samples(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    plain = Image.new("RGB", (320, 220), color=(116, 74, 146))
    plain_path = output_dir / "plain.png"
    plain.save(plain_path, format="PNG")

    marked_path = output_dir / "marked-aigc.png"
    marked_path.write_bytes(plain_path.read_bytes() + b'\n"AI_GENERATED"\n')

    edited = Image.new("RGB", (320, 220), color=(232, 235, 228))
    draw = ImageDraw.Draw(edited)
    draw.rectangle((36, 30, 284, 188), fill=(120, 40, 80))
    draw.ellipse((112, 54, 206, 148), fill=(245, 205, 72))
    edited_path = output_dir / "edited-compressed.jpg"
    edited.save(edited_path, format="JPEG", quality=62)

    return [plain_path, marked_path, edited_path]


def main() -> None:
    output_dir = Path(argv[1]) if len(argv) > 1 else Path("/private/tmp/trustpic-samples")
    generate_samples(output_dir)

    print(f"Wrote sample images to {output_dir}")


if __name__ == "__main__":
    main()
