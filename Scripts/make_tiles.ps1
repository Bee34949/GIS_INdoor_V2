python - << 'PY'
import json, pathlib
gj=json.loads(pathlib.Path("dist/indoor_all.recentered.geojson").read_text(encoding="utf-8"))
rooms=[f for f in gj["features"] if f.get("properties",{}).get("group")=="room"]
feats=[f for f in gj["features"] if f.get("properties",{}).get("group")!="room"]
pathlib.Path("dist/_tmp").mkdir(parents=True, exist_ok=True)
pathlib.Path("dist/_tmp/rooms.geojson").write_text(json.dumps({"type":"FeatureCollection","features":rooms}, ensure_ascii=False), encoding="utf-8")
pathlib.Path("dist/_tmp/features.geojson").write_text(json.dumps({"type":"FeatureCollection","features":feats}, ensure_ascii=False), encoding="utf-8")
PY

tippecanoe -o dist/indoor.mbtiles -Z14 -z22 -rg --drop-densest-as-needed `
  -L name=rooms file=dist/_tmp/rooms.geojson `
  -L name=features file=dist/_tmp/features.geojson
Write-Host "MBTiles -> dist/indoor.mbtiles"