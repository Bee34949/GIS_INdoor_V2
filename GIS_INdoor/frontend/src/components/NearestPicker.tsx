import React from "react";
import { nearest } from "../services/router";

type Props = {
  onPick: (nodeId: string) => void;   // why: ส่งผลลัพธ์กลับหน้าแม่
  label: string;                      // “Set Start …” หรือ “Set Goal …”
  defaultFloor?: string;              // F1/F2...
};
export default function NearestPicker({ onPick, label, defaultFloor="F2" }: Props) {
  const [x, setX] = React.useState<number>(900);
  const [y, setY] = React.useState<number>(240);
  const [floor, setFloor] = React.useState<string>(defaultFloor);
  const [busy, setBusy] = React.useState(false);
  const [err, setErr] = React.useState<string | null>(null);

  async function doPick() {
    setBusy(true); setErr(null);
    try { const ids = await nearest(x, y, floor, 1); if (ids[0]) onPick(ids[0]); else setErr("ไม่พบโหนดใกล้เคียง"); }
    catch (e:any) { setErr(e?.message ?? "nearest failed"); }
    finally { setBusy(false); }
  }

  return (
    <div style={{display:"flex", gap:6, alignItems:"center", flexWrap:"wrap"}}>
      <span>{label}</span>
      <label>X:<input type="number" value={x} onChange={e=>setX(+e.target.value)} style={{width:90}}/></label>
      <label>Y:<input type="number" value={y} onChange={e=>setY(+e.target.value)} style={{width:90}}/></label>
      <select value={floor} onChange={e=>setFloor(e.target.value)}>
        <option value="F1">F1</option>
        <option value="F2">F2</option>
      </select>
      <button onClick={doPick} disabled={busy}>Pick</button>
      {err && <small style={{color:"#b91c1c"}}>{err}</small>}
      {/* NOTE: ถ้าคุณมีแผนที่จริง ให้แทน X/Y ด้วยค่าคลิกจากแผนที่ แล้วเรียก doPick() */}
    </div>
  );
}