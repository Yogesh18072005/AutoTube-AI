"use client";

import { useState } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
type Report = {
  period: { start_date: string; end_date: string; days: number };
  current: Record<string, number>;
  previous: Record<string, number>;
  videos: Array<Record<string, string | number | null>>;
  recommendations: Array<{ priority: string; title: string; detail: string }>;
  data_source: string;
  disclaimer: string;
};
const panel: React.CSSProperties = { background: "#111827", border: "1px solid #263247", borderRadius: 14, padding: 22, marginTop: 18 };
const metricNames: Array<[string, string]> = [["views", "Views"], ["estimatedMinutesWatched", "Watch time (minutes)"], ["averageViewDuration", "Average view duration (seconds)"], ["subscribersGained", "Subscribers gained"], ["subscribersLost", "Subscribers lost"], ["likes", "Likes"], ["comments", "Comments"], ["shares", "Shares"]];
export default function IntelligencePage() {
  const [end, setEnd] = useState(new Date(Date.now() - 86400000).toISOString().slice(0, 10));
  const [start, setStart] = useState(new Date(Date.now() - 29 * 86400000).toISOString().slice(0, 10));
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function load() {
    setBusy(true); setError(""); setReport(null);
    try {
      const response = await fetch(API + "/api/v1/intelligence/channel?start_date=" + start + "&end_date=" + end);
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Could not load channel intelligence.");
      setReport(data as Report);
    } catch (e) { setError(e instanceof Error ? e.message : "Request failed."); }
    finally { setBusy(false); }
  }
  return <main style={{ minHeight: "100vh", background: "#080d18", color: "#e5e7eb", padding: "36px 5vw", fontFamily: "Arial, sans-serif" }}>
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>
      <Link href="/" style={{ color: "#a78bfa", textDecoration: "none" }}>← Back to AutoTube AI</Link>
      <p style={{ color: "#a78bfa", letterSpacing: 2, fontSize: 12, fontWeight: 700, marginTop: 28 }}>CHANNEL PERFORMANCE</p>
      <h1 style={{ fontSize: 36, margin: "8px 0" }}>Creator Intelligence</h1>
      <p style={{ color: "#9ca3af", lineHeight: 1.6 }}>Understand what is happening on your connected channel using actual YouTube Analytics data. No estimated or fabricated metrics.</p>
      <section style={panel}>
        <h2>Reporting period</h2>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 14, alignItems: "end" }}>
          <label>From<input type="date" value={start} max={end} onChange={e => setStart(e.target.value)} style={{ display: "block", marginTop: 6, padding: 10, background: "#0b1220", color: "white", border: "1px solid #34445c", borderRadius: 8 }} /></label>
          <label>To<input type="date" value={end} min={start} max={new Date(Date.now() - 86400000).toISOString().slice(0, 10)} onChange={e => setEnd(e.target.value)} style={{ display: "block", marginTop: 6, padding: 10, background: "#0b1220", color: "white", border: "1px solid #34445c", borderRadius: 8 }} /></label>
          <button onClick={() => void load()} disabled={busy} style={{ padding: "11px 16px", border: 0, borderRadius: 8, background: "#8b5cf6", color: "white", fontWeight: 700 }}>{busy ? "Loading…" : "Analyze channel"}</button>
        </div>
        {error && <p role="alert" style={{ color: "#fca5a5" }}>{error}</p>}
      </section>
      {report && <>
        <section style={panel}><h2>Channel overview</h2><p style={{ color: "#9ca3af" }}>{report.period.start_date} to {report.period.end_date} · compared with the immediately preceding {report.period.days} days</p><div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(190px,1fr))", gap: 12 }}>{metricNames.map(([key,label]) => <article key={key} style={{ background: "#0b1220", border: "1px solid #263247", borderRadius: 10, padding: 16 }}><small style={{ color: "#9ca3af" }}>{label}</small><h2 style={{ fontSize: 25, margin: "8px 0" }}>{(report.current[key] ?? 0).toLocaleString(undefined, { maximumFractionDigits: 1 })}</h2><small style={{ color: "#9ca3af" }}>Previous: {(report.previous[key] ?? 0).toLocaleString(undefined, { maximumFractionDigits: 1 })}</small></article>)}</div></section>
        <section style={panel}><h2>Evidence-based recommendations</h2>{report.recommendations.map((item,i)=><article key={i} style={{ borderBottom: "1px solid #263247", padding: "12px 0" }}><b>{item.title}</b><p style={{ color: "#9ca3af", lineHeight: 1.5 }}>{item.detail}</p><small style={{ color: "#a78bfa" }}>{item.priority.toUpperCase()}</small></article>)}</section>
        <section style={panel}><h2>Top videos in this period</h2>{report.videos.length ? <div style={{ overflowX: "auto" }}><table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}><thead><tr>{["Video ID","Views","Watch minutes","Avg duration","Subs gained","Engagement"].map(x=><th key={x} style={{ padding: 10, borderBottom: "1px solid #34445c" }}>{x}</th>)}</tr></thead><tbody>{report.videos.map((v,i)=><tr key={String(v.video_id ?? i)}><td style={{ padding: 10 }}><a href={String(v.url ?? "#")} target="_blank" rel="noreferrer" style={{ color: "#a78bfa" }}>{String(v.video_id ?? "Unavailable")}</a></td><td>{String(v.views ?? 0)}</td><td>{String(v.watch_minutes ?? 0)}</td><td>{String(v.average_view_duration_seconds ?? 0)}</td><td>{String(v.subscribers_gained ?? 0)}</td><td>{String((Number(v.likes)||0)+(Number(v.comments)||0)+(Number(v.shares)||0))}</td></tr>)}</tbody></table></div> : <p style={{ color: "#9ca3af" }}>No video-level rows were returned for this period.</p>}</section>
        <p style={{ color: "#64748b", fontSize: 12 }}>{report.data_source}. {report.disclaimer}</p>
      </>}
    </div>
  </main>;
}
