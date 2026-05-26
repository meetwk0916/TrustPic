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
  status_label: "支持证据" | "需留意" | "未发现" | "无法分析";
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
    confidence_label: "强" | "较强" | "中等" | "有限";
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

function preferredTheme(): Theme {
  if (typeof window === "undefined") return "light";
  const savedTheme = window.localStorage.getItem("trustpic-theme");
  if (savedTheme === "light" || savedTheme === "dark") return savedTheme;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [report, setReport] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [theme, setTheme] = useState<Theme>(preferredTheme);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem("trustpic-theme", theme);
  }, [theme]);

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
      setError("Select an image before running analysis.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/api/v1/analyze`, {
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
      setError(err instanceof Error ? err.message : "Analysis failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="workspace">
        <header className="topbar">
          <div>
            <h1>TrustPic</h1>
            <p>Single-image evidence report</p>
          </div>
          <div className="topbar-actions">
            <button
              className="theme-toggle"
              type="button"
              aria-label="切换明暗模式"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            >
              {theme === "dark" ? "亮色" : "暗色"}
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
            <span>{file ? file.name : "Choose JPG, PNG, or WebP"}</span>
          </label>
          <button type="submit" disabled={loading || !file}>
            {loading ? "Analyzing" : "Analyze"}
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
                      <dt>File</dt>
                      <dd>{file.name}</dd>
                    </div>
                    <div>
                      <dt>Type</dt>
                      <dd>{file.type || "unknown"}</dd>
                    </div>
                    <div>
                      <dt>Size</dt>
                      <dd>{formatBytes(file.size)}</dd>
                    </div>
                  </dl>
                )}
              </div>
            ) : (
              <div className="empty-state">No image selected</div>
            )}
          </div>

          <div className="report-pane">
            {report ? (
              <>
                <section className="interpretation">
                  <div className="confidence-card">
                    <span>置信度</span>
                    <strong>{report.interpretation.confidence_label}</strong>
                  </div>
                  <div className="conclusion-card">
                    <h2>结论</h2>
                    <p>{report.interpretation.conclusion}</p>
                  </div>
                </section>

                {aiAlert && <AiAlert evidence={aiAlert} />}

                <EvidenceChain evidence={coreEvidence} />

                {localDifference && (
                  <LocalDifferenceSection
                    evidence={localDifference}
                    heatmapUrl={report.assets.ela_heatmap_data_url}
                  />
                )}

                <ReportNotes limits={report.interpretation.limits} />
              </>
            ) : (
              <div className="empty-state">Report will appear here</div>
            )}
          </div>
        </section>
      </section>
    </main>
  );
}

function AiAlert({ evidence }: { evidence: InterpretationEvidence }) {
  return (
    <section className="ai-alert">
      <div>
        <span>AI 相关证据</span>
        <strong>{evidence.summary}</strong>
      </div>
      <p>{evidence.means}</p>
    </section>
  );
}

function EvidenceChain({ evidence }: { evidence: InterpretationEvidence[] }) {
  return (
    <section className="evidence-chain">
      <h2>核心证据</h2>
      <div className="evidence-list">
        {evidence.map((item) => (
          <EvidenceArticle item={item} key={item.key} />
        ))}
      </div>
    </section>
  );
}

function LocalDifferenceSection({
  evidence,
  heatmapUrl,
}: {
  evidence: InterpretationEvidence;
  heatmapUrl: string | null;
}) {
  return (
    <section className="local-difference-section">
      <h2>局部差异分析</h2>
      <EvidenceArticle item={evidence} />
      {heatmapUrl && (
        <div className="heatmap">
          <h3>局部差异热图</h3>
          <img src={heatmapUrl} alt="ELA heatmap" />
        </div>
      )}
    </section>
  );
}

function EvidenceArticle({ item }: { item: InterpretationEvidence }) {
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
        <summary>展开解释</summary>
        <div className="explain-grid">
          <div>
            <h4>能说明什么</h4>
            <p>{item.means}</p>
          </div>
          <div>
            <h4>不能说明什么</h4>
            <p>{item.does_not_mean}</p>
          </div>
        </div>
        {Object.keys(item.details).length > 0 && (
          <details className="technical-details">
            <summary>技术细节</summary>
            <pre>{JSON.stringify(item.details, null, 2)}</pre>
          </details>
        )}
      </details>
    </article>
  );
}

function ReportNotes({ limits }: { limits: string[] }) {
  return (
    <section className="report-notes">
      <h2>报告怎么读</h2>
      <ul>
        {limits.map((item) => (
          <li key={item}>{rewriteLimit(item)}</li>
        ))}
      </ul>
    </section>
  );
}

function statusClass(status: InterpretationEvidence["status_label"]) {
  const classes: Record<InterpretationEvidence["status_label"], string> = {
    支持证据: "status-support",
    需留意: "status-warning",
    未发现: "status-neutral",
    无法分析: "status-unavailable",
  };
  return classes[status];
}

function aiStrongAlert(evidence: InterpretationEvidence[]) {
  const aiMarker = evidence.find((item) => item.key === "gb45438" && item.status_label === "支持证据");
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

function rewriteLimit(limit: string) {
  const copy: Record<string, string> = {
    "没有发现证据，不等于图片一定不是 AI 生成。": "没有发现可读证据，不等于图片一定不是 AI 生成。",
    "压缩或编辑痕迹不等于图片一定被篡改或 P 图。":
      "局部差异只是线索，不能单独证明图片被篡改、P 图或 AI 生成。",
    "来源记录能说明文件里带有可验证信息，但不等于图片内容一定真实。":
      "来源记录能说明文件里带有可验证信息，但不等于图片内容一定真实或上下文完整。",
  };
  return copy[limit] ?? limit;
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
