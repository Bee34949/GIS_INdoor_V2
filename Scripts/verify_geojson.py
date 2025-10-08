"""
Quick stats & sample for a GeoJSON.
Usage:
  python scripts/verify_geojson.py dist/all.grouped.geojson --limit 5
"""
import json, argparse

def main(p, limit):
    with open(p,"r",encoding="utf-8") as f:
        gj = json.load(f)
    assert gj.get("type")=="FeatureCollection", "Not a FeatureCollection"
    counts={}
    for ft in gj.get("features", []):
        g = ft.get("properties",{}).get("group","unknown")
        counts[g]=counts.get(g,0)+1
    print("[verify] counts:", counts)
    print(f"[verify] sample {min(limit, len(gj['features']))} features:")
    for ft in gj["features"][:limit]:
        props = ft.get("properties",{})
        print(" -", props.get("id") or props.get("name") or props.get("title"), "| group:", props.get("group"))
    return 0

if __name__=="__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("geojson")
    ap.add_argument("--limit", type=int, default=5)
    args = ap.parse_args()
    raise SystemExit(main(args.geojson, args.limit))