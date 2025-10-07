import React from "react";
import { routerAPI } from "./services/newRouterAdapter";
import { useRoutePlayer } from "./hooks/useRoutePlayer";

type Props = {
  // วาดเส้นทางด้วยระบบเดิมของคุณ
  onDrawPath: (nodeIds: string[]) => void;
  // อ่านพิกัดคลิกจากแผนที่จริงของคุณ
  onRequestMapClick?: (cb: (x:number, y:number)=>void) => void;
  defaultFloor?: string;
  nodeOptions: Array<{ id: string; label?: string }>;
};

export default function WireUpExample({ onDrawPath, onRequestMapClick, defaultFloor="F2", nodeOptions }: Props) {
  const [start, setStart] = React.useState(nodeOptions[0]?.id ?? "");
  const [goal, setGoal] = React.useState(nodeOptions[1]?.id ?? "");
  const [steps, setSteps] = React.useState<string[]>([]);
  const [busy, setBusy] = React.useState(false);
  const [follow, setFollow] = React.useState(true);
  const [speed, setSpeed] = React.useState(450);
  const [followZoom, setFollowZoom] = React.useState(90);
  const [lockZoom, setLockZoom] = React.useState(true);
  const [pathIds, setPathIds] = React.useState<string[]>([]);
  const [pick, setPick] = React.useState<null|"start"|"goal">(null);
  const [floor, setFloor] = React.useState(defaultFloor);

  const player = useRoutePlayer(pathIds.length, {
    speedMs: speed,
    onTick: (i) => {
      // why: จุดที่คุณจะสั่ง map follow จุดที่ i
      // e.g., map.followNode(pathIds[i], { zoom: follow? followZoom/100 : undefined })
    }
  });

  async function compute() {
    if (!start || !goal) return;
    setBusy(true);
    try {
      const res = await routerAPI.route(start, goal);
      setPathIds(res.path);
      setSteps(res.steps);
      onDrawPath(res.path);            // <<— วาดด้วยระบบเดิมของคุณ
      player.reset();
    } finally {
      setBusy(false);
    }
  }

  function enablePick(kind: "start"|"goal") {
    setPick(kind);
    onRequestMapClick?.(async (x,y) => {
      try {
        const [nid] = await routerAPI.nearest(x, y, floor, 1);
        if (nid) {
          if (kind==="start") setStart(nid); else setGoal(nid);
        }
      } finally { setPick(null); }
    });
  }

  return (
    <div style={{display:"grid", gap:8}}>
      {/* แถวคอนโทรลให้เหมือนรูปของคุณ */}
      <div style={{display:"flex", alignItems:"center", gap:8, flexWrap:"wrap"}}>
        <div>ชั้นที่ดู:</div>
        <select value={floor} onChange={e=>setFloor(e.target.value)}>
          <option value="F1">Floor 1</option>
          <option value="F2">Floor 2</option>
        </select>
        <button onClick={()=>{ setStart(""); setGoal(""); setPathIds([]); setSteps([]); }}>Clear</button>

        <div style={{marginLeft:8}}>เริ่มต้น</div>
        <select value={start} onChange={e=>setStart(e.target.value)}>
          {nodeOptions.map(n=><option key={n.id} value={n.id}>{n.label ?? n.id}</option>)}
        </select>

        <div>ปลายทาง</div>
        <select value={goal} onChange={e=>setGoal(e.target.value)}>
          {nodeOptions.map(n=><option key={n.id} value={n.id}>{n.label ?? n.id}</option>)}
        </select>

        <button disabled={busy} onClick={compute} style={{padding:"8px 12px"}}>หาเส้นทาง (ข้ามชั้น)</button>

        <button onClick={player.prev}>Prev</button>
        <button onClick={player.play}>Play</button>
        <button onClick={player.pause}>Pause</button>
        <button onClick={player.next}>Next</button>
        <button onClick={player.reset}>Reset</button>

        <label><input type="checkbox" checked={follow} onChange={e=>setFollow(e.target.checked)}/> Follow</label>
        <div>Speed(ms/step)</div><input type="number" value={speed} onChange={e=>setSpeed(+e.target.value)} style={{width:70}}/>
        <div>Follow Zoom(%)</div><input type="number" value={followZoom} onChange={e=>setFollowZoom(+e.target.value)} style={{width:70}}/>
        <label><input type="checkbox" checked={lockZoom} onChange={e=>setLockZoom(e.target.checked)}/> Lock Zoom (pan only)</label>

        <button onClick={()=>enablePick("start")}>Set Start from Click</button>
        <button onClick={()=>enablePick("goal")}>Set Goal from Click</button>
        {pick && <span style={{color:"#2563eb"}}>กำลังรอคลิกบนแผนที่เพื่อเลือก {pick}</span>}
      </div>

      {/* แพแนลขั้นตอน */}
      <div style={{background:"#fff", border:"1px solid #e5e7eb", borderRadius:8, padding:12}}>
        <strong>ขั้นตอน</strong>
        <ol style={{marginTop:8}}>{steps.length ? steps.map((s,i)=><li key={i}>{s}</li>) : <li>-</li>}</ol>
      </div>
    </div>
  );
}
