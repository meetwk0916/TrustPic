import argparse
import json
from pathlib import Path

from PIL import Image

from app.services.ela import inspect_ela
from generate_sample_images import generate_samples


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect ELA metrics for generated and external samples.")
    parser.add_argument(
        "--sample-dir",
        default="/private/tmp/trustpic-samples",
        help="Directory containing samples to inspect.",
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate TrustPic smoke samples before calibration.",
    )
    parser.add_argument(
        "--json-output",
        help="Optional path to write JSON results.",
    )
    parser.add_argument(
        "--markdown-output",
        help="Optional path to write a Markdown table.",
    )
    args = parser.parse_args()

    sample_dir = Path(args.sample_dir)
    if args.generate:
        generate_samples(sample_dir)

    results = [inspect_sample(path) for path in sorted(iter_image_paths(sample_dir))]
    payload = {"sample_dir": str(sample_dir), "results": results}

    if args.json_output:
        Path(args.json_output).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.markdown_output:
        Path(args.markdown_output).write_text(render_markdown(results), encoding="utf-8")

    print(json.dumps(payload, indent=2))


def iter_image_paths(sample_dir: Path):
    for path in sample_dir.iterdir():
        if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
            yield path


def inspect_sample(path: Path) -> dict:
    image = Image.open(path)
    image.load()
    signal, _ = inspect_ela(image)
    return {
        "file": path.name,
        "status": signal.status,
        "detected": signal.detected,
        "mean_error": signal.details["mean_error"],
        "review_threshold": signal.details["review_threshold"],
        "jpeg_quality": signal.details["jpeg_quality"],
        "amplification": signal.details["amplification"],
    }


def render_markdown(results: list[dict]) -> str:
    lines = [
        "# ELA Calibration Snapshot",
        "",
        "| file | status | mean_error | review_threshold |",
        "|---|---:|---:|---:|",
    ]
    for item in results:
        lines.append(
            f"| `{item['file']}` | {item['status']} | {item['mean_error']} | {item['review_threshold']} |"
        )
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
