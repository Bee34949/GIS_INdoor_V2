export const ROUTER_BASE =
  import.meta.env.VITE_NEW_ROUTER_BASE ?? "http://localhost:8100";
export const TILE_BASE = import.meta.env.VITE_TILE_BASE ?? "http://localhost:8080"; // tileserver
// ต้องตั้งค่าให้ตรงกับ build_tiles.ps1
export const TILE_LON0 = Number(import.meta.env.VITE_TILE_LON0 ?? "100.5018");
export const TILE_LAT0 = Number(import.meta.env.VITE_TILE_LAT0 ?? "13.7563");
export const TILE_SCALE = Number(import.meta.env.VITE_TILE_SCALE ?? "0.00001");

// why: แปลงพิกัดจากกราฟ (px) -> lon/lat ให้ทับกับ vector tiles
export function pxToLonLat(x: number, y: number): [number, number] {
  const lon = TILE_LON0 + x * TILE_SCALE;
  const lat = TILE_LAT0 - y * TILE_SCALE; // y กลับ
  return [lon, lat];
}