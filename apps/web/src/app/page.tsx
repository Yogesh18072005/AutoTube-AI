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

type Item = { id: string; kind: string; status: string; data: Record<string, unknown>; created_at: string };
type Metrics = { ideas: number; scripts: number; videos: number; awaiting_review: number; approved: number; scheduled: number; published: number; views: number; watch_time_hours: number; note?: string };
type YoutubeReport = { rows?: Array<Array<string | number | null>> };
const emptyMetrics: Metrics = { ideas: 0, scripts: 0, videos: 0, awaiting_review: 0, approved: 0, scheduled: 0, published: 0, views: 0, watch_time_hours: 0 };

async function request(path: string, options?: RequestInit) {
  const response = await fetch(API + path, { ...options, headers: { "Content-Type": "application/json", ...(options?.headers || {}) } });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || data.message || data.error || "Request failed");
  return data;
}

export default function Home() {
  const [active, setActive] = useState<string>("overview");
  const [items, setItems] = useState<Item[]>([]);
  const [metrics, setMetrics] = useState<Metrics>(emptyMetrics);
  const [youtubeReport, setYoutubeReport] = useState<YoutubeReport | null>(null);
  const [youtubeReportError, setYoutubeReportError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [topic, setTopic] = useState("");
  const [language, setLanguage] = useState("en");
  const [format, setFormat] = useState("short");
  const [tone, setTone] = useState("clear and engaging");
  const [settings, setSettings] = useState({ channel_name: "", default_language: "en", default_format: "short", ai_provider: "none", tts_provider: "none" });

  const refresh = useCallback(async () => {
    try {
      const [all, stats, config] = await Promise.all([
        request("/api/v1/records"), request("/api/v1/analytics/overview"), request("/api/v1/settings")
      ]);
      setItems(all); setMetrics(stats); setSettings(config);
      setMessage("");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "API unavailable. Start the FastAPI service with Docker Compose.");
    }
  }, []);

  useEffect(() => { void refresh(); }, [refresh]);

  useEffect(() => {
    if (active !== "analytics") return;
    const end = new Date().toISOString().slice(0, 10);
    const start = new Date(Date.now() - 28 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
    request(`/api/v1/analytics/youtube?start_date=${start}&end_date=${end}`)
      .then(data => {
        setYoutubeReport(data as YoutubeReport);
        setYoutubeReportError("");
      })
      .catch(error => {
        setYoutubeReport(null);
        setYoutubeReportError(error instanceof Error ? error.message : "Could not load YouTube Analytics.");
      });
  }, [active]);

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

  const createIdea = () => run(() => request("/api/v1/ideas", { method: "POST", body: JSON.stringify({ topic, language, format, audience: "Beginners" }) }), "Idea saved to your workspace.");
  const createResearch = () => run(() => request("/api/v1/research/brief", { method: "POST", body: JSON.stringify({ topic, language, format, audience: "Beginners" }) }), "AI research brief created.");
  const createScript = () => run(() => request("/api/v1/scripts/generate", { method: "POST", body: JSON.stringify({ topic, language, format, tone }) }), "Script draft created.");
  const createVideo = () => run(() => request("/api/v1/videos", { method: "POST", body: JSON.stringify({ title: topic, description: "", language, format, script: "", tags: [], duration_seconds: format === "short" ? 60 : 600 }) }), "Video draft added to review.");
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

        {active === "research" && <><div className="intro"><span className="eyebrow">DISCOVER YOUR NEXT VIDEO</span><h2>AI Research & Ideas</h2><p>Save topic ideas and create structured research briefs. Live trend/source discovery becomes available when a research provider is connected.</p></div><div className="form-card"><label>Topic or question<input value={topic} onChange={e=>setTopic(e.target.value)} placeholder="e.g. How AI agents are changing software development"/></label><div className="form-row"><label>Language<select value={language} onChange={e=>setLanguage(e.target.value)}><option value="en">English</option><option value="hi">Hindi</option></select></label><label>Format<select value={format} onChange={e=>setFormat(e.target.value)}><option value="short">YouTube Shorts</option><option value="long">Long-form video</option></select></label></div><div className="form-row"><button disabled={!topic.trim()||loading} className="primary-button" onClick={()=>void createResearch()}>Create research brief ✦</button><button disabled={!topic.trim()||loading} className="text-button" onClick={()=>void createIdea()}>Save as idea</button></div></div><RecordList items={visible}/></>}

        {active === "scripts" && <><div className="intro"><span className="eyebrow">BILINGUAL WRITING ROOM</span><h2>Script Studio</h2><p>Draft a structured script with a hook and scene plan. Connect an AI provider for original, researched scripts.</p></div><div className="form-card"><label>Video topic<input value={topic} onChange={e=>setTopic(e.target.value)} placeholder="What should the video explain?"/></label><div className="form-row"><label>Language<select value={language} onChange={e=>setLanguage(e.target.value)}><option value="en">English</option><option value="hi">Hindi</option></select></label><label>Format<select value={format} onChange={e=>setFormat(e.target.value)}><option value="short">Short (under 60 sec)</option><option value="long">Long-form</option></select></label></div><label>Tone<input value={tone} onChange={e=>setTone(e.target.value)} /></label><div className="form-row"><button disabled={!topic.trim()||loading} className="primary-button" onClick={()=>void createScript()}>Generate script draft ✦</button><button disabled={!topic.trim()||loading} className="text-button" onClick={()=>void createVideo()}>Create video draft</button></div></div><RecordList items={visible}/></>}

        {active === "approval" && <><div className="intro"><span className="eyebrow">YOUR FINAL CHECK</span><h2>Approval Queue</h2><p>Only videos explicitly approved here can enter the publishing workflow.</p></div><RecordList items={visible} onApprove={id=>run(()=>request("/api/v1/videos/"+id+"/approve",{method:"POST",body:JSON.stringify({note:"Approved in creator workspace"})}),"Video approved.")} onReject={id=>run(()=>request("/api/v1/videos/"+id+"/reject",{method:"POST",body:JSON.stringify({note:"Changes requested"})}),"Changes requested.")}/></>}

        {active === "publishing" && <><div className="intro"><span className="eyebrow">YOUTUBE DELIVERY</span><h2>Publishing</h2><p>Scheduling is protected by a server-side approval check. Add YouTube OAuth credentials to enable the publishing adapter.</p></div><div className="status-card"><b>Approval gate: enforced</b><span>Unapproved videos are rejected by the API.</span></div><RecordList items={visible} onSchedule={id=>run(()=>request("/api/v1/publishing/"+id+"/schedule",{method:"POST",body:JSON.stringify({scheduled_at:new Date(Date.now()+86400000).toISOString()})}),"Video scheduled.")}/></>}

        {active === "analytics" && <><div className="intro"><span className="eyebrow">MEASURE WHAT MATTERS</span><h2>Channel Analytics</h2><p>Workspace pipeline totals and live YouTube channel performance for the last 28 days.</p></div><div className="metric-grid">{[["Videos",metrics.videos],["Approved",metrics.approved],["Scheduled",metrics.scheduled],["Published",metrics.published]].map(([label,value])=><article className="metric-card" key={String(label)}><div className="metric-top"><span>{label}</span></div><strong>{value}</strong><small>Workspace total</small></article>)}</div><div className="section-row"><div><span className="eyebrow">YOUTUBE ANALYTICS API</span><h2>Daily channel performance</h2></div></div>{youtubeReport?.rows?.length ? <div className="record-list">{youtubeReport.rows.map((row,index)=><article className="record-card" key={index}><div className="record-main"><span className="record-kind">DAILY CHANNEL REPORT</span><h3>{String(row[0] ?? "Date unavailable")}</h3><p>Views: {String(row[1] ?? "—")} · Watch time (minutes): {String(row[2] ?? "—")} · Average view duration (seconds): {String(row[3] ?? "—")} · Subscribers gained: {String(row[4] ?? "—")}</p></div></article>)}</div> : <div className="status-card">{youtubeReportError || "Loading YouTube Analytics…"}</div>}</>}

        {active === "settings" && <><div className="intro"><span className="eyebrow">WORKSPACE CONFIGURATION</span><h2>Settings & Providers</h2><p>Choose defaults and connect providers through server environment variables. Never paste secret keys into the browser.</p></div><div className="form-card"><label>Channel name<input value={settings.channel_name} onChange={e=>setSettings({...settings,channel_name:e.target.value})} placeholder="Your YouTube channel"/></label><div className="form-row"><label>Default language<select value={settings.default_language} onChange={e=>setSettings({...settings,default_language:e.target.value})}><option value="en">English</option><option value="hi">Hindi</option></select></label><label>Default format<select value={settings.default_format} onChange={e=>setSettings({...settings,default_format:e.target.value})}><option value="short">Shorts</option><option value="long">Long-form</option></select></label></div><div className="form-row"><label>AI provider<select value={settings.ai_provider} onChange={e=>setSettings({...settings,ai_provider:e.target.value})}><option value="none">Not connected</option><option value="openai">OpenAI</option><option value="google">Google</option><option value="other">Other / custom</option></select></label><label>Voice provider<select value={settings.tts_provider} onChange={e=>setSettings({...settings,tts_provider:e.target.value})}><option value="none">Not connected</option><option value="elevenlabs">ElevenLabs</option><option value="google">Google</option><option value="other">Other / custom</option></select></label></div><button className="primary-button" disabled={loading} onClick={()=>void saveSettings()}>Save settings</button></div></>}

        {["channels","voice","media","editor","thumbnails","seo","automation"].includes(active) && <ModulePanel active={active} />}
      </section>
    </main>
  );
}

function RecordList({items,onApprove,onReject,onSchedule}:{items:Item[];onApprove?:(id:string)=>void;onReject?:(id:string)=>void;onSchedule?:(id:string)=>void}) {
  if (!items.length) return <div className="empty-state"><span>◌</span><b>Nothing here yet</b><p>New items you create will appear in this workspace.</p></div>;
  return <div className="record-list">{items.map(item=><article className="record-card" key={item.id}><div className="record-main"><span className="record-kind">{item.kind.toUpperCase()} · {String(item.data.language ?? "EN")} · {String(item.data.format ?? "—")}</span><h3>{String(item.data.topic ?? item.data.title ?? "Untitled item")}</h3><p>{String(item.data.full_text ?? item.data.provider_message ?? item.data.description ?? item.data.angle ?? "Workspace item")}</p><span className={"status status-"+item.status}>{item.status.replaceAll("_"," ")}</span></div><div className="record-actions">{onApprove&&<button className="small-primary" onClick={()=>onApprove(item.id)}>Approve</button>}{onReject&&<button className="small-quiet" onClick={()=>onReject(item.id)}>Request changes</button>}{onSchedule&&item.status==="approved"&&<button className="small-primary" onClick={()=>onSchedule(item.id)}>Schedule</button>}</div></article>)}</div>;
}

function ModulePanel({active}:{active:string}) {
  const [voiceText,setVoiceText] = useState("");
  const [title,setTitle] = useState("");
  const [seoTopic,setSeoTopic] = useState("");
  const [notice,setNotice] = useState("");
  const [busy,setBusy] = useState(false);
  const [result,setResult] = useState<unknown>(null);
  const [pipelineTopic,setPipelineTopic] = useState("");
  const [connection,setConnection] = useState<{connected:boolean;reason?:string}|null>(null);

  const content:Record<string,{tag:string;title:string;desc:string;steps:string[];note:string}> = {
    channels:{tag:"CHANNEL MANAGEMENT",title:"Connect your YouTube channel",desc:"Channel identity, OAuth permissions and upload defaults live here.",steps:["Create a Google Cloud project","Enable YouTube Data API v3 and YouTube Analytics API","Configure OAuth consent and redirect URI","Store client credentials in the API environment"],note:"Connect the Google account that owns the YouTube channel. Tokens are encrypted on the API host."},
    voice:{tag:"NARRATION WORKSPACE",title:"Voice Studio",desc:"Generate Hindi or English narration from your approved script text.",steps:["Choose a voice ID in the server environment","Generate narration audio","Review the MP3 asset in the media library"],note:"ElevenLabs generates an MP3 when ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID are configured on the API server."},
    media:{tag:"ASSET LIBRARY",title:"Media Library",desc:"Generated audio and rendered video files are served from the local media directory.",steps:["Track asset source and license","Attach assets to scenes","Move production assets to durable object storage before deployment"],note:"OpenAI image generation is available when OPENAI_API_KEY is configured. Generated assets are stored in the local media volume; cloud object storage is not configured."},
    editor:{tag:"VIDEO PRODUCTION",title:"Video Editor & Renderer",desc:"Render a basic 1080p title-card MP4 with optional generated narration.",steps:["Install FFmpeg and add it to PATH","Render a title card","Review the MP4 before using it in a final edit"],note:"The editor action renders a simple title-card MP4 with FFmpeg. The automation worker can render a sequence of text-based scene cards and attach generated narration; stock footage and motion graphics are not included."},
    thumbnails:{tag:"CLICK-THROUGH STUDIO",title:"Thumbnail Studio",desc:"Prepare thumbnail concepts and production metadata.",steps:["Generate thumbnail concepts","Apply channel brand kit","Check mobile readability","Export 1280 × 720 image"],note:"The API creates 1280 × 720 thumbnails locally with Pillow. Generated image assets can be created separately with the OpenAI image endpoint."},
    seo:{tag:"DISCOVERY OPTIMIZATION",title:"SEO Studio",desc:"Generate YouTube title options, descriptions, tags and hashtags.",steps:["Enter the video topic","Generate metadata with the configured AI provider","Review every claim and edit before approval"],note:"SEO titles, descriptions, tags and hashtags are generated through the configured OpenAI-compatible provider. Live search-volume and ranking data are not included."},
    automation:{tag:"WORKFLOW ORCHESTRATION",title:"AUTOMATION CONTROL",desc:"The pipeline includes explicit checkpoints and a human approval boundary.",steps:["Research topic","Generate script and narration","Create visuals and render video","Generate thumbnail and SEO metadata","Human approval","Schedule and reconcile publication"],note:"The Redis/Celery worker creates an AI brief, script, optional narration, scene-card MP4, thumbnail, SEO metadata and a video draft. A person must review and approve it before publishing."},
  };
  const item=content[active];

  useEffect(() => {
    if (active !== "channels") return;
    fetch(API + "/api/v1/auth/google/status")
      .then(response => response.json())
      .then(data => setConnection(data))
      .catch(() => setConnection({ connected: false, reason: "api_unavailable" }));
  }, [active]);

  async function connectYouTube() {
    setBusy(true); setNotice("");
    try {
      const response = await fetch(API + "/api/v1/auth/google/start");
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Could not start YouTube authorization.");
      if (!data.authorization_url) throw new Error("The API did not return an authorization URL.");
      window.location.assign(data.authorization_url);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "YouTube connection failed.");
      setBusy(false);
    }
  }

  async function run(path:string,payload:Record<string,unknown>,success:string) {
    setBusy(true); setNotice(""); setResult(null);
    try {
      const data=await request(path,{method:"POST",body:JSON.stringify(payload)});
      setResult(data); setNotice(success);
    } catch(error) {
      setNotice(error instanceof Error ? error.message : "Production request failed.");
    } finally { setBusy(false); }
  }

  return <><div className="intro"><span className="eyebrow">{item.tag}</span><h2>{item.title}</h2><p>{item.desc}</p></div><div className="workflow-card">
    <h3>Workflow</h3><ol>{item.steps.map(step=><li key={step}>{step}</li>)}</ol>
    <div className="notice warning">{item.note}</div>
    {active==="channels"&&<><div className="status-card">{connection?.connected?"YouTube channel connected.":connection?.reason==="stored_token_unreadable"?"Stored YouTube token cannot be decrypted. Check the token encryption key.":"YouTube channel is not connected."}</div><button className="primary-button" disabled={busy} onClick={()=>void connectYouTube()}>{busy?"Opening Google…":"Connect YouTube with Google"}</button></>}
    {active==="automation"&&<><label className="tool-label">Video topic<input value={pipelineTopic} onChange={e=>setPipelineTopic(e.target.value)} placeholder="What should AutoTube produce?"/></label><button className="primary-button" disabled={busy||!pipelineTopic.trim()} onClick={()=>void run("/api/v1/automation/queue",{topic:pipelineTopic,language:"en",format:"short"},"Automation job queued. Check the job result and approval queue.")}>{busy?"Queueing…":"Run content production pipeline"}</button></>}
    {active==="voice"&&<><label className="tool-label">Narration text<textarea value={voiceText} onChange={e=>setVoiceText(e.target.value)} placeholder="Paste your approved narration here..." rows={5}/></label><button className="primary-button" disabled={busy||!voiceText.trim()} onClick={()=>void run("/api/v1/voice/generate",{text:voiceText},"Narration generated.")}>{busy?"Generating…":"Generate voiceover"}</button></>}
    {active==="editor"&&<><label className="tool-label">Video title<input value={title} onChange={e=>setTitle(e.target.value)} placeholder="Enter a title for the video"/></label><button className="primary-button" disabled={busy||!title.trim()} onClick={()=>void run("/api/v1/render/title-card",{title,duration_seconds:5},"Title-card video rendered.")}>{busy?"Rendering…":"Render title-card MP4"}</button></>}
    {active==="seo"&&<><label className="tool-label">Video topic<input value={seoTopic} onChange={e=>setSeoTopic(e.target.value)} placeholder="Enter the topic for metadata"/></label><button className="primary-button" disabled={busy||!seoTopic.trim()} onClick={()=>void run("/api/v1/seo/generate",{topic:seoTopic,language:"en",format:"short"},"SEO draft generated.")}>{busy?"Generating…":"Generate SEO metadata"}</button></>}
    {active==="thumbnails"&&<><label className="tool-label">Thumbnail title<input value={seoTopic} onChange={e=>setSeoTopic(e.target.value)} placeholder="Enter thumbnail title"/></label><button className="primary-button" disabled={busy||!seoTopic.trim()} onClick={()=>void run("/api/v1/thumbnails/generate",{title:seoTopic,subtitle:"AutoTube AI"},"Thumbnail generated.")}>{busy?"Generating…":"Generate thumbnail"}</button></>}
    {active==="media"&&<><label className="tool-label">Image prompt<textarea value={seoTopic} onChange={e=>setSeoTopic(e.target.value)} placeholder="Describe the visual asset you need..." rows={4}/></label><button className="primary-button" disabled={busy||seoTopic.trim().length<5} onClick={()=>void run("/api/v1/media/image",{prompt:seoTopic},"Image generated.")}>{busy?"Generating…":"Generate image asset"}</button></>}
    {notice&&<div className={notice.includes("not configured")||notice.includes("requires")?"notice warning":"notice"}>{notice}</div>}
    {result !== null && <pre className="result-json">{JSON.stringify(result,null,2)}</pre>}
  </div></>;
}
