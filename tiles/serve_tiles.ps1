$ErrorActionPreference = "Stop"
$mb = "tiles/dist/indoor.mbtiles"
if (!(Test-Path $mb)) { throw "Not found: $mb (build first)" }
npx tileserver-gl-light $mb --port 8080