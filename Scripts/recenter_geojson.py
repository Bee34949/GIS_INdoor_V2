#!/usr/bin/env python3
import argparse, json, math
from pathlib import Path
def collect(coords, xs, ys):
    if isinstance(coords, list):
        if len(coords)>=2 and isinstance(coords[0], (int,float)) and isinstance(coords[1], (int,float)):
            xs.append(float(coords[0])); ys.append(float(coords[1]))
        for k in coords: collect(k, xs, ys)
def bbox(feats):
    xs,ys=[],[]
    for f in feats:
        g=f.get("geometry") or {}
        collect(g.get("coordinates"), xs, ys)
    if not xs: raise ValueError("no coords")
    return min(xs),min(ys),max(xs),max(ys)
def xform(coords, sx, sy, dx, dy):
    if isinstance(coords, list):
        if len(coords)>=2 and isinstance(coords[0], (int,float)) and isinstance(coords[1], (int,float)):
            return [coords[0]*sx+dx, coords[1]*sy+dy] + coords[2:]
        return [xform(c, sx, sy, dx, dy) for c in coords]
    return coords
def main(inp, outp, lon, lat, meters, scale):
    data = json.loads(Path(inp).read_text(encoding="utf-8"))
    feats = data.get("features", [])
    minx,miny,maxx,maxy = bbox(feats)
    cx, cy = (minx+maxx)/2.0, (miny+maxy)/2.0
    if scale is not None:
        sx = sy = float(scale)
    elif meters:
        sy = 1.0/111320.0
        sx = 1.0/(111320.0*max(math.cos(math.radians(lat)), 1e-8))
    else:
        sx = sy = 1.0
    dx = lon - cx*sx
    dy = lat - cy*sy
    for f in feats:
        g=f.get("geometry")
        if g and g.get("coordinates") is not None:
            g["coordinates"] = xform(g["coordinates"], sx, sy, dx, dy)
    Path(outp).write_text(json.dumps({"type":"FeatureCollection","features":feats}, ensure_ascii=False), encoding="utf-8")
    print(f"[recenter] in={inp}")
    print(f"[recenter] bbox_in=[{minx:.3f},{miny:.3f},{maxx:.3f},{maxy:.3f}]")
    print(f"[recenter] sx={sx:.8f} sy={sy:.8f} meters={meters}")
    print(f"[recenter] dx={dx:.8f} dy={dy:.8f}")
    print(f"[recenter] out={outp}")
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", dest="out", required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--meters", action="store_true")
    ap.add_argument("--scale", type=float, default=None)
    a=ap.parse_args()
    main(a.inp, a.out, a.lon, a.lat, a.meters, a.scale)
