from __future__ import annotations
import os, json
from pathlib import Path
from typing import Dict, List, Tuple
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from fastapi.responses import JSONResponse
APP = FastAPI(title="Indoor Router (new)")

GRAPH_PATH = Path(os.getenv("INDOOR_GRAPH_PATH", "out_json/graph.json"))

class Node(BaseModel):
    id: str; x: float; y: float; floor_id: str; type: str; name: str | None = None
class Edge(BaseModel):
    id: str; u: str; v: str; weight: float; kind: str; oneway: bool = False
class Graph(BaseModel):
    floors: List[dict]
    nodes: Dict[str, Node]
    edges: Dict[str, Edge]

def load_graph() -> Graph:
    if not GRAPH_PATH.exists():
        raise FileNotFoundError(f"graph not found: {GRAPH_PATH}")
    data = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    nodes = {k: Node(**v) for k, v in data["nodes"].items()}
    edges = {k: Edge(**v) for k, v in data["edges"].items()}
    return Graph(floors=data["floors"], nodes=nodes, edges=edges)

G: Graph | None = None

def build_adj(g: Graph) -> Dict[str, List[Tuple[str, float]]]:
    adj: Dict[str, List[Tuple[str, float]]] = {nid: [] for nid in g.nodes.keys()}
    for e in g.edges.values():
        adj[e.u].append((e.v, e.weight))
        if not e.oneway:
            adj[e.v].append((e.u, e.weight))
    return adj

def heuristic(a: Node, b: Node) -> float:
    import math
    penalty = 400.0 if a.floor_id != b.floor_id else 0.0
    return math.hypot(a.x - b.x, a.y - b.y) + penalty

def astar(g: Graph, start: str, goal: str) -> List[str] | None:
    if start not in g.nodes or goal not in g.nodes:
        return None
    adj = build_adj(g); nodes = g.nodes
    open_set = {start}; came: Dict[str, str | None] = {}; gscore = {start: 0.0}
    fscore = {start: heuristic(nodes[start], nodes[goal])}

    def best() -> str | None:
        return min(open_set, key=lambda n: fscore.get(n, float("inf"))) if open_set else None

    while open_set:
        cur = best()
        if cur == goal:
            break
        open_set.remove(cur)  # type: ignore[arg-type]
        for nxt, w in adj[cur]:  # type: ignore[index]
            tent = gscore[cur] + w
            if tent < gscore.get(nxt, float("inf")):
                came[nxt] = cur
                gscore[nxt] = tent
                fscore[nxt] = tent + heuristic(nodes[nxt], nodes[goal])
                open_set.add(nxt)

    if goal not in came and start != goal:
        return None
    path = [goal]; c = goal
    while c != start:
        c = came[c]  # type: ignore[index]
        if c is None: return None
        path.append(c)
    path.reverse()
    return path

class RouteResponse(BaseModel):
    path: List[str]
    steps: List[str]

@APP.on_event("startup")
def _startup():
    global G
    G = load_graph()

@APP.get("/healthz")
def healthz(): return {"status": "ok", "graph_loaded": bool(G)}

@APP.get("/nearest")
def nearest(x: float, y: float, floor_id: str, k: int = 1):
    if not G: raise HTTPException(503, "graph not loaded")
    cand = [n for n in G.nodes.values() if n.floor_id == floor_id]
    if not cand: raise HTTPException(404, "no nodes on floor")
    cand.sort(key=lambda n: (n.x-x)**2 + (n.y-y)**2)
    return [c.id for c in cand[:k]]

@APP.get("/route")
def route(start_id: str = Query(...), goal_id: str = Query(...)):
    if not G: raise HTTPException(503, "graph not loaded")
    path = astar(G, start_id, goal_id)
    if not path: raise HTTPException(404, "no path")

    def floor_name_for(nfloor: str) -> str:
        for f in G.floors:
            if f.get("id") == nfloor:
                return f.get("name", nfloor)
        return nfloor

    steps = [to_step_fmt(G.nodes[nid], floor_name_for(G.nodes[nid].floor_id), i)
             for i, nid in enumerate(path)]

    return JSONResponse(
        content={"path": path, "steps": steps},
        media_type="application/json; charset=utf-8",
    )

def to_step_fmt(n, floor_name: str, idx: int) -> str:
    # why: ตัดช่องว่าง/อักขระเกิน ป้องกัน mojibake จากการพิมพ์
    label = (n.name or n.id).strip()
    fname = (floor_name or n.floor_id).strip()
    prefix = "เริ่มที่" if idx == 0 else "ไปยัง"
    return f"{prefix}: {fname} : {label}"




def main():
    import uvicorn
    port = int(os.getenv("INDOOR_ROUTER_PORT", "8100"))
    uvicorn.run("backend_ext.app:APP", host="0.0.0.0", port=port, reload=True)

if __name__ == "__main__":
    main()

@APP.get("/graph")
def graph_summary():
    if G is None:
        raise HTTPException(503, "graph not loaded")
    # why: FE ต้องใช้พิกัดเพื่อวาดเส้นทาง
    nodes = {k: {"x": v.x, "y": v.y, "floor_id": v.floor_id, "name": v.name} for k, v in G.nodes.items()}
    floors = G.floors
    return {"nodes": nodes, "floors": floors}


