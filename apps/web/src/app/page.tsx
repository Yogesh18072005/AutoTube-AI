"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const nav = [
  ["overview", "Overview", "⌂"], ["channels", "Channels", "▣"], ["research", "AI Research", "⌕"],
  ["scripts", "Script Studio", "✎"], ["voice", "Voice Studio", "◖"], ["media", "Media Library", "▧"],
  ["editor", "Video Editor", "▤"], ["thumbnails", "Thumbnail Studio", "▣"], ["seo", "SEO Studio", "↗"],
  ["approval", "Approval Queue", "✓"], ["publishing", "Publishing", "⇧"], ["analytics", "Analytics", "⌁"],
  ["automation", "Automation", "⟳"], ["settings", "Settings", "⚙"],
] as const;

type Item = { id: string; kind: string; status: string; data: Record<string, any>; created_at: string };
type Metrics = { ideas: number; scripts: number; videos: number; awaiting_review: number; approved: number; scheduled: number; published: number; views: number; watch_time_hours: number; note?: string };
const emptyMetrics: Metrics = { ideas: 0, scripts: 0, videos: 0, awaiting_review: 0, approved: 0, scheduled: 0, published: 0, views: 0, watch_time_hours: 0 };

async function request(path: string, options?: RequestInit) {
  const response = await fetch(API + path, { ...options, headers: { "Content-Type": "application/json", ...(options?.headers || {}) } });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || "Request failed");
  return data;
}

export default function Home() {
  const [active, setActive] = useState<string>("overview");
  const [items, setItems] = useState<Item[]>([]);
  const [metrics, setMetrics] = useState<Metrics>(emptyMetrics);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [topic, setTopic] = useState("");
  const [language, setLanguage] = useState("en");
  const [format, setFormat] = useState("short");
  const [tone, setTone] = useState("clear and engaging");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [settings, setSettings] = useState({ channel_name: "", default_language: "en", default_format: "short", ai_provider: "none", tts_provider: "none" });

  const refresh = useCallback(async () => {
    try {
      const [all, stats, config] = await Promise.all([
        request("/api/v1/records"), request("/api/v1/analytics/overview"), request("/api/v1/settings")
      ]);
      setItems(all); setMetrics(stats); setSettings(config);
      setMessage("");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "API unavailable. Start the FastAPI server.");
    }
  }, []);

  useEffect(() => { void refresh(); }, [refresh]);

  const visible = useMemo(() => items.filter(x => {
    if (active === "approval") return x.kind === "video" && x.status === "video_review";
    if (active === "publishing") return x.kind === "video";
    if (active === "scripts") return x.kind === "script";
    if (active === "research") return x.kind === "research" || x.kind === "idea";
    if (active === "media" || active === "editor" || active === "thumbnails" || active === "seo") return x.kind === "video";
    return true;
  }), [items, active]);

  async function run(action: () => Promise<unknown>, success: string) {
    setLoading(true); setMessage("");
    try { await action(); await refresh(); setMessage(success); }
    catch (error) { setMessage(error instanceof Error ? error.message : "Something went wrong"); }
    finally { setLoading(false); }
  }

  const createResearch = () => run(() => request("/api/v1/research", { method: "POST", body: JSON.stringify({ topic, language, format, audience: "Beginners" }) }), "Research brief created.");
  const createScript = () => run(() => request("/api/v1/scripts/generate", { method: "POST", body: JSON.stringify({ topic, language, format, tone }) }), "Script draft created.");
  const createVideo = () => run(() => request("/api/v1/videos", { method: "POST", body: JSON.stringify({ title: title || topic, description, language, format, script: "", tags: [], duration_seconds: format === "short" ? 60 : 600 }) }), "Video draft added to review.");
  const saveSettings = () => run(() => request("/api/v1/settings", { method: "PUT", body: JSON.stringify(settings) }), "Settings saved.");

  function heading() {
    return nav.find(x => x[0] === active)?.[1] || "Overview";
  }

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark">A</span><span>AutoTube<span className="brand-ai"> AI</span><small>CREATOR WORKSPACE</small></span></div>
        <div className="workspace-label">WORKSPACE</div>
        <nav>{nav.map(([id, label, icon]) => <button key={id} className={active === id ? "nav-item active" : "nav-item"} onClick={() => { setActive(id); setMessage(""); }}><span className="nav-icon">{icon}</span>{label}{id === "approval" && metrics.awaiting_review > 0 && <b className="nav-count">{metrics.awaiting_review}</b>}</button>)}</nav>
        <div className="sidebar-bottom"><span className="online-dot" /> Local workspace <small>Provider connections pending</small></div>
      </aside>

      <section className="main-area">
        <header className="topbar"><div><span className="eyebrow">AUTOTUBE AI / STUDIO</span><h1>{heading()}</h1></div><div className="top-actions"><span className="language-pill">EN / HI</span><button className="icon-button" onClick={() => void refresh()} title="Refresh">↻</button><div className="avatar">Y</div></div></header>
        {message && <div className={message.includes("unavailable") || message.includes("blocked") || message.includes("not configured") ? "notice warning" : "notice"}>{message}</div>}

        {active === "overview" && <><section className="hero-panel"><div><span className="eyebrow">YOUR CONTENT ENGINE</span><h2>Turn ideas into<br/><em>upload-ready videos.</em></h2><p>Research, write, produce and manage your Hindi and English AI & technology content from one workspace.</p><div className="hero-tags"><span>Hindi + English</span><span>Shorts + Long-form</span><span>Human approval gate</span></div></div><div className="hero-orbit"><div className="orbit-ring"><div className="orbit-core">A<span>AI</span></div><i className="orbit-node node-one">✦</i><i className="orbit-node node-two">▶</i><i className="orbit-node node-three">✎</i></div></div></section>
          <div className="metric-grid">{[["Ideas",metrics.ideas,"⌕"],["Scripts",metrics.scripts,"✎"],["Videos",metrics.videos,"▷"],["Awaiting review",metrics.awaiting_review,"✓"]].map(([label,value,icon])=><article className="metric-card" key={String(label)}><div className="metric-top"><span>{label}</span><b>{icon}</b></div><strong>{value}</strong><small>All-time workspace total</small></article>)}</div>
          <div className="section-row"><div><span className="eyebrow">PRODUCTION PIPELINE</span><h2>Everything in one place</h2></div><button className="text-button" onClick={() => setActive("research")}>Create content ↗</button></div>
          <div className="module-grid">{nav.slice(2).map(([id,label,icon])=><button className="module-card" key={id} onClick={()=>setActive(id)}><span className="module-icon">{icon}</span><strong>{label}</strong><small>Open workspace <span>↗</span></small></button>)}</div>
        </>}

        {active === "research" && <><div className="intro"><span className="eyebrow">DISCOVER YOUR NEXT VIDEO</span><h2>AI Research & Ideas</h2><p>Save topic ideas and create structured research briefs. Live trend/source discovery becomes available when a research provider is connected.</p></div><div className="form-card"><label>Topic or question<input value={topic} onChange={e=>setTopic(e.target.value)} placeholder="e.g. How AI agents are changing software development"/></label><div className="form-row"><label>Language<select value={language} onChange={e=>setLanguage(e.target.value)}><option value="en">English</option><option value="hi">Hindi</option></select></label><label>Format<select value={format} onChange={e=>setFormat(e.target.value)}><option value="short">YouTube Shorts</option><option value="long">Long-form video</option></select></label></div><button disabled={!topic.trim()||loading} className="primary-button" onClick={()=>void createResearch()}>Create research brief ✦</button></div><RecordList items={visible}/></>}

        {active === "scripts" && <><div className="intro"><span className="eyebrow">BILINGUAL WRITING ROOM</span><h2>Script Studio</h2><p>Draft a structured script with a hook and scene plan. Connect an AI provider for original, researched scripts.</p></div><div className="form-card"><label>Video topic<input value={topic} onChange={e=>setTopic(e.target.value)} placeholder="What should the video explain?"/></label><div className="form-row"><label>Language<select value={language} onChange={e=>setLanguage(e.target.value)}><option value="en">English</option><option value="hi">Hindi</option></select></label><label>Format<select value={format} onChange={e=>setFormat(e.target.value)}><option value="short">Short (under 60 sec)</option><option value="long">Long-form</option></select></label></div><label>Tone<input value={tone} onChange={e=>setTone(e.target.value)} /></label><button disabled={!topic.trim()||loading} className="primary-button" onClick={()=>void createScript()}>Generate script draft ✦</button></div><RecordList items={visible}/></>}

        {active === "approval" && <><div className="intro"><span className="eyebrow">YOUR FINAL CHECK</span><h2>Approval Queue</h2><p>Only videos explicitly approved here can enter the publishing workflow.</p></div><RecordList items={visible} onApprove={id=>run(()=>request("/api/v1/videos/"+id+"/approve",{method:"POST",body:JSON.stringify({note:"Approved in creator workspace"})}),"Video approved.")} onReject={id=>run(()=>request("/api/v1/videos/"+id+"/reject",{method:"POST",body:JSON.stringify({note:"Changes requested"})}),"Changes requested.")}/></>}

        {active === "publishing" && <><div className="intro"><span className="eyebrow">YOUTUBE DELIVERY</span><h2>Publishing</h2><p>Scheduling is protected by a server-side approval check. Add YouTube OAuth credentials to enable the publishing adapter.</p></div><div className="status-card"><b>Approval gate: enforced</b><span>Unapproved videos are rejected by the API.</span></div><RecordList items={visible} onSchedule={id=>run(()=>request("/api/v1/publishing/"+id+"/schedule",{method:"POST",body:JSON.stringify({scheduled_at:new Date(Date.now()+86400000).toISOString()})}),"Video scheduled.")}/></>}

        {active === "analytics" && <><div className="intro"><span className="eyebrow">MEASURE WHAT MATTERS</span><h2>Channel Analytics</h2><p>Workspace pipeline totals are available now. Connect YouTube Analytics to retrieve real views, watch time and audience retention.</p></div><div className="metric-grid">{[["Videos",metrics.videos],["Approved",metrics.approved],["Scheduled",metrics.scheduled],["Published",metrics.published],["Views",metrics.views],["Watch time (hrs)",metrics.watch_time_hours]].map(([label,value])=><article className="metric-card" key={String(label)}><div className="metric-top"><span>{label}</span></div><strong>{value}</strong><small>{Number(value)===0?"Waiting for channel connection":"Workspace data"}</small></article>)}</div><div className="status-card">{metrics.note}</div></>}

        {active === "settings" && <><div className="intro"><span className="eyebrow">WORKSPACE CONFIGURATION</span><h2>Settings & Providers</h2><p>Choose defaults and connect providers through server environment variables. Never paste secret keys into the browser.</p></div><div className="form-card"><label>Channel name<input value={settings.channel_name} onChange={e=>setSettings({...settings,channel_name:e.target.value})} placeholder="Your YouTube channel"/></label><div className="form-row"><label>Default language<select value={settings.default_language} onChange={e=>setSettings({...settings,default_language:e.target.value})}><option value="en">English</option><option value="hi">Hindi</option></select></label><label>Default format<select value={settings.default_format} onChange={e=>setSettings({...settings,default_format:e.target.value})}><option value="short">Shorts</option><option value="long">Long-form</option></select></label></div><div className="form-row"><label>AI provider<select value={settings.ai_provider} onChange={e=>setSettings({...settings,ai_provider:e.target.value})}><option value="none">Not connected</option><option value="openai">OpenAI</option><option value="google">Google</option><option value="other">Other / custom</option></select></label><label>Voice provider<select value={settings.tts_provider} onChange={e=>setSettings({...settings,tts_provider:e.target.value})}><option value="none">Not connected</option><option value="elevenlabs">ElevenLabs</option><option value="google">Google</option><option value="other">Other / custom</option></select></label></div><button className="primary-button" disabled={loading} onClick={()=>void saveSettings()}>Save settings</button></div></>}

        {["channels","voice","media","editor","thumbnails","seo","automation"].includes(active) && <ModulePanel active={active} onCreateVideo={()=>setActive("approval")} />}
      </section>
    </main>
  );
}

function RecordList({items,onApprove,onReject,onSchedule}:{items:Item[];onApprove?:(id:string)=>void;onReject?:(id:string)=>void;onSchedule?:(id:string)=>void}) {
  if (!items.length) return <div className="empty-state"><span>◌</span><b>Nothing here yet</b><p>New items you create will appear in this workspace.</p></div>;
  return <div className="record-list">{items.map(item=><article className="record-card" key={item.id}><div className="record-main"><span className="record-kind">{item.kind.toUpperCase()} · {item.data.language||"EN"} · {item.data.format||"—"}</span><h3>{item.data.topic||item.data.title||"Untitled item"}</h3><p>{item.data.full_text||item.data.provider_message||item.data.description||item.data.angle||"Workspace item"}</p><span className={"status status-"+item.status}>{item.status.replaceAll("_"," ")}</span></div><div className="record-actions">{onApprove&&<button className="small-primary" onClick={()=>onApprove(item.id)}>Approve</button>}{onReject&&<button className="small-quiet" onClick={()=>onReject(item.id)}>Request changes</button>}{onSchedule&&item.status==="approved"&&<button className="small-primary" onClick={()=>onSchedule(item.id)}>Schedule</button>}</div></article>)}</div>;
}

function ModulePanel({active,onCreateVideo}:{active:string;onCreateVideo:()=>void}) {
  const content:Record<string,{tag:string;title:string;desc:string;steps:string[];note:string}> = {
    channels:{tag:"CHANNEL MANAGEMENT",title:"Connect your YouTube channel",desc:"Channel identity, OAuth permissions and upload defaults live here.",steps:["Create a Google Cloud project","Enable YouTube Data API v3 and YouTube Analytics API","Configure OAuth consent and redirect URI","Store client credentials in the API environment"],note:"OAuth callback and token storage must be configured before a channel can be connected."},
    voice:{tag:"NARRATION WORKSPACE",title:"Voice Studio",desc:"Prepare narration for Hindi and English scripts.",steps:["Choose language and voice","Preview pronunciation and pacing","Generate narration audio","Attach approved audio to a video project"],note:"Text-to-speech provider is not connected yet. No audio is fabricated by this starter."},
    media:{tag:"ASSET LIBRARY",title:"Media Library",desc:"Organize generated images, footage, music and other production assets.",steps:["Track asset source and license","Attach assets to scenes","Store files in object storage","Keep a provenance record"],note:"Object storage and image/video generation credentials are required for real asset generation."},
    editor:{tag:"VIDEO PRODUCTION",title:"Video Editor & Renderer",desc:"Prepare vertical Shorts and horizontal long-form timelines.",steps:["9:16 Shorts composition","16:9 long-form composition","Captions, transitions and audio mix","FFmpeg render job and preview"],note:"FFmpeg render worker is a separate background service and is not active in this API-only starter."},
    thumbnails:{tag:"CLICK-THROUGH STUDIO",title:"Thumbnail Studio",desc:"Create consistent thumbnail concepts and export-ready assets.",steps:["Generate thumbnail concepts","Apply channel brand kit","Check mobile readability","Export 1280 × 720 image"],note:"Connect an image-generation provider and storage to produce real files."},
    seo:{tag:"DISCOVERY OPTIMIZATION",title:"SEO Studio",desc:"Prepare titles, descriptions, tags and publishing metadata.",steps:["Draft searchable title variations","Write a clear description","Suggest relevant tags and hashtags","Review metadata before approval"],note:"SEO metadata is stored with video records. AI-assisted optimization requires a configured model provider."},
    automation:{tag:"WORKFLOW ORCHESTRATION",title:"AUTOMATION CONTROL",desc:"A complete production pipeline with explicit checkpoints.",steps:["Research topic","Generate script and narration","Create visuals and render video","Generate thumbnail and SEO metadata","Human approval","Schedule and reconcile publication"],note:"The API exposes automation status. Redis/Celery worker execution and provider credentials remain deployment tasks."},
  };
  const item=content[active];
  return <><div className="intro"><span className="eyebrow">{item.tag}</span><h2>{item.title}</h2><p>{item.desc}</p></div><div className="workflow-card"><h3>Workflow</h3><ol>{item.steps.map(step=><li key={step}>{step}</li>)}</ol><div className="notice warning">{item.note}</div>{active==="seo"&&<button className="primary-button" onClick={onCreateVideo}>Create a video draft</button>}</div></>;
}
