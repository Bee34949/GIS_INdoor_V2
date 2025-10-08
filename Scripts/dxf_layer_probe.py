import sys, argparse, re
from pathlib import Path
import geopandas as gpd
import fiona
import yaml
from collections import Counter, defaultdict

PREFERRED_SUBLAYERS = ["entities","hatches","lines","polylines","lwpolylines","points"]

def list_files_from_dir(d):
    exts = (".dxf",".DXF",".dwg",".DWG",".gpkg",".GPKG")
    return [p for p in Path(d).iterdir() if p.suffix in exts and p.is_file()]

def read_any(path: Path) -> gpd.GeoDataFrame:
    if path.suffix.lower() in (".gpkg",):
        # read all layers concat
        layers = fiona.listlayers(str(path))
        frames = []
        for ly in layers:
            try:
                frames.append(gpd.read_file(str(path), layer=ly).assign(__src=ly))
            except Exception:
                pass
        if frames:
            import pandas as pd
            return pd.concat(frames, ignore_index=True)
        return gpd.GeoDataFrame()
    # DXF/DWG
    for sub in PREFERRED_SUBLAYERS:
        try:
            gdf = gpd.read_file(str(path), layer=sub)
            if len(gdf) > 0:
                gdf["__src"]=sub
                return gdf
        except Exception:
            continue
    try:
        return gpd.read_file(str(path))
    except Exception:
        return gpd.GeoDataFrame()

def normalize_layer_column(gdf):
    for cand in ["Layer","CADLayer","layer","LAYER"]:
        if cand in gdf.columns:
            if cand != "Layer":
                gdf = gdf.rename(columns={cand:"Layer"})
            return gdf
    gdf["Layer"] = ""
    return gdf

def guess_groups(layer_counts):
    # heuristic: เดา group เบื้องต้นจากชื่อเลเยอร์
    room_rx = re.compile(r"(?i)\b(ROOM|RM[_-]|AREA|SPACE|UNIT)\b")
    wall_rx = re.compile(r"(?i)\b(WALL|A[-_]WALL|PARTITION|STRUCT|COL)\b")
    door_rx = re.compile(r"(?i)\b(DOOR|A[-_]DOOR|OPENING)\b")
    groups = defaultdict(list)
    for ly, _ in layer_counts.most_common():
        if door_rx.search(ly): groups["door"].append(ly)
        elif wall_rx.search(ly): groups["wall"].append(ly)
        elif room_rx.search(ly): groups["room"].append(ly)
    # compile to regex list
    def to_patterns(names): 
        return [rf"(?i)^{re.escape(n)}$" for n in names[:12]]
    return {
        "room": to_patterns(groups["room"]),
        "wall": to_patterns(groups["wall"]),
        "door": to_patterns(groups["door"]),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", nargs="*", help="DXF/DWG/GPKG file paths")
    ap.add_argument("--dir", help="folder containing DXF/DWG/GPKG")
    ap.add_argument("--out", default="scripts/dxf_mapping.yaml")
    args = ap.parse_args()

    files = []
    if args.inputs: files.extend([Path(p) for p in args.inputs])
    if args.dir: files.extend(list_files_from_dir(args.dir))
    if not files:
        print("Provide --inputs or --dir with DXF/DWG/GPKG files"); sys.exit(1)

    layer_counts = Counter()
    by_file = {}
    sample_layers = defaultdict(set)

    for f in files:
        gdf = read_any(f)
        if gdf.empty:
            print(f"[warn] empty/unsupported: {f}")
            continue
        gdf = normalize_layer_column(gdf)
        cnt = Counter(gdf["Layer"].astype(str).fillna(""))
        layer_counts.update(cnt)
        by_file[f.name] = cnt.most_common(20)
        # collect top few per file for preview
        for ly, _ in by_file[f.name][:10]:
            sample_layers[ly].add(f.name)

    print("\n== Top layers (overall) ==")
    for ly, c in layer_counts.most_common(30):
        print(f"{c:6d}  {ly}")

    print("\n== Per-file (top 10) ==")
    for name, lst in by_file.items():
        print(f"[{name}]")
        for ly, c in lst[:10]:
            print(f"  {c:6d}  {ly}")

    # build mapping draft
    mapping = {
        "groups": guess_groups(layer_counts),
        "floor_from": {
            "filename_regex": r"(?i)floor[-_ ]?(\d+)|fl(\d+)|(\d+)",
            "layer_regex": r"(?i)\bFLOOR[-_ ]?(\d+)|\bF(\d+)\b"
        }
    }
    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    with open(outp, "w", encoding="utf-8") as f:
        yaml.safe_dump(mapping, f, sort_keys=False, allow_unicode=True)
    print(f"\n[wrote] mapping draft -> {outp}")

if __name__=="__main__":
    main()