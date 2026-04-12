import { useState, useEffect, useCallback, useRef } from "react";
import type { Match, SportFilter } from "../types";

// ─── useHeroSlider ────────────────────────────────────────────────────────────

export function useHeroSlider(length: number, intervalMs = 5000) {
  const [idx, setIdx] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const resetTimer = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = setInterval(() => setIdx(i => (i + 1) % length), intervalMs);
  }, [length, intervalMs]);

  useEffect(() => {
    resetTimer();
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [resetTimer]);

  const goTo = useCallback((i: number) => { setIdx(i); resetTimer(); }, [resetTimer]);
  const next  = useCallback(() => goTo((idx + 1) % length), [idx, length, goTo]);
  const prev  = useCallback(() => goTo((idx - 1 + length) % length), [idx, length, goTo]);

  return { idx, goTo, next, prev };
}

// ─── useMatchFilter ───────────────────────────────────────────────────────────

export function useMatchFilter(matches: Match[]) {
  const [sport, setSport] = useState<SportFilter>("All");
  const [query, setQuery] = useState("");

  const filtered = matches.filter(m => {
    const matchesSport = sport === "All" || m.sport === sport;
    const q = query.toLowerCase();
    const matchesQuery =
      q === "" ||
      m.home.name.toLowerCase().includes(q) ||
      m.away.name.toLowerCase().includes(q) ||
      m.league.toLowerCase().includes(q);
    return matchesSport && matchesQuery;
  });

  const reset = useCallback(() => { setSport("All"); setQuery(""); }, []);

  return { sport, setSport, query, setQuery, filtered, reset };
}

// ─── useModal ─────────────────────────────────────────────────────────────────

export function useModal<T>() {
  const [item, setItem] = useState<T | null>(null);

  // Lock body scroll when modal is open
  useEffect(() => {
    if (item) document.body.style.overflow = "hidden";
    else      document.body.style.overflow = "";
    return () => { document.body.style.overflow = ""; };
  }, [item]);

  const open  = useCallback((t: T) => setItem(t),   []);
  const close = useCallback(()      => setItem(null), []);

  return { item, open, close, isOpen: item !== null };
}

// ─── useSearch ────────────────────────────────────────────────────────────────

export function useSearch() {
  const [query,   setQuery]   = useState("");
  const [focused, setFocused] = useState(false);
  const clear = useCallback(() => setQuery(""), []);
  return { query, setQuery, focused, setFocused, clear };
}

// ─── useLocalStorage ─────────────────────────────────────────────────────────

export function useLocalStorage<T>(key: string, initial: T) {
  const [value, setValue] = useState<T>(() => {
    try {
      const stored = localStorage.getItem(key);
      return stored ? (JSON.parse(stored) as T) : initial;
    } catch { return initial; }
  });

  const set = useCallback((v: T) => {
    setValue(v);
    try { localStorage.setItem(key, JSON.stringify(v)); } catch { /* noop */ }
  }, [key]);

  return [value, set] as const;
}

// ─── useCountdown ─────────────────────────────────────────────────────────────

export function useCountdown(targetDate: string) {
  const calc = () => {
    const diff = new Date(targetDate).getTime() - Date.now();
    if (diff <= 0) return { days:0, hours:0, minutes:0, seconds:0, expired:true };
    return {
      days:    Math.floor(diff / 86400000),
      hours:   Math.floor((diff % 86400000) / 3600000),
      minutes: Math.floor((diff % 3600000)  / 60000),
      seconds: Math.floor((diff % 60000)    / 1000),
      expired: false,
    };
  };

  const [time, setTime] = useState(calc);
  useEffect(() => {
    const t = setInterval(() => setTime(calc()), 1000);
    return () => clearInterval(t);
  }, [targetDate]);

  return time;
}

// ─── useFollowToggle ──────────────────────────────────────────────────────────
// Optimistic UI — calls your Flask API, reverts on error

export function useFollowToggle(initialState: boolean, onToggle: (follow: boolean) => Promise<void>) {
  const [following, setFollowing] = useState(initialState);
  const [loading,   setLoading]   = useState(false);

  const toggle = useCallback(async () => {
    const next = !following;
    setFollowing(next);  // optimistic
    setLoading(true);
    try {
      await onToggle(next);
    } catch {
      setFollowing(!next); // revert on error
    } finally {
      setLoading(false);
    }
  }, [following, onToggle]);

  return { following, toggle, loading };
}
