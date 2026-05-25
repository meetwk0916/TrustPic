import json

import pytest

from scripts.audit_dataset_window import (
    build_auto_suite_config,
    discover_sources,
    load_remote_catalog_sources,
    normalize_name,
)


def _write_png(path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x89PNG\r\n\x1a\nwindow-test")


def test_discover_sources_finds_known_local_dataset_alias(tmp_path) -> None:
    dataset = tmp_path / "aigc-artifacts-raw"
    _write_png(dataset / "real" / "one.png")

    sources = discover_sources([tmp_path])

    assert sources[0]["name"] == "AIGC-Artifacts-Raw"
    assert sources[0]["mode"] == "local"
    assert sources[0]["path"] == str(dataset)
    assert "expectations" in sources[0]


def test_build_auto_suite_config_can_use_remote_only_catalog(tmp_path) -> None:
    catalog = tmp_path / "remote-catalog.json"
    catalog.write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "name": "Real-World-AIGC",
                        "mode": "hf",
                        "dataset": "org/real-world-aigc",
                        "split": "train",
                        "image_column": "image",
                        "label_column": "label",
                        "streaming": True,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    config = build_auto_suite_config(
        [tmp_path / "missing-local-root"],
        remote_catalog=catalog,
        remote_only=True,
        max_per_label=7,
        min_confidence_level="medium",
        min_confidence_score=0.6,
        require_completed_sources=1,
        min_alignment_rate=0.8,
    )

    assert config["sources"] == [
        {
            "name": "Real-World-AIGC",
            "mode": "hf",
            "dataset": "org/real-world-aigc",
            "metadata_policy": "metadata-preserving source files only",
            "split": "train",
            "image_column": "image",
            "label_column": "label",
            "streaming": True,
            "expectations": {
                "real": {"verdict": ["no_supported_signal_found", "review_recommended"]},
                "ai": {"verdict": ["supported_signal_detected", "review_recommended", "no_supported_signal_found"]},
            },
        }
    ]
    assert config["defaults"]["max_per_label"] == 7
    assert config["gate"]["require_completed_sources"] == 1


def test_load_remote_catalog_skips_disabled_sources(tmp_path) -> None:
    catalog = tmp_path / "remote-catalog.json"
    catalog.write_text(
        json.dumps(
            {
                "sources": [
                    {"name": "disabled", "mode": "hf", "enabled": False, "dataset": "org/disabled"},
                    {"name": "enabled", "mode": "hf", "dataset": "org/enabled"},
                ]
            }
        ),
        encoding="utf-8",
    )

    assert [source["name"] for source in load_remote_catalog_sources(catalog)] == ["enabled"]


def test_remote_catalog_rejects_non_hf_sources(tmp_path) -> None:
    catalog = tmp_path / "remote-catalog.json"
    catalog.write_text(json.dumps({"sources": [{"name": "bad", "mode": "local", "path": "/tmp/data"}]}), encoding="utf-8")

    with pytest.raises(SystemExit):
        load_remote_catalog_sources(catalog)


def test_normalize_name_ignores_case_and_separators() -> None:
    assert normalize_name("Real-World_AIGC") == "realworldaigc"
