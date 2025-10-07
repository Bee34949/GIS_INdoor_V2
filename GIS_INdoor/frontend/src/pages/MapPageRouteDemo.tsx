import React from "react";
import { getRoute, getGraph, nearest } from "../services/router";
import RouterStatus from "../components/RouterStatus";
import PathCanvas from "../components/PathCanvas";

export default function MapPageRouteDemo() {
  const [graph, setGraph] = React.useState<{nodes:Record<string,{x:number;y:number;floor_id:string}>; floors:any[]}>({nodes:{}, floors:[]});
  const [viewFloor, setViewFloor] = React.useState("F2");

  const [start, setStart] = React.useState("F2_A");
  const [goal, setGoal] = React.useState("F2_C");
  const [steps, setSteps] = React.useState<string[]>([]);
  const [pathIds, setPathIds] = React.useState<string[]>([]);
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState<string|null>(null);
  const [pickMode, setPickMode] = React.useState<null|"start"|"goal">(null);

  React.useEffect(()=>{
    (async()=>{ const g = await getGraph(); setGraph(g); if (g.floors?.[0]?.id) setViewFloor(g.floors[0].id); })();
  },[]);

  async function findRoute() {
    setBusy(true); setError(null);
    try { const res = await getRoute(start, goal); setPathIds(res.path); setSteps(res.steps); }
    catch(e:any){ setError(e?.message ?? "route failed"); setPathIds([]); setSteps([]); }
    finally { setBusy(false); }
  }

  async function onMapClick(p:{x:number;y:number}) {
    if (!pickMode) return;
    try {
      const ids = await nearest(p.x, p.y, viewFloor, 1);
      if (ids[0]) {
        if (pickMode === "start") setStart(ids[0]); else setGoal(ids[0]);
        setPickMode(null);
      }
    } catch(e:any) { setError(e?.message ?? "nearest failed"); }
  }

  return (
    <div style={{padding:12}}>
      <div style={{display:"flex", gap:8, alignItems:"center", marginBottom:12}}>
        <RouterStatus />
        <select value={viewFloor} onChange={e=>setViewFloor(e.target.value)}>
          {(graph.floors?.length?graph.floors:[{id:"F1",name:"F1"},{id:"F2",name:"F2"}]).map((f:any)=>(
            <option key={f.id ?? f.name} value={f.id ?? f.name}>{f.name ?? f.id}</option>
          ))}
        </select>
        <div style={{marginLeft:8}}>Start</div>
        <select value={start} onChange={e=>setStart(e.target.value)}>
          {Object.keys(graph.nodes).map(id=> <option key={id} value={id}>{id}</option>)}
        </select>
        <div>→</div>
        <div>Goal</div>
        <select value={goal} onChange={e=>setGoal(e.target.value)}>
          {Object.keys(graph.nodes).map(id=> <option key={id} value={id}>{id}</option>)}
        </select>
        <button onClick={findRoute} disabled={busy}>หาเส้นทาง</button>
        <button onClick={()=>setPickMode("start")} disabled={busy}>Set Start from Click</button>
        <button onClick={()=>setPickMode("goal")} disabled={busy}>Set Goal from Click</button>
        {pickMode && <span style={{color:"#2563eb"}}>คลิกบนแผนที่เพื่อเลือก {pickMode}</span>}
      </div>

      {error && <div style={{color:"#b91c1c", marginBottom:8}}>{error}</div>}

      <div style={{display:"grid", gridTemplateColumns:"1fr 320px", gap:12}}>
        <div>
          <PathCanvas
            nodes={graph.nodes}
            pathIds={pathIds}
            viewFloor={viewFloor}
            onClickXY={onMapClick}
          />
        </div>
        <aside style={{background:"#fff", border:"1px solid #e5e7eb", borderRadius:8, padding:12}}>
          <strong>ขั้นตอน</strong>
          <ol style={{marginTop:8}}>{steps.length ? steps.map((s,i)=><li key={i}>{s}</li>) : <li>-</li>}</ol>
        </aside>
      </div>
    </div>
  );
}