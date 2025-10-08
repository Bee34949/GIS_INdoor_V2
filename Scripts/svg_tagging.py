import sys, re
from xml.etree import ElementTree as ET

ROOM_FILLS   = { "#f0f0f0", "#ffffff", "white" }
WALL_STROKES = { "#000000", "black", "#333333" }
DOOR_STROKES = { "#ff9900", "#ffa500", "orange" }

SVGNS = "http://www.w3.org/2000/svg"

def guess_class(el):
    text = "".join((
        el.findtext(f"{{{SVGNS}}}title") or "",
        el.findtext(f"{{{SVGNS}}}desc") or "",
    )).lower()

    if "room" in text: return "room"
    if "wall" in text: return "wall"
    if "door" in text: return "door"

    style = (el.get("style") or "").lower()
    fill  = (el.get("fill") or "")
    stroke= (el.get("stroke") or "")
    sw    = (el.get("stroke-width") or "")

    mfill = re.search(r"fill:\s*([#a-z0-9]+)", style)
    mstrk = re.search(r"stroke:\s*([#a-z0-9]+)", style)
    if mfill: fill = mfill.group(1)
    if mstrk: stroke = mstrk.group(1)

    if fill.lower() in ROOM_FILLS and (stroke.lower() in WALL_STROKES or stroke == ""):
        return "room"
    if stroke.lower() in WALL_STROKES and (sw and float(re.sub("[^0-9.]", "", sw) or 0) >= 2.0):
        return "wall"
    if stroke.lower() in DOOR_STROKES:
        return "door"
    return None

def tag_svg(svg_in, svg_out):
    ET.register_namespace("", SVGNS)
    tree = ET.parse(svg_in)
    root = tree.getroot()
    ns = {"svg": SVGNS}
    q = ".//svg:path|.//svg:polygon|.//svg:polyline|.//svg:rect|.//svg:circle|.//svg:ellipse"
    changed = 0
    for el in root.findall(q, ns):
        cls = el.get("class") or ""
        if any(k in cls.split() for k in ("room","wall","door")):
            continue
        g = guess_class(el)
        if g:
            el.set("class", (cls + " " + g).strip() if cls else g)
            changed += 1
    tree.write(svg_out, encoding="utf-8", xml_declaration=True)
    print(f"[svg_tagging] wrote: {svg_out} (tagged {changed} elements)")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/svg_tagging.py input.svg output.tagged.svg")
        sys.exit(1)
    tag_svg(sys.argv[1], sys.argv[2])
