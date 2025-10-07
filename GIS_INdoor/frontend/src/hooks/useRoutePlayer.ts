import { useEffect, useRef, useState } from "react";

export function useRoutePlayer(total: number, opts: {speedMs?: number, onTick?: (i:number)=>void} = {}) {
  const { speedMs=450, onTick } = opts;
  const [index, setIndex] = useState(0);
  const timer = useRef<number | null>(null);

  function _tick(next: number) {
    setIndex(next);
    onTick?.(next);
  }
  function play() {
    if (timer.current !== null) return;
    timer.current = window.setInterval(() => {
      _tick(Math.min(index + 1, total - 1)); // increment index safely
    }, Math.max(16, speedMs));
  }
  // fix: simpler version
  function playSimple() {
    if (timer.current !== null) return;
    timer.current = window.setInterval(() => {
      setIndex(i => {
        const n = Math.min(i + 1, total - 1);
        onTick?.(n);
        if (n >= total - 1) { pause(); }
        return n;
      });
    }, Math.max(16, speedMs));
  }
  function pause(){ if (timer.current!==null) { window.clearInterval(timer.current); timer.current=null; } }
  function reset(){ pause(); _tick(0); }
  function next(){ _tick(Math.min(index + 1, total - 1)); }
  function prev(){ _tick(Math.max(index - 1, 0)); }

  useEffect(()=>{ if (index > total-1) setIndex(0); }, [total]);
  return { index, play: playSimple, pause, reset, next, prev, setIndex };
}
