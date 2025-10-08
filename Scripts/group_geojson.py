"""
Group GeoJSON features into room/wall/door/unknown.
- Heuristics: class/id, keywords (name/title/label/desc), fill/stroke, style.
- Configurable via YAML: keywords/colors.
Usage:
  python scripts/group_geojson.py in.geojson out.geojson [--config scripts/config.yaml] [--stats]
"""
import json, re, sys, argparse
from pathlib import Path

try:
    import yaml  # why: allow external config overrides
except Exception:
    yaml = None

def _norm(s): return str(s or "").strip().lower()

def _load_config(pth):
    base = {
        "keywords": {
            "room": ["room","rm","office","lab","class","bath","bed","living"],
            "wall": ["wall","partition","colour","color","struct"],
            "door": ["door","entry","gate","portal"],
        },
        "colors": {
            "room_fills": ["#f0f0f0","#ffffff","white"],
            "wall_strokes": ["#000000","black","#333333"],
            "door_strokes": ["#ff9900","#ffa500","orange"],
        },
    }
    if not pth: return base
    if not yaml:
        print("[WARN] PyYAML not installed; ignoring config file", file=sys.stderr)
        return base
    with open(pth, "r", encoding="utf-8") as f:
        user = yaml.safe_load(f) or {}
    # shallow merge
    for k in ("keywords","colors"):
        if k in user and isinstance(user[k], dict):
            base[k].update({kk: list(vv) for kk, vv in user[k].items()})
    return base

def _compile_keywords(cfg):
    def rx(words): return re.compile(r"\b(" + "|".join(map(re.escape, words)) + r")\b", re.I)
    kw = cfg["keywords"]
    return {
        "room": rx(kw["room"]),
        "wall": rx(kw["wall"]),
        "door": rx(kw["door"]),
    }

def _colors(cfg):
    c = cfg["colors"]
    return (
        set(map(str.lower, c["room_fills"])),
        set(map(str.lower, c["wall_strokes"])),
        set(map(str.lower, c["door_strokes"])),
    )

def _pick_class(props, kw_rx, room_fills, wall_strokes, door_strokes):
    c = _norm(props.get("class")); i = _norm(props.get("id"))
    for token in (c, i):
        if "room" in token: return "room"
        if "wall" in token: return "wall"
        if "door" in token: return "door"

    text = " ".join(_norm(props.get(k)) for k in ("name","title","label","desc"))
    if kw_rx["room"].search(text): return "room"
    if kw_rx["wall"].search(text): return "wall"
    if kw_rx["door"].search(text): return "door"

    style = _norm(props.get("style"))
    fill  = _norm(props.get("fill"))
    stroke= _norm(props.get("stroke"))
    mfill = re.search(r"fill:\s*([#a-z0-9]+)", style)
    mstrk = re.search(r"stroke:\s*([#a-z0-9]+)", style)
    if mfill: fill = mfill.group(1).lower()
    if mstrk: stroke = mstrk.group(1).lower()

    if fill in room_fills: return "room"
    if stroke in wall_strokes: return "wall"
    if stroke in door_strokes: return "door"
    return "unknown"

def group(in_path, out_path, config_path=None, show_stats=False):
    cfg = _load_config(config_path)
    kw_rx = _compile_keywords(cfg)
    room_fills, wall_strokes, door_strokes = _colors(cfg)

    with open(in_path, "r", encoding="utf-8") as f:
        gj = json.load(f)
    if gj.get("type") != "FeatureCollection":
        raise ValueError("Input must be FeatureCollection")

    counts = {"room":0,"wall":0,"door":0,"unknown":0}
    for ft in gj.get("features", []):
        props = ft.setdefault("properties", {})
        cls = _pick_class(props, kw_rx, room_fills, wall_strokes, door_strokes)
        props["group"] = cls
        props.setdefault("layer", cls)
        counts[cls] += 1

    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(gj, f, ensure_ascii=False)
        print(f"[group_geojson] wrote: {out_path}")
    if show_stats:
        print(f"[group_geojson] counts = {counts}")
    return counts

def _parse():
    ap = argparse.ArgumentParser()
    ap.add_argument("in_geojson")
    ap.add_argument("out_geojson")
    ap.add_argument("--config", default=None)
    ap.add_argument("--stats", action="store_true")
    return ap.parse_args()

if __name__ == "__main__":
    args = _parse()
    group(args.in_geojson, args.out_geojson, args.config, args.stats)
