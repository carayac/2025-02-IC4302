"use client"

import { useState } from "react"
import s from "./Ask.module.css"

const Ask = () => {
  const [prompt, setPrompt] = useState("")
  const [searchResults, setSearchResults] = useState([])
  const [selectedSource, setSelectedSource] = useState("")
  const [isSearching, setIsSearching] = useState(false)
  const [theme, setTheme] = useState("colorful") // 'colorful' or 'formal'

  const sources = [
    { id: "vector-search", name: "Vector Search", icon: "🔍" },
    { id: "vector-reviews", name: "Vector Reviews", icon: "⭐" },
    { id: "text-books", name: "Text Books", icon: "📚" },
    { id: "text-reviews", name: "Text Reviews", icon: "📝" },
    { id: "mariadb", name: "MariaDB", icon: "🗄️" },
  ]

  const mockBooks = [
    {
      id: 1,
      title: "The Art of Clean Code",
      authors: ["Robert C. Martin", "John Doe"],
      description: "A comprehensive guide to writing maintainable and readable code that stands the test of time.",
      publishedDate: "2023-05-15",
      previewLink: "https://example.com/preview/1",
      publisher: "Tech Publications",
      rating: 4.8,
      categories: ["Programming", "Software Development", "Best Practices"],
    },
    {
      id: 2,
      title: "Modern React Patterns",
      authors: ["Jane Smith"],
      description: "Explore advanced React patterns and techniques for building scalable applications.",
      publishedDate: "2023-08-22",
      previewLink: "https://example.com/preview/2",
      publisher: "Web Dev Press",
      rating: 4.6,
      categories: ["React", "JavaScript", "Frontend"],
    },
    {
      id: 3,
      title: "Database Design Fundamentals",
      authors: ["Michael Johnson", "Sarah Wilson"],
      description: "Learn the principles of effective database design and optimization strategies.",
      publishedDate: "2023-03-10",
      previewLink: "https://example.com/preview/3",
      publisher: "Data Science Books",
      rating: 4.7,
      categories: ["Database", "SQL", "Data Management"],
    },
  ]

  const handleSearch = () => {
    if (!prompt.trim()) return
    setIsSearching(true)
    setSearchResults([])
    setSelectedSource("")

    // Simulate search delay
    setTimeout(() => {
      setIsSearching(false)
    }, 1000)
  }

  const handleSourceSelect = (sourceId) => {
    setSelectedSource(sourceId)
    setSearchResults(mockBooks)
  }

  const handlePublishToFeed = () => {
    if (!prompt.trim()) return
    // Simulate publishing prompt to feed
    alert(`Prompt published to feed: "${prompt}"`)
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    })
  }

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
            Publish to my Feed
          </button>
        </div>
      </div>

      {!isSearching && prompt && !selectedSource && (
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
        <button className={`${s.navItem} ${s.active}`} aria-label="Find Books">
          <span className={s.navIcon}>📚</span>
          <span className={s.navLabel}>Find Book</span>
        </button>
        <button className={s.navItem} aria-label="Friends">
          <span className={s.navIcon}>👥</span>
          <span className={s.navLabel}>Friends</span>
        </button>
        <button className={s.navItem} aria-label="Prompts">
          <span className={s.navIcon}>💭</span>
          <span className={s.navLabel}>Prompts</span>
        </button>
        <button className={s.navItem} aria-label="Feed">
          <span className={s.navIcon}>📰</span>
          <span className={s.navLabel}>Feed</span>
        </button>
        <button className={s.navItem} aria-label="Profile">
          <span className={s.navIcon}>👤</span>
          <span className={s.navLabel}>Me</span>
        </button>
      </nav>
    </div>
  )
}

export default Ask
