"use client"

import { useEffect, useMemo, useState, useCallback } from "react"
import s from "./Feed.module.css"
import { NavLink, useNavigate } from "react-router-dom";
import { Prompts } from "../../lib/api/APIcalls"; //Objeti de endpoints

//MUESTRA PROMPTS PROPIOS Y DE AMIGOS
//PERMITE BUSCAR EL PROMPT DIRECTAMENTE 

//Navegación entre rutas
const navItemClass = ({ isActive }) =>
  `${s.navBtn} ${isActive ? s.active : ""}`;

//Geting the main user from Local Storage
function getStoredUser() {
  try {
    const raw = localStorage.getItem("user"); //User guardado
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}
function getUserId(u) {
  if (!u) return null;
  return u.id_user ?? u.id ?? u.userid ?? u.userId ?? u._id ?? null;
}

//Conversión de la fecha a tiempo de publicacion
function timeAgo(input) {
  if (!input) return "";
  const date = new Date(input); //Convierte texto a fecha
  const diffSec = Math.floor((date.getTime() - Date.now()) / 1000); //Calcula diferencia con la hora actual
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
  const [theme, setTheme] = useState("formal");
  const [feedPosts, setFeedPosts] = useState([]); //Guarda los posts que se mostrarán
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");


  const user = useMemo(() => getStoredUser(), []);  //Scaa el usuario de local storage
  const id_user = useMemo(() => getUserId(user), [user]); //Scaa el id de user
  const username = user?.name || user?.username || "me";

  const navigate = useNavigate();

  function normalizeArray(maybeArrayOrObj) {
    if (!maybeArrayOrObj) return [];
    if (Array.isArray(maybeArrayOrObj)) return maybeArrayOrObj;
    return [maybeArrayOrObj];
  }

  //Organización de la infromación de un post
  function mapPrompt(p) {
    const authorName = `${p.name ?? ""} ${p.lastname ?? ""}`.trim()
      || p.username
      || "Usuario";

    return {
      id: p.id,
      user: {
        username: authorName,
        avatar: p.avatar || p.user?.avatar || "",
      },
      prompt: p.text ?? p.prompt ?? "",
      createdAtISO: p.created_at || p.createdAt || null,
      timestamp: timeAgo(p.created_at || p.createdAt),

    };
  }

  //Función para cargar los posts propios y de amigos
  const load = useCallback(async () => {
    setLoading(true);
    setErr("");
    try {
      const [mineRaw, feedRaw] = await Promise.all([
        Prompts.getMyPrompts(id_user),  //Propios posts
        Prompts.getFeed(id_user), //Friends posts
      ]);

      //Normaliza la respuesta
      const mine = normalizeArray(mineRaw).map((p) => mapPrompt(p, username));
      const friendsFeed = normalizeArray(feedRaw).flatMap((item) =>
        normalizeArray(item).map((p) => mapPrompt(p))
      );

      //Mapea los posts repetidos y los quita
      const byId = new Map();
      [...mine, ...friendsFeed].forEach((p) => {
        if (!byId.has(p.id)) byId.set(p.id, p);
      });

      // Ordena los post por fecha
      const merged = Array.from(byId.values()).sort((a, b) => {
        const ta = a.createdAtISO ? new Date(a.createdAtISO).getTime() : 0;
        const tb = b.createdAtISO ? new Date(b.createdAtISO).getTime() : 0;
        return tb - ta;
      });

      setFeedPosts(merged); //Guarda los resultados en la constante de estado
    } catch (e) {
      setErr(e.message || "Error loading feed.");
    } finally {
      setLoading(false);
    }
  }, [id_user, username]);

  useEffect(() => { load(); }, [load]); //Ejecuta load una vez se abra la pagina

  const refresh = load;

  //Redirige a /ask en caso de que se quiera buscar el prompt con el promt seleccionado
  const handleBuscar = (post) => {
    navigate("/ask", { state: { presetPrompt: post.prompt ?? "" } });
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
                    src={post.user.avatar || "/neutral-avatar.svg"}
                    alt={`${post.user.username}'s avatar`}
                    className={s.avatar}
                    loading="lazy"
                    referrerPolicy="no-referrer"
                    onError={(e) => { e.currentTarget.src = "/neutral-avatar.svg"; e.currentTarget.onerror = null; }}
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
                  onClick={() => handleBuscar(post)}
                  className={s.searchBtn || s.likeBtn}
                  title="Buscar"
                  aria-label="Buscar"
                >
                  <svg
                    className={s.searchIcon || s.heartIcon}
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <circle cx="11" cy="11" r="7" />
                    <line x1="21" y1="21" x2="16.65" y2="16.65" />
                  </svg>
                  <span className={s.searchLabel || s.likeCount}>Search</span>
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
          <span className={s.navLabel}>Find Friends</span>
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
          <span className={s.navLabel}>Search Prompts</span>
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

        <NavLink to="/myFriends" className={navItemClass} aria-label="Friends">
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
