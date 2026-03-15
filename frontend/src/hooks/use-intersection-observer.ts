import { useEffect, useRef, useCallback } from "react";

export function useIntersectionObserver(
  callback: () => void,
  options?: { enabled?: boolean; rootMargin?: string }
) {
  const ref = useRef<HTMLDivElement>(null);
  const callbackRef = useRef(callback);

  // Keep callback ref up to date without re-subscribing the observer
  useEffect(() => {
    callbackRef.current = callback;
  });

  const stableCallback = useCallback(() => {
    callbackRef.current();
  }, []);

  useEffect(() => {
    if (!options?.enabled) return;
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) stableCallback();
      },
      { rootMargin: options?.rootMargin ?? "200px" }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [stableCallback, options?.enabled, options?.rootMargin]);

  return ref;
}
