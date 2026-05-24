from io import BytesIO

from PIL import Image

from argparse import Namespace

from scripts.audit_dataset_suite import (
    cli_gate_requested,
    combine_expectation_summaries,
    evaluate_gate,
    render_suite_markdown,
    run_suite,
)


def _write_png(path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (32, 32), color=(40, 120, 90))
    out = BytesIO()
    image.save(out, format="PNG")
    path.write_bytes(out.getvalue())


def test_run_suite_combines_multiple_local_sources(tmp_path) -> None:
    raw_source = tmp_path / "aigc-artifacts-raw"
    dnd_source = tmp_path / "dnd-dataset"
    _write_png(raw_source / "real" / "camera.png")
    _write_png(raw_source / "fake" / "generated.png")
    _write_png(dnd_source / "nature" / "photo.png")
    _write_png(dnd_source / "aigc" / "synthetic.png")

    payload = run_suite(
        {
            "suite": "trustpic-public-smoke",
            "defaults": {"max_per_label": 1},
            "sources": [
                {"name": "AIGC-Artifacts-Raw", "mode": "local", "path": str(raw_source)},
                {"name": "DND-Dataset", "mode": "local", "path": str(dnd_source)},
            ],
        }
    )

    assert payload["completed_source_count"] == 2
    assert payload["total_samples"] == 4
    assert payload["confidence"]["level"] in {"low", "medium", "high"}
    assert payload["gate"]["status"] == "passed"
    assert payload["combined_expectation_summary"]["configured"] is False
    assert set(payload["combined_summary"]["by_label"]) == {"aigc", "fake", "nature", "real"}
    assert {item["dataset_source"] for source in payload["sources"] for item in source["results"]} == {
        "AIGC-Artifacts-Raw",
        "DND-Dataset",
    }


def test_run_suite_can_skip_missing_allowed_source(tmp_path) -> None:
    payload = run_suite(
        {
            "suite": "trustpic-public-smoke",
            "sources": [
                {
                    "name": "missing-raw-source",
                    "mode": "local",
                    "path": str(tmp_path / "missing"),
                    "allow_missing": True,
                }
            ],
        }
    )

    assert payload["completed_source_count"] == 0
    assert payload["skipped_source_count"] == 1
    assert payload["sources"][0]["status"] == "skipped"
    assert payload["confidence"]["level"] == "insufficient"
    assert payload["gate"]["status"] == "passed"


def test_render_suite_markdown_includes_combined_confidence(tmp_path) -> None:
    raw_source = tmp_path / "real-world-aigc"
    _write_png(raw_source / "real" / "camera.png")
    _write_png(raw_source / "ai" / "generated.png")
    payload = run_suite(
        {
            "suite": "trustpic-public-smoke",
            "sources": [{"name": "Real-World-AIGC", "mode": "local", "path": str(raw_source)}],
        }
    )

    markdown = render_suite_markdown(payload)

    assert "# TrustPic Dataset Audit Suite" in markdown
    assert "Combined Confidence" in markdown
    assert "`Real-World-AIGC`" in markdown


def test_evaluate_gate_fails_when_confidence_or_source_count_is_low(tmp_path) -> None:
    raw_source = tmp_path / "real-world-aigc"
    _write_png(raw_source / "real" / "camera.png")
    payload = run_suite(
        {
            "suite": "trustpic-public-smoke",
            "sources": [{"name": "Real-World-AIGC", "mode": "local", "path": str(raw_source)}],
        }
    )

    gate = evaluate_gate(
        payload,
        min_confidence_level="high",
        min_confidence_score=0.9,
        require_completed_sources=3,
    )

    assert gate["status"] == "failed"
    assert len(gate["failures"]) == 3


def test_run_suite_applies_configured_gate(tmp_path) -> None:
    raw_source = tmp_path / "real-world-aigc"
    _write_png(raw_source / "real" / "camera.png")
    payload = run_suite(
        {
            "suite": "trustpic-public-smoke",
            "gate": {"min_confidence_level": "medium", "require_completed_sources": 2},
            "sources": [{"name": "Real-World-AIGC", "mode": "local", "path": str(raw_source)}],
        }
    )

    assert payload["gate"]["status"] == "failed"
    assert "Completed source count 1 is below required count 2." in payload["gate"]["failures"]


def test_cli_gate_requested_only_when_gate_args_are_present() -> None:
    assert cli_gate_requested(
        Namespace(
            min_confidence_level=None,
            min_confidence_score=None,
            require_completed_sources=None,
            min_alignment_rate=None,
        )
    ) is False
    assert cli_gate_requested(
        Namespace(
            min_confidence_level="medium",
            min_confidence_score=None,
            require_completed_sources=None,
            min_alignment_rate=None,
        )
    ) is True


def test_expectations_compute_alignment_rate(tmp_path) -> None:
    raw_source = tmp_path / "real-world-aigc"
    _write_png(raw_source / "real" / "camera.png")
    _write_png(raw_source / "ai" / "generated.png")
    payload = run_suite(
        {
            "suite": "trustpic-public-smoke",
            "gate": {"min_alignment_rate": 1.0},
            "sources": [
                {
                    "name": "Real-World-AIGC",
                    "mode": "local",
                    "path": str(raw_source),
                    "expectations": {
                        "real": {"verdict": ["no_supported_signal_found", "review_recommended"]},
                        "ai": {"verdict": ["no_supported_signal_found", "review_recommended"]},
                    },
                }
            ],
        }
    )

    assert payload["combined_expectation_summary"]["configured"] is True
    assert payload["combined_expectation_summary"]["checked"] == 2
    assert payload["combined_expectation_summary"]["alignment_rate"] == 1.0
    assert payload["gate"]["status"] == "passed"
    assert all(item["expectation"]["matched"] for item in payload["sources"][0]["results"])


def test_alignment_gate_fails_on_expectation_mismatch(tmp_path) -> None:
    raw_source = tmp_path / "real-world-aigc"
    _write_png(raw_source / "real" / "camera.png")
    payload = run_suite(
        {
            "suite": "trustpic-public-smoke",
            "gate": {"min_alignment_rate": 1.0},
            "sources": [
                {
                    "name": "Real-World-AIGC",
                    "mode": "local",
                    "path": str(raw_source),
                    "expectations": {"real": {"verdict": "supported_signal_detected"}},
                }
            ],
        }
    )

    assert payload["combined_expectation_summary"]["alignment_rate"] == 0.0
    assert payload["gate"]["status"] == "failed"
    assert "Combined alignment rate 0.0 is below required rate 1.0." in payload["gate"]["failures"]


def test_combine_expectation_summaries_marks_unconfigured_when_empty() -> None:
    assert combine_expectation_summaries([]) == {
        "configured": False,
        "configured_source_count": 0,
        "checked": 0,
        "matched": 0,
        "mismatched": 0,
        "alignment_rate": None,
        "mismatches": [],
    }
