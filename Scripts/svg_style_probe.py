import sys, re, json
from pathlib import Path
from collections import Counter, defaultdict
from xml.etree import ElementTree as ET

try:
    import yaml  # ทำไฟล์ config.yaml
except Exception:
    yaml = None

SVGNS = "http://www.w3.org/2000/svg"
NS = {"svg": SVGNS}

# เหตุผล: สี/สไตล์ที่มักใช้วาดผนัง/ประตู/ห้องใน floorplan ทั่วไป (ใช้เป็น prior)
DEFAULT_PRIOR = {
    "room_fills":   {"#ffffff", "#f0f0f0", "white"},
    "wall_strokes": {"#000000", "#333333", "black"},
    "door_strokes": {"#ffa500", "#ff9900", "orange"},
}
THAI_HINTS = {
    "room": ["ห้อง","office","room","lab","class","rm"],
    "wall": ["ผนัง","กำแพง","wall","partition","struct"],
    "door": ["ประตู","เข้า","ทางเข้า","door","gate","entry","portal"],
}

def norm_hex(s: str) -> str:
    s = (s or "").strip().lower()
    if s.startswith("#") and len(s) in (4,7):
        return s
    return s  # คงค่าเดิมไว้ เช่น "black", "none"

def extract_style(el):
    style = (el.get("style") or "")
    fill = el.get("fill")
    stroke = el.get("stroke")
    mfill = re.search(r"fill\s*:\s*([^;]+)", style, flags=re.I)
    mstrk = re.search(r"stroke\s*:\s*([^;]+)", style, flags=re.I)
    if mfill: fill = mfill.group(1)
    if mstrk: stroke = mstrk.group(1)
    return norm_hex(fill), norm_hex(stroke)

def scan_svg(svg_path: Path, counters):
    try:
        ET.register_namespace("", SVGNS)
        tree = ET.parse(svg_path)
        root = tree.getroot()
    except Exception as e:
        print(f"[WARN] parse fail {svg_path}: {e}")
        return

    geom_q = ".//svg:path|.//svg:polygon|.//svg:polyline|.//svg:rect|.//svg:circle|.//svg:ellipse"
    for el in root.findall(geom_q, NS):
        fill, stroke = extract_style(el)
        if fill: counters["fill"][fill] += 1
        if stroke and stroke != "none": counters["stroke"][stroke] += 1

        # เก็บคำใบ้จาก class/id/title/desc
        cls = (el.get("class") or "").lower()
        _id = (el.get("id") or "").lower()
        title = el.findtext(f"{{{SVGNS}}}title") or ""
        desc = el.findtext(f"{{{SVGNS}}}desc") or ""
        text = " ".join([cls, _id, title.lower(), desc.lower()])
        for token in re.findall(r"[A-Za-zก-๙0-9]+", text):
            counters["tokens"][token] += 1

def suggest_config(counters):
    fills = [c for c, _ in counters["fill"].most_common()]
    strokes = [c for c, _ in counters["stroke"].most_common()]
    tokens = [t for t, _ in counters["tokens"].most_common(200)]

    # heuristic: walls มักเด่นใน stroke ดำ/เทา, doors มัก stroke สีส้ม/สด, rooms มัก fill อ่อน
    def pick_room_fills():
        base = list(DEFAULT_PRIOR["room_fills"])
        for f in fills[:10]:
            if re.fullmatch(r"#f{2,6}|#e\w{5}", f) or f in ("white",):
                base.append(f)
        return sorted(set(base), key=lambda x: (x.startswith("#")==False, x))[:8]

    def pick_wall_strokes():
        base = list(DEFAULT_PRIOR["wall_strokes"])
        for s in strokes[:10]:
            if s in ("black","#000","#000000","#333","#333333"): base.append(s)
        return sorted(set(base))[:8]

    def pick_door_strokes():
        base = list(DEFAULT_PRIOR["door_strokes"])
        for s in strokes[:15]:
            if re.match(r"#ff9|#ffa|#ff8|#f90|#fa0", s): base.append(s)
            if s in ("orange","goldenrod"): base.append(s)
        return sorted(set(base))[:8]

    def pick_keywords():
        def top_like(keys):
            return [t for t in tokens if any(k in t for k in keys)][:12]
        return {
            "room": sorted(set(THAI_HINTS["room"] + top_like(["room","office","lab","class","ห้อง"])) )[:12],
            "wall": sorted(set(THAI_HINTS["wall"] + top_like(["wall","ผนัง","กำแพง","partition","struct"])) )[:12],
            "door": sorted(set(THAI_HINTS["door"] + top_like(["door","gate","entry","portal","ประตู","เข้า"])) )[:12],
        }

    cfg = {
        "keywords": pick_keywords(),
        "colors": {
            "room_fills": pick_room_fills(),
            "wall_strokes": pick_wall_strokes(),
            "door_strokes": pick_door_strokes(),
        },
    }
    return cfg

def load_existing_cfg(cfg_path: Path):
    if not yaml or not cfg_path.exists():
        return {}
    try:
        return yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}

def merge_preserve_user(base: dict, user: dict) -> dict:
    out = base.copy()
    for k in ("keywords","colors"):
        out[k] = out.get(k, {})
        user_k = user.get(k, {})
        for kk, vv in out[k].items():
            # ถ้ามีของผู้ใช้อยู่แล้ว ให้รวมและคงลำดับผู้ใช้ไว้หน้า
            uv = user_k.get(kk)
            if uv:
                out[k][kk] = list(dict.fromkeys(list(uv) + list(vv)))
    return out

def main(root_dir: str, cfg_out: str):
    root = Path(root_dir)
    cfg_path = Path(cfg_out)
    counters = {"fill": Counter(), "stroke": Counter(), "tokens": Counter()}

    svgs = list(root.rglob("*.svg"))
    if not svgs:
        print(f"[ERROR] ไม่พบไฟล์ SVG ใน {root.resolve()}")
        return 2

    for p in svgs:
        scan_svg(p, counters)

    cfg = suggest_config(counters)
    user_cfg = load_existing_cfg(cfg_path)
    final_cfg = merge_preserve_user(cfg, user_cfg)

    preview = {
        "top_fills": counters["fill"].most_common(8),
        "top_strokes": counters["stroke"].most_common(8),
        "top_tokens": counters["tokens"].most_common(12),
    }
    print("[probe] summary:", json.dumps(preview, ensure_ascii=False, indent=2))

    if yaml:
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        cfg_path.write_text(yaml.safe_dump(final_cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")
        print(f"[probe] wrote config -> {cfg_path}")
    else:
        print("[WARN] ไม่ได้ติดตั้ง PyYAML จึงไม่เขียนไฟล์ config.yaml ให้ (pip install pyyaml)")

    print("[next] แนะนำรัน: make tiles-nofilter group")
    return 0

if __name__ == "__main__":
    # ใช้: python scripts/svg_style_probe.py <dir_with_svgs> scripts/config.yaml
    if len(sys.argv) < 3:
        print("Usage: python scripts/svg_style_probe.py <svg_root_dir> scripts/config.yaml")
        sys.exit(1)
    sys.exit(main(sys.argv[1], sys.argv[2]))