import { useEffect, useRef } from "react";

/**
 * Custom hook that automatically scrolls to the bottom of a container
 * when dependencies change (e.g., new messages, loading state)
 * 
 * @param dependencies - Array of dependencies to watch for changes
 * @returns A ref to attach to the scroll target element
 */
export const useAutoScroll = <T,>(dependencies: T[]) => {
  const scrollTargetRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollTargetRef.current?.scrollIntoView({ behavior: "smooth" });
  }, dependencies);

  return scrollTargetRef;
};

