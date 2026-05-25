import argparse
import json
from pathlib import Path

try:
    from audit_dataset_suite import render_suite_markdown, run_suite
except ImportError:
    from scripts.audit_dataset_suite import render_suite_markdown, run_suite


DEFAULT_ROOTS = ["/private/tmp/trustpic-datasets"]

KNOWN_DATASETS = {
    "AIGC-Artifacts-Raw": {
        "aliases": ["AIGC-Artifacts-Raw", "aigc-artifacts-raw", "AIGC_Artifacts_Raw"],
        "metadata_policy": "raw branch only; do not use WebP classification mirror",
        "expectations": {
            "real": {"verdict": ["no_supported_signal_found", "review_recommended"]},
            "fake": {"verdict": ["supported_signal_detected", "review_recommended", "no_supported_signal_found"]},
        },
    },
    "DND-Dataset": {
        "aliases": ["DND-Dataset", "dnd-dataset", "DND"],
        "metadata_policy": "metadata-preserving source files only",
        "expectations": {
            "nature": {"verdict": ["no_supported_signal_found", "review_recommended"]},
            "aigc": {"verdict": ["supported_signal_detected", "review_recommended", "no_supported_signal_found"]},
        },
    },
    "Real-World-AIGC": {
        "aliases": ["Real-World-AIGC", "real-world-aigc", "RealWorldAIGC"],
        "metadata_policy": "metadata-preserving source files only",
        "expectations": {
            "real": {"verdict": ["no_supported_signal_found", "review_recommended"]},
            "ai": {"verdict": ["supported_signal_detected", "review_recommended", "no_supported_signal_found"]},
        },
    },
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Auto-discover TrustPic dataset sources and run the validation window."
    )
    parser.add_argument(
        "--root",
        action="append",
        dest="roots",
        help="Directory to scan for known raw dataset folders. Can be repeated.",
    )
    parser.add_argument("--max-per-label", type=int, default=25, help="Maximum samples per inferred label.")
    parser.add_argument(
        "--remote-catalog",
        help="Optional JSON catalog of remote/Hugging Face dataset sources to extract from directly.",
    )
    parser.add_argument(
        "--remote-only",
        action="store_true",
        help="Use only remote catalog sources and skip local directory discovery.",
    )
    parser.add_argument("--min-confidence-level", default="medium", choices=["insufficient", "low", "medium", "high"])
    parser.add_argument("--min-confidence-score", type=float, default=0.6)
    parser.add_argument("--require-completed-sources", type=int, default=3)
    parser.add_argument("--min-alignment-rate", type=float, default=0.8)
    parser.add_argument("--config-output", help="Optional path to write the auto-generated suite config.")
    parser.add_argument("--json-output", help="Optional JSON report output path.")
    parser.add_argument("--markdown-output", help="Optional Markdown report output path.")
    args = parser.parse_args()

    config = build_auto_suite_config(
        [Path(root) for root in (args.roots or DEFAULT_ROOTS)],
        remote_catalog=Path(args.remote_catalog) if args.remote_catalog else None,
        remote_only=args.remote_only,
        max_per_label=args.max_per_label,
        min_confidence_level=args.min_confidence_level,
        min_confidence_score=args.min_confidence_score,
        require_completed_sources=args.require_completed_sources,
        min_alignment_rate=args.min_alignment_rate,
    )

    if args.config_output:
        Path(args.config_output).write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

    payload = run_suite(config)

    if args.json_output:
        Path(args.json_output).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.markdown_output:
        Path(args.markdown_output).write_text(render_suite_markdown(payload), encoding="utf-8")

    print(json.dumps(payload, indent=2))
    if payload["gate"]["status"] == "failed":
        raise SystemExit(1)


def build_auto_suite_config(
    roots: list[Path],
    *,
    remote_catalog: Path | None = None,
    remote_only: bool = False,
    max_per_label: int,
    min_confidence_level: str,
    min_confidence_score: float,
    require_completed_sources: int,
    min_alignment_rate: float,
) -> dict:
    sources = []
    if not remote_only:
        sources.extend(discover_sources(roots))
    if remote_catalog:
        sources.extend(load_remote_catalog_sources(remote_catalog))

    if not sources:
        raise SystemExit(
            "No known TrustPic dataset sources found. "
            "Place raw datasets under /private/tmp/trustpic-datasets, pass --root, "
            "or provide --remote-catalog."
        )

    return {
        "suite": "trustpic-auto-dataset-window",
        "metadata_policy": "auto-discovered raw/original local and remote dataset sources",
        "defaults": {
            "max_per_label": max_per_label,
            "label_from": "parent",
            "include_webp": False,
            "allow_missing": False,
        },
        "gate": {
            "min_confidence_level": min_confidence_level,
            "min_confidence_score": min_confidence_score,
            "require_completed_sources": require_completed_sources,
            "min_alignment_rate": min_alignment_rate,
        },
        "sources": sources,
    }


def load_remote_catalog_sources(path: Path) -> list[dict]:
    try:
        catalog = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid remote catalog JSON {path}: {exc}") from exc

    raw_sources = catalog.get("sources")
    if not isinstance(raw_sources, list):
        raise SystemExit("Remote catalog must contain a 'sources' list.")

    sources = []
    for source in raw_sources:
        normalized = normalize_remote_source(source)
        if normalized:
            sources.append(normalized)
    return sources


def normalize_remote_source(source: dict) -> dict | None:
    if source.get("enabled", True) is False:
        return None
    mode = source.get("mode", "hf")
    if mode != "hf":
        raise SystemExit(f"Remote catalog source '{source.get('name', 'unnamed-source')}' must use mode 'hf'.")
    if not source.get("dataset"):
        raise SystemExit(f"Remote catalog source '{source.get('name', 'unnamed-source')}' is missing dataset.")

    name = source.get("name") or source["dataset"]
    preset = KNOWN_DATASETS.get(name, {})
    normalized = {
        "name": name,
        "mode": "hf",
        "dataset": source["dataset"],
        "metadata_policy": source.get("metadata_policy", preset.get("metadata_policy", "remote raw bytes via HF dataset")),
        "split": source.get("split", "train"),
        "image_column": source.get("image_column", "image"),
        "label_column": source.get("label_column", "label"),
        "source_column": source.get("source_column"),
        "streaming": bool(source.get("streaming", True)),
        "max_per_label": source.get("max_per_label"),
        "max_samples": source.get("max_samples"),
        "expectations": source.get("expectations", preset.get("expectations", {})),
    }
    if source.get("config"):
        normalized["config"] = source["config"]
    return {key: value for key, value in normalized.items() if value is not None}


def discover_sources(roots: list[Path]) -> list[dict]:
    discovered = []
    seen_names = set()
    candidates = list_candidate_dirs(roots)
    for canonical_name, metadata in KNOWN_DATASETS.items():
        for candidate in candidates:
            if candidate_matches(candidate, metadata["aliases"]) and contains_supported_images(candidate):
                if canonical_name in seen_names:
                    continue
                discovered.append(
                    {
                        "name": canonical_name,
                        "mode": "local",
                        "path": str(candidate),
                        "metadata_policy": metadata["metadata_policy"],
                        "expectations": metadata["expectations"],
                    }
                )
                seen_names.add(canonical_name)
                break
    return discovered


def list_candidate_dirs(roots: list[Path]) -> list[Path]:
    candidates = []
    for root in roots:
        if not root.exists() or not root.is_dir():
            continue
        candidates.append(root)
        candidates.extend(path for path in sorted(root.iterdir()) if path.is_dir())
    return candidates


def candidate_matches(path: Path, aliases: list[str]) -> bool:
    normalized_name = normalize_name(path.name)
    return any(normalized_name == normalize_name(alias) for alias in aliases)


def normalize_name(value: str) -> str:
    return "".join(character.lower() for character in value if character.isalnum())


def contains_supported_images(path: Path) -> bool:
    for candidate in path.rglob("*"):
        if candidate.is_file() and candidate.suffix.lower() in {".jpg", ".jpeg", ".png"}:
            return True
    return False


if __name__ == "__main__":
    main()
