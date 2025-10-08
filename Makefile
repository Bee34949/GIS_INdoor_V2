.PHONY: etl route-api
etl:
	python -m tools.indoor_etl.cli --floors tools/sample/floors.csv --nodes tools/sample/nodes.csv --edges tools/sample/edges.csv --out out_json
route-api:
	python -m backend_ext.app

SVG_IN ?= data/floorplan.svg
SVG_TAGGED ?= data/floorplan.tagged.svg
DIST_DIR ?= dist

.PHONY: svg-tag tiles tiles-nofilter group stats test ci clean

svg-tag:
	python3 scripts/svg_tagging.py $(SVG_IN) $(SVG_TAGGED)

tiles: $(SVG_TAGGED)
	mkdir -p $(DIST_DIR)
	pwsh scripts/build_tiles.ps1 -SvgPath $(SVG_TAGGED)

tiles-nofilter:
	mkdir -p $(DIST_DIR)
	pwsh scripts/build_tiles.ps1 -SvgPath $(SVG_IN) -NoFilter

group:
	python3 scripts/group_geojson.py $(DIST_DIR)/all.geojson $(DIST_DIR)/all.grouped.geojson --config scripts/config.yaml --stats

stats:
	python3 scripts/verify_geojson.py $(DIST_DIR)/all.grouped.geojson --limit 10

test:
	pytest -q

ci: test

clean:
	rm -rf $(DIST_DIR) .pytest_cache