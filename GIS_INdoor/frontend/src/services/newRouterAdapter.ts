const BASE = import.meta.env.VITE_NEW_ROUTER_BASE ?? "http://localhost:8100";

export type RouteResp = { path: string[]; steps: string[] };
export type HealthResp = { status: string; graph_loaded: boolean; graph_path: string };

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${BASE}${path}`, init);
  if (!r.ok) throw new Error(`${path} ${r.status}`);
  return r.json() as Promise<T>;
}

export const routerAPI = {
  health: () => http<HealthResp>("/healthz"),
  reload: () => http<{graph_loaded: boolean; graph_path: string}>("/reload", { method: "POST" }),
  route: (startId: string, goalId: string) =>
    http<RouteResp>(`/route?start_id=${encodeURIComponent(startId)}&goal_id=${encodeURIComponent(goalId)}`),
  nearest: (x: number, y: number, floorId: string, k=1) =>
    http<string[]>(`/nearest?x=${x}&y=${y}&floor_id=${encodeURIComponent(floorId)}&k=${k}`),
};
