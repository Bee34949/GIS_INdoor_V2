from __future__ import annotations
import asyncio, json, math, os, time, random, pathlib
from typing import Dict, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

ANCHOR_LON = float(os.getenv("ANCHOR_LON", "100.531"))
ANCHOR_LAT = float(os.getenv("ANCHOR_LAT", "13.736"))
ENABLE_SIM = os.getenv("ENABLE_SIM", "1") == "1"

app = FastAPI(title="Indoor RTLS")

class LocalMeters(BaseModel):
    x: float; y: float
    floor: Optional[str] = None
    accuracy_m: Optional[float] = None
    ts: Optional[float] = None

class Wgs84Point(BaseModel):
    lon: float; lat: float
    floor: Optional[str] = None
    accuracy_m: Optional[float] = None
    ts: Optional[float] = None

class PosUpsert(BaseModel):
    deviceId: str = Field(..., examples=["dev-01"])
    wgs84: Optional[Wgs84Point] = None
    local: Optional[LocalMeters] = None

class Hub:
    def __init__(self): self.clients: List[WebSocket] = []
    async def connect(self, ws: WebSocket): await ws.accept(); self.clients.append(ws)
    def disconnect(self, ws: WebSocket): 
        if ws in self.clients: self.clients.remove(ws)
    async def broadcast(self, data: dict):
        for ws in list(self.clients):
            try: await ws.send_text(json.dumps(data))
            except Exception: self.disconnect(ws)

hub = Hub()
latest: Dict[str, Wgs84Point] = {}

def meters_to_deg(dx_m: float, dy_m: float, lat_ref: float):
    dlat = dy_m / 111_320.0
    dlon = dx_m / (111_320.0 * max(math.cos(math.radians(lat_ref)), 1e-8))
    return dlon, dlat

@app.post("/api/pos")
async def upsert_position(payload: PosUpsert):
    if payload.local:
        dlon, dlat = meters_to_deg(payload.local.x, payload.local.y, ANCHOR_LAT)
        wgs = Wgs84Point(
            lon=ANCHOR_LON + dlon, lat=ANCHOR_LAT + dlat,
            floor=payload.local.floor, accuracy_m=payload.local.accuracy_m,
            ts=payload.local.ts or time.time(),
        )
    elif payload.wgs84:
        wgs = payload.wgs84; wgs.ts = wgs.ts or time.time()
    else:
        return JSONResponse({"error":"need wgs84 or local"}, status_code=400)

    latest[payload.deviceId] = wgs
    msg = {"type":"pos","deviceId":payload.deviceId,"wgs84":wgs.model_dump()}
    await hub.broadcast(msg)
    return {"ok":True}

@app.websocket("/ws/pos")
async def ws_pos(ws: WebSocket):
    await hub.connect(ws)
    for dev, p in latest.items():
        await ws.send_text(json.dumps({"type":"pos","deviceId":dev,"wgs84":p.model_dump()}))
    try:
        while True: await ws.receive_text()
    except WebSocketDisconnect:
        hub.disconnect(ws)

def _bbox_from(path: pathlib.Path):
    try:
        gj = json.loads(path.read_text(encoding="utf-8"))
        xs, ys = [], []
        def walk(c):
            if isinstance(c, list):
                if len(c)>=2 and isinstance(c[0], (int,float)) and isinstance(c[1], (int,float)):
                    xs.append(c[0]); ys.append(c[1])
                for k in c: walk(k)
        for f in gj.get("features",[]): 
            g=f.get("geometry") or {}
            walk(g.get("coordinates"))
        return (min(xs),min(ys),max(xs),max(ys)) if xs else None
    except Exception:
        return None

async def simulator(device_id="sim-01", floor="1"):
    bbox = _bbox_from(pathlib.Path("/app/dist/indoor_all.recentered.geojson")) or (ANCHOR_LON-0.0005,ANCHOR_LAT-0.0005,ANCHOR_LON+0.0005,ANCHOR_LAT+0.0005)
    minx,miny,maxx,maxy = bbox
    x,y = (minx+maxx)/2,(miny+maxy)/2
    while True:
        x += random.uniform(-1,1)*1e-5; y += random.uniform(-1,1)*1e-5
        x = max(minx, min(maxx, x)); y = max(miny, min(maxy, y))
        await upsert_position(PosUpsert(deviceId=device_id, wgs84=Wgs84Point(lon=x, lat=y, floor=floor)))
        await asyncio.sleep(0.5)

@app.on_event("startup")
async def _start():
    # mount dist if exists (optional)
    try: pathlib.Path("/app/dist").mkdir(exist_ok=True, parents=True)
    except Exception: pass
    if ENABLE_SIM:
        asyncio.create_task(simulator("sim-01","1"))
        asyncio.create_task(simulator("sim-02","2"))