"use client"

import { useEffect, useMemo, useRef, useState, useCallback } from "react"
import { useNavigate, NavLink } from "react-router-dom"
import s from "./Me.module.css"
import { AuthApi, Prompts } from "../../lib/api/APIcalls" //Objeto de funciones

//PERFIL DEL USUARIO

//Navegación entre rutas
const navItemClass = ({ isActive }) =>
  `${s.navItem} ${isActive ? s.active : ""}`;

//Read the user from Local Storage
function getStoredUser() {
  try {
    const raw = localStorage.getItem("user")  //Leer user
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}
//User id 
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

  const [theme, setTheme] = useState("formal")
  const [isEditing, setIsEditing] = useState(false)
  const [editingPromptId, setEditingPromptId] = useState(null)
  const [isChangingPassword, setIsChangingPassword] = useState(false) 


  //Estado con la info de perfil
  const [profile, setProfile] = useState({
    id: null,
    name: "",
    lastname: "",
    email: "",
    description: "",
    avatar: "/neutral-avatar.svg",
    followers: 0,
    following: 0,
  })

  //Formulario de edición de perfil
  const [editForm, setEditForm] = useState({
    name: "",
    lastname: "",
    description: "",
  })

  //Formulario para cambio de contraseña
  const [passwordForm, setPasswordForm] = useState({
    oldpass: "",
    newpass: "",
    confirm: "",
  })


  const [prompts, setPrompts] = useState([])  //Para lista de prompts

  const [editPromptText, setEditPromptText] = useState("")
  const [loading, setLoading] = useState(true)
  const [savingProfile, setSavingProfile] = useState(false)
  const [savingPrompt, setSavingPrompt] = useState(false)
  const [errorMsg, setErrorMsg] = useState("")
  const [infoMsg, setInfoMsg] = useState("")
  const [savingPassword, setSavingPassword] = useState(false)


  useEffect(() => {

    //Solicitando user logueado a local storage
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
        //Datos del ususario del backend
        const userRes = await AuthApi.me(id)

        if (!cancelled && userRes) {
          setProfile((prev) => ({
            //Asignación del perfil 
            ...prev,
            id: userRes.id ?? id,
            name: userRes.name ?? "",
            lastname: userRes.lastname ?? "",
            email: userRes.email ?? "",
            description: userRes.description ?? "",
            followers: Number(userRes.followers ?? 0), 
            following: Number(userRes.following ?? 0), 
          }))
          //Llena el form de edit con los datos del backenn
          setEditForm({
            name: userRes.name ?? "",
            lastname: userRes.lastname ?? "",
            description: userRes.description ?? "",
          })
        }

        //Lista de prompts desde el backend
        const myPrompts = await Prompts.getMyPrompts(id)

        if (!cancelled && Array.isArray(myPrompts)) {
          setPrompts(

            myPrompts.map((p) => ({
              //Asignación de valores con lo mandado por el backend
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

  //Handler de editar el perfil
  const handleEditProfile = () => {
    setIsChangingPassword(false)  //Cerrar vista de editar contraseña 
    setIsEditing(true)  //Abrir vista de editar
    setEditForm({
      name: profile.name,
      lastname: profile.lastname,
      description: profile.description,
    })
  }

  //Hnalder de editar contraseña
  const handleChangePassword = () => {
    setIsEditing(false)
    setIsChangingPassword(true)
    setPasswordForm({ oldpass: "", newpass: "", confirm: "" })
    setErrorMsg("")
    setInfoMsg("")
  }

  //Hanlder para guardar la edición del perfil
  const handleSaveProfile = async () => {
    if (!profile.id) return
    setSavingProfile(true)
    setErrorMsg("")
    setInfoMsg("")
    try {
      await AuthApi.editUser({  //Cambios enviados al backend
        id: profile.id,
        name: editForm.name,
        lastname: editForm.lastname,
        description: editForm.description,
      })
      //Cambia los datos del perfil en la UI
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
  //Handler de cancelar la edición
  const handleCancelEdit = () => {
    setIsEditing(false) //Oculta vista de editar
    setEditForm({
      name: profile.name,
      lastname: profile.lastname,
      description: profile.description,
    })
  }

  //Handler para guardar la contraseña
  const handleSubmitPassword = async (e) => {
    e.preventDefault()
    if (!profile.id) return

    setErrorMsg("")
    setInfoMsg("")

    // Validaciones mínimas de contraseña
    const { oldpass, newpass, confirm } = passwordForm
    if (!oldpass || !newpass || !confirm) {
      setErrorMsg("Please complete all password fields.")
      return
    }
    if (newpass.length < 8) {
      setErrorMsg("New password must be at least 8 characters.")
      return
    }
    if (newpass !== confirm) {
      setErrorMsg("New password and confirmation do not match.")
      return
    }

    setSavingPassword(true) 
    try {
      await AuthApi.changePassword({  //Mnada datos de cambio de contraseña al backend
        id: profile.id,
        oldpass,
        newpass,
      })
      setIsChangingPassword(false)  
      setPasswordForm({ oldpass: "", newpass: "", confirm: "" })
      setInfoMsg("Your password has been updated.")
    } catch (err) {

      setErrorMsg("Could not change your password. Check your current password.")
    } finally {
      setSavingPassword(false)
    }
  }

  //Hanlder para cancelar cambio de contraseña
  const handleCancelChangePassword = () => {
    setIsChangingPassword(false)  //Oculta vista
    setPasswordForm({ oldpass: "", newpass: "", confirm: "" })
  }

  //Handler vista de editar prompts
  const handleEditPrompt = (prompt) => {
    setEditingPromptId(prompt.id)
    setEditPromptText(prompt.text)
  }


  //Handler de guardar prompts
  const handleSavePrompt = async (id) => {
    setSavingPrompt(true)
    setErrorMsg("")
    setInfoMsg("")
    try {
      await Prompts.editPrompt(id, editPromptText)  //Mnada datos al backend

      setPrompts((curr) => curr.map((p) => (p.id === id ? { ...p, text: editPromptText } : p))) //Actualiza lista de prompts local
      setEditingPromptId(null)
      setEditPromptText("")
      setInfoMsg("Your prompt has been updated.")
    } catch (err) {
      setErrorMsg("Could not update the prompt.")
    } finally {
      setSavingPrompt(false)
    }
  }

  //Handler de eliminar prompt
  const handleDeletePrompt = async (id) => {
    if (!window.confirm("Are you sure you want to delete this prompt?")) return //Confirmación de ususario 
    setErrorMsg("")
    setInfoMsg("")
    try {
      await Prompts.deletePrompt(id)  //Solicitud al backend
      setPrompts((curr) => curr.filter((p) => p.id !== id)) //Actualiza lista local sin la eliminada
      setInfoMsg("Your prompt has been deleted.")
    } catch (err) {
      setErrorMsg("Could not delete this prompt.")
    }
  }

  //Handler para cerrar sesión
  const handleLogout = () => {
    if (window.confirm("Are you sure you want to log out?")) {
      try {
        localStorage.removeItem("user") //Cierra el usuario de Local storage
      } catch { }
      navigate("/") //Navegación hasta login 
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
        {(loading || savingProfile || savingPrompt || savingPassword) && (
          <div className={s.infoBanner} role="status">Loading...</div>
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
                  {profile.followers}
                </span>
                <span className={s.statLabel}>Followers</span>
              </div>
              <div className={s.statItem}>
                <span className={s.statNumber}>
                  {profile.following}
                </span>
                <span className={s.statLabel}>Following</span>
              </div>
            </div>
          </div>


          {!isEditing && !isChangingPassword ? (
            <div className={s.profileInfo}>
              <h2 className={s.profileName}>
                {profile.name} {profile.lastname}
              </h2>
              <p className={s.profileEmail}>{profile.email}</p>
              <p className={s.profileBio}>{profile.description}</p>

              <div className={s.formActions}>
                <button onClick={handleEditProfile} className={s.editButton} aria-label="Edit profile">
                  Edit Profile
                </button>

                <button onClick={handleChangePassword} className={s.editButton} aria-label="Change password">
                  Change Password
                </button>
              </div>
            </div>
          ) : null}

          {/* Formulario Editar Perfil */}
          {isEditing && !isChangingPassword && (
            <form
              className={s.editForm}
              onSubmit={(e) => {
                e.preventDefault()
                handleSaveProfile()
              }}
            >
              <div className={s.formGroup}>
                <label htmlFor="name" className={s.label}>Name</label>
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
                <label htmlFor="lastname" className={s.label}>Lastname</label>
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
                <label htmlFor="description" className={s.label}>Description</label>
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

          {isChangingPassword && !isEditing && (
            <form className={s.editForm} onSubmit={handleSubmitPassword}>
              <div className={s.formGroup}>
                <label htmlFor="oldpass" className={s.label}>Current Password</label>
                <input
                  id="oldpass"
                  type="password"
                  value={passwordForm.oldpass}
                  onChange={(e) => setPasswordForm({ ...passwordForm, oldpass: e.target.value })}
                  className={s.input}
                  autoComplete="current-password"
                  aria-required="true"
                />
              </div>

              <div className={s.formGroup}>
                <label htmlFor="newpass" className={s.label}>New Password</label>
                <input
                  id="newpass"
                  type="password"
                  value={passwordForm.newpass}
                  onChange={(e) => setPasswordForm({ ...passwordForm, newpass: e.target.value })}
                  className={s.input}
                  autoComplete="new-password"
                  aria-required="true"
                />
                <small className={s.passwordHint}>At least 8 characters.</small>
              </div>

              <div className={s.formGroup}>
                <label htmlFor="confirm" className={s.label}>Confirm New Password</label>
                <input
                  id="confirm"
                  type="password"
                  value={passwordForm.confirm}
                  onChange={(e) => setPasswordForm({ ...passwordForm, confirm: e.target.value })}
                  className={s.input}
                  autoComplete="new-password"
                  aria-required="true"
                />
              </div>

              <div className={s.formActions}>
                <button type="submit" className={s.saveButton} aria-label="Save password" disabled={savingPassword}>
                  {savingPassword ? "Saving..." : "Save Password"}
                </button>
                <button type="button" onClick={handleCancelChangePassword} className={s.cancelButton} aria-label="Cancel password change">
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
        <NavLink to="/ask" className={navItemClass} aria-label="Find Book">
          <svg className={s.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
          </svg>
          <span className={s.navLabel}>Find Book</span>
        </NavLink>

        <NavLink to="/friends" className={navItemClass} aria-label="Find Friends">
          <svg className={s.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
            <circle cx="9" cy="7" r="4" />
            <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
            <path d="M16 3.13a4 4 0 0 1 0 7.75" />
          </svg>
          <span className={s.navLabel}>Find Friends</span>
        </NavLink>

        <NavLink to="/prompt" className={navItemClass} aria-label="Search Prompts">
          <svg className={s.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <circle cx="12" cy="12" r="10" />
            <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
          <span className={s.navLabel}>Search Prompts</span>
        </NavLink>

        <NavLink to="/feed" className={navItemClass} aria-label="Feed">
          <svg className={s.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <path d="M4 11a9 9 0 0 1 9 9" />
            <path d="M4 4a16 16 0 0 1 16 16" />
            <circle cx="5" cy="19" r="1" />
          </svg>
          <span className={s.navLabel}>Feed</span>
        </NavLink>

        <NavLink to="/myFriends" className={navItemClass} aria-label="Find Friends">
          <svg className={s.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
            <circle cx="9" cy="7" r="4" />
            <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
            <path d="M16 3.13a4 4 0 0 1 0 7.75" />
          </svg>
          <span className={s.navLabel}>Friends</span>
        </NavLink>

        <NavLink to="/me" className={navItemClass} aria-label="Me">
          <svg className={s.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
          <span className={s.navLabel}>Me</span>
        </NavLink>
      </nav>
    </div>
  )
}
