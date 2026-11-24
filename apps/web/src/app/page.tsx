const modules = [
  ["01", "Research", "Discover AI and technology topics worth covering."],
  ["02", "Script Studio", "Create Hindi and English scripts for Shorts and long videos."],
  ["03", "Production", "Generate narration, visuals, captions and rendered videos."],
  ["04", "Review Queue", "Inspect every video and approve or request changes."],
  ["05", "Publishing", "Schedule approved videos to your connected YouTube channel."],
  ["06", "Analytics", "Learn from views, watch time and audience retention."],
];

export default function Home() {
  return (
    <main style={{ maxWidth: 1120, margin: "0 auto", padding: "56px 24px" }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 16 }}>
        <strong style={{ fontSize: 22 }}>◈ AutoTube AI</strong>
        <span style={{ color: "#a7b4d2", fontSize: 13 }}>PRIVATE CREATOR WORKSPACE</span>
      </header>
      <section style={{ padding: "76px 0 48px" }}>
        <p style={{ color: "#8da9ff", letterSpacing: 3, fontSize: 12 }}>YOUR AI-POWERED YOUTUBE STUDIO</p>
        <h1 style={{ fontSize: "clamp(42px, 7vw, 76px)", lineHeight: 1.03, margin: "14px 0" }}>
          From idea to <span style={{ color: "#8da9ff" }}>upload-ready.</span>
        </h1>
        <p style={{ maxWidth: 650, color: "#a7b4d2", fontSize: 18, lineHeight: 1.7 }}>
          Research, write, produce and review bilingual AI & technology videos.
          You stay in control: nothing gets published without your approval.
        </p>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 24 }}>
          {["Hindi + English", "Shorts + Long-form", "Approval required"].map(x =>
            <span key={x} style={{ border: "1px solid #293858", borderRadius: 99, padding: "9px 14px", color: "#cbd6f2", fontSize: 13 }}>{x}</span>
          )}
        </div>
      </section>
      <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 14 }}>
        {modules.map(([n, title, desc]) => (
          <article key={n} style={{ background: "#111a2c", border: "1px solid #263653", borderRadius: 16, padding: 22 }}>
            <span style={{ color: "#8da9ff", fontSize: 13 }}>{n} / MODULE</span>
            <h2 style={{ margin: "14px 0 8px", fontSize: 21 }}>{title}</h2>
            <p style={{ color: "#a7b4d2", lineHeight: 1.6, margin: 0 }}>{desc}</p>
          </article>
        ))}
      </section>
      <footer style={{ color: "#7383a4", fontSize: 12, marginTop: 44 }}>
        AutoTube AI · Foundation scaffold · Publishing is approval-gated
      </footer>
    </main>
  );
}
