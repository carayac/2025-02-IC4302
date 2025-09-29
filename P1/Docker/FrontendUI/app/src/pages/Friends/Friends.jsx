"use client"

import { useState } from "react"
import s from "./Friends.module.css"

const Friends = () => {
  const [searchTerm, setSearchTerm] = useState("")
  const [theme, setTheme] = useState("colorful")
  const [followedUsers, setFollowedUsers] = useState(new Set())

  // Mock users data
  const mockUsers = [
    { id: 1, username: "bookworm_sarah", fullName: "Sarah Johnson", avatar: "👩‍💼", followers: 1234 },
    { id: 2, username: "reading_enthusiast", fullName: "Mike Chen", avatar: "👨‍🎓", followers: 856 },
    { id: 3, username: "novel_lover", fullName: "Emma Davis", avatar: "👩‍🎨", followers: 2341 },
    { id: 4, username: "bookclub_admin", fullName: "Alex Rodriguez", avatar: "👨‍💻", followers: 567 },
    { id: 5, username: "literature_fan", fullName: "Jessica Brown", avatar: "👩‍🔬", followers: 1789 },
    { id: 6, username: "story_seeker", fullName: "David Wilson", avatar: "👨‍🎨", followers: 923 },
    { id: 7, username: "page_turner", fullName: "Lisa Anderson", avatar: "👩‍🏫", followers: 1456 },
    { id: 8, username: "book_reviewer", fullName: "Tom Garcia", avatar: "👨‍🔬", followers: 678 },
  ]

  const filteredUsers = mockUsers.filter(
    (user) =>
      user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.fullName.toLowerCase().includes(searchTerm.toLowerCase()),
  )

  const handleFollow = (userId) => {
    setFollowedUsers((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(userId)) {
        newSet.delete(userId)
      } else {
        newSet.add(userId)
      }
      return newSet
    })
  }

  const toggleTheme = () => {
    setTheme((prev) => (prev === "colorful" ? "formal" : "colorful"))
  }

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
              placeholder="Search by username or name..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className={s.searchInput}
              aria-describedby="search-help"
            />
            <span id="search-help" className={s.searchHelp}>
              Find friends by typing their username or full name
            </span>
          </div>
        </div>

        <div className={s.resultsSection}>
          <div className={s.resultsHeader}>
            <h2 className={s.resultsTitle}>{searchTerm ? `Results for "${searchTerm}"` : "Suggested Friends"}</h2>
            <span className={s.resultsCount}>
              {filteredUsers.length} {filteredUsers.length === 1 ? "user" : "users"} found
            </span>
          </div>

          <div className={s.usersList}>
            {filteredUsers.map((user) => (
              <div key={user.id} className={s.userCard}>
                <div className={s.userInfo}>
                  <div className={s.userAvatar} aria-hidden="true">
                    {user.avatar}
                  </div>
                  <div className={s.userDetails}>
                    <h3 className={s.username}>{user.username}</h3>
                    <p className={s.fullName}>{user.fullName}</p>
                    <span className={s.followers}>{user.followers.toLocaleString()} followers</span>
                  </div>
                </div>
                <button
                  onClick={() => handleFollow(user.id)}
                  className={`${s.followButton} ${followedUsers.has(user.id) ? s.following : s.notFollowing}`}
                  aria-label={`${followedUsers.has(user.id) ? "Unfollow" : "Follow"} ${user.username}`}
                >
                  {followedUsers.has(user.id) ? "Unfollow" : "Follow"}
                </button>
              </div>
            ))}
          </div>

          {filteredUsers.length === 0 && searchTerm && (
            <div className={s.noResults}>
              <p className={s.noResultsText}>No users found matching "{searchTerm}"</p>
              <p className={s.noResultsSubtext}>Try searching with a different term</p>
            </div>
          )}
        </div>
      </main>

      <nav className={s.bottomNav} role="navigation" aria-label="Main navigation">
        <button className={s.navItem} aria-label="Find Book">
          <span className={s.navIcon}>📚</span>
          <span className={s.navLabel}>Find Book</span>
        </button>
        <button className={`${s.navItem} ${s.active}`} aria-label="Friends" aria-current="page">
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

export default Friends
