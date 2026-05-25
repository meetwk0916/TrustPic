import argparse
from pathlib import Path
from shutil import copyfile

from generate_sample_images import generate_samples


FIXTURE_LAYOUT = {
    "gb45438-xmp.png": ("gb45438", "gb45438-xmp.png"),
    "metadata-stripped.jpg": ("metadata_stripped", "metadata-stripped.jpg"),
    "ela-review-compressed.jpg": ("ela_review", "ela-review-compressed.jpg"),
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare local TrustPic v0 fixtures for first-phase dataset audits.")
    parser.add_argument(
        "--output-dir",
        default="/private/tmp/trustpic-first-phase-fixtures/TrustPic-V0-Fixtures",
        help="Directory to write the local fixture dataset layout.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    source_dir = output_dir.parent / "_generated"
    sample_paths = {path.name: path for path in generate_samples(source_dir)}

    for sample_name, (label, filename) in FIXTURE_LAYOUT.items():
        target = output_dir / label / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        copyfile(sample_paths[sample_name], target)

    print(f"Wrote first-phase fixtures to {output_dir}")


if __name__ == "__main__":
    main()
