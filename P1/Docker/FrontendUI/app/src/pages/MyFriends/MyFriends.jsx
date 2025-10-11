"use client"

import { useEffect, useMemo, useState, useCallback } from "react"
import s from "./MyFriends.module.css"
import { NavLink } from "react-router-dom";
import { Friends as FriendsApi } from "../../lib/api/APIcalls"; //Objeto de funciones

// LISTA LOS AMIGOS DEL USUARIO

const navBtnClass = ({ isActive }) => `${s.navButton} ${isActive ? s.active : ""}`; //Navegación entre rutas

//Read the user from Local Storage
function getStoredUser() {
  try {
    const raw = localStorage.getItem("user"); //Leer user
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}
//User id 
function getUserId(u) {
  if (!u) return null;
  return u.id_user ?? u.id ?? u.userid ?? u.userId ?? u._id ?? null;
}


export default function MyFriends() {
  const [theme, setTheme] = useState("colorful")
  const [friends, setFriends] = useState([]); //lista de amigos
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [busyIds, setBusyIds] = useState(new Set()); 

  const me = getStoredUser(); //Lectura de usuario registrado
  const myId = useMemo(() => getUserId(me), [me]);

  
  //Lista de amigos
  useEffect(() => {
    let alive = true;
    async function load() {
      if (!myId) {
        setErr("No active session found.");
        setLoading(false);
        return;
      }
      setLoading(true);
      setErr("");
      try {
        const res = await FriendsApi.getMyFriends(myId);  //solicita lista de amigos al backed
        if (!alive) return;

        const normalized = (Array.isArray(res) ? res : []).map((f) => ({
          ...f,
          followers:
            typeof f.followers === "number" ? f.followers : Number(f.followers ?? 0),
          isFollowing: true, //para boton de is following es true
        }));

        setFriends(normalized); //Set lista de amigos
      } catch (e) {
        if (!alive) return;
        setErr(e?.message || "Failed to load your friends.");
      } finally {
        if (alive) setLoading(false);
      }
    }
    load();
    return () => {
      alive = false;
    };
  }, [myId]);

  //Cantidad de usuarios seguidos
  const followingCount = useMemo(
    () => friends.filter((f) => f.isFollowing).length,
    [friends]
  );

  //Hanlder para seguir/dejar de seguir
  const handleToggleFollow = useCallback(
    async (friend) => {
      if (!myId || !friend?.id) return;

      const { id } = friend;
      setBusyIds((prev) => new Set(prev).add(id));
      setErr("");

     
      const prevFriends = friends;  //Guarda lista actual

      
      const nextFriends = prevFriends.map((f) => {
        if (f.id !== id) return f;
        const goingToFollow = !f.isFollowing;
        const nextFollowers = Math.max(0, f.followers + (goingToFollow ? 1 : -1));
        return { ...f, isFollowing: goingToFollow, followers: nextFollowers };
      });
      setFriends(nextFriends);

      try {
        if (friend.isFollowing) {
          //Si ya se seguía, llama al backend para unfollow
          await FriendsApi.unfollow(myId, id);
        } else {
          //Si no segría, llama al backend para follow
          await FriendsApi.follow(myId, id);
        }
      } catch (e) {
        
        setFriends(prevFriends);  
        setErr(
          e?.message ||
            (friend.isFollowing
              ? "Could not unfollow. Please try again."
              : "Could not follow. Please try again.")
        );
      } finally {
        setBusyIds((prev) => {
          const n = new Set(prev);
          n.delete(id);
          return n;
        });
      }
    },
    [myId, friends]
  );

  return (
    <div className={`${s.container} ${s[theme]}`}>
      {/* Header */}
      <header className={s.header}>
        <div className={s.headerContent}>
          <h1 className={s.title}>My Friends</h1>
          <button
            onClick={() => setTheme(theme === "colorful" ? "formal" : "colorful")}
            className={s.themeToggle}
            aria-label="Toggle theme"
          >
            {theme === "colorful" ? "🎨" : "💼"}
          </button>
        </div>
        <p className={s.subtitle}>
          {loading ? "Loading…" : `${followingCount} friends`}
        </p>
      </header>

      {/* Friends List */}
      <main className={s.main}>
        {err && (
          <div className={s.error} role="alert">
            {err}
          </div>
        )}

        {loading && (
          <div className={s.loading} aria-busy="true">
            Loading your friends…
          </div>
        )}

        {!loading && !err && friends.length === 0 && (
          <div className={s.empty}>You are not following anyone yet.</div>
        )}

        {!loading && !err && friends.length > 0 && (
          <div className={s.friendsList}>
            {friends.map((f) => {
              const fullName = [f.name, f.lastname].filter(Boolean).join(" ");
              return (
                <div key={f.id} className={s.friendCard}>
                  <div className={s.friendInfo}>
                    <img
                      src={"/neutral-avatar.svg"} 
                      alt={`${fullName || "User"} avatar`}
                      className={s.avatar}
                    />
                    <div className={s.userDetails}>
                      <h3 className={s.username}>{fullName || "Unnamed user"}</h3>
                      <p className={s.fullName}>
                        Followers: <strong>{f.followers}</strong>
                      </p>
                      {f.description ? (
                        <p className={s.mutualFriends}>{f.description}</p>
                      ) : null}
                    </div>
                  </div>

                  <button
                    onClick={() => handleToggleFollow(f)}
                    className={`${s.followButton} ${f.isFollowing ? s.following : s.notFollowing}`}
                    aria-label={`${f.isFollowing ? "Unfollow" : "Follow"} ${fullName || "this user"}`}
                    disabled={busyIds.has(f.id)}
                    title={f.isFollowing ? "Unfollow" : "Follow"}
                  >
                    {busyIds.has(f.id)
                      ? "Processing…"
                      : f.isFollowing
                      ? "Unfollow"
                      : "Follow"}
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </main>


      {/* Bottom Navigation */}
      <nav className={s.bottomNav} role="navigation" aria-label="Main navigation">
        <NavLink to="/ask" className={navBtnClass} aria-label="Find Book">
          <svg className={s.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
          </svg>
          <span className={s.navLabel}>Find Book</span>
        </NavLink>

        <NavLink to="/friends" className={navBtnClass} aria-label="Find Friends">
          <svg className={s.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="8" r="5" />
            <path d="M20 21a8 8 0 1 0-16 0" />
            <path d="M12 13v8" />
            <path d="M8 17h8" />
          </svg>
          <span className={s.navLabel}>Find Friends</span>
        </NavLink>

        <NavLink to="/prompt" className={navBtnClass} aria-label="Search Prompts">
          <svg className={s.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.35-4.35" />
          </svg>
          <span className={s.navLabel}>Search Prompts</span>
        </NavLink>


        <NavLink to="/feed" className={navBtnClass} aria-label="Feed">
          <svg className={s.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="3" width="18" height="18" rx="2" />
            <path d="M3 9h18" />
            <path d="M9 21V9" />
          </svg>
          <span className={s.navLabel}>Feed</span>
        </NavLink>

        <NavLink to="/friends" className={navBtnClass} aria-label="Friends">
          <svg className={s.navIcon} viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="2">
            <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
            <circle cx="9" cy="7" r="4" />
            <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
            <path d="M16 3.13a4 4 0 0 1 0 7.75" />
          </svg>
          <span className={s.navLabel}>Friends</span>
        </NavLink>

        <NavLink to="/me" className={navBtnClass} aria-label="Profile">
          <svg className={s.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
          <span className={s.navLabel}>Me</span>
        </NavLink>
      </nav>

    </div>
  )
}
