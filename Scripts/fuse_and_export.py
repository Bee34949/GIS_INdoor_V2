# =========================================
# 1) รวมเลเยอร์ใช้งาน (room/wall/door)
#    path: scripts/fuse_and_export.py
# =========================================
#!/usr/bin/env python3
import sys, argparse, subprocess, shutil, json
from pathlib import Path
import geopandas as gpd
import pandas as pd

DEFAULT_KEEP = ["room","wall","door"]

def load_gdf(p: Path) -> gpd.GeoDataFrame:
    return gpd.read_file(p) if p and p.exists() else gpd.GeoDataFrame(geometry=[])

def fuse_layers(base_gj: Path, rooms_gj: Path, out_gj: Path, keep_groups):
    base = load_gdf(base_gj)
    rooms = load_gdf(rooms_gj)
    frames = []
    if not rooms.empty:
        r = rooms.copy()
        r["group"] = "room"
        r["layer"] = "room"
        r["z"] = 10
        frames.append(r)
    if not base.empty:
        b = base.copy()
        b = b[b["group"].isin(keep_groups)]
        b["layer"] = b.get("layer", b["group"])
        b["z"] = b["group"].map({"wall":5,"door":20}).fillna(1).astype(int)
        frames.append(b)
    if not frames:
        print("[fuse] nothing to write"); return 1
    allg = pd.concat(frames, ignore_index=True)
    crs = rooms.crs or base.crs
    allg = gpd.GeoDataFrame(allg, crs=crs)
    out_gj.parent.mkdir(parents=True, exist_ok=True)
    allg.to_file(out_gj, driver="GeoJSON")
    print(f"[fuse] wrote -> {out_gj}  ({len(allg)} features; keep={keep_groups})")
    return 0

def make_mbtiles(geojson: Path, mbtiles: Path):
    tip = shutil.which("tippecanoe")
    if not tip:
        print("[mbtiles] tippecanoe not found; skip")
        return
    data = json.loads(geojson.read_text(encoding="utf-8"))
    rooms = {"type":"FeatureCollection","features":[f for f in data["features"] if f.get("properties",{}).get("group")=="room"]}
    feats = {"type":"FeatureCollection","features":[f for f in data["features"] if f.get("properties",{}).get("group")!="room"]}
    tmp = mbtiles.parent / "_tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp/"rooms.geojson").write_text(json.dumps(rooms, ensure_ascii=False), encoding="utf-8")
    (tmp/"features.geojson").write_text(json.dumps(feats, ensure_ascii=False), encoding="utf-8")
    cmd = [tip,"-o",str(mbtiles),"-Z","14","-z","22","-rg",
           "-L",f"name=rooms file={tmp/'rooms.geojson'}",
           "-L",f"name=features file={tmp/'features.geojson'}"]
    subprocess.run(cmd, check=True)
    for p in tmp.iterdir(): p.unlink()
    tmp.rmdir()
    print(f"[mbtiles] wrote -> {mbtiles}")

def parse():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="dist/all_floors.geojson")
    ap.add_argument("--rooms", required=True, help="dist/all_floors.rooms.geojson")
    ap.add_argument("--out", required=True, help="dist/indoor_all.geojson")
    ap.add_argument("--keep", nargs="*", default=DEFAULT_KEEP)
    ap.add_argument("--mbtiles", default=None)
    return ap.parse_args()

if __name__=="__main__":
    a = parse()
    rc = fuse_layers(Path(a.base), Path(a.rooms), Path(a.out), a.keep)
    if rc==0 and a.mbtiles:
        make_mbtiles(Path(a.out), Path(a.mbtiles))