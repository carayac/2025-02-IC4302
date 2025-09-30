"use client"

import { useState } from "react"
import s from "./Prompt.module.css"

const Prompt = () => {
  const [searchTerm, setSearchTerm] = useState("")
  const [theme, setTheme] = useState("colorful")
  const [prompts, setPrompts] = useState([
    {
      id: 1,
      text: "What are the best practices for React component optimization?",
      username: "reactdev_pro",
      likes: 24,
      timestamp: "2 hours ago",
    },
    {
      id: 2,
      text: "How to implement dark mode in a React application?",
      username: "ui_designer",
      likes: 18,
      timestamp: "4 hours ago",
    },
    {
      id: 3,
      text: "Best strategies for state management in large React apps?",
      username: "senior_dev",
      likes: 31,
      timestamp: "6 hours ago",
    },
    {
      id: 4,
      text: "How to optimize bundle size in React applications?",
      username: "performance_guru",
      likes: 15,
      timestamp: "8 hours ago",
    },
    {
      id: 5,
      text: "What's the difference between useEffect and useLayoutEffect?",
      username: "react_teacher",
      likes: 42,
      timestamp: "1 day ago",
    },
  ])

  const handleLike = (promptId) => {
    setPrompts((prevPrompts) =>
      prevPrompts.map((prompt) => (prompt.id === promptId ? { ...prompt, likes: prompt.likes + 1 } : prompt)),
    )
  }

  const filteredPrompts = prompts.filter(
    (prompt) =>
      prompt.text.toLowerCase().includes(searchTerm.toLowerCase()) ||
      prompt.username.toLowerCase().includes(searchTerm.toLowerCase()),
  )

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
            Search prompts or users
          </label>
          <div className={s.searchInputWrapper}>
            <input
              id="search"
              type="text"
              className={s.searchInput}
              placeholder="Search by prompt text or username..."
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
            Find prompts by content or discover posts from specific users
          </p>
        </div>
      </section>

      {/* Results Section */}
      <main className={s.resultsSection}>
        <div className={s.resultsHeader}>
          <h2 className={s.resultsTitle}>{searchTerm ? `Results for "${searchTerm}"` : "Recent Prompts"}</h2>
          <span className={s.resultsCount}>
            {filteredPrompts.length} prompt{filteredPrompts.length !== 1 ? "s" : ""}
          </span>
        </div>

        <div className={s.promptsList}>
          {filteredPrompts.map((prompt) => (
            <article key={prompt.id} className={s.promptCard}>
              <div className={s.promptHeader}>
                <div className={s.userInfo}>
                  <div className={s.avatar}>{prompt.username.charAt(0).toUpperCase()}</div>
                  <div className={s.userDetails}>
                    <h3 className={s.username}>@{prompt.username}</h3>
                    <time className={s.timestamp}>{prompt.timestamp}</time>
                  </div>
                </div>
              </div>

              <div className={s.promptContent}>
                <p className={s.promptText}>{prompt.text}</p>
              </div>

              <div className={s.promptActions}>
                <button
                  className={s.likeButton}
                  onClick={() => handleLike(prompt.id)}
                  aria-label={`Like prompt by ${prompt.username}`}
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
                  </svg>
                  <span className={s.likeCount}>{prompt.likes}</span>
                </button>
              </div>
            </article>
          ))}
        </div>

        {filteredPrompts.length === 0 && (
          <div className={s.emptyState}>
            <div className={s.emptyIcon}>
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <circle cx="11" cy="11" r="8"></circle>
                <path d="m21 21-4.35-4.35"></path>
              </svg>
            </div>
            <h3 className={s.emptyTitle}>No prompts found</h3>
            <p className={s.emptyDescription}>Try adjusting your search terms or browse all prompts</p>
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

        <button className={s.navItem} aria-label="Friends">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
            <circle cx="9" cy="7" r="4"></circle>
            <path d="M22 21v-2a4 4 0 0 0-3-3.87"></path>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
          </svg>
          <span>Friends</span>
        </button>

        <button className={`${s.navItem} ${s.active}`} aria-label="Prompts" aria-current="page">
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

        <button className={s.navItem} aria-label="Profile">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
            <circle cx="12" cy="7" r="4"></circle>
          </svg>
          <span>Me</span>
        </button>
      </nav>
    </div>
  )
}

export default Prompt
