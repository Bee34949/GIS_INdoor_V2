# =========================================
# path: scripts/polygonize_rooms.py
# =========================================
#!/usr/bin/env python3
import sys
from pathlib import Path
from typing import Iterable, List

import geopandas as gpd
import pandas as pd
from shapely.geometry import (
    LineString,
    MultiLineString,
    Polygon,
    MultiPolygon,
    GeometryCollection,
)
from shapely.ops import polygonize, unary_union

def _to_lines(geom) -> List[LineString]:
    """Convert any geom to a list of LineString for polygonize.
    Why: walls อาจเป็นเส้น/โพลิกอน/มัลติ/คอลเลกชัน"""
    if geom is None or geom.is_empty:
        return []
    gt = geom.geom_type
    if gt == "LineString":
        return [geom]
    if gt == "MultiLineString":
        return [ls for ls in geom.geoms if ls.length > 0]
    if gt == "Polygon":
        # ใช้ขอบนอกเท่านั้น (เลี่ยงช่องว่างภายในก่อน)
        exterior = geom.exterior
        return [LineString(exterior.coords)] if exterior and len(exterior.coords) > 1 else []
    if gt == "MultiPolygon":
        lines = []
        for poly in geom.geoms:
            lines.extend(_to_lines(poly))
        return lines
    if gt == "GeometryCollection":
        lines = []
        for g in geom.geoms:
            lines.extend(_to_lines(g))
        return lines
    # จุด/อื่นๆ ข้าม
    return []

def polygonize_one(gdf: gpd.GeoDataFrame, floor_val=None, min_area: float = 1.0) -> gpd.GeoDataFrame:
    walls = gdf[gdf.get("group") == "wall"].copy()
    if walls.empty:
        return gpd.GeoDataFrame(columns=["group", "floor", "source"], geometry=[], crs=gdf.crs)

    # รวบรวมเส้นทั้งหมดจากผนัง
    line_parts: List[LineString] = []
    for geom in walls.geometry:
        line_parts.extend(_to_lines(geom))

    if not line_parts:
        return gpd.GeoDataFrame(columns=["group", "floor", "source"], geometry=[], crs=gdf.crs)

    # รวมเส้นให้ snap กันดีขึ้น
    merged = unary_union(MultiLineString(line_parts))  # อาจได้ LineString/MultiLineString
    # ทำ polygonize
    polys = list(polygonize(merged))
    if not polys:
        return gpd.GeoDataFrame(columns=["group", "floor", "source"], geometry=[], crs=gdf.crs)

    rooms = gpd.GeoDataFrame(geometry=polys, crs=gdf.crs)
    # กรองเศษเล็กๆ
    rooms["area"] = rooms.geometry.area
    rooms = rooms[rooms["area"] >= float(min_area)].drop(columns="area", errors="ignore")
    rooms["group"] = "room"
    rooms["source"] = "polygonize_walls"
    if floor_val is not None:
        rooms["floor"] = floor_val
    elif "floor" in gdf.columns and not gdf["floor"].isna().all():
        rooms["floor"] = gdf["floor"].mode().iat[0]

    return rooms

def run(input_path: Path, out_path: Path, min_area: float = 1.0):
    if input_path.is_dir():
        outs = []
        for f in sorted(input_path.glob("*.grouped.geojson")):
            g = gpd.read_file(f)
            floor_val = None
            if "floor" in g.columns and len(g) > 0 and not g["floor"].isna().all():
                floor_val = g["floor"].mode().iat[0]
            rooms = polygonize_one(g, floor_val=floor_val, min_area=min_area)
            if not rooms.empty:
                rooms_path = f.with_name(f"{f.stem}.rooms.geojson")
                rooms.to_file(rooms_path, driver="GeoJSON")
                outs.append(rooms)
                print(f"[rooms] {rooms_path} ({len(rooms)})")
            else:
                print(f"[rooms] {f.name}: no rooms")
        if outs:
            allr = pd.concat(outs, ignore_index=True)
            allg = gpd.GeoDataFrame(allr, crs=outs[0].crs)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            allg.to_file(out_path, driver="GeoJSON")
            print(f"[rooms] merged -> {out_path} ({len(allg)})")
        else:
            print("[rooms] nothing to merge")
    else:
        g = gpd.read_file(input_path)
        floor_val = None
        if "floor" in g.columns and len(g) > 0 and not g["floor"].isna().all():
            floor_val = g["floor"].mode().iat[0]
        rooms = polygonize_one(g, floor_val=floor_val, min_area=min_area)
        if rooms.empty:
            print("[rooms] empty result")
            return
        out_path.parent.mkdir(parents=True, exist_ok=True)
        rooms.to_file(out_path, driver="GeoJSON")
        print(f"[rooms] wrote -> {out_path} ({len(rooms)})")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/polygonize_rooms.py <dist_dir or grouped.geojson> <out.geojson> [min_area]")
        sys.exit(1)
    ip = Path(sys.argv[1]); op = Path(sys.argv[2])
    min_area = float(sys.argv[3]) if len(sys.argv) >= 4 else 1.0
    run(ip, op, min_area)
