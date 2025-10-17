"use client"

import { useMemo, useRef, useState, useEffect } from "react"
import s from "./Ask.module.css"
import { Link, NavLink, useNavigate, useLocation } from "react-router-dom";
import { Prompts } from "../../lib/api/APIcalls"; //Objeto de funciones

// LISTA LOS RESULTADOS DE BUSQUEDA Y PUBLICA PROMPTS

//Navegación entre rutas
const navItemClass = ({ isActive }) =>
  `${s.navItem} ${isActive ? s.active : ""}`

const Ask = () => {
  const [prompt, setPrompt] = useState("")
  const [searchResults, setSearchResults] = useState([])  //Resultados de busquedas
  const [selectedSource, setSelectedSource] = useState("")  //Fuente de busqueda
  const [isSearching, setIsSearching] = useState(false)
  const [hasSearched, setHasSearched] = useState(false);
  const [theme, setTheme] = useState("formal") // 'colorful' or 'formal'

  //Guarda todos los reusltados distintos de los tipos
  const [allResults, setAllResults] = useState({
    books_text: [],
    books_vector: [],
    reviews_text: [],
    reviews_vector: [],
    mariadb: []
  });

  const [sourceTimes, setSourceTimes] = useState({}) //Tiempos de respuesta por fuente

  const keyForSource = (sourceId) => {
    switch (sourceId) {
      case "vector-search": return "books_vector"
      case "vector-reviews": return "reviews_vector"
      case "text-books": return "books_text"
      case "text-reviews": return "reviews_text"
      case "mariadb": return "mariadb"
      default: return "books_text"
    }
  }

  const formatMs = (ms) => {
    if (ms == null || Number.isNaN(Number(ms))) return "—"
    const n = Number(ms)
    return n >= 1000 ? `${(n / 1000).toFixed(2)} s` : `${Math.round(n)} ms`
  }

  //Fuentes disponibles
  const sources = [
    { id: "vector-search", name: "Vector Search", icon: "🔍" },
    { id: "vector-reviews", name: "Vector Reviews", icon: "⭐" },
    { id: "text-books", name: "Text Books", icon: "📚" },
    { id: "text-reviews", name: "Text Reviews", icon: "📝" },
    { id: "mariadb", name: "MariaDB", icon: "🗄️" },
  ]

  // Publicación
  const [isPosting, setIsPosting] = useState(false);
  const [postOk, setPostOk] = useState(false);
  const [postError, setPostError] = useState("");

  const inputRef = useRef(null);
  const user = getStoredUser(); //Usear de local storage
  const id_user = getUserId(user);  //id de local storage

  const location = useLocation(); //Estado para recibir desde otras pantallas


  useEffect(() => {

    //Prompt pre cargado de otro pantalla
    const fromState = location.state && location.state.presetPrompt;

    //Bringing back the prompt from feed
    let fromQuery = null;
    try {
      const qs = new URLSearchParams(location.search);
      fromQuery = qs.get("prompt");
    } catch { }

    const incoming = fromState ?? fromQuery;
    if (incoming && !prompt) {
      setPrompt(incoming);  //Set prompt desde otra pantalla

      requestAnimationFrame(() => inputRef.current?.focus());
    }
  }, [location.state, location.search]);


  //Read the user from Local Storage
  function getStoredUser() {
    try {
      const raw = localStorage.getItem("user");
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

  //handler de boton search
  const handleSearch = async () => {
    if (!prompt.trim()) return;

    setIsSearching(true);
    setHasSearched(true);
    setSearchResults([]);
    setSelectedSource("");
    setAllResults({
      books_text: [],
      books_vector: [],
      reviews_text: [],
      reviews_vector: [],
      mariadb: []
    })
    setSourceTimes({})

    try {
      const result = await Prompts.generatePrompt(prompt.trim());
      console.log("Result from backend:", result);

      setAllResults({
        books_text: result.books_text || [],
        books_vector: result.books_vector || [],
        reviews_text: result.reviews_text || [],
        reviews_vector: result.reviews_vector || [],
        mariadb: result.mariadb || []
      })

      setSourceTimes(result.timings_ms || {})


    } catch (err) {
      console.error("Error fetching results:", err);
    } finally {
      setIsSearching(false);
    }
  };

  //adapta los campos 
  const formatResults = (data, sourceType) => {
    if (!Array.isArray(data)) return [];

    return data.map((item) => {
      const src = item._source || item; // resultados desde source

      if (sourceType.includes("book")) {
        // results for books
        return {
          id: item._id || src.book_id || Math.random(),
          type: "book",
          title: src.title || "Untitled",
          description: src.description || "No description available.",
          authors: src.authors,
          categories: src.categories,
          publisher: src.publisher || "",
          publishedDate: src.publisheddate || "",
          previewLink: src.previewlink || "",
          infoLink: src.infolink || "",
          image: src.image || "",
          ratings: src.ratingscount || src.review_score || 0,
          sourceType
        };
      }

      if (sourceType.includes("review")) {
        // results for reviews
        return {
          id: item._id || Math.random(),
          type: "review",
          title: src.title || "No title",
          summary: src["review/summary"] || "",
          text: src["review/text"] || "",
          score: src["review/score"] || 0,
          helpfulness: src["review/helpfulness"] || "",
          user: src.profilename || src.user_id || "",
          time: src["review/time"] || "",
          book_id: src.book_id || "",

          image_link: src.image_link,
          preview_link: src.preview_link,
          info_link: src.info_link,
          publisher: src.publisher,
          authors: src.authors,
          categories: src.categories,
          description: src.description,

          price: src.price,
          asin_or_id: src.id,
          _score: item._score,

          sourceType
        };
      }

      // Results for maria
      return {
        id: src.book_id || Math.random(),
        type: "mariadb",
        title: src.title || "Untitled",
        description: src.description || "",
        authors: src.authors,
        categories: src.categories,
        publisher: src.publisher || "",
        publishedDate: src.review_time || "",
        previewLink: src.preview_link || "",
        infoLink: src.info_link || "",
        image: src.image_link || "",
        ratings: src.review_score || src.ratings_count || 0,

        review_title: src.review_title,
        review_text: src.review_text,
        review_id: src.review_id,
        profile_name: src.profile_name,
        user_id: src.user_id,
        ratings_count: src.ratings_count,
        _score: item._score,

        sourceType
      };
    });
  };


  //Muestra resultados segun fuente elegida
  const handleSourceSelect = (sourceId) => {
    setSelectedSource(sourceId);

    let key = "";
    switch (sourceId) {
      case "vector-search":
        key = "books_vector";
        break;
      case "vector-reviews":
        key = "reviews_vector";
        break;
      case "text-books":
        key = "books_text";
        break;
      case "text-reviews":
        key = "reviews_text";
        break;
      case "mariadb":
        key = "mariadb";
        break;
      default:
        key = "books_text";
    }

    const formatted = formatResults(allResults[key], key);
    setSearchResults(formatted);
  };


  //Publicar prompt en el feed
  const handlePublishToFeed = async () => {
    if (!prompt.trim()) {
      inputRef.current?.focus();
      return;
    }
    if (!id_user) {
      setPostError("Please Login to publish a prompt.");
      return;
    }

    setIsPosting(true);
    setPostOk(false);
    setPostError("");

    try {
      //Llamar al backend para publicar
      await Prompts.postPrompt(id_user, prompt.trim());
      setPostOk(true);  //Mensaje de exito
      setPrompt("");
      setTimeout(() => setPostOk(false), 1500);
    } catch (e) {
      setPostError(e.message || "Error during prompt posting");
    } finally {
      setIsPosting(false);
    }
  };



  const canPublish = useMemo(
    () => Boolean(prompt.trim()) && !isPosting,
    [prompt, isPosting]
  );

  return (
    <div className={`${s.container} ${s[theme]}`}>
      <div className={s.header}>
        <h1 className={s.title}>Find Books</h1>
        <button
          className={s.themeToggle}
          onClick={() => setTheme(theme === "colorful" ? "formal" : "colorful")}
          aria-label="Toggle theme"
        >
          {theme === "colorful" ? "🎨" : "💼"}
        </button>
      </div>

      <div className={s.searchSection}>
        <div className={s.inputGroup}>
          <label htmlFor="search-prompt" className={s.label}>
            What are you looking for?
          </label>
          <textarea
            id="search-prompt"
            className={s.textarea}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Enter your search prompt here..."
            rows={4}
            aria-describedby="search-help"
            ref={inputRef}
          />
          <p id="search-help" className={s.helpText}>
            Describe the type of book or topic you're interested in
          </p>
        </div>

        <div className={s.buttonGroup}>
          <button
            className={`${s.button} ${s.searchButton}`}
            onClick={handleSearch}
            disabled={!prompt.trim() || isSearching}
            aria-label="Search for books"
          >
            {isSearching ? "Searching..." : "Search"}
          </button>
          <button
            className={`${s.button} ${s.publishButton}`}
            onClick={handlePublishToFeed}
            disabled={!prompt.trim()}
            aria-label="Publish prompt to feed"
          >
            {isPosting ? "Publishing…" : "Publish to my Feed"}
          </button>
        </div>

        {postOk && <div className={s.successBanner}>Prompt published</div>}
        {!!postError && <div className={s.errorBanner}>Error when posting {postError}</div>}
      </div>

      {/* Seleccion de fuentes */}
      {!isSearching && hasSearched && !selectedSource && (
        <div className={s.sourcesSection}>
          <h2 className={s.sectionTitle}>Choose a source to search:</h2>
          <div className={s.sourceGrid}>
            {sources.map((source) => {
              const key = keyForSource(source.id);
              const time = sourceTimes[key];
              return (
                <button
                  key={source.id}
                  className={s.sourceButton}
                  onClick={() => handleSourceSelect(source.id)}
                  aria-label={`Search in ${source.name} (${formatMs(time)})`}
                >
                  {/* Espacio de tiempo */}
                  <span className={s.sourceIcon}>{formatMs(time)}</span>
                  <span className={s.sourceName}>{source.name}</span>
                </button>
              )
            })}
          </div>
        </div>
      )}

      {searchResults.length > 0 && (
        <div className={s.resultsSection}>
          <div className={s.resultsHeader}>
            <h2 className={s.sectionTitle}>
              Results from {sources.find((s) => s.id === selectedSource)?.name}
            </h2>
            <button
              className={s.backButton}
              onClick={() => {
                setSelectedSource("");
                setSearchResults([]);
              }}
              aria-label="Back to sources"
            >
              ← Back to sources
            </button>
          </div>

          <div className={s.booksGrid}>
            {searchResults.map((item) => (
              <div key={item.id} className={s.bookCard}>
                {/* score */}
                {typeof item._score === "number" && (
                  <div className={s.badge}>score: {item._score.toFixed(2)}</div>
                )}

                <h3 className={s.bookTitle}>{item.title}</h3>

                {/* results for books */}
                {item.type === "book" && (
                  <>
                    {item.image && (
                      <img src={item.image} alt={item.title} className={s.bookImage} />
                    )}
                    <p className={s.bookDescription}>{item.description}</p>

                    
                    {item.authors != null && (
                      <div><strong>Authors:</strong> {String(item.authors)}</div>
                    )}
                    {item.categories != null && (
                      <div><strong>Categories:</strong> {String(item.categories)}</div>
                    )}

                    <div><strong>Publisher:</strong> {item.publisher}</div>
                    <div><strong>Date:</strong> {item.time}</div>
                    <div><strong>Ratings:</strong> {item.ratings}</div>
                    {item.previewLink && (
                      <a href={item.previewLink} target="_blank" rel="noreferrer">Preview</a>
                    )}
                    {item.infoLink && (
                      <a href={item.infoLink} target="_blank" rel="noreferrer">Info</a>
                    )}
                  </>
                )}

                {/* results for reviews */}
                {item.type === "review" && (
                  <>
                    
                    {item.image_link && (
                      <img src={item.image_link} alt={`${item.title} cover`} className={s.bookImage} />
                    )}

                    <p><strong>Summary:</strong> {item.summary}</p>
                    <p>{item.text}</p>

                    <div><strong>Score:</strong> {item.score}</div>
                    <div><strong>User:</strong> {item.user}</div>
                    <div><strong>Date:</strong> {item.time}</div>
                    <div><strong>Book ID:</strong> {item.book_id}</div>

                    
                    {item.publisher && (
                      <div><strong>Publisher:</strong> {item.publisher}</div>
                    )}
                    {item.authors != null && (
                      <div><strong>Authors:</strong> {String(item.authors)}</div>
                    )}
                    {item.categories != null && (
                      <div><strong>Categories:</strong> {String(item.categories)}</div>
                    )}
                    {item.description && (
                      <p><strong>Book description:</strong> {item.description}</p>
                    )}
                    {item["review/helpfulness"] && (
                      <div><strong>Helpfulness:</strong> {item["review/helpfulness"]}</div>
                    )}
                    {item.asin_or_id && (
                      <div><strong>ID:</strong> {item.asin_or_id}</div>
                    )}
                    {item.price != null && (
                      <div><strong>Price:</strong> {item.price}</div>
                    )}
                    {item.preview_link && (
                      <a href={item.preview_link} target="_blank" rel="noreferrer">Preview</a>
                    )}
                    {item.info_link && (
                      <a href={item.info_link} target="_blank" rel="noreferrer">Info</a>
                    )}
                  </>
                )}

                {/* results from mariadb */}
                {item.type === "mariadb" && (
                  <>
                    {item.image && (
                      <img src={item.image} alt={item.title} className={s.bookImage} />
                    )}
                    <p>{item.description}</p>

                    {item.authors != null && (
                      <div><strong>Authors:</strong> {String(item.authors)}</div>
                    )}
                    {item.categories != null && (
                      <div><strong>Categories:</strong> {String(item.categories)}</div>
                    )}

                    <div><strong>Publisher:</strong> {item.publisher}</div>
                    <div><strong>Date:</strong> {item.publishedDate}</div>
                    <div><strong>Ratings / Score:</strong> {item.ratings}</div>
                    {item.previewLink && (
                      <a href={item.previewLink} target="_blank" rel="noreferrer">Preview</a>
                    )}
                    {item.infoLink && (
                      <a href={item.infoLink} target="_blank" rel="noreferrer">Info</a>
                    )}

                    {/* reviews for maria */}
                    {item.review_title && (
                      <div><strong>Review title:</strong> {item.review_title}</div>
                    )}
                    {item.review_text && (
                      <p>{item.review_text}</p>
                    )}
                    {item.review_id && (
                      <div><strong>Review ID:</strong> {item.review_id}</div>
                    )}
                    {item.profile_name && (
                      <div><strong>Profile:</strong> {item.profile_name}</div>
                    )}
                    {item.user_id && (
                      <div><strong>User ID:</strong> {item.user_id}</div>
                    )}
                    {item.ratings_count != null && (
                      <div><strong>Ratings (book):</strong> {item.ratings_count}</div>
                    )}
                  </>
                )}

                <div className={s.metaItem}>
                  <strong>Source:</strong> {item.sourceType}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

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
          <span className={s.navLabel}>Find Friends</span>
        </NavLink>

        <NavLink to="/me" className={navItemClass} aria-label="Me">
          <span className={s.navIcon}>👤</span>
          <span className={s.navLabel}>Me</span>
        </NavLink>
      </nav>
    </div>
  )
}

export default Ask