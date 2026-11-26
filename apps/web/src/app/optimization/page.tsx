"use client";

import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Tool = "hook" | "title" | "retention" | "shorts";
type Result = Record<string, unknown>;

async function post(path: string, payload: unknown): Promise<Result> {
  const response = await fetch(API + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || "Analysis request failed.");
  return data as Result;
}

const panelStyle: React.CSSProperties = { background: "#111827", border: "1px solid #263247", borderRadius: 14, padding: 22, marginTop: 18 };
const fieldStyle: React.CSSProperties = { display: "block", width: "100%", marginTop: 8, padding: 12, borderRadius: 8, border: "1px solid #34445c", background: "#0b1220", color: "#f8fafc", font: "inherit" };
const buttonStyle: React.CSSProperties = { border: 0, borderRadius: 8, padding: "11px 16px", background: "#8b5cf6", color: "white", fontWeight: 700, cursor: "pointer", marginTop: 14 };

export default function OptimizationPage() {
  const [tool, setTool] = useState<Tool>("hook");
  const [hook, setHook] = useState("");
  const [title, setTitle] = useState("");
  const [thumbnail, setThumbnail] = useState("");
  const [retention, setRetention] = useState("0,100\n15,90\n30,75\n45,68\n60,60");
  const [transcript, setTranscript] = useState("0-6 | Why do most people misunderstand this?\n6-15 | The first important idea is simpler than you think.\n15-25 | Here is a practical example you can use today.");
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function analyze() {
    setBusy(true); setError(""); setResult(null);
    try {
      let data: Result;
      if (tool === "hook") data = await post("/api/v1/optimization/hook-score", { hook });
      else if (tool === "title") data = await post("/api/v1/optimization/title-check", { title, thumbnail_text: thumbnail });
      else if (tool === "retention") {
        const points = retention.split(/\r?\n/).filter(Boolean).map((line) => {
          const [seconds, audience_percent] = line.split(",").map(Number);
          if (!Number.isFinite(seconds) || !Number.isFinite(audience_percent)) throw new Error("Use one seconds,percentage pair per line.");
          return { seconds, audience_percent };
        });
        data = await post("/api/v1/optimization/retention", { points });
      } else {
        const segments = transcript.split(/\r?\n/).filter(Boolean).map((line) => {
          const match = line.match(/^\s*(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)\s*\|\s*(.+)$/);
          if (!match) throw new Error("Use this format: start-end | spoken words");
          return { start_seconds: Number(match[1]), end_seconds: Number(match[2]), text: match[3] };
        });
        data = await post("/api/v1/optimization/shorts-candidates", { segments });
      }
      setResult(data);
    } catch (err) { setError(err instanceof Error ? err.message : "Could not complete analysis."); }
    finally { setBusy(false); }
  }

  const tabs: Array<[Tool, string]> = [["hook", "Hook score"], ["title", "Title + thumbnail"], ["retention", "Retention"], ["shorts", "Shorts finder"]];

  return <main style={{ minHeight: "100vh", background: "#080d18", color: "#e5e7eb", padding: "36px 5vw", fontFamily: "Arial, sans-serif" }}>
    <div style={{ maxWidth: 1050, margin: "0 auto" }}>
      <a href="/" style={{ color: "#a78bfa", textDecoration: "none" }}>← Back to AutoTube AI</a>
      <p style={{ color: "#a78bfa", letterSpacing: 2, fontSize: 12, fontWeight: 700, marginTop: 28 }}>CREATOR INTELLIGENCE</p>
      <h1 style={{ fontSize: 36, margin: "8px 0" }}>Optimization Lab</h1>
      <p style={{ color: "#9ca3af", lineHeight: 1.6 }}>Practical, explainable checks for your opening hook, packaging, audience retention and Shorts opportunities.</p>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 24 }}>
        {tabs.map(([key, label]) => <button key={key} onClick={() => { setTool(key); setResult(null); setError(""); }} style={{ ...buttonStyle, marginTop: 0, background: tool === key ? "#8b5cf6" : "#1f2937" }}>{label}</button>)}
      </div>
      <section style={panelStyle}>
        {tool === "hook" && <><h2>Hook score</h2><p style={{ color: "#9ca3af" }}>Score specificity, viewer relevance, stakes, curiosity and brevity. The score is a heuristic, not a performance forecast.</p><label>Opening line<textarea value={hook} onChange={e => setHook(e.target.value)} rows={4} style={fieldStyle} placeholder="Write the first line of your video..." /></label></>}
        {tool === "title" && <><h2>Title + thumbnail checker</h2><p style={{ color: "#9ca3af" }}>Check title length, vague wording, front-loaded clarity and repeated thumbnail text.</p><label>Video title<input value={title} onChange={e => setTitle(e.target.value)} style={fieldStyle} placeholder="Your YouTube title" /></label><label style={{ display: "block", marginTop: 16 }}>Thumbnail words<input value={thumbnail} onChange={e => setThumbnail(e.target.value)} style={fieldStyle} placeholder="Text shown on the thumbnail" /></label></>}
        {tool === "retention" && <><h2>Audience retention analyzer</h2><p style={{ color: "#9ca3af" }}>Paste timestamp,percentage pairs from your YouTube Studio export. Example: 15,82 means 82% at 15 seconds.</p><label>Seconds, audience percentage<textarea value={retention} onChange={e => setRetention(e.target.value)} rows={8} style={fieldStyle} /></label></>}
        {tool === "shorts" && <><h2>Shorts candidate finder</h2><p style={{ color: "#9ca3af" }}>Paste timestamped transcript segments. Each line must look like 0-8 | spoken words.</p><label>Transcript segments<textarea value={transcript} onChange={e => setTranscript(e.target.value)} rows={8} style={fieldStyle} /></label></>}
        <button onClick={() => void analyze()} disabled={busy} style={{ ...buttonStyle, opacity: busy ? 0.6 : 1 }}>{busy ? "Analyzing…" : "Analyze"}</button>
        {error && <p role="alert" style={{ color: "#fca5a5" }}>{error}</p>}
      </section>
      {result && <section style={panelStyle}><h2>Analysis result</h2><pre style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere", color: "#cbd5e1", lineHeight: 1.6 }}>{JSON.stringify(result, null, 2)}</pre></section>}
      <p style={{ color: "#64748b", fontSize: 12, marginTop: 24 }}>Review all recommendations manually. These tools do not guarantee views, clicks or audience retention.</p>
    </div>
  </main>;
}
