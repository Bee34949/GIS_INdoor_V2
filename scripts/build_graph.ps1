# Requires: python in .\.venv
$ErrorActionPreference = "Stop"
$py = ".\.venv\Scripts\python.exe"
& $py -m tools.indoor_etl.cli --floors tools\sample\floors.csv --nodes tools\sample\nodes.csv --edges tools\sample\edges.csv --out out_json
Write-Host "Graph built at $((Resolve-Path .\out_json\graph.json))"

# scripts/run_router.ps1  (Windows: ตั้ง env และรัน API)
$ErrorActionPreference = "Stop"
$py = ".\.venv\Scripts\python.exe"
$env:INDOOR_GRAPH_PATH = (Resolve-Path .\out_json\graph.json)
$env:INDOOR_ROUTER_PORT = "8100"
& $py -m backend_ext.app