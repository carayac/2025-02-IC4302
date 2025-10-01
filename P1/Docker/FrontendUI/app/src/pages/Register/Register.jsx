"use client"

import { useState } from "react"
import s from "./Register.module.css"
import { AuthApi } from "../../lib/api/APIcalls"
import { useNavigate } from "react-router-dom"

const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const Register = () => {
  const [formData, setFormData] = useState({
    name: "",
    lastname: "",
    description: "",
    email: "",
    password: "",
  })
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  const navigate = useNavigate()

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }))
    if (error) setError("")
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    const { name, lastname, description, email, password } = formData
    const requiredFields = ["name", "lastname", "email", "password"]
    const emptyFields = requiredFields.filter((field) => !formData[field].trim())

    if (emptyFields.length > 0) {
      setError("Please fill in all required fields")
      return
    }

    if (!emailRegex.test(email)) {
      setError("Please enter a valid email address")
      return
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters long")
      return
    }

    try {
      setLoading(true)

      //Calling register backend
      await AuthApi.register({ name, lastname, description, email, password })

      //Calling Auto-login and saving user
      const user = await AuthApi.login(email, password)
      localStorage.setItem("user", JSON.stringify(user))

      
      navigate("/feed")
    } catch (err) {
      console.error("Register error:", err)
      const msg = err?.message || err?.error || "Register failed"
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={s.container}>
      <div className={s.card}>
        <h1 className={s.title}>Register</h1>

        <form onSubmit={handleSubmit} className={s.form}>
          <div className={s.inputGroup}>
            <label htmlFor="name" className={s.label}>
              First Name *
            </label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              className={s.input}
              aria-describedby={error ? "error-message" : undefined}
              disabled={loading}
            />
          </div>

          <div className={s.inputGroup}>
            <label htmlFor="lastname" className={s.label}>
              Last Name *
            </label>
            <input
              type="text"
              id="lastname"
              name="lastname"
              value={formData.lastname}
              onChange={handleChange}
              className={s.input}
              aria-describedby={error ? "error-message" : undefined}
              disabled={loading}
            />
          </div>

          <div className={s.inputGroup}>
            <label htmlFor="description" className={s.label}>
              Description
            </label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              className={s.textarea}
              rows="3"
              placeholder="Tell us about yourself..."
              disabled={loading}
            />
          </div>

          <div className={s.inputGroup}>
            <label htmlFor="email" className={s.label}>
              Email *
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className={s.input}
              aria-describedby={error ? "error-message" : undefined}
              disabled={loading}
            />
          </div>

          <div className={s.inputGroup}>
            <label htmlFor="password" className={s.label}>
              Password *
            </label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className={s.input}
              aria-describedby={error ? "error-message" : undefined}
              disabled={loading}
            />
            <small className={s.hint}>At least 8 characters</small>
          </div>

          {error && (
            <div id="error-message" className={s.error} role="alert">
              {error}
            </div>
          )}

          <button type="submit" className={s.submitButton} disabled={loading}>
            {loading ? "Creating account..." : "Create Account"}
          </button>
        </form>
      </div>
    </div>
  )
}

export default Register
