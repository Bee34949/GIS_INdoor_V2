import React from "react";
import { routerHealth, reloadGraph } from "../services/router";
export default function RouterStatus() {
  const [status, setStatus] = React.useState<"loading"|"ok"|"no-graph"|"error">("loading");
  const [path, setPath] = React.useState("-");
  const [busy, setBusy] = React.useState(false);

  async function refresh() {
    try { const h = await routerHealth(); setStatus(h.graph_loaded ? "ok" : "no-graph"); setPath(h.graph_path); }
    catch { setStatus("error"); }
  }
  React.useEffect(()=>{ refresh(); },[]);

  return (
    <div style={{display:"flex", gap:8, alignItems:"center"}}>
      <span style={{padding:"2px 8px", borderRadius:8, background: status==="ok"?"#DCFCE7":status==="no-graph"?"#FEF9C3":status==="loading"?"#E5E7EB":"#FEE2E2"}}>
        {status==="ok"?"Router: OK":status==="no-graph"?"Router: No Graph":status==="loading"?"Router: Loading…":"Router: Error"}
      </span>
      <small title={path} style={{maxWidth:260, overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap"}}>{path}</small>
      <button disabled={busy} onClick={async()=>{ setBusy(true); await reloadGraph().catch(()=>{}); await refresh(); setBusy(false); }}>Reload</button>
    </div>
  );
}