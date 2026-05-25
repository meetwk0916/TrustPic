from io import BytesIO

from PIL import Image

from scripts.audit_public_dataset import (
    audit_samples,
    guess_content_type,
    iter_local_samples,
    normalize_hf_value,
    normalize_hf_rows_value,
    normalize_image_content_type,
    render_markdown,
    samples_from_hf_rows_payload,
    sample_from_hf_row,
    sample_from_url_entry,
)


def _write_png(path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (32, 32), color=(20, 80, 140))
    out = BytesIO()
    image.save(out, format="PNG")
    path.write_bytes(out.getvalue())


def test_iter_local_samples_infers_labels_and_skips_webp_by_default(tmp_path) -> None:
    _write_png(tmp_path / "real" / "camera.png")
    _write_png(tmp_path / "fake" / "generated.png")
    (tmp_path / "fake" / "compressed.webp").write_bytes(b"webp")

    samples = iter_local_samples(tmp_path, max_samples=None, max_per_label=None)

    assert [sample.label for sample in samples] == ["fake", "real"]
    assert [sample.relative_path for sample in samples] == ["fake/generated.png", "real/camera.png"]
    assert all(sample.file_name != "compressed.webp" for sample in samples)


def test_iter_local_samples_can_cap_per_label(tmp_path) -> None:
    _write_png(tmp_path / "real" / "one.png")
    _write_png(tmp_path / "real" / "two.png")
    _write_png(tmp_path / "fake" / "one.png")

    samples = iter_local_samples(tmp_path, max_samples=None, max_per_label=1)

    assert [sample.relative_path for sample in samples] == ["fake/one.png", "real/one.png"]


def test_audit_samples_groups_results_by_label_and_source(tmp_path) -> None:
    _write_png(tmp_path / "real" / "camera.png")
    _write_png(tmp_path / "fake" / "generated.png")
    samples = iter_local_samples(tmp_path, max_samples=None, max_per_label=None)

    payload = audit_samples(samples, dataset=str(tmp_path), mode="local")

    assert payload["total"] == 2
    assert set(payload["summary"]["by_label"]) == {"fake", "real"}
    assert payload["summary"]["by_label"]["fake"]["count"] == 1
    assert payload["summary"]["by_label"]["real"]["count"] == 1
    assert len(payload["results"]) == 2
    assert {item["status_code"] for item in payload["results"]} == {200}


def test_render_markdown_includes_label_summary(tmp_path) -> None:
    _write_png(tmp_path / "real" / "camera.png")
    samples = iter_local_samples(tmp_path, max_samples=None, max_per_label=None)
    payload = audit_samples(samples, dataset=str(tmp_path), mode="local")

    markdown = render_markdown(payload)

    assert "# TrustPic Public Dataset Audit" in markdown
    assert "## Label Summary" in markdown
    assert "`real`" in markdown


def test_hf_raw_bytes_sample_infers_content_type_without_extension() -> None:
    image = Image.new("RGB", (16, 16), color=(200, 40, 40))
    out = BytesIO()
    image.save(out, format="PNG")

    sample = sample_from_hf_row(
        {"bytes": out.getvalue(), "path": None},
        sample_id="0",
        label="fake",
        source="raw-dataset",
    )

    assert sample.file_name == "hf-0.image"
    assert sample.content_type == "image/png"
    assert guess_content_type(sample.file_name, sample.image_bytes) == "image/png"


def test_normalize_hf_value_uses_class_label_names() -> None:
    class FakeClassLabel:
        def int2str(self, value: int) -> str:
            return ["real", "fake"][value]

    assert normalize_hf_value({"label": 1}, "label", {"label": FakeClassLabel()}) == "fake"
    assert normalize_hf_value({"label": "real"}, "label", {}) == "real"


def test_hf_rows_payload_downloads_image_and_uses_class_label_names() -> None:
    image = Image.new("RGB", (16, 16), color=(30, 90, 150))
    out = BytesIO()
    image.save(out, format="JPEG")

    class FakeResponse:
        headers = {"content-type": "image/jpeg"}
        content = out.getvalue()

        def raise_for_status(self) -> None:
            pass

    class FakeClient:
        def get(self, url):
            assert url == "https://example.test/image.jpg"
            return FakeResponse()

    payload = {
        "features": [
            {"name": "label", "type": {"names": ["real", "fake"], "_type": "ClassLabel"}},
            {"name": "generator", "type": {"names": ["Real", "ADM"], "_type": "ClassLabel"}},
        ],
        "rows": [
            {
                "row_idx": 7,
                "row": {
                    "image": {"src": "https://example.test/image.jpg"},
                    "label": 1,
                    "generator": 1,
                },
            }
        ],
    }

    samples = samples_from_hf_rows_payload(
        payload,
        client=FakeClient(),
        image_column="image",
        label_column="label",
        source_column="generator",
        default_label=None,
        default_source=None,
        counters={},
        max_per_label=None,
    )

    assert len(samples) == 1
    assert samples[0].sample_id == "7"
    assert samples[0].file_name == "image.jpg"
    assert samples[0].label == "fake"
    assert samples[0].source == "ADM"
    assert samples[0].content_type == "image/jpeg"


def test_normalize_hf_rows_value_handles_class_label_json() -> None:
    features = {"label": {"names": ["real", "fake"], "_type": "ClassLabel"}}

    assert normalize_hf_rows_value({"label": 0}, "label", features) == "real"
    assert normalize_hf_rows_value({"label": "fake"}, "label", features) == "fake"


def test_normalize_image_content_type_uses_file_signature_for_octet_stream() -> None:
    assert normalize_image_content_type("binary/octet-stream", "image.jpg", b"\xff\xd8\xff\xe0") == "image/jpeg"
    assert normalize_image_content_type("image/png; charset=utf-8", "image.png", b"") == "image/png"


def test_hf_rows_payload_can_use_default_label_and_source() -> None:
    image = Image.new("RGB", (16, 16), color=(30, 90, 150))
    out = BytesIO()
    image.save(out, format="JPEG")

    class FakeResponse:
        headers = {"content-type": "binary/octet-stream"}
        content = out.getvalue()

        def raise_for_status(self) -> None:
            pass

    class FakeClient:
        def get(self, url):
            return FakeResponse()

    payload = {"features": [{"name": "image", "type": {"_type": "Image"}}], "rows": [{"row_idx": 1, "row": {"image": {"src": "https://example.test/image"}}}]}
    samples = samples_from_hf_rows_payload(
        payload,
        client=FakeClient(),
        image_column="image",
        label_column=None,
        source_column=None,
        default_label="exif_photo",
        default_source="DataSeeds DSD",
        counters={},
        max_per_label=None,
    )

    assert samples[0].label == "exif_photo"
    assert samples[0].source == "DataSeeds DSD"
    assert samples[0].content_type == "image/jpeg"


def test_sample_from_url_entry_downloads_bytes_and_metadata() -> None:
    class FakeResponse:
        headers = {"content-type": "binary/octet-stream"}
        content = b"\xff\xd8\xff\xe0url-test"

        def raise_for_status(self) -> None:
            pass

    class FakeClient:
        def get(self, url):
            assert url == "https://example.test/C.jpg"
            return FakeResponse()

    sample = sample_from_url_entry(
        {
            "url": "https://example.test/C.jpg",
            "file_name": "C.jpg",
            "label": "c2pa_positive",
            "source": "contentauth/c2pa-attacks",
        },
        client=FakeClient(),
        index=0,
    )

    assert sample.sample_id == "C.jpg"
    assert sample.file_name == "C.jpg"
    assert sample.label == "c2pa_positive"
    assert sample.source == "contentauth/c2pa-attacks"
    assert sample.content_type == "image/jpeg"
