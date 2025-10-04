"use client"

import { useMemo, useRef, useState, useEffect } from "react"
import s from "./Ask.module.css"
import { Link, NavLink, useNavigate, useLocation } from "react-router-dom";
import { Prompts } from "../../lib/api/APIcalls"; //Objeto de funciones


const navItemClass = ({ isActive }) =>
  `${s.navItem} ${isActive ? s.active : ""}`

const Ask = () => {
  const [prompt, setPrompt] = useState("")
  const [searchResults, setSearchResults] = useState([])
  const [selectedSource, setSelectedSource] = useState("")
  const [isSearching, setIsSearching] = useState(false)
  const [hasSearched, setHasSearched] = useState(false);
  const [theme, setTheme] = useState("colorful") // 'colorful' or 'formal'

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
  const user = getStoredUser();
  const id_user = getUserId(user);

  const location = useLocation();


  useEffect(() => {

    const fromState = location.state && location.state.presetPrompt;

    //Bringing back the prompt from feed
    let fromQuery = null;
    try {
      const qs = new URLSearchParams(location.search);
      fromQuery = qs.get("prompt");
    } catch { }

    const incoming = fromState ?? fromQuery;
    if (incoming && !prompt) {
      setPrompt(incoming);

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

  //User id for the post Endpoint
  function getUserId(u) {
    if (!u) return null;
    return u.id_user ?? u.id ?? u.userid ?? u.userId ?? u._id ?? null;
  }

  const handleSearch = () => {
    if (!prompt.trim()) return;
    setIsSearching(true);
    setHasSearched(true);
    setSearchResults([]);
    setSelectedSource("");

    // GENERATE ENDPOINT
    setTimeout(() => {
      setIsSearching(false);
    }, 600);
  };

  const handleSourceSelect = (sourceId) => {
    setSelectedSource(sourceId);
    setSearchResults([]);
  }

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
      await Prompts.postPrompt(id_user, prompt.trim());
      setPostOk(true);
      setPrompt("");
      setTimeout(() => setPostOk(false), 1500);
    } catch (e) {
      setPostError(e.message || "Error during prompt posting");
    } finally {
      setIsPosting(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    })
  }

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

        { }
        {postOk && (
          <div className={s.successBanner}>
            Prompt published
          </div>
        )}
        {!!postError && (
          <div className={s.errorBanner}>
            Error when posting {postError}
          </div>
        )}

      </div>

      {!isSearching && hasSearched && !selectedSource && (
        <div className={s.sourcesSection}>
          <h2 className={s.sectionTitle}>Choose a source to search:</h2>
          <div className={s.sourceGrid}>
            {sources.map((source) => (
              <button
                key={source.id}
                className={s.sourceButton}
                onClick={() => handleSourceSelect(source.id)}
                aria-label={`Search in ${source.name}`}
              >
                <span className={s.sourceIcon}>{source.icon}</span>
                <span className={s.sourceName}>{source.name}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {searchResults.length > 0 && (
        <div className={s.resultsSection}>
          <div className={s.resultsHeader}>
            <h2 className={s.sectionTitle}>Results from {sources.find((s) => s.id === selectedSource)?.name}</h2>
            <button
              className={s.backButton}
              onClick={() => {
                setSelectedSource("")
                setSearchResults([])
              }}
              aria-label="Back to sources"
            >
              ← Back to sources
            </button>
          </div>

          <div className={s.booksGrid}>
            {searchResults.map((book) => (
              <div key={book.id} className={s.bookCard}>
                <div className={s.bookHeader}>
                  <h3 className={s.bookTitle}>{book.title}</h3>
                  <div className={s.rating}>
                    <span className={s.stars}>⭐</span>
                    <span className={s.ratingValue}>{book.rating}</span>
                  </div>
                </div>

                <div className={s.bookAuthors}>By: {book.authors.join(", ")}</div>

                <p className={s.bookDescription}>{book.description}</p>

                <div className={s.bookMeta}>
                  <div className={s.metaItem}>
                    <strong>Publisher:</strong> {book.publisher}
                  </div>
                  <div className={s.metaItem}>
                    <strong>Published:</strong> {formatDate(book.publishedDate)}
                  </div>
                </div>

                <div className={s.categories}>
                  {book.categories.map((category, index) => (
                    <span key={index} className={s.category}>
                      {category}
                    </span>
                  ))}
                </div>

                <div className={s.bookActions}>
                  <a
                    href={book.previewLink}
                    className={s.previewLink}
                    target="_blank"
                    rel="noopener noreferrer"
                    aria-label={`Preview ${book.title}`}
                  >
                    Preview
                  </a>
                  <button className={s.moreInfoButton}>More Information</button>
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
