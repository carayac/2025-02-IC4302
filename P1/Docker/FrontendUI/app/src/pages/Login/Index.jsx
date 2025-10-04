"use client"

import React, { useState } from "react"
import s from "./Index.module.css"
import { AuthApi } from "../../lib/api/APIcalls";
import { useNavigate } from "react-router-dom"
import { Link } from "react-router-dom"



const Login = () => {
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  })
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

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

  const { email, password } = formData

  if (!email.trim() || !password.trim()) {
    setError("Please fill in all fields")
    return
  }

  // Email Validation
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(email)) {
    setError("Please enter a valid email address")
    return
  }

  // Password with at least 8 letters
  if (password.length < 8) {
    setError("Password must be at least 8 characters long")
    return
  }

    try { //Calling Backend
      setLoading(true)
      const user = await AuthApi.login(formData.email, formData.password) 

      localStorage.setItem("user", JSON.stringify(user))

      console.log("Login Successfull:", user)
      navigate("/feed")

    } catch (err) {
      console.error("Login error:", err)
      setError(err.message || "Invalid email or password")
    } finally {
      setLoading(false)
    }

  }

  return (
    <div className={s.container}>
      <div className={s.card}>
        <h1 className={s.title}>Login</h1>

        <form onSubmit={handleSubmit} className={s.form}>
          <div className={s.inputGroup}>
            <label htmlFor="email" className={s.label}>
              Email
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
              Password
            </label>
            <input
              type={showPassword ? "text" : "password"}
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className={s.input}
              aria-describedby={error ? "error-message" : undefined}
              disabled={loading}
            />

            <button
              type="button"
              onClick={() => setShowPassword((prev) => !prev)}
              className={s.eyeButton}
            >
              {showPassword ? "👁" : "👁"}
            </button>
          </div>

          {error && (
            <div id="error-message" className={s.error} role="alert">
              {error}
            </div>
          )}

          <p className={s.alt}>
            Don’t have an account?{" "}
            <Link to="/register" className={s.forgotLink}>
              Create an account
            </Link>
          </p>

          <button type="submit" className={s.submitButton} disabled={loading}>
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>
      </div>
    </div>
  )
}

export default Login
