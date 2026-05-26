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


class InterpretationEvidence(BaseModel):
    key: Literal["gb45438", "ela", "c2pa", "exif"]
    title: str
    status_label: Literal["支持证据", "需留意", "未发现", "无法分析"]
    summary: str
    means: str
    does_not_mean: str
    details: dict = Field(default_factory=dict)


class ReportInterpretation(BaseModel):
    confidence_label: Literal["强", "较强", "中等", "有限"]
    conclusion: str
    evidence_chain: list[InterpretationEvidence]
    limits: list[str]


class AnalyzeResponse(BaseModel):
    status: Literal["success"] = "success"
    verdict: Verdict
    summary: str
    signals: ReportSignals
    interpretation: ReportInterpretation
    limitations: list[str]
    recommendation: str
    assets: ReportAssets = Field(default_factory=ReportAssets)
