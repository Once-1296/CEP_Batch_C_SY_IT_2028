import React, { useState } from 'react'

const API_BASE = 'http://localhost:8000'

export default function LoginPage({ onLogin }) {
  const [mode, setMode]         = useState('login') // 'login' | 'signup'
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState(null)
  const [success, setSuccess]   = useState(null)

  const handleSubmit = async () => {
    if (!username.trim() || !password.trim()) {
      setError('Please enter both username and password.')
      return
    }
    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      const endpoint = mode === 'login' ? '/api/login' : '/api/signup'
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })
      const data = await res.json()

      if (!res.ok) throw new Error(data.detail || 'Request failed')

      if (mode === 'signup') {
        setSuccess('Account created! You can now log in.')
        setMode('login')
      } else {
        // Store token and proceed
        localStorage.setItem('ag_token', data.token)
        localStorage.setItem('ag_user', username)
        onLogin(username)
      }
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

        {/* Card */}
        <div className="bg-[#161b22] border border-[#21262d] rounded-xl p-6">
          {/* Tab toggle */}
          <div className="flex bg-[#0d1117] border border-[#21262d] rounded-lg p-1 mb-6 gap-1">
            {['login', 'signup'].map((m) => (
              <button key={m} onClick={() => { setMode(m); setError(null); setSuccess(null) }}
                className={`flex-1 py-2 rounded-md text-[13px] font-medium transition-all
                  ${mode === m ? 'bg-[#1D9E75] text-white' : 'text-[#8b949e] hover:text-[#e2e8f0]'}`}>
                {m === 'login' ? 'Login' : 'Sign Up'}
              </button>
            ))}
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

            {error && (
              <div className="bg-red-950/40 border border-red-800/40 rounded-lg px-3 py-2.5 text-[12px] text-red-400">
                {error}
              </div>
            )}
            {success && (
              <div className="bg-emerald-950/40 border border-emerald-800/40 rounded-lg px-3 py-2.5 text-[12px] text-emerald-400">
                {success}
              </div>
            )}

            <button onClick={handleSubmit} disabled={loading}
              className="w-full btn btn-primary py-3 text-[14px] disabled:opacity-50 disabled:cursor-not-allowed mt-2">
              {loading ? 'Please wait…' : mode === 'login' ? 'Login as Pharmacist' : 'Create Account'}
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
