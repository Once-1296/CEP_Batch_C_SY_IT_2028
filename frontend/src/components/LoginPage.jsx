import React, { useState } from 'react'

// ── CHANGED: Login page rewritten — signup removed entirely ────────────────
// Single clean login form: username + password
// Role determined from backend response — no UI role selector
// On success: stores { token, role, name, username } in localStorage('ag_user')

const API_BASE = 'http://localhost:8000'

export default function LoginPage({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState(null)

  // CHANGED: Removed mode/signup state entirely — login only
  const handleSubmit = async () => {
    if (!username.trim() || !password.trim()) {
      setError('Please enter both username and password.')
      return
    }
    setLoading(true)
    setError(null)

    try {
      // CHANGED: Only /api/login — no /api/signup
      const res = await fetch(`${API_BASE}/api/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: username.trim(), password }),
      })
      const data = await res.json()

      if (!res.ok) throw new Error(data.detail || 'Login failed')

      // CHANGED: Store role and name alongside token in localStorage
      const userData = {
        token: data.token,
        role: data.role,           // 'admin' | 'pharmacist'
        name: data.name,
        username: username.trim(),
      }
      localStorage.setItem('ag_user', JSON.stringify(userData))

      // CHANGED: Pass full user object to parent for role-based routing
      onLogin(userData)
    } catch (err) {
      if (err.message === 'Failed to fetch') {
        setError('Cannot connect to backend. Make sure FastAPI is running: uvicorn main:app --reload')
      } else {
        setError(err.message)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#0d1117] flex items-center justify-center p-5">
      <div className="w-full max-w-sm">

        {/* Logo */}
        <div className="flex items-center gap-3 mb-8 justify-center">
          <div className="w-10 h-10 bg-[#1D9E75] rounded-[10px] flex items-center justify-center">
            <svg viewBox="0 0 24 24" className="w-5 h-5 fill-white">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 15v-4H7l5-8v4h4l-5 8z" />
            </svg>
          </div>
          <div>
            <div className="text-[18px] font-semibold text-[#e2e8f0] tracking-tight">Ayush-Guard</div>
            <div className="text-[11px] text-[#484f58]">Clinical Decision Support System</div>
          </div>
        </div>

        {/* CHANGED: Single login card — no signup tab toggle */}
        <div className="bg-[#161b22] border border-[#21262d] rounded-xl p-6">
          {/* CHANGED: Simple "Sign In" header instead of tab toggle */}
          <div className="text-center mb-6">
            <div className="text-[15px] font-semibold text-[#e2e8f0]">Sign In</div>
            <div className="text-[12px] text-[#484f58] mt-1">Admin or Pharmacist credentials</div>
          </div>

          {/* Form */}
          <div className="space-y-3">
            <div>
              <label className="text-[11px] font-bold text-[#484f58] uppercase tracking-widest block mb-1.5">
                Username
              </label>
              <input type="text" value={username} onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter username"
                className="w-full px-3.5 py-2.5 border border-[#21262d] rounded-lg text-[14px] outline-none
                           bg-[#0d1117] text-[#e2e8f0] placeholder-[#484f58]
                           focus:border-[#1D9E75] focus:ring-2 focus:ring-[#1D9E75]/20 transition-all" />
            </div>
            <div>
              <label className="text-[11px] font-bold text-[#484f58] uppercase tracking-widest block mb-1.5">
                Password
              </label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
                placeholder="Enter password"
                className="w-full px-3.5 py-2.5 border border-[#21262d] rounded-lg text-[14px] outline-none
                           bg-[#0d1117] text-[#e2e8f0] placeholder-[#484f58]
                           focus:border-[#1D9E75] focus:ring-2 focus:ring-[#1D9E75]/20 transition-all" />
            </div>

            {/* CHANGED: Inline error display — no success message (no signup) */}
            {error && (
              <div className="bg-red-950/40 border border-red-800/40 rounded-lg px-3 py-2.5 text-[12px] text-red-400">
                {error}
              </div>
            )}

            <button onClick={handleSubmit} disabled={loading}
              className="w-full btn btn-primary py-3 text-[14px] disabled:opacity-50 disabled:cursor-not-allowed mt-2">
              {loading ? 'Signing in…' : 'Sign In'}
            </button>
          </div>
        </div>

        <p className="text-center text-[11px] text-[#484f58] mt-4">
          Make sure FastAPI backend is running on port 8000
        </p>
      </div>
    </div>
  )
}
