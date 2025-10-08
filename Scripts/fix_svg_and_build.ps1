set -euo pipefail

SVG_DIR="tiles/src"
OUT_DIR="dist"
CONFIG="scripts/config.yaml"

# --- parse args ---
while getopts "s:o:c:" opt; do
  case "$opt" in
    s) SVG_DIR="$OPTARG" ;;
    o) OUT_DIR="$OPTARG" ;;
    c) CONFIG="$OPTARG" ;;
  esac
done

echo "[cfg] SVG_DIR=$SVG_DIR"
echo "[cfg] OUT_DIR=$OUT_DIR"
echo "[cfg] CONFIG=$CONFIG"

# --- require commands ---
need() { command -v "$1" >/dev/null 2>&1 || { echo "Error: '$1' not found in PATH"; exit 1; }; }
need python
need mapshaper

# Inkscape detection (linux/mac: inkscape; windows git-bash: inkscape.exe/.com)
INKSCAPE_BIN="$(command -v inkscape || true)"
if [[ -z "${INKSCAPE_BIN}" ]]; then
  for p in "/c/Program Files/Inkscape/bin/inkscape.com" "/c/Program Files/Inkscape/bin/inkscape.exe" ; do
    if [[ -x "$p" ]]; then INKSCAPE_BIN="$p"; break; fi
  done
fi
if [[ -z "${INKSCAPE_BIN}" ]]; then
  echo "Error: Inkscape not found. Install Inkscape 1.2+ and ensure 'inkscape' is in PATH."
  exit 1
fi
echo "[tool] inkscape=$INKSCAPE_BIN"

mkdir -p "$OUT_DIR"
FIXED_DIR="$OUT_DIR/fixed_svg"
mkdir -p "$FIXED_DIR"

# --- quick inspect (optional) ---
python - "$SVG_DIR" <<'PY'
import sys, json
from pathlib import Path
from xml.etree import ElementTree as ET
SVGNS="http://www.w3.org/2000/svg"; NS={"svg":SVGNS}
def count_elems(p):
    try:
        root=ET.parse(p).getroot()
    except Exception as e:
        return {"file":str(p),"error":str(e)}
    q=".//svg:path|.//svg:rect|.//svg:circle|.//svg:ellipse|.//svg:polygon|.//svg:polyline"
    return {
        "file": str(p),
        "geom": len(root.findall(q,NS)),
        "use":  len(root.findall(".//svg:use",NS)),
        "image":len(root.findall(".//svg:image",NS)),
        "text": len(root.findall(".//svg:text",NS)),
        "defs": len(root.findall(".//svg:defs",NS)),
    }
svgdir = Path(sys.argv[1])
items=[count_elems(p) for p in sorted(svgdir.glob("*.svg"))]
print(json.dumps(items, ensure_ascii=False, indent=2))
PY

# --- 1) Flatten each SVG to plain/path via Inkscape actions ---
shopt -s nullglob
SVGS=("$SVG_DIR"/*.svg)
if (( ${#SVGS[@]} == 0 )); then
  echo "Error: no SVGs in $SVG_DIR"; exit 2
fi

for svg in "${SVGS[@]}"; do
  base="$(basename "$svg" .svg)"
  out_svg="$FIXED_DIR/${base}.plain.svg"
  # actions: open -> select-all -> object-to-path -> stroke-to-path -> ungroup x3 -> vacuum-defs -> export-plain-svg -> close
  actions="file-open:\"$svg\";select-all;object-to-path;stroke-to-path;selection-ungroup;selection-ungroup;selection-ungroup;vacuum-defs;export-plain-svg:\"$out_svg\";file-close"
  "$INKSCAPE_BIN" --actions="$actions" >/dev/null 2>&1 || { echo "Inkscape failed on $svg"; exit 3; }
  [[ -f "$out_svg" ]] || { echo "Error: missing $out_svg"; exit 3; }
  echo "[fix] $svg -> $out_svg"
done

# --- 2) Convert to GeoJSON (no filter) + group ---
GROUPED_LIST=()
for plain in "$FIXED_DIR"/*.plain.svg; do
  b="$(basename "$plain" .plain.svg)"         # floor1
  OUT_SUB="$OUT_DIR/$b"
  mkdir -p "$OUT_SUB"
  ALL_GJ="$OUT_SUB/all.geojson"
  GRP_GJ="$OUT_SUB/all.grouped.geojson"

  mapshaper "$plain" -o format=geojson "$ALL_GJ" force
  echo "[gj] $ALL_GJ"
  python scripts/group_geojson.py "$ALL_GJ" "$GRP_GJ" --config "$CONFIG" --stats
  [[ -f "$GRP_GJ" ]] && GROUPED_LIST+=("$GRP_GJ")
done

# --- 3) Merge all floors ---
if (( ${#GROUPED_LIST[@]} > 0 )); then
  MERGED="$OUT_DIR/all_floors.geojson"
  mapshaper "${GROUPED_LIST[@]}" -merge-layers -o format=geojson "$MERGED" force
  echo "[merge] -> $MERGED"
  python scripts/verify_geojson.py "$MERGED" --limit 10 || true
else
  echo "Warn: no grouped outputs to merge."
fi

echo "DONE."