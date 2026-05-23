import json
import sys
from types import SimpleNamespace

from app.services.c2pa_signal import inspect_c2pa


class FakeReader:
    def __init__(self, content_type, image_stream) -> None:
        self.content_type = content_type
        self.image_stream = image_stream

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def json(self) -> str:
        return json.dumps(
            {
                "active_manifest": "test:manifest",
                "manifests": {
                    "test:manifest": {
                        "claim_generator": "make_test_images/0.12.0 c2pa-rs/0.12.0",
                        "title": "C.jpg",
                        "format": "image/jpeg",
                        "assertions": [{"label": "c2pa.actions.v2"}],
                        "signature_info": {
                            "issuer": "C2PA Test Signing Cert",
                            "common_name": "C2PA Signer",
                            "time": "2022-08-19T19:03:41+00:00",
                        },
                        "claim_version": 1,
                    }
                },
                "validation_state": "Valid",
                "validation_status": [{"code": "signingCredential.untrusted"}],
            }
        )


def test_c2pa_manifest_presence_is_detected_without_ai_false_positive(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "c2pa", SimpleNamespace(Reader=FakeReader))

    signal = inspect_c2pa(b"fake jpeg bytes", "image/jpeg")

    assert signal.detected is True
    assert signal.status == "detected"
    assert signal.details["ai_related"] is False
    assert signal.details["validation_state"] == "Valid"
    assert signal.details["validation_status"] == ["signingCredential.untrusted"]
