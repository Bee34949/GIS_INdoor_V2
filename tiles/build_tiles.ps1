param(
  [string]$SvgDir = "tiles\src",
  [string]$DistRoot = "dist",
  [string]$ConfigPath = "scripts\config.yaml",
  [switch]$Retag    # ใช้ถ้าต้องการทางถาวร: tag SVG แล้วค่อยกรอง
)

$ErrorActionPreference = "Stop"

# ตรวจเครื่องมือ
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  throw "ไม่พบ python ใน PATH"
}
if (-not (Get-Command mapshaper -ErrorAction SilentlyContinue)) {
  throw "ไม่พบ mapshaper CLI -> ติดตั้ง: npm i -g mapshaper"
}

# เตรียมโฟลเดอร์ผลลัพธ์
New-Item -ItemType Directory -Force -Path $DistRoot | Out-Null

# เก็บรายชื่อไฟล์ SVG
$svgs = Get-ChildItem -Path $SvgDir -Filter "floor*.svg" -File
if ($svgs.Count -eq 0) {
  throw "ไม่พบไฟล์ SVG ใน $SvgDir (คาดหวัง floor1.svg, floor2.svg, ...)"
}

# ประมวลผลทีละชั้น
$grouped = @()
foreach ($svg in $svgs) {
  $name = $svg.BaseName
  $outDir = Join-Path $DistRoot $name
  New-Item -ItemType Directory -Force -Path $outDir | Out-Null

  if ($Retag) {
    # ทางถาวร: เติม class จาก heuristics แล้วกรองตอน export
    $tagged = Join-Path $svg.DirectoryName ($name + ".tagged.svg")
    python .\scripts\svg_tagging.py $svg.FullName $tagged
    pwsh .\scripts\build_tiles.ps1 -SvgPath $tagged -OutDir $outDir
  } else {
    # ทางชั่วคราว: ไม่กรอง -> จัดกลุ่มทีหลัง
    pwsh .\scripts\build_tiles.ps1 -SvgPath $svg.FullName -NoFilter -OutDir $outDir
    python .\scripts\group_geojson.py (Join-Path $outDir "all.geojson") (Join-Path $outDir "all.grouped.geojson") --config $ConfigPath --stats
  }

  $gg = Join-Path $outDir "all.grouped.geojson"
  if (Test-Path $gg) { $grouped += $gg } else { Write-Warning "ไม่มี $gg สำหรับ $name" }
}

# รวมทุกชั้น (merge-layers จะรวมเป็นชั้นเดียว)
if ($grouped.Count -gt 0) {
  $merged = Join-Path $DistRoot "all_floors.geojson"
  mapshaper $grouped -merge-layers -o format=geojson $merged force
  Write-Host "Merged -> $merged"
  python .\scripts\verify_geojson.py $merged --limit 10
} else {
  Write-Warning "ไม่มีไฟล์ grouped สำหรับรวมผล"
}

Write-Host "DONE."