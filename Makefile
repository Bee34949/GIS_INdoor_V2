.PHONY: etl route-api
etl:
	python -m tools.indoor_etl.cli --floors tools/sample/floors.csv --nodes tools/sample/nodes.csv --edges tools/sample/edges.csv --out out_json
route-api:
	python -m backend_ext.app
