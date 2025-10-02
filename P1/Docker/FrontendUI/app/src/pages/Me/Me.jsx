"use client"

import { useEffect, useMemo, useRef, useState, useCallback } from "react" 
import { useNavigate } from "react-router-dom"                             
import s from "./Me.module.css"
import { AuthApi, Prompts } from "../../lib/api/APIcalls"                 


function getStoredUser() {
  try {
    const raw = localStorage.getItem("user")
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}
function getUserId(u) {
  if (!u) return null
  return u.id_user ?? u.id ?? u.userid ?? u.userId ?? u._id ?? null
}
function formatDate(d) {
  try {
    return new Date(d).toLocaleDateString()
  } catch {
    return d ?? ""
  }
}

export default function Me() {
  const navigate = useNavigate() 

  const [theme, setTheme] = useState("colorful")
  const [isEditing, setIsEditing] = useState(false)
  const [editingPromptId, setEditingPromptId] = useState(null)

  
  const [profile, setProfile] = useState({
    id: null,                
    name: "",                
    lastname: "",            
    email: "",               
    description: "",         
    avatar: "/diverse-woman-avatar.png",
    followers: null,        
    following: null,         
  })

  
  const [editForm, setEditForm] = useState({
    name: "",
    lastname: "",
    description: "",
  })

  
  const [prompts, setPrompts] = useState([])

  const [editPromptText, setEditPromptText] = useState("")
  const [loading, setLoading] = useState(true)        
  const [savingProfile, setSavingProfile] = useState(false) 
  const [savingPrompt, setSavingPrompt] = useState(false)   
  const [errorMsg, setErrorMsg] = useState("")        
  const [infoMsg, setInfoMsg] = useState("")         

 
  useEffect(() => {
    const u = getStoredUser()
    const id = getUserId(u)
    if (!id) {
      
      navigate("/")
      return
    }

    let cancelled = false
    async function loadAll() {
      setLoading(true)
      setErrorMsg("")
      try {
        //Showing profile data
        const userRes = await AuthApi.me(id)
        
        if (!cancelled && userRes) {
          setProfile((prev) => ({
            ...prev,
            id: userRes.id ?? id,
            name: userRes.name ?? "",
            lastname: userRes.lastname ?? "",
            email: userRes.email ?? "",
            description: userRes.description ?? "",
            //AQUI FOLLOWERS
          }))
          setEditForm({
            name: userRes.name ?? "",
            lastname: userRes.lastname ?? "",
            description: userRes.description ?? "",
          })
        }

        //Showing prompts
        const myPrompts = await Prompts.getMyPrompts(id)
        
        if (!cancelled && Array.isArray(myPrompts)) {
          setPrompts(
            myPrompts.map((p) => ({
              id: p.id,
              text: p.text,
              createdAt: p.created_at, 
              likes: p.likes,
            }))
          )
        }
      } catch (err) {
        if (!cancelled) {
          setErrorMsg("Error loading information. Try again.")
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    loadAll()
    return () => {
      cancelled = true
    }
  }, [navigate])

  const handleEditProfile = () => {
    setIsEditing(true)
    setEditForm({
      name: profile.name,
      lastname: profile.lastname,
      description: profile.description,
    })
  }

  
  const handleSaveProfile = async () => {
    if (!profile.id) return
    setSavingProfile(true)
    setErrorMsg("")
    setInfoMsg("")
    try {
      await AuthApi.editUser({
        id: profile.id,
        name: editForm.name,
        lastname: editForm.lastname,
        description: editForm.description,
      })
      setProfile((prev) => ({
        ...prev,
        name: editForm.name,
        lastname: editForm.lastname,
        description: editForm.description,
      }))
      setIsEditing(false)
      setInfoMsg("Your profile has been updated")
    } catch (err) {
      setErrorMsg("Could not save changes.")
    } finally {
      setSavingProfile(false)
    }
  }

  const handleCancelEdit = () => {
    setIsEditing(false)
    setEditForm({
      name: profile.name,
      lastname: profile.lastname,
      description: profile.description,
    })
  }

  const handleEditPrompt = (prompt) => {
    setEditingPromptId(prompt.id)
    setEditPromptText(prompt.text)
  }

  
 //Handle of saving prompt
  const handleSavePrompt = async (id) => {
    setSavingPrompt(true)
    setErrorMsg("")
    setInfoMsg("")
    try {
      await Prompts.editPrompt(id, editPromptText)
      setPrompts((curr) => curr.map((p) => (p.id === id ? { ...p, text: editPromptText } : p)))
      setEditingPromptId(null)
      setEditPromptText("")
      setInfoMsg("Your prompt has been updated.")
    } catch (err) {
      setErrorMsg("Could not update the prompt.")
    } finally {
      setSavingPrompt(false)
    }
  }

 //Handle of deleting prompt
  const handleDeletePrompt = async (id) => {
    if (!window.confirm("Are you sure you want to delete this prompt?")) return
    setErrorMsg("")
    setInfoMsg("")
    try {
      await Prompts.deletePrompt(id)
      setPrompts((curr) => curr.filter((p) => p.id !== id))
      setInfoMsg("Your prompt has been deleted.")
    } catch (err) {
      setErrorMsg("Could not delete this prompt.")
    }
  }

  //Handle of login out
  const handleLogout = () => {
    if (window.confirm("Are you sure you want to log out?")) {
      try {
        localStorage.removeItem("user") 
      } catch {}
      navigate("/")               
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
        
        {(loading || savingProfile || savingPrompt) && (
          <div className={s.infoBanner} role="status">Cargando...</div>
        )}
        {errorMsg && <div className={s.errorBanner} role="alert">{errorMsg}</div>}
        {infoMsg && <div className={s.successBanner} role="status">{infoMsg}</div>}

        
        <section className={s.profileSection}>
          <div className={s.profileHeader}>
            
            <img
              src={profile.avatar || "/placeholder.svg"}
              alt={`${profile.name} ${profile.lastname} avatar`}
              className={s.avatar}
            />
            <div className={s.stats}>
              <div className={s.statItem}>
                <span className={s.statNumber}>
                  {profile.followers ?? "--" }
                </span>
                <span className={s.statLabel}>Followers</span>
              </div>
              <div className={s.statItem}>
                <span className={s.statNumber}>
                  {profile.following ?? "--" }
                </span>
                <span className={s.statLabel}>Following</span>
              </div>
            </div>
          </div>

          {!isEditing ? (
            <div className={s.profileInfo}>
              
              <h2 className={s.profileName}>
                {profile.name} {profile.lastname}
              </h2>
              <p className={s.profileEmail}>{profile.email}</p>

              <p className={s.profileBio}>{profile.description}</p>

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
                <label htmlFor="name" className={s.label}>
                  Name
                </label>
                <input
                  id="name"
                  type="text"
                  value={editForm.name}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                  className={s.input}
                  aria-required="true"
                />
              </div>

              <div className={s.formGroup}>
                <label htmlFor="lastname" className={s.label}>
                  Lastname
                </label>
                <input
                  id="lastname"
                  type="text"
                  value={editForm.lastname}
                  onChange={(e) => setEditForm({ ...editForm, lastname: e.target.value })}
                  className={s.input}
                  aria-required="true"
                />
              </div>

              <div className={s.formGroup}>
                <label htmlFor="description" className={s.label}>
                  Description
                </label>
                <textarea
                  id="description"
                  value={editForm.description}
                  onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                  className={s.textarea}
                  rows="3"
                  aria-label="Profile description"
                />
              </div>

              <div className={s.formActions}>
                <button type="submit" className={s.saveButton} aria-label="Save changes" disabled={savingProfile}>
                  {savingProfile ? "Saving..." : "Save Changes"}
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
                          disabled={savingPrompt}
                        >
                          {savingPrompt ? "Saving..." : "Save"}
                        </button>
                        <button
                          onClick={() => {
                            setEditingPromptId(null)
                            setEditPromptText("")
                          }}
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
                          <span className={s.promptDate}>{formatDate(prompt.createdAt)}</span>
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
          <svg className={s.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
          </svg>
          <span className={s.navLabel}>Find Book</span>
        </button>

        <button className={s.navItem} aria-label="Find Friends">
          <svg className={s.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
            <circle cx="9" cy="7" r="4" />
            <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
            <path d="M16 3.13a4 4 0 0 1 0 7.75" />
          </svg>
          <span className={s.navLabel}>Friends</span>
        </button>

        <button className={s.navItem} aria-label="Search Prompts">
          <svg className={s.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <circle cx="12" cy="12" r="10" />
            <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
          <span className={s.navLabel}>Prompts</span>
        </button>

        <button className={s.navItem} aria-label="Feed">
          <svg className={s.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <path d="M4 11a9 9 0 0 1 9 9" />
            <path d="M4 4a16 16 0 0 1 16 16" />
            <circle cx="5" cy="19" r="1" />
          </svg>
          <span className={s.navLabel}>Feed</span>
        </button>

        <button className={s.navItem} aria-label="Friends">
          <svg className={s.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
            <circle cx="9" cy="7" r="4" />
            <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
            <path d="M16 3.13a4 4 0 0 1 0 7.75" />
          </svg>
          <span className={s.navLabel}>Friends</span>
        </button>

        <button className={`${s.navItem} ${s.active}`} aria-label="Me" aria-current="page">
          <svg className={s.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
          <span className={s.navLabel}>Me</span>
        </button>

        
      </nav>
    </div>
  )
}
