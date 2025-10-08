import sys, re, argparse
from pathlib import Path
import geopandas as gpd
import pandas as pd
import fiona
import yaml

PREFERRED_SUBLAYERS = ["entities","hatches","lines","polylines","lwpolylines","points"]

def read_any(path: Path):
    if path.suffix.lower()==".gpkg":
        frames=[]; 
        for ly in fiona.listlayers(str(path)):
            try: frames.append(gpd.read_file(str(path), layer=ly).assign(__src=ly))
            except Exception: pass
        return pd.concat(frames, ignore_index=True) if frames else gpd.GeoDataFrame()
    for sub in PREFERRED_SUBLAYERS:
        try:
            gdf = gpd.read_file(str(path), layer=sub)
            if len(gdf)>0: return gdf.assign(__src=sub)
        except Exception: continue
    try: return gpd.read_file(str(path))
    except Exception: return gpd.GeoDataFrame()

def norm_layer(gdf):
    for cand in ["Layer","CADLayer","layer","LAYER"]:
        if cand in gdf.columns:
            if cand!="Layer": gdf=gdf.rename(columns={cand:"Layer"})
            break
    else:
        gdf["Layer"]=""
    return gdf

def explode_clean(gdf):
    if gdf.empty: return gdf
    gdf = gdf[gdf.geometry.notnull() & (~gdf.geometry.is_empty)].copy()
    gdf = gdf.explode(index_parts=False).reset_index(drop=True)
    gdf = gdf[gdf.geometry.is_valid].copy()
    if gdf.crs is None:
        gdf.set_crs(4326, allow_override=True, inplace=True)
    return gdf

def load_mapping(yaml_path: Path):
    if not yaml_path.exists():
        return {
            "groups": {
                "room":[r"(?i)\bROOM\b", r"(?i)RM[_-]"],
                "wall":[r"(?i)\bWALL\b", r"(?i)A[-_]WALL\b", r"(?i)PARTITION"],
                "door":[r"(?i)\bDOOR\b", r"(?i)A[-_]DOOR\b", r"(?i)OPENING"]
            },
            "floor_from":{
                "filename_regex": r"(?i)floor[-_ ]?(\d+)|fl(\d+)|(\d+)",
                "layer_regex": r"(?i)\bFLOOR[-_ ]?(\d+)|\bF(\d+)\b"
            }
        }
    return yaml.safe_load(open(yaml_path,"r",encoding="utf-8"))

def pick_group(layer, mapping):
    s = (layer or "").strip()
    for g, pats in mapping["groups"].items():
        for p in (pats or []):
            if re.search(p, s):
                return g
    return "unknown"

def pick_floor(stem, layer, mapping):
    rx1 = mapping.get("floor_from",{}).get("filename_regex")
    if rx1:
        m=re.search(rx1, stem or "")
        if m:
            for g in m.groups():
                if g: return g
    rx2 = mapping.get("floor_from",{}).get("layer_regex")
    if rx2:
        m=re.search(rx2, layer or "")
        if m:
            for g in m.groups():
                if g: return g
    return ""

def run(inputs, gpkg, outdir: Path, mapping_yaml: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    mapping = load_mapping(mapping_yaml)

    out_files=[]
    if gpkg:
        layers=fiona.listlayers(str(gpkg))
        for ly in layers:
            gdf=gpd.read_file(str(gpkg), layer=ly)
            gdf=norm_layer(gdf); gdf=explode_clean(gdf)
            if gdf.empty: continue
            gdf["group"]=gdf["Layer"].apply(lambda x: pick_group(x, mapping))
            gdf["floor"]=gdf["Layer"].apply(lambda x: pick_floor(ly, x, mapping)) or ly
            outp=outdir/f"{ly}.grouped.geojson"
            gdf.to_file(outp, driver="GeoJSON"); out_files.append(outp)
            print(f"[write] {outp} ({len(gdf)})")
    else:
        for p in inputs:
            p=Path(p)
            gdf=read_any(p); gdf=norm_layer(gdf); gdf=explode_clean(gdf)
            if gdf.empty: 
                print(f"[warn] empty: {p}"); 
                continue
            gdf["group"]=gdf["Layer"].apply(lambda x: pick_group(x, mapping))
            gdf["floor"]=gdf["Layer"].apply(lambda x: pick_floor(p.stem, x, mapping))
            outp=outdir/f"{p.stem}.grouped.geojson"
            gdf.to_file(outp, driver="GeoJSON"); out_files.append(outp)
            print(f"[write] {outp} ({len(gdf)})")

    if out_files:
        frames=[gpd.read_file(f) for f in out_files]
        import pandas as pd
        allg=pd.concat(frames, ignore_index=True)
        merged=outdir/"all_floors.geojson"
        allg.to_file(merged, driver="GeoJSON")
        print(f"[merged] {merged} ({len(allg)})")
    else:
        print("[warn] nothing written.")

def parse():
    ap=argparse.ArgumentParser()
    ap.add_argument("--inputs", nargs="*", help="DXF/DWG files")
    ap.add_argument("--gpkg", help="GeoPackage file")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--mapping", default="scripts/dxf_mapping.yaml")
    a=ap.parse_args()
    if not a.inputs and not a.gpkg:
        ap.error("Provide --inputs (DXF/DWG...) or --gpkg")
    return a

if __name__=="__main__":
    a=parse(); 
    run([Path(p) for p in (a.inputs or [])], Path(a.gpkg) if a.gpkg else None, Path(a.outdir), Path(a.mapping))