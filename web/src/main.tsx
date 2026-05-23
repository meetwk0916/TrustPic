import React, { ChangeEvent, FormEvent, useMemo, useState } from "react";
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
  limitations: string[];
  recommendation: string;
  assets: {
    ela_heatmap_data_url: string | null;
  };
};

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [report, setReport] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const verdictLabel = useMemo(() => {
    if (!report) return null;
    const labels: Record<Verdict, string> = {
      supported_signal_detected: "Supported Signal Detected",
      review_recommended: "Review Recommended",
      no_supported_signal_found: "No Supported Signal Found",
      unsupported: "Unsupported",
    };
    return labels[report.verdict];
  }, [report]);

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
          <span className="status-pill">v0</span>
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
              <img src={previewUrl} alt="Selected upload preview" />
            ) : (
              <div className="empty-state">No image selected</div>
            )}
          </div>

          <div className="report-pane">
            {report ? (
              <>
                <div className={`verdict verdict-${report.verdict}`}>
                  <span>{verdictLabel}</span>
                  <strong>{report.summary}</strong>
                </div>

                <SignalList signals={report.signals} />

                {report.assets.ela_heatmap_data_url && (
                  <section className="heatmap">
                    <h2>ELA Heatmap</h2>
                    <img src={report.assets.ela_heatmap_data_url} alt="ELA heatmap" />
                  </section>
                )}

                <section className="text-section">
                  <h2>Recommendation</h2>
                  <p>{report.recommendation}</p>
                </section>

                <section className="text-section">
                  <h2>Limitations</h2>
                  <ul>
                    {report.limitations.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </section>
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

function SignalList({ signals }: { signals: AnalyzeResponse["signals"] }) {
  const entries: Array<[string, EvidenceSignal]> = [
    ["C2PA", signals.c2pa],
    ["GB 45438", signals.gb45438],
    ["EXIF", signals.exif],
    ["ELA", signals.ela],
  ];

  return (
    <section className="signals">
      <h2>Evidence</h2>
      <div className="signal-list">
        {entries.map(([label, signal]) => (
          <article className="signal-row" key={label}>
            <div>
              <h3>{label}</h3>
              <p>{signal.summary}</p>
            </div>
            <span className={signal.detected ? "badge badge-detected" : "badge"}>
              {signal.status}
            </span>
          </article>
        ))}
      </div>
    </section>
  );
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

