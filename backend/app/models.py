from typing import Literal

from pydantic import BaseModel, Field


Verdict = Literal[
    "supported_signal_detected",
    "review_recommended",
    "no_supported_signal_found",
    "unsupported",
]


class EvidenceSignal(BaseModel):
    checked: bool = True
    detected: bool = False
    status: str
    summary: str
    details: dict = Field(default_factory=dict)


class ReportSignals(BaseModel):
    c2pa: EvidenceSignal
    gb45438: EvidenceSignal
    exif: EvidenceSignal
    ela: EvidenceSignal


class ReportAssets(BaseModel):
    ela_heatmap_data_url: str | None = None


class AnalyzeResponse(BaseModel):
    status: Literal["success"] = "success"
    verdict: Verdict
    summary: str
    signals: ReportSignals
    limitations: list[str]
    recommendation: str
    assets: ReportAssets = Field(default_factory=ReportAssets)

