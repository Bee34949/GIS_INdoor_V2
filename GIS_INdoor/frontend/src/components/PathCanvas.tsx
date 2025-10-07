import React from "react";

type NodeMap = Record<string, { x:number; y:number; floor_id:string }>;
type Props = {
  nodes: NodeMap;
  pathIds: string[];
  viewFloor: string;                 // F1/F2...
  onClickXY?: (p:{x:number;y:number}) => void; // why: ใช้สำหรับ nearest
};

export default function PathCanvas({nodes, pathIds, viewFloor, onClickXY}: Props) {
  const ref = React.useRef<HTMLCanvasElement>(null);
  React.useEffect(()=>{
    const c = ref.current!; const ctx = c.getContext("2d")!;
    const w = c.clientWidth, h = c.clientHeight;
    c.width = w * devicePixelRatio; c.height = h * devicePixelRatio;
    ctx.setTransform(devicePixelRatio,0,0,devicePixelRatio,0,0);
    ctx.clearRect(0,0,w,h);
    ctx.fillStyle="#fff"; ctx.fillRect(0,0,w,h);
    ctx.strokeStyle="#ddd"; ctx.strokeRect(0,0,w,h);

    // draw nodes (เฉพาะชั้นที่ดู)
    for (const [id,n] of Object.entries(nodes)) {
      if (n.floor_id !== viewFloor) continue;
      ctx.beginPath(); ctx.arc(n.x, n.y, 3, 0, Math.PI*2); ctx.fillStyle="#888"; ctx.fill();
    }
    // draw path polyline
    const pts = pathIds.map(id => nodes[id]).filter(n => n && n.floor_id===viewFloor);
    if (pts.length>0) {
      ctx.strokeStyle="#2563eb"; ctx.lineWidth=3;
      ctx.beginPath(); ctx.moveTo(pts[0].x, pts[0].y);
      for (let i=1;i<pts.length;i++) ctx.lineTo(pts[i].x, pts[i].y);
      ctx.stroke();
      // start/end
      ctx.fillStyle="#16a34a"; ctx.beginPath(); ctx.arc(pts[0].x, pts[0].y, 5, 0, Math.PI*2); ctx.fill();
      ctx.fillStyle="#dc2626"; ctx.beginPath(); ctx.arc(pts[pts.length-1].x, pts[pts.length-1].y, 5, 0, Math.PI*2); ctx.fill();
    }
  },[nodes, pathIds, viewFloor]);

  // map click -> pass raw canvas coords (ระบบคุณอาจมี scale/transform ของตัวเอง)
  function onClick(e: React.MouseEvent) {
    if (!onClickXY) return;
    const rect = (e.target as HTMLCanvasElement).getBoundingClientRect();
    const x = e.clientX - rect.left, y = e.clientY - rect.top;
    onClickXY({x, y});
  }

  return <canvas ref={ref} style={{width:"100%", height:"60vh", background:"#fff", border:"1px solid #e5e7eb", borderRadius:8}} onClick={onClick} />;
}