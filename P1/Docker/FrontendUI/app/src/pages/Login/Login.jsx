"use client"

import { useState } from "react"
import s from "./Login.module.css"

const Login = () => {
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  })
  const [error, setError] = useState("")

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }))
    if (error) setError("")
  }

  const handleSubmit = (e) => {
    e.preventDefault()

    if (!formData.email.trim() || !formData.password.trim()) {
      setError("Please fill in all fields")
      return
    }

    // Handle login logic here
    console.log("Login attempt:", formData)
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
            />
          </div>

          <div className={s.inputGroup}>
            <label htmlFor="password" className={s.label}>
              Password
            </label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className={s.input}
              aria-describedby={error ? "error-message" : undefined}
            />
          </div>

          {error && (
            <div id="error-message" className={s.error} role="alert">
              {error}
            </div>
          )}

          <a href="#" className={s.forgotLink}>
            Forgot your password?
          </a>

          <button type="submit" className={s.submitButton}>
            Sign In
          </button>
        </form>
      </div>
    </div>
  )
}

export default Login
