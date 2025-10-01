"use client"

import { useState } from "react"
import s from "./Me.module.css"

export default function Me() {
  const [theme, setTheme] = useState("colorful")
  const [isEditing, setIsEditing] = useState(false)
  const [editingPromptId, setEditingPromptId] = useState(null)

  const [profile, setProfile] = useState({
    username: "johndoe",
    fullName: "John Doe",
    email: "john.doe@example.com",
    bio: "Book lover and AI enthusiast",
    avatar: "/diverse-woman-avatar.png",
    followers: 1234,
    following: 567,
  })

  const [editForm, setEditForm] = useState({ ...profile })

  const [prompts, setPrompts] = useState([
    {
      id: 1,
      text: "Find me books about artificial intelligence and machine learning for beginners",
      createdAt: "2024-01-15",
      likes: 45,
    },
    {
      id: 2,
      text: "Looking for mystery novels set in Victorian England",
      createdAt: "2024-01-10",
      likes: 32,
    },
    {
      id: 3,
      text: "Recommend science fiction books with strong female protagonists",
      createdAt: "2024-01-05",
      likes: 78,
    },
  ])

  const [editPromptText, setEditPromptText] = useState("")

  const handleEditProfile = () => {
    setIsEditing(true)
    setEditForm({ ...profile })
  }

  const handleSaveProfile = () => {
    setProfile({ ...editForm })
    setIsEditing(false)
  }

  const handleCancelEdit = () => {
    setIsEditing(false)
    setEditForm({ ...profile })
  }

  const handleEditPrompt = (prompt) => {
    setEditingPromptId(prompt.id)
    setEditPromptText(prompt.text)
  }

  const handleSavePrompt = (id) => {
    setPrompts(prompts.map((p) => (p.id === id ? { ...p, text: editPromptText } : p)))
    setEditingPromptId(null)
    setEditPromptText("")
  }

  const handleCancelPromptEdit = () => {
    setEditingPromptId(null)
    setEditPromptText("")
  }

  const handleDeletePrompt = (id) => {
    if (window.confirm("Are you sure you want to delete this prompt?")) {
      setPrompts(prompts.filter((p) => p.id !== id))
    }
  }

  const handleLogout = () => {
    if (window.confirm("Are you sure you want to logout?")) {
      console.log("Logging out...")
      // Logout logic here
    }
  }

  return (
    <div className={`${s.container} ${s[theme]}`}>
      <header className={s.header}>
        <h1 className={s.title}>My Profile</h1>
        <button
          onClick={() => setTheme(theme === "colorful" ? "formal" : "colorful")}
          className={s.themeToggle}
          aria-label="Toggle theme"
        >
          {theme === "colorful" ? "🎨" : "💼"}
        </button>
      </header>

      <main className={s.main}>
        {/* Profile Section */}
        <section className={s.profileSection}>
          <div className={s.profileHeader}>
            <img src={profile.avatar || "/placeholder.svg"} alt={`${profile.username}'s avatar`} className={s.avatar} />
            <div className={s.stats}>
              <div className={s.statItem}>
                <span className={s.statNumber}>{profile.followers}</span>
                <span className={s.statLabel}>Followers</span>
              </div>
              <div className={s.statItem}>
                <span className={s.statNumber}>{profile.following}</span>
                <span className={s.statLabel}>Following</span>
              </div>
            </div>
          </div>

          {!isEditing ? (
            <div className={s.profileInfo}>
              <h2 className={s.profileName}>{profile.fullName}</h2>
              <p className={s.profileUsername}>@{profile.username}</p>
              <p className={s.profileEmail}>{profile.email}</p>
              <p className={s.profileBio}>{profile.bio}</p>
              <button onClick={handleEditProfile} className={s.editButton} aria-label="Edit profile">
                Edit Profile
              </button>
            </div>
          ) : (
            <form
              className={s.editForm}
              onSubmit={(e) => {
                e.preventDefault()
                handleSaveProfile()
              }}
            >
              <div className={s.formGroup}>
                <label htmlFor="fullName" className={s.label}>
                  Full Name
                </label>
                <input
                  id="fullName"
                  type="text"
                  value={editForm.fullName}
                  onChange={(e) => setEditForm({ ...editForm, fullName: e.target.value })}
                  className={s.input}
                  aria-required="true"
                />
              </div>

              <div className={s.formGroup}>
                <label htmlFor="username" className={s.label}>
                  Username
                </label>
                <input
                  id="username"
                  type="text"
                  value={editForm.username}
                  onChange={(e) => setEditForm({ ...editForm, username: e.target.value })}
                  className={s.input}
                  aria-required="true"
                />
              </div>

              <div className={s.formGroup}>
                <label htmlFor="email" className={s.label}>
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  value={editForm.email}
                  onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                  className={s.input}
                  aria-required="true"
                />
              </div>

              <div className={s.formGroup}>
                <label htmlFor="bio" className={s.label}>
                  Bio
                </label>
                <textarea
                  id="bio"
                  value={editForm.bio}
                  onChange={(e) => setEditForm({ ...editForm, bio: e.target.value })}
                  className={s.textarea}
                  rows="3"
                  aria-label="Biography"
                />
              </div>

              <div className={s.formActions}>
                <button type="submit" className={s.saveButton} aria-label="Save changes">
                  Save Changes
                </button>
                <button type="button" onClick={handleCancelEdit} className={s.cancelButton} aria-label="Cancel editing">
                  Cancel
                </button>
              </div>
            </form>
          )}
        </section>

        {/* My Prompts Section */}
        <section className={s.promptsSection}>
          <h2 className={s.sectionTitle}>My Prompts</h2>
          <div className={s.promptsList}>
            {prompts.length === 0 ? (
              <p className={s.emptyState}>You haven't created any prompts yet.</p>
            ) : (
              prompts.map((prompt) => (
                <div key={prompt.id} className={s.promptCard}>
                  {editingPromptId === prompt.id ? (
                    <div className={s.promptEditForm}>
                      <textarea
                        value={editPromptText}
                        onChange={(e) => setEditPromptText(e.target.value)}
                        className={s.promptTextarea}
                        rows="3"
                        aria-label="Edit prompt text"
                      />
                      <div className={s.promptActions}>
                        <button
                          onClick={() => handleSavePrompt(prompt.id)}
                          className={s.savePromptButton}
                          aria-label="Save prompt"
                        >
                          Save
                        </button>
                        <button
                          onClick={handleCancelPromptEdit}
                          className={s.cancelPromptButton}
                          aria-label="Cancel editing prompt"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className={s.promptContent}>
                        <p className={s.promptText}>{prompt.text}</p>
                        <div className={s.promptMeta}>
                          <span className={s.promptDate}>{new Date(prompt.createdAt).toLocaleDateString()}</span>
                          <span className={s.promptLikes}>
                            <svg className={s.heartIcon} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
                            </svg>
                            {prompt.likes}
                          </span>
                        </div>
                      </div>
                      <div className={s.promptActions}>
                        <button
                          onClick={() => handleEditPrompt(prompt)}
                          className={s.editPromptButton}
                          aria-label={`Edit prompt: ${prompt.text}`}
                        >
                          <svg
                            className={s.icon}
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            aria-hidden="true"
                          >
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                          </svg>
                          Edit
                        </button>
                        <button
                          onClick={() => handleDeletePrompt(prompt.id)}
                          className={s.deletePromptButton}
                          aria-label={`Delete prompt: ${prompt.text}`}
                        >
                          <svg
                            className={s.icon}
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            aria-hidden="true"
                          >
                            <polyline points="3 6 5 6 21 6" />
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                          </svg>
                          Delete
                        </button>
                      </div>
                    </>
                  )}
                </div>
              ))
            )}
          </div>
        </section>

        {/* Logout Section */}
        <section className={s.logoutSection}>
          <button onClick={handleLogout} className={s.logoutButton} aria-label="Logout from account">
            <svg
              className={s.logoutIcon}
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              aria-hidden="true"
            >
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
            Logout
          </button>
        </section>
      </main>

      {/* Bottom Navigation */}
      <nav className={s.bottomNav} role="navigation" aria-label="Main navigation">
        <button className={s.navItem} aria-label="Find Book">
          <svg
            className={s.navIcon}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            aria-hidden="true"
          >
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
          </svg>
          <span className={s.navLabel}>Find Book</span>
        </button>

        <button className={s.navItem} aria-label="Friends">
          <svg
            className={s.navIcon}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            aria-hidden="true"
          >
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
            <circle cx="9" cy="7" r="4" />
            <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
            <path d="M16 3.13a4 4 0 0 1 0 7.75" />
          </svg>
          <span className={s.navLabel}>Friends</span>
        </button>

        <button className={s.navItem} aria-label="Prompts">
          <svg
            className={s.navIcon}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            aria-hidden="true"
          >
            <circle cx="12" cy="12" r="10" />
            <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
          <span className={s.navLabel}>Prompts</span>
        </button>

        <button className={s.navItem} aria-label="Feed">
          <svg
            className={s.navIcon}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            aria-hidden="true"
          >
            <path d="M4 11a9 9 0 0 1 9 9" />
            <path d="M4 4a16 16 0 0 1 16 16" />
            <circle cx="5" cy="19" r="1" />
          </svg>
          <span className={s.navLabel}>Feed</span>
        </button>

        <button className={`${s.navItem} ${s.active}`} aria-label="Me" aria-current="page">
          <svg
            className={s.navIcon}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            aria-hidden="true"
          >
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
          <span className={s.navLabel}>Me</span>
        </button>
      </nav>
    </div>
  )
}
