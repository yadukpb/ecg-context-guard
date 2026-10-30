import { useEffect, useRef, useState } from "react";

/**
 * Polls `fetcher` every `intervalMs` while `active` is true. A v1 simplification in place of
 * websockets/SSE — see docs/building/01-architecture.md for the tradeoff.
 */
export function usePolling(fetcher, intervalMs, active = true, deps = []) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  useEffect(() => {
    if (!active) return undefined;
    let cancelled = false;

    async function tick() {
      try {
        const result = await fetcherRef.current();
        if (!cancelled) {
          setData(result);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) setError(err);
      }
    }

    tick();
    const id = setInterval(tick, intervalMs);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active, intervalMs, ...deps]);

  return { data, error };
}
