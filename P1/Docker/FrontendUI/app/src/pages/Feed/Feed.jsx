"use client"

import { useEffect, useMemo, useState, useCallback } from "react"
import s from "./Feed.module.css"
import { NavLink } from "react-router-dom";
import { Prompts } from "../../lib/api/APIcalls"; //Objeto de funciones
import { Likes } from "../../lib/api/APIcalls"; //Objeto de funciones

const navItemClass = ({ isActive }) =>
  `${s.navBtn} ${isActive ? s.active : ""}`;


//Geting the main user
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


//Posting time 
function timeAgo(input) {
  if (!input) return "";
  const date = new Date(input);
  const diffSec = Math.floor((date.getTime() - Date.now()) / 1000);
  const rtf = new Intl.RelativeTimeFormat("es", { numeric: "auto" });
  const steps = [
    ["second", 60], ["minute", 60], ["hour", 24],
    ["day", 7], ["week", 4.34524], ["month", 12], ["year", Infinity],
  ];
  let v = diffSec;
  for (const [unit, amt] of steps) {
    if (Math.abs(v) < amt) return rtf.format(Math.round(v), unit);
    v /= amt;
  }
  return "";
}

export default function Feed() {
  const [theme, setTheme] = useState("colorful");
  const [feedPosts, setFeedPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [likeErr, setLikeErr] = useState("");

  const user = useMemo(() => getStoredUser(), []);
  const id_user = useMemo(() => getUserId(user), [user]);
  const username = user?.name || user?.username || "me";

  const load = useCallback(async () => {
    setLoading(true);
    setErr("");
    try {
      const data = await Prompts.getMyPrompts(id_user); //Calling endpoint
      const mapped = (Array.isArray(data) ? data : []).map((p) => ({
        id: p.id,
        user: { username, avatar: "/placeholder.svg" },
        prompt: p.text,
        likes: Number(p.likes ?? 0),
        isLiked: false,
        createdAtISO: p.created_at,
        timestamp: timeAgo(p.created_at),
        likeBusy: false,
      }));
      setFeedPosts(mapped);
    } catch (e) {
      setErr(e.message || "Error loading feed.");
    } finally {
      setLoading(false);
    }
  }, [id_user, username]);

  useEffect(() => { load(); }, [load]);

  // Refres when publish 
  const refresh = load;


  const handleToggleLike = async (postId) => {
    setLikeErr("");

    const prevFeed = feedPosts;
    const target = prevFeed.find((p) => p.id === postId);
    if (!target) return;
    const wasLiked = target.isLiked;

    // Marcar busy
    setFeedPosts((prev) =>
      prev.map((p) =>
        p.id === postId
          ? {
            ...p,
            likeBusy: true,
            isLiked: !p.isLiked,
            likes: p.isLiked ? Math.max(0, p.likes - 1) : p.likes + 1,
          }
          : p
      )
    );

    try {
      //Calling endpoints
      if (wasLiked) {
        await Likes.unlike(id_user, postId);
      } else {
        await Likes.like(id_user, postId);
      }
      //Quitando like busy
      setFeedPosts((prev) =>
        prev.map((p) => (p.id === postId ? { ...p, likeBusy: false } : p))
      );
    } catch (e) {
      //Rollback
      setLikeErr(e.message || "Error updating like.");
      setFeedPosts(prevFeed);
    }
  };

  return (
    <div className={`${s.container} ${s[theme]}`}>
      <header className={s.header}>
        <h1 className={s.title}>Feed</h1>
        <div className={s.themeToggle}>
          <button
            onClick={() => setTheme("colorful")}
            className={`${s.themeBtn} ${theme === "colorful" ? s.active : ""}`}
            aria-label="Switch to colorful theme"
          >
            Colorful
          </button>
          <button
            onClick={() => setTheme("formal")}
            className={`${s.themeBtn} ${theme === "formal" ? s.active : ""}`}
            aria-label="Switch to formal theme"
          >
            Formal
          </button>
        </div>
      </header>

      <main className={s.main}>
        <div className={s.feedContainer}>
          {feedPosts.map((post) => (
            <article key={post.id} className={s.postCard}>
              <div className={s.postHeader}>
                <div className={s.userInfo}>
                  <img
                    src={post.user.avatar || "/placeholder.svg"}
                    alt={`${post.user.username}'s avatar`}
                    className={s.avatar}
                  />
                  <span className={s.username}>{post.user.username}</span>
                  <span className={s.timestamp}>{post.timestamp}</span>
                </div>
              </div>

              <div className={s.postContent}>
                <p className={s.promptText}>{post.prompt}</p>
              </div>

              <div className={s.postFooter}>
                <button
                  onClick={() => handleToggleLike(post.id)}
                  className={`${s.likeBtn} ${post.isLiked ? s.liked : ""}`}
                  disabled={post.likeBusy}
                  title={post.isLiked ? "Unlike post" : "Like post"}
                  aria-label={post.isLiked ? "Unlike post" : "Like post"}
                >
                  <svg
                    className={s.heartIcon}
                    viewBox="0 0 24 24"
                    fill={post.isLiked ? "currentColor" : "none"}
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
                  </svg>
                  <span className={s.likeCount}>{post.likes.toLocaleString()}</span>
                </button>
              </div>
            </article>
          ))}
        </div>
      </main>

      <nav className={s.bottomNav} role="navigation" aria-label="Main navigation">
        <NavLink to="/ask" className={navItemClass} aria-label="Find Book">
          <svg
            className={s.navIcon}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
          </svg>
          <span className={s.navLabel}>Find Book</span>
        </NavLink>

        <NavLink to="/friends" className={navItemClass} aria-label="Find Friends">
          <svg
            className={s.navIcon}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
            <circle cx="9" cy="7" r="4" />
            <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
            <path d="M16 3.13a4 4 0 0 1 0 7.75" />
          </svg>
          <span className={s.navLabel}>Friends</span>
        </NavLink>

        <NavLink to="/prompt" className={navItemClass} aria-label="Search Prompts">
          <svg
            className={s.navIcon}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
          <span className={s.navLabel}>Prompts</span>
        </NavLink>

        <NavLink to="/feed" className={navItemClass} aria-label="Feed">
          <svg
            className={s.navIcon}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <rect x="3" y="3" width="7" height="7" />
            <rect x="14" y="3" width="7" height="7" />
            <rect x="14" y="14" width="7" height="7" />
            <rect x="3" y="14" width="7" height="7" />
          </svg>
          <span className={s.navLabel}>Feed</span>
        </NavLink>

        <NavLink to="/me" className={navItemClass} aria-label="Me">
          <svg
            className={s.navIcon}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
          <span className={s.navLabel}>Me</span>
        </NavLink>
      </nav>
    </div>
  )
}
