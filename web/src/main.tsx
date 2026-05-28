import React, { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

type Verdict =
  | "supported_signal_detected"
  | "review_recommended"
  | "no_supported_signal_found"
  | "unsupported";

type EvidenceSignal = {
  checked: boolean;
  detected: boolean;
  status: string;
  summary: string;
  details: Record<string, unknown>;
};

type InterpretationEvidence = {
  key: "gb45438" | "ela" | "c2pa" | "exif";
  title: string;
  status_label: string;
  summary: string;
  means: string;
  does_not_mean: string;
  details: Record<string, unknown>;
};

type AnalyzeResponse = {
  status: "success";
  verdict: Verdict;
  summary: string;
  signals: {
    c2pa: EvidenceSignal;
    gb45438: EvidenceSignal;
    exif: EvidenceSignal;
    ela: EvidenceSignal;
  };
  interpretation: {
    confidence_label: string;
    conclusion: string;
    evidence_chain: InterpretationEvidence[];
    limits: string[];
  };
  limitations: string[];
  recommendation: string;
  assets: {
    ela_heatmap_data_url: string | null;
  };
};

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

type Theme = "light" | "dark";
type Locale = "zh-CN" | "en-US";

const UI_COPY: Record<Locale, Record<string, string>> = {
  "zh-CN": {
    subtitle: "单图证据报告",
    themeAria: "切换明暗模式",
    lightTheme: "亮色",
    darkTheme: "暗色",
    localeAria: "切换语言",
    chooseFile: "选择 JPG、PNG 或 WebP",
    analyze: "分析",
    analyzing: "分析中",
    selectFirst: "请先选择一张图片。",
    analysisFailed: "分析失败。",
    noImage: "未选择图片",
    reportEmpty: "报告会显示在这里",
    file: "文件",
    type: "类型",
    size: "大小",
    unknown: "未知",
    confidence: "置信度",
    conclusion: "结论",
    aiEvidence: "AI 相关证据",
    coreEvidence: "核心证据",
    localDifference: "局部差异分析",
    heatmap: "局部差异热图",
    heatmapAlt: "ELA 热图",
    expand: "展开解释",
    means: "能说明什么",
    doesNotMean: "不能说明什么",
    technicalDetails: "技术细节",
    reportNotes: "报告怎么读",
  },
  "en-US": {
    subtitle: "Single-image evidence report",
    themeAria: "Toggle dark mode",
    lightTheme: "Light",
    darkTheme: "Dark",
    localeAria: "Switch language",
    chooseFile: "Choose JPG, PNG, or WebP",
    analyze: "Analyze",
    analyzing: "Analyzing",
    selectFirst: "Select an image before running analysis.",
    analysisFailed: "Analysis failed.",
    noImage: "No image selected",
    reportEmpty: "Report will appear here",
    file: "File",
    type: "Type",
    size: "Size",
    unknown: "unknown",
    confidence: "Confidence",
    conclusion: "Conclusion",
    aiEvidence: "AI-related evidence",
    coreEvidence: "Core evidence",
    localDifference: "Local difference analysis",
    heatmap: "Local difference heatmap",
    heatmapAlt: "ELA heatmap",
    expand: "Expand explanation",
    means: "What it can show",
    doesNotMean: "What it cannot show",
    technicalDetails: "Technical details",
    reportNotes: "How to read this report",
  },
};

function preferredTheme(): Theme {
  if (typeof window === "undefined") return "light";
  const savedTheme = window.localStorage.getItem("trustpic-theme");
  if (savedTheme === "light" || savedTheme === "dark") return savedTheme;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function preferredLocale(): Locale {
  if (typeof window === "undefined") return defaultLocale();
  const savedLocale = window.localStorage.getItem("trustpic-locale");
  if (savedLocale === "zh-CN" || savedLocale === "en-US") return savedLocale;
  return defaultLocale();
}

function defaultLocale(): Locale {
  return import.meta.env.VITE_DEFAULT_LOCALE === "en-US" ? "en-US" : "zh-CN";
}

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [report, setReport] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [theme, setTheme] = useState<Theme>(preferredTheme);
  const [locale, setLocale] = useState<Locale>(preferredLocale);
  const copy = UI_COPY[locale];

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem("trustpic-theme", theme);
  }, [theme]);

  useEffect(() => {
    document.documentElement.lang = locale === "en-US" ? "en" : "zh-CN";
    window.localStorage.setItem("trustpic-locale", locale);
  }, [locale]);

  const coreEvidence = report?.interpretation.evidence_chain.filter((item) => item.key !== "ela") ?? [];
  const localDifference = report?.interpretation.evidence_chain.find((item) => item.key === "ela") ?? null;
  const aiAlert = report ? aiStrongAlert(report.interpretation.evidence_chain) : null;

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0] ?? null;
    setFile(selected);
    setReport(null);
    setError(null);

    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(selected ? URL.createObjectURL(selected) : null);
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!file) {
      setError(copy.selectFirst);
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(analyzeEndpoint(locale), {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new Error(payload?.detail ?? `Request failed with ${response.status}`);
      }

      setReport((await response.json()) as AnalyzeResponse);
    } catch (err) {
      setReport(null);
      setError(err instanceof Error ? err.message : copy.analysisFailed);
    } finally {
      setLoading(false);
    }
  }

  function toggleLocale() {
    setLocale((current) => (current === "en-US" ? "zh-CN" : "en-US"));
    setReport(null);
    setError(null);
  }

  return (
    <main className="app-shell">
      <section className="workspace">
        <header className="topbar">
          <div>
            <h1>TrustPic</h1>
            <p>{copy.subtitle}</p>
          </div>
          <div className="topbar-actions">
            <button className="theme-toggle" type="button" aria-label={copy.localeAria} onClick={toggleLocale}>
              {locale === "en-US" ? "中文" : "English"}
            </button>
            <button
              className="theme-toggle"
              type="button"
              aria-label={copy.themeAria}
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            >
              {theme === "dark" ? copy.lightTheme : copy.darkTheme}
            </button>
            <span className="status-pill">v0</span>
          </div>
        </header>

        <form className="upload-panel" onSubmit={handleSubmit}>
          <label className="file-drop">
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={handleFileChange}
            />
            <span>{file ? file.name : copy.chooseFile}</span>
          </label>
          <button type="submit" disabled={loading || !file}>
            {loading ? copy.analyzing : copy.analyze}
          </button>
        </form>

        {error && <div className="notice error">{error}</div>}

        <section className="results-grid">
          <div className="image-pane">
            {previewUrl ? (
              <div className="preview-stack">
                <img src={previewUrl} alt="Selected upload preview" />
                {file && (
                  <dl className="file-meta">
                    <div>
                      <dt>{copy.file}</dt>
                      <dd>{file.name}</dd>
                    </div>
                    <div>
                      <dt>{copy.type}</dt>
                      <dd>{file.type || copy.unknown}</dd>
                    </div>
                    <div>
                      <dt>{copy.size}</dt>
                      <dd>{formatBytes(file.size)}</dd>
                    </div>
                  </dl>
                )}
              </div>
            ) : (
              <div className="empty-state">{copy.noImage}</div>
            )}
          </div>

          <div className="report-pane">
            {report ? (
              <>
                <section className="interpretation">
                  <div className="confidence-card">
                    <span>{copy.confidence}</span>
                    <strong>{report.interpretation.confidence_label}</strong>
                  </div>
                  <div className="conclusion-card">
                    <h2>{copy.conclusion}</h2>
                    <p>{report.interpretation.conclusion}</p>
                  </div>
                </section>

                {aiAlert && <AiAlert evidence={aiAlert} copy={copy} />}

                <EvidenceChain evidence={coreEvidence} copy={copy} />

                {localDifference && (
                  <LocalDifferenceSection
                    evidence={localDifference}
                    heatmapUrl={report.assets.ela_heatmap_data_url}
                    copy={copy}
                  />
                )}

                <ReportNotes limits={report.interpretation.limits} copy={copy} />
              </>
            ) : (
              <div className="empty-state">{copy.reportEmpty}</div>
            )}
          </div>
        </section>
      </section>
    </main>
  );
}

function AiAlert({ evidence, copy }: { evidence: InterpretationEvidence; copy: Record<string, string> }) {
  return (
    <section className="ai-alert">
      <div>
        <span>{copy.aiEvidence}</span>
        <strong>{evidence.summary}</strong>
      </div>
      <p>{evidence.means}</p>
    </section>
  );
}

function EvidenceChain({
  evidence,
  copy,
}: {
  evidence: InterpretationEvidence[];
  copy: Record<string, string>;
}) {
  return (
    <section className="evidence-chain">
      <h2>{copy.coreEvidence}</h2>
      <div className="evidence-list">
        {evidence.map((item) => (
          <EvidenceArticle item={item} key={item.key} copy={copy} />
        ))}
      </div>
    </section>
  );
}

function LocalDifferenceSection({
  evidence,
  heatmapUrl,
  copy,
}: {
  evidence: InterpretationEvidence;
  heatmapUrl: string | null;
  copy: Record<string, string>;
}) {
  return (
    <section className="local-difference-section">
      <h2>{copy.localDifference}</h2>
      <EvidenceArticle item={evidence} copy={copy} />
      {heatmapUrl && (
        <div className="heatmap">
          <h3>{copy.heatmap}</h3>
          <img src={heatmapUrl} alt={copy.heatmapAlt} />
        </div>
      )}
    </section>
  );
}

function EvidenceArticle({ item, copy }: { item: InterpretationEvidence; copy: Record<string, string> }) {
  return (
    <article className={`evidence-card evidence-${item.key}`}>
      <header>
        <div>
          <h3>{item.title}</h3>
          <p>{item.summary}</p>
        </div>
        <span className={`evidence-status ${statusClass(item.status_label)} signal-${item.key}`}>
          {item.status_label}
        </span>
      </header>
      <details className="evidence-details">
        <summary>{copy.expand}</summary>
        <div className="explain-grid">
          <div>
            <h4>{copy.means}</h4>
            <p>{item.means}</p>
          </div>
          <div>
            <h4>{copy.doesNotMean}</h4>
            <p>{item.does_not_mean}</p>
          </div>
        </div>
        {Object.keys(item.details).length > 0 && (
          <details className="technical-details">
            <summary>{copy.technicalDetails}</summary>
            <pre>{JSON.stringify(item.details, null, 2)}</pre>
          </details>
        )}
      </details>
    </article>
  );
}

function ReportNotes({ limits, copy }: { limits: string[]; copy: Record<string, string> }) {
  return (
    <section className="report-notes">
      <h2>{copy.reportNotes}</h2>
      <ul>
        {limits.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

function statusClass(status: InterpretationEvidence["status_label"]) {
  if (status === "支持证据" || status === "Supporting evidence") return "status-support";
  if (status === "需留意" || status === "Needs attention") return "status-warning";
  if (status === "无法分析" || status === "Not analyzed") return "status-unavailable";
  return "status-neutral";
}

function aiStrongAlert(evidence: InterpretationEvidence[]) {
  const aiMarker = evidence.find((item) => item.key === "gb45438" && isSupportingEvidence(item.status_label));
  if (aiMarker) return aiMarker;

  const sourceRecord = evidence.find((item) => item.key === "c2pa");
  if (!sourceRecord) return null;

  const details = sourceRecord.details;
  if (details.ai_related === true) return sourceRecord;
  const text = [
    sourceRecord.summary,
    sourceRecord.means,
    details.signature_issuer,
    details.signature_common_name,
    details.claim_generator,
    details.title,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  const terms = ["openai", "dall-e", "dalle", "gemini", "notebooklm", "imagen", "synthid", "nano banana"];
  return terms.some((term) => text.includes(term)) ? sourceRecord : null;
}

function isSupportingEvidence(status: string) {
  return status === "支持证据" || status === "Supporting evidence";
}

function analyzeEndpoint(locale: Locale) {
  const base = API_BASE.endsWith("/") ? API_BASE.slice(0, -1) : API_BASE;
  return `${base}/api/v1/analyze?locale=${encodeURIComponent(locale)}`;
}

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
