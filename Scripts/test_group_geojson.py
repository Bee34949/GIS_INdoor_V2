import json, tempfile, os, sys
from pathlib import Path

# import target
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import group_geojson as gg  # noqa

def _fc(features):
    return {"type":"FeatureCollection","features":features}

def _ft(props):
    return {"type":"Feature","geometry":{"type":"Polygon","coordinates":[[[0,0],[1,0],[1,1],[0,1],[0,0]]]},"properties":props}

def test_by_class_id():
    gj = _fc([
        _ft({"class":"room A"}),
        _ft({"id":"main-wall"}),
        _ft({"class":"door-01"}),
    ])
    with tempfile.TemporaryDirectory() as d:
        i = Path(d)/"in.json"; o = Path(d)/"out.json"
        i.write_text(json.dumps(gj), encoding="utf-8")
        counts = gg.group(str(i), str(o))
        out = json.loads(o.read_text("utf-8"))
        groups = [ft["properties"]["group"] for ft in out["features"]]
        assert groups == ["room","wall","door"]
        assert counts["room"]==1 and counts["wall"]==1 and counts["door"]==1

def test_by_keywords_default():
    gj = _fc([
        _ft({"title":"Office 101"}),
        _ft({"label":"Partition X"}),
        _ft({"name":"Main Gate"}),
        _ft({"name":"???"}),
    ])
    with tempfile.TemporaryDirectory() as d:
        i = Path(d)/"in.json"; o = Path(d)/"out.json"
        i.write_text(json.dumps(gj), encoding="utf-8")
        counts = gg.group(str(i), str(o))
        out = json.loads(o.read_text("utf-8"))
        groups = [ft["properties"]["group"] for ft in out["features"]]
        assert groups[:3] == ["room","wall","door"]
        assert "unknown" in groups

def test_by_style_colors():
    gj = _fc([
        _ft({"style":"fill:#ffffff;stroke:#333333"}),
        _ft({"stroke":"#000000"}),
        _ft({"stroke":"#ffa500"}),
    ])
    with tempfile.TemporaryDirectory() as d:
        i = Path(d)/"in.json"; o = Path(d)/"out.json"
        i.write_text(json.dumps(gj), encoding="utf-8")
        counts = gg.group(str(i), str(o))
        out = json.loads(o.read_text("utf-8"))
        groups = [ft["properties"]["group"] for ft in out["features"]]
        assert groups == ["room","wall","door"]

def test_config_override(tmp_path):
    cfg = {
        "keywords": {
            "door": ["ทางเข้า"]  # Thai word for entry
        },
        "colors": {
            "door_strokes": ["#00ff00"]
        }
    }
    # write config
    cpath = tmp_path / "cfg.yaml"
    import yaml
    cpath.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    gj = _fc([
        _ft({"name":"ทางเข้า 1"}),                 # keyword override -> door
        _ft({"style":"stroke:#00ff00"}),           # color override -> door
        _ft({"name":"UNKNOWN"})                     # -> unknown
    ])
    i = tmp_path/"in.json"; o = tmp_path/"out.json"
    i.write_text(json.dumps(gj), encoding="utf-8")
    counts = gg.group(str(i), str(o), str(cpath))
    out = json.loads(o.read_text("utf-8"))
    groups = [ft["properties"]["group"] for ft in out["features"]]
    assert groups[0]=="door" and groups[1]=="door" and "unknown" in groups
    assert counts["door"]==2