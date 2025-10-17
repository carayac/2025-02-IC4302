"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import s from "./Friends.module.css"
import { Link, NavLink, useNavigate } from "react-router-dom";
import { Friends as FriendsApi } from "../../lib/api/APIcalls"; //Objeto de funciones

// BUSQUEDA DE AMIGOS, PUEDE SEGUIR/DEJAR DE SEGUIR

//Navegación entre rutas
const navItemClass = ({ isActive }) =>
  `${s.navItem} ${isActive ? s.active : ""}`


//Geting the main user from Local Storage
function getStoredUser() {
  try {
    const raw = localStorage.getItem("user")  //User guardado
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function getUserId(u) {
  if (!u) return null
  return u.id_user ?? u.id ?? u.userid ?? u.userId ?? u._id ?? null
}


const AVATARS = ["👩‍💼", "👨‍🎓", "👩‍🎨", "👨‍💻", "👩‍🔬", "👨‍🎨", "👩‍🏫", "👨‍🔬"]
function getAvatarFor(id) {
  if (typeof id !== "number") return "👤"
  return AVATARS[id % AVATARS.length]
}

//Validate if you already followed the user
const FOLLOW_KEY = (uid) => `followed:${uid}` 
//Carga lista de seguidos
function loadFollowed(uid) {
  try {
    const raw = localStorage.getItem(FOLLOW_KEY(uid))
    if (!raw) return new Set()
    const arr = JSON.parse(raw)
    return new Set((arr || []).map(Number))
  } catch {
    return new Set()
  }
}
//Guarda personas seguidas en Local Storage
function saveFollowed(uid, followedSet) {
  try {
    localStorage.setItem(FOLLOW_KEY(uid), 
    JSON.stringify(Array.from(followedSet)))
  } catch { }
}


const Friends = () => {
  const navigate = useNavigate()  //Navegación entre rutas
  const [meId, setMeId] = useState(null)

  const [searchTerm, setSearchTerm] = useState("")  //Escritura de prompts
  const [theme, setTheme] = useState("formal")
  const [results, setResults] = useState([])  //Resultados de busqueda
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [followedUsers, setFollowedUsers] = useState(new Set()) //Ids seguidos
  const [pending, setPending] = useState(new Set())

  const debounceRef = useRef(null)
  const abortRef = useRef(null)
  const reqCounterRef = useRef(0)



  useEffect(() => {
    //User y Id desde Local storage
    const me = getStoredUser()
    const uid = getUserId(me)
    if (!uid) {
      navigate("/", { replace: true })
      return
    }
    setMeId(Number(uid))

    //Get people you already follow on Local storage
    const stored = loadFollowed(uid)
    setFollowedUsers(stored)
  }, [navigate])


    useEffect(() => {
    if (meId == null) return;
    let cancelled = false;

    (async () => {
      try {
        const list = await FriendsApi.getMyFriends(meId);   //Lista de personas seguidas al backend
        
        // Lista de IDS numericos
        const ids = Array.isArray(list)
          ? list.map(u => Number(u?.id)).filter(Number.isFinite)
          : [];
        const serverSet = new Set(ids); //Conjunto sin repetidos
        if (!cancelled) {
          setFollowedUsers(serverSet);   
          saveFollowed(meId, serverSet);  //Se actualiza en local storage las persoans seguidas
        }
      } catch {
        
      }
    })();

    return () => { cancelled = true; };
  }, [meId]);
  

  //Show data while writing
  useEffect(() => {
    setError("")
    //Limpiar y cancelar busquedas pendientes
    if (!searchTerm.trim()) {
      setResults([])
      if (abortRef.current) abortRef.current.abort()
      if (debounceRef.current) clearTimeout(debounceRef.current)
      return
    }

    if (debounceRef.current) clearTimeout(debounceRef.current)
    //Esperar 300 ms para buscar la persona
    debounceRef.current = setTimeout(async () => {

      //Abortar bsuquedas anteriores
      if (abortRef.current) abortRef.current.abort()
      const ctrl = new AbortController()
      abortRef.current = ctrl

      const reqId = ++reqCounterRef.current
      setLoading(true)
      try {
        //Calling Backend
        const res = await FriendsApi.findFriend(searchTerm)

        const raw = Array.isArray(res?.results || res) ? (res.results || res) : []
        // Dont show the user of the account
        const list = (meId == null)
          ? raw
          : raw.filter(x => Number(x?.id) !== Number(meId))
        if (reqId === reqCounterRef.current) {
          setResults(list)
        }

      } catch (e) {
        if (e?.name !== "AbortError") {
          setError("No se pudo obtener resultados. Intenta de nuevo.")
        }
      } finally {
        if (reqId === reqCounterRef.current) {
          setLoading(false)
        }
      }
    }, 300)

    return () => {
      //Reincio de temporizador
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [searchTerm, meId])

  
  //Filtrar el propio ususario en caso de que esté dentro de la lista
  useEffect(() => {
    if (meId == null || results.length === 0) return
    setResults(prev => prev.filter(x => Number(x?.id) !== Number(meId)))
  }, [meId])

  //Guarda el conjunto de seguidos en costante y en local storage
  function setAndPersistFollow(nextSet) {
    setFollowedUsers(nextSet)
    if (meId != null) saveFollowed(meId, nextSet)
  }

  //Manejo de seguir/dejar de seguir 
  const handleFollowToggle = async (userId) => {
    if (!meId) return
    if (pending.has(userId)) return

    setPending(prev => {
      const ns = new Set(prev)
      ns.add(userId)
      return ns
    })

    const already = followedUsers.has(userId) //Verificar si era ya seguido

    //Seguir dejar de seguir segun followedUsers
    const optimistic = new Set(followedUsers)
    if (already) optimistic.delete(userId)  
    else optimistic.add(userId)
    setAndPersistFollow(optimistic)

    try {
      if (already) { //Si ya lo seguia llama backend de unfollow
        const res = await FriendsApi.unfollow(meId, userId)
        if (res?.error && !/not following/i.test(res.error)) {
          throw new Error(res.error)
        }
      } else {  //Si no se seguía llama backend de follow
        const res = await FriendsApi.follow(meId, userId)
        if (res?.error && !/already following/i.test(res.error)) {
          throw new Error(res.error)
        }
      }

      //Lista de seguidos según el backend
      FriendsApi.getMyFriends(meId)
        .then(list => {
          const ids = Array.isArray(list) //Ids numericos
            ? list.map(u => Number(u && u.id)).filter(Number.isFinite)
            : []
          const fresh = new Set(ids)  //Conjunto sin repeticiones
          setAndPersistFollow(fresh)  //Actualizar lista de seguidos 
        })
        .catch(() => { })

    } catch (e) {
      const status = e?.status ?? 0
      const msg = (e && e.message) ? e.message : ""
      const idempotentOk =
        (!already && (/already following/i.test(msg) || status === 400)) ||
        (already && (/not following/i.test(msg) || status === 400))

      if (!idempotentOk) {
        const revert = new Set(optimistic)
        if (already) revert.add(userId)
        else revert.delete(userId)
        setAndPersistFollow(revert)
        setError("Could not update the follow.")
      }
    } finally {
      setPending(prev => {
        const ns = new Set(prev)
        ns.delete(userId)
        return ns
      })
    }
  }
  
  //Cambio de temas
  const toggleTheme = () => {
    setTheme((prev) => (prev === "colorful" ? "formal" : "colorful"))
  }

  const resultsTitle = useMemo(() => {
    if (!searchTerm.trim()) return "Suggested Friends"
    return `Results for "${searchTerm}"`
  }, [searchTerm])


  return (
    <div className={`${s.container} ${s[theme]}`}>
      <header className={s.header}>
        <div className={s.headerContent}>
          <h1 className={s.title}>Find Friends</h1>
          <button
            onClick={toggleTheme}
            className={s.themeToggle}
            aria-label={`Switch to ${theme === "colorful" ? "formal" : "colorful"} theme`}
          >
            {theme === "colorful" ? "🎨" : "💼"}
          </button>
        </div>
      </header>

      <main className={s.main}>
        <div className={s.searchSection}>
          <div className={s.searchContainer}>
            <label htmlFor="search-input" className={s.searchLabel}>
              Search for friends
            </label>
            <input
              id="search-input"
              type="text"
              placeholder="Search by name or lastname"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className={s.searchInput}
              aria-describedby="search-help"
            />
            <span id="search-help" className={s.searchHelp}>
              Find friends by typing their name or lastname
            </span>
          </div>
        </div>

        <div className={s.resultsSection}>
          <div className={s.resultsHeader}>
            <h2 className={s.resultsTitle}>{resultsTitle}</h2>
            {searchTerm.trim() ? (
              <span className={s.resultsCount}>
                {results.length} {results.length === 1 ? "user" : "users"} found
              </span>
            ) : null}
          </div>

          {loading && (
            <div className={s.loading} role="status" aria-live="polite">
              Searching…
            </div>
          )}
          {error && !loading && (
            <div className={s.error} role="alert">
              {error}
            </div>
          )}

          <div className={s.usersList}>
            {!loading &&
              results
                .filter((u) => Number(u.id) !== Number(meId))
                .map((u) => {
                  const id = Number(u.id)
                  const fullName = `${u.name ?? ""} ${u.lastname ?? ""}`.trim() || "Unnamed"
                  const avatar = getAvatarFor(id)
                  const isFollowing = followedUsers.has(id)
                  const isPending = pending.has(id)

                  return (
                    <div key={id} className={s.userCard}>
                      <div className={s.userInfo}>
                        <div className={s.userAvatar} aria-hidden="true">
                          {avatar}
                        </div>
                        <div className={s.userDetails}>
                          <h3 className={s.username}>{fullName}</h3>
                        </div>
                      </div>

                      { }
                      <button
                        onClick={() => handleFollowToggle(id)}
                        className={`${s.followButton} ${isFollowing ? s.following : s.notFollowing}`}
                        aria-label={`${isFollowing ? "Unfollow" : "Follow"} ${fullName}`}
                        disabled={isPending || !meId}
                      >
                        {isPending ? "..." : isFollowing ? "Unfollow" : "Follow"}
                      </button>
                    </div>
                  )
                })}
          </div>

          {!loading && results.length === 0 && searchTerm.trim() && (
            <div className={s.noResults}>
              <p className={s.noResultsText}>No users found matching "{searchTerm}"</p>
              <p className={s.noResultsSubtext}>Try searching with a different term</p>
            </div>
          )}

          {!loading && !searchTerm.trim() && (
            <div className={s.noResults}>
              <p className={s.noResultsText}>Start typing to search for friends</p>
            </div>
          )}
        </div>
      </main>

      <nav className={s.bottomNav} role="navigation" aria-label="Main navigation">
        <NavLink to="/ask" className={navItemClass} aria-label="Find Books">
          <span className={s.navIcon}>📚</span>
          <span className={s.navLabel}>Find Book</span>
        </NavLink>

        <NavLink to="/friends" className={navItemClass} aria-label="Find Friends">
          <span className={s.navIcon}>👥</span>
          <span className={s.navLabel}>Find Friends</span>
        </NavLink>

        <NavLink to="/prompt" className={navItemClass} aria-label="Search Prompts">
          <span className={s.navIcon}>💭</span>
          <span className={s.navLabel}>Search Prompts</span>
        </NavLink>

        <NavLink to="/feed" className={navItemClass} aria-label="Feed">
          <span className={s.navIcon}>📰</span>
          <span className={s.navLabel}>Feed</span>
        </NavLink>

        <NavLink to="/myFriends" className={navItemClass} aria-label="Friends">
          <span className={s.navIcon}>👥</span>
          <span className={s.navLabel}>Friends</span>
        </NavLink>

        <NavLink to="/me" className={navItemClass} aria-label="Me">
          <span className={s.navIcon}>👤</span>
          <span className={s.navLabel}>Me</span>
        </NavLink>
      </nav>
    </div>
  )
}

export default Friends
