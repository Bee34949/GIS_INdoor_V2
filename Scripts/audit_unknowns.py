# ==============================
# path: scripts/audit_unknowns.py
# purpose: สรุป unknown แยกตาม Layer + ชนิด geometry
# run:
#   python scripts/audit_unknowns.py dist/all_floors.geojson
# ==============================
#!/usr/bin/env python3
import sys, json
from collections import Counter, defaultdict

def main(p):
    with open(p,"r",encoding="utf-8") as f:
        gj=json.load(f)
    if gj.get("type")!="FeatureCollection":
        print("not a FeatureCollection"); return 2
    by_layer=Counter()
    by_gtype=Counter()
    samples=defaultdict(int)
    for ft in gj.get("features",[]):
        props=ft.get("properties",{}) or {}
        if props.get("group")!="unknown": 
            continue
        ly = props.get("Layer") or "(no Layer)"
        by_layer[ly]+=1
        g=ft.get("geometry") or {}
        by_gtype[g.get("type","(no geom)")] += 1
        if samples[ly]<2:
            samples[ly]+=1
    print("== unknown by Layer ==")
    for ly,c in by_layer.most_common(30):
        print(f"{c:6d}  {ly}")
    print("\n== unknown by geometry type ==")
    for gt,c in by_gtype.most_common():
        print(f"{c:6d}  {gt}")
    return 0

if __name__=="__main__":
    if len(sys.argv)<2:
        print("Usage: python scripts/audit_unknowns.py dist/all_floors.geojson")
        sys.exit(1)
    sys.exit(main(sys.argv[1]))


