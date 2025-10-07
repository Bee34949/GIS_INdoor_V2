import { ROUTER_BASE } from "../config";

export type RouteResp = { path: string[]; steps: string[] };
export type HealthResp = { status: string; graph_loaded: boolean; graph_path: string };

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${ROUTER_BASE}${path}`, init);
  if (!r.ok) throw new Error(`${path} ${r.status}`);
  return (await r.json()) as T;
}

export function routerHealth(): Promise<HealthResp> {
  return http<HealthResp>("/healthz"); // <-- ต้อง return
}

export function reloadGraph(): Promise<{ graph_loaded: boolean; graph_path: string }> {
  return http("/reload", { method: "POST" });
}

export function getRoute(startId: string, goalId: string): Promise<RouteResp> {
  const url = `/route?start_id=${encodeURIComponent(startId)}&goal_id=${encodeURIComponent(goalId)}`;
  return http<RouteResp>(url);
}

export function nearest(x: number, y: number, floorId: string, k = 1): Promise<string[]> {
  const url = `/nearest?x=${x}&y=${y}&floor_id=${encodeURIComponent(floorId)}&k=${k}`;
  return http<string[]>(url);
}

export type GraphResp = {
  nodes: Record<string, { x: number; y: number; floor_id: string; name?: string }>;
  floors: any[];
};
export function getGraph(): Promise<GraphResp> {
  return http<GraphResp>("/graph");
}