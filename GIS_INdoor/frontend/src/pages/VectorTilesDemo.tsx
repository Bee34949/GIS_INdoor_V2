// frontend/src/pages/VectorTilesDemo.tsx  (แก้เฉพาะสไตล์และ center)
import React from "react";
import maplibregl, { Map } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { ROUTER_BASE, TILE_BASE, TILE_LON0, TILE_LAT0, pxToLonLat } from "@/config";

export default function VectorTilesDemo() {
  const ref = React.useRef<HTMLDivElement>(null);
  const [map, setMap] = React.useState<Map | null>(null);

  React.useEffect(() => {
    if (!ref.current) return;
    const m = new maplibregl.Map({
      container: ref.current,
      style: {
        version: 8,
        sources: {
          indoor: {
            type: "vector",
            // ถ้าใช้ Martin ให้เปลี่ยนเป็น `${TILE_BASE}/indoor/{z}/{x}/{y}.pbf`
            tiles: [`${TILE_BASE}/data/indoor/{z}/{x}/{y}.pbf`],
            minzoom: 14,
            maxzoom: 22
          } as any
        },
        glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
        layers: [
          { id: "walls", type: "line", source: "indoor", "source-layer": "walls",
            paint: { "line-color": "#111", "line-width": ["interpolate",["linear"],["zoom"],15,0.5,20,2] } },
          { id: "rooms", type: "fill", source: "indoor", "source-layer": "rooms",
            paint: { "fill-color": "#f5f5f4", "fill-outline-color": "#d4d4d4" } },
          { id: "doors", type: "circle", source: "indoor", "source-layer": "doors",
            paint: { "circle-radius": ["interpolate",["linear"],["zoom"],15,1.5,19,3], "circle-color": "#16a34a" } },
        ]
      } as any,
      center: [TILE_LON0, TILE_LAT0], // ให้มีจุดเริ่ม
      zoom: 18
    });
    m.addControl(new maplibregl.NavigationControl());
    setMap(m);
    return () => { m.remove(); };
  }, []);

  async function drawRoute() {
    if (!map) return;
    const r = await fetch(`${ROUTER_BASE}/route?start_id=F2_A&goal_id=F2_C`).then(r=>r.json());
    const g = await fetch(`${ROUTER_BASE}/graph`).then(r=>r.json());
    const coords = (r.path as string[]).map((id: string) => pxToLonLat(g.nodes[id].x, g.nodes[id].y));
    const fc = { type:"FeatureCollection", features:[{ type:"Feature", properties:{}, geometry:{ type:"LineString", coordinates: coords } }]};
    if (!map.getSource("route")) {
      map.addSource("route", { type:"geojson", data: fc } as any);
      map.addLayer({ id:"route-line", type:"line", source:"route",
        paint:{ "line-color":"#2563eb","line-width":3 }}, "doors");
    } else {
      (map.getSource("route") as any).setData(fc);
    }
    map.fitBounds(coords.reduce((b,[x,y])=>b.extend([x,y]), new maplibregl.LngLatBounds(coords[0], coords[0])), {padding: 40});
  }

  return (
    <div style={{display:"grid", gridTemplateRows:"48px 1fr", gap:8, height:"calc(100vh - 120px)"}}>
      <div style={{display:"flex", gap:8, alignItems:"center", padding:"8px"}}>
        <a href="/map/route-demo">กลับหน้าเดิม (SVG)</a>
        <button onClick={drawRoute}>วาดเส้นทางตัวอย่าง (F2_A ➜ F2_C)</button>
        <span>Tiles: {TILE_BASE}</span>
      </div>
      {/* ให้ความสูงแน่นอน ไม่ใช่ 100% */}
      <div ref={ref} style={{width:"100%", height:"70vh", minHeight:480, border:"1px solid #eee"}} />
    </div>
  );
}
