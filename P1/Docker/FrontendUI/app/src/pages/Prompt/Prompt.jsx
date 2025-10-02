"use client"

import { useEffect, useMemo, useRef, useState, useCallback } from "react"
import s from "./Prompt.module.css"
import { Likes } from "../../lib/api/APIcalls"
import { NavLink } from "react-router-dom"
import { Prompts } from "../../lib/api/APIcalls"

const navItemClass = ({ isActive }) =>
  `${s.navItem ?? ""} ${isActive ? (s.active ?? "") : ""}`

function getStoredUser() {
  try {
    const raw = localStorage.getItem("user");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}
function getUserId(u) {
  if (!u) return null;
  return u.id_user ?? u.id ?? u.userid ?? u.userId ?? u._id ?? null;
}

const DEBOUNCE_MS = 350;


function useDebouncedCallback(fn, delay) {
  const fnRef = useRef(fn);
  const t = useRef(null);

  useEffect(() => {
    fnRef.current = fn;
  }, [fn]);

  return useMemo(() => {
    return (...args) => {
      if (t.current) clearTimeout(t.current);
      t.current = setTimeout(() => {
        fnRef.current?.(...args);
      }, delay);
    };
  }, [delay]);
}


function loadLikedSet(userId) {
  if (!userId) return new Set();
  try {
    const raw = localStorage.getItem(`liked_prompts:${userId}`);
    const arr = raw ? JSON.parse(raw) : [];
    return new Set(arr);
  } catch {
    return new Set();
  }
}
function saveLikedSet(userId, likedSet) {
  if (!userId) return;
  try {
    localStorage.setItem(
      `liked_prompts:${userId}`,
      JSON.stringify(Array.from(likedSet))
    );
  } catch { }
}
function loadCounts() {
  try {
    const raw = localStorage.getItem("prompt_like_counts");
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}
function saveCounts(mapObj) {
  try {
    localStorage.setItem("prompt_like_counts", JSON.stringify(mapObj));
  } catch { }
}


function extractErrorMessage(e, { action } = {}) {

  const status = e?.response?.status ?? e?.status;
  const code =
    e?.response?.data?.code ??
    e?.data?.code ??
    e?.code;

  const msgPayload =
    e?.response?.data?.message ??
    e?.response?.data?.error ??
    e?.data?.message ??
    e?.message ??
    e?.toString?.();


  if (status === 409 || code === "ALREADY_LIKED") {
    return "Ya habías dado like a este prompt.";
  }
  if (status === 404 || code === "NOT_LIKED") {
    return "No tenías like en este prompt.";
  }
  if (status === 401 || status === 403) {
    return "No tienes permisos para realizar esta acción.";
  }


  if (action === "like") {
    return typeof msgPayload === "string" && msgPayload.trim()
      ? msgPayload
      : "No se pudo registrar el like.";
  }
  if (action === "unlike") {
    return typeof msgPayload === "string" && msgPayload.trim()
      ? msgPayload
      : "No se pudo quitar el like.";
  }
  if (action === "search") {
    return typeof msgPayload === "string" && msgPayload.trim()
      ? msgPayload
      : "No se pudo buscar prompts.";
  }

  return typeof msgPayload === "string" && msgPayload.trim()
    ? msgPayload
    : "Ocurrió un error inesperado.";
}


function useToast(autoHideMs = 3500) {
  const [toast, setToast] = useState({ open: false, text: "", type: "error" });
  const timerRef = useRef(null);

  const show = useCallback((text, type = "error") => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setToast({ open: true, text, type });
    timerRef.current = setTimeout(() => {
      setToast(t => ({ ...t, open: false }));
    }, autoHideMs);
  }, [autoHideMs]);

  const hide = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setToast(t => ({ ...t, open: false }));
  }, []);

  return { toast, show, hide };
}

const Prompt = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [theme, setTheme] = useState("colorful");

  const [prompts, setPrompts] = useState([]); // prompts from api
  const [loading, setLoading] = useState(false);


  const [err, setErr] = useState("");


  const { toast, show: showToast, hide: hideToast } = useToast(3500);

  const user = getStoredUser();
  const userId = getUserId(user);

  const [likedSet, setLikedSet] = useState(() => loadLikedSet(userId));
  useEffect(() => {
    setLikedSet(loadLikedSet(userId));
  }, [userId]);

  const [likeCounts, setLikeCounts] = useState(() => loadCounts());
  useEffect(() => {
    saveCounts(likeCounts);
  }, [likeCounts]);


  const requestIdRef = useRef(0);

  const handleSearch = useCallback(async (q) => {
    const id = ++requestIdRef.current;

    if (!q || !q.trim()) {
      if (id === requestIdRef.current) {
        setPrompts([]);
        setErr("");
        setLoading(false);
      }
      return;
    }

    setLoading(true);
    setErr("");

    try {
      const res = await Prompts.search(q.trim());
      const dataRaw = Array.isArray(res) ? res : (res?.data ?? []);
      const data = [...dataRaw].sort((a, b) => {
        const ai = String(a.id ?? "");
        const bi = String(b.id ?? "");
        return ai.localeCompare(bi);
      });

      if (id !== requestIdRef.current) return;
      setPrompts(data);
    } catch (e) {
      if (id !== requestIdRef.current) return;
      setErr(extractErrorMessage(e, { action: "search" }));
    } finally {
      if (id === requestIdRef.current) setLoading(false);
    }
  }, []);

  const debouncedSearch = useDebouncedCallback(handleSearch, DEBOUNCE_MS);

  useEffect(() => {
    debouncedSearch(searchTerm);

  }, [searchTerm]);

  const likePrompt = async (promptId) => {
    if (!userId) {
      const msg = "No se pudo identificar al usuario.";
      setErr(msg);
      showToast(msg);
      return;
    }
    if (likedSet.has(promptId)) {

      showToast("Ya habías dado like a este prompt.");
      return;
    }

    // UI optimista
    const prevLiked = new Set(likedSet);
    const nextLiked = new Set(likedSet);
    nextLiked.add(promptId);
    setLikedSet(nextLiked);
    saveLikedSet(userId, nextLiked);

    const prevCounts = { ...likeCounts };
    const nextCounts = { ...likeCounts, [promptId]: (likeCounts[promptId] ?? 0) + 1 };
    setLikeCounts(nextCounts);

    try {
      await Likes.like(userId, promptId);
    } catch (e) {

      setLikedSet(prevLiked);
      saveLikedSet(userId, prevLiked);
      setLikeCounts(prevCounts);

      const msg = extractErrorMessage(e, { action: "like" });
      setErr(msg);
      showToast(msg);
    }
  };

  const unlikePrompt = async (promptId) => {
    if (!userId) {
      const msg = "No se pudo identificar al usuario.";
      setErr(msg);
      showToast(msg);
      return;
    }
    if (!likedSet.has(promptId)) {
      showToast("No tenías like en este prompt.");
      return;
    }

    // UI optimista
    const prevLiked = new Set(likedSet);
    const nextLiked = new Set(likedSet);
    nextLiked.delete(promptId);
    setLikedSet(nextLiked);
    saveLikedSet(userId, nextLiked);

    const prevCounts = { ...likeCounts };
    const nextCounts = {
      ...likeCounts,
      [promptId]: Math.max(0, (likeCounts[promptId] ?? 0) - 1),
    };
    setLikeCounts(nextCounts);

    try {
      await Likes.unlike(userId, promptId);
    } catch (e) {

      setLikedSet(prevLiked);
      saveLikedSet(userId, prevLiked);
      setLikeCounts(prevCounts);

      const msg = extractErrorMessage(e, { action: "unlike" });
      setErr(msg);
      showToast(msg);
    }
  };

  return (
    <div className={`${s.container} ${s[theme]}`}>
      {/* Header */}
      <header className={s.header}>
        <div className={s.headerContent}>
          <h1 className={s.title}>Prompts</h1>
          <button
            className={s.themeToggle}
            onClick={() => setTheme(theme === "colorful" ? "formal" : "colorful")}
            aria-label="Toggle theme"
          >
            {theme === "colorful" ? "🎨" : "💼"}
          </button>
        </div>
      </header>

      {/* Search Section */}
      <section className={s.searchSection}>
        <div className={s.searchContainer}>
          <label htmlFor="search" className={s.searchLabel}>
            Search prompts
          </label>
          <div className={s.searchInputWrapper}>
            <input
              id="search"
              type="text"
              className={s.searchInput}
              placeholder="Search by prompt text..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              aria-describedby="search-help"
            />
            <div className={s.searchIcon}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8"></circle>
                <path d="m21 21-4.35-4.35"></path>
              </svg>
            </div>
          </div>
          <p id="search-help" className={s.searchHelp}>
            Results update as you type
          </p>
          {loading && <p className={s.loadingText}>Buscando…</p>}
          {err && <p className={s.errorText}>{err}</p>}
        </div>
      </section>

      {/* Results Section */}
      <main className={s.resultsSection}>
        <div className={s.resultsHeader}>
          <h2 className={s.resultsTitle}>
            {searchTerm ? `Results for "${searchTerm}"` : "Start typing to search"}
          </h2>
        </div>

        <div className={s.promptsList}>
          {prompts.map((p) => {
            const liked = likedSet.has(p.id);
            const count = likeCounts[p.id] ?? 0;
            return (
              <article key={p.id} className={s.promptCard}>
                <div className={s.promptContent}>
                  <p className={s.promptText}>{p.text}</p>
                </div>

                <div className={s.promptActions}>
                  {!liked ? (
                    <button
                      className={s.likeButton}
                      onClick={() => likePrompt(p.id)}
                      aria-label={`Like prompt ${p.id}`}
                    >
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
                      </svg>
                      <span className={s.likeCount}>{count}</span>
                    </button>
                  ) : (
                    <button
                      className={s.likeButton}
                      onClick={() => unlikePrompt(p.id)}
                      aria-label={`Quitar like prompt ${p.id}`}
                    >
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
                      </svg>
                      <span className={s.likeCount}>{count}</span>
                    </button>
                  )}
                </div>
              </article>
            );
          })}
        </div>

        {(!loading && prompts.length === 0 && searchTerm.trim()) && (
          <div className={s.emptyState}>
            <div className={s.emptyIcon}>
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <circle cx="11" cy="11" r="8"></circle>
                <path d="m21 21-4.35-4.35"></path>
              </svg>
            </div>
            <h3 className={s.emptyTitle}>No prompts found</h3>
            <p className={s.emptyDescription}>Try adjusting your search terms</p>
          </div>
        )}
      </main>

      {/* Bottom Navigation */}
      <nav className={s.bottomNav} role="navigation" aria-label="Main navigation">
        <button className={s.navItem} aria-label="Find Book">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
          </svg>
          <span>Find Book</span>
        </button>

        <button className={s.navItem} aria-label="Find Friends">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
            <circle cx="9" cy="7" r="4"></circle>
            <path d="M22 21v-2a4 4 0 0 0-3-3.87"></path>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
          </svg>
          <span>Friends</span>
        </button>

        <button className={`${s.navItem} ${s.active}`} aria-label="Search Prompts" aria-current="page">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
          <span>Prompts</span>
        </button>

        <button className={s.navItem} aria-label="Feed">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M4 11a9 9 0 0 1 9 9"></path>
            <path d="M4 4a16 16 0 0 1 16 16"></path>
            <circle cx="5" cy="19" r="1"></circle>
          </svg>
          <span>Feed</span>
        </button>

        <button className={s.navItem} aria-label="Friends">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
            <circle cx="9" cy="7" r="4"></circle>
            <path d="M22 21v-2a4 4 0 0 0-3-3.87"></path>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
          </svg>
          <span>Friends</span>
        </button>


        <button className={s.navItem} aria-label="Me">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
            <circle cx="12" cy="7" r="4"></circle>
          </svg>
          <span>Me</span>
        </button>

      </nav>

      {/* --- Toast --- */}
      {toast.open && (
        <div
          className={`${s.toast} ${toast.type === "error" ? s.toastError : s.toastInfo}`}
          role="status"
          aria-live="polite"
          onClick={hideToast}
        >
          {toast.text}
        </div>
      )}
    </div>
  )
}

export default Prompt
