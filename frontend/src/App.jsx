import { useState } from 'react'

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isLoginMode, setIsLoginMode] = useState(true)

  // Dashboard State
  const [abhaId, setAbhaId] = useState('ABHA-1234-5678') // Default to our mock patient
  const [query, setQuery] = useState('')
  const [alertData, setAlertData] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleAuth = async (e) => {
    e.preventDefault()
    const endpoint = isLoginMode ? '/api/login' : '/api/signup'
    
    try {
      const res = await fetch(`http://localhost:8000${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      })
      const data = await res.json()
      
      if (res.ok) {
        if (isLoginMode) setIsAuthenticated(true)
        else alert("Signup successful! Please login.")
      } else {
        alert(data.detail)
      }
    } catch (error) {
      console.error("Auth error", error)
    }
  }

  const handleCheckDrug = async (e) => {
    e.preventDefault()
    setLoading(true)
    setAlertData(null)

    try {
      const res = await fetch('http://localhost:8000/api/check-drug', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pharmacist_query: query, patient_id: abhaId })
      })
      const data = await res.json()
      setAlertData(data)
    } catch (error) {
      console.error("Check error", error)
    } finally {
      setLoading(false)
    }
  }

  // --- LOGIN SCREEN ---
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
        {/* Animated Background Blob */}
        <div className="absolute w-96 h-96 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"></div>
        
        {/* Glassmorphism Card */}
        <div className="relative z-10 w-full max-w-md bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl p-8 shadow-2xl transition-all">
          <h1 className="text-3xl font-bold text-white mb-2 tracking-tight">Ayush-Guard</h1>
          <p className="text-slate-300 mb-8 text-sm">Secure Point-of-Sale CDSS Terminal</p>
          
          <form onSubmit={handleAuth} className="space-y-4">
            <input 
              type="text" placeholder="Pharmacist ID / Username" 
              className="w-full bg-slate-800/50 border border-slate-600 text-white rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
              value={username} onChange={(e) => setUsername(e.target.value)} required
            />
            <input 
              type="password" placeholder="Password" 
              className="w-full bg-slate-800/50 border border-slate-600 text-white rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
              value={password} onChange={(e) => setPassword(e.target.value)} required
            />
            <button type="submit" className="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg px-4 py-3 transition-colors shadow-lg shadow-blue-500/30">
              {isLoginMode ? 'Authenticate' : 'Register Terminal'}
            </button>
          </form>
          
          <p className="text-slate-400 text-sm mt-6 text-center cursor-pointer hover:text-white transition-colors" onClick={() => setIsLoginMode(!isLoginMode)}>
            {isLoginMode ? "Need to register? Click here." : "Already registered? Login."}
          </p>
        </div>
      </div>
    )
  }

  // --- DASHBOARD SCREEN ---
  return (
    <div className="min-h-screen bg-slate-900 text-slate-200 p-6 font-sans">
      <header className="flex justify-between items-center mb-8 border-b border-white/10 pb-4">
        <h1 className="text-2xl font-bold text-white tracking-wide">Ayush-Guard <span className="text-sm font-normal text-slate-400 bg-slate-800 px-2 py-1 rounded-md ml-2">Sandbox Environment</span></h1>
        <button onClick={() => setIsAuthenticated(false)} className="text-sm text-slate-400 hover:text-white transition-colors">Logout</button>
      </header>

      <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8">
        
        {/* Left Pane: Patient Context (Glassmorphism) */}
        <div className="md:col-span-1 bg-white/5 backdrop-blur-lg border border-white/10 rounded-2xl p-6 shadow-xl h-fit">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center"><span className="w-2 h-2 rounded-full bg-green-500 mr-2 animate-pulse"></span> Patient Context (ABDM)</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1 uppercase tracking-wider">ABHA ID (Consent Approved)</label>
              <input 
                type="text" className="w-full bg-slate-800/80 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm focus:ring-1 focus:ring-blue-500 outline-none"
                value={abhaId} onChange={(e) => setAbhaId(e.target.value)}
              />
            </div>
            <div className="bg-slate-800/50 rounded-lg p-4 border border-white/5">
              <p className="text-xs text-slate-400 mb-1">Simulated Profile Loaded:</p>
              <p className="text-sm font-medium text-white mb-2">Rajesh Kumar (58 Yrs)</p>
              <div className="flex flex-wrap gap-2 mt-3">
                <span className="px-2 py-1 bg-red-500/20 text-red-300 text-xs rounded-md border border-red-500/20">Kidney Disease</span>
                <span className="px-2 py-1 bg-yellow-500/20 text-yellow-300 text-xs rounded-md border border-yellow-500/20">Taking: Methotrexate</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Pane: Point of Sale Action */}
        <div className="md:col-span-2 flex flex-col space-y-6">
          
          {/* Search Box */}
          <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-2xl p-6 shadow-xl">
            <h2 className="text-lg font-semibold text-white mb-4">Dispense Medication</h2>
            <form onSubmit={handleCheckDrug} className="flex gap-4">
              <input 
                type="text" placeholder="e.g., Tab Augmentin 625mg or Allegra" 
                className="flex-1 bg-slate-800/80 border border-slate-600 text-white rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-lg"
                value={query} onChange={(e) => setQuery(e.target.value)} required
              />
              <button disabled={loading} type="submit" className="bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg px-8 py-3 transition-colors shadow-lg shadow-blue-500/30 disabled:opacity-50">
                {loading ? 'Scanning...' : 'Verify Risk'}
              </button>
            </form>
          </div>

          {/* Dynamic Alert UI */}
          {alertData && (
            <div className={`rounded-2xl p-6 shadow-2xl border transition-all duration-500 animate-in slide-in-from-bottom-4 ${
              alertData.severity_tier === 'Red' ? 'bg-red-950/80 border-red-500/50 shadow-red-900/50' : 
              alertData.severity_tier === 'Yellow' ? 'bg-yellow-950/80 border-yellow-500/50 shadow-yellow-900/50' : 
              'bg-green-950/80 border-green-500/50 shadow-green-900/50'
            }`}>
              
              <div className="flex items-start justify-between">
                <div>
                  <h3 className={`text-2xl font-bold mb-2 flex items-center ${
                    alertData.severity_tier === 'Red' ? 'text-red-400' : 
                    alertData.severity_tier === 'Yellow' ? 'text-yellow-400' : 'text-green-400'
                  }`}>
                    {alertData.severity_tier === 'Red' && '🚨 CRITICAL INTERACTION DETECTED'}
                    {alertData.severity_tier === 'Yellow' && '⚠️ CLINICAL WARNING'}
                    {alertData.severity_tier === 'Green' && '✅ SAFE TO DISPENSE'}
                  </h3>
                  <p className="text-lg text-white font-medium mb-4">{alertData.message}</p>
                </div>
              </div>

              {/* Resolution Data */}
              <div className="bg-black/30 rounded-lg p-4 mb-4 font-mono text-sm text-slate-300">
                <p>Entity Resolved: <span className="text-white">{alertData.resolved_data.brand_matched}</span></p>
                <p>Underlying Salt: <span className="text-white">{alertData.resolved_data.generic_salt}</span></p>
                <p>NLP Confidence: {alertData.resolved_data.match_score}%</p>
              </div>

              {/* Safety Swap Suggestion */}
              {alertData.suggested_alternative && (
                <div className="mt-4 p-4 bg-blue-900/40 border border-blue-500/30 rounded-lg">
                  <p className="text-sm text-blue-300 mb-1 uppercase tracking-wider font-semibold">💡 Safety-Swap Suggestion</p>
                  <p className="text-white">Consider switching to: <span className="font-bold text-blue-400 text-lg">{alertData.suggested_alternative}</span></p>
                  <p className="text-xs text-blue-200 mt-1">Belongs to the same therapeutic class but carries no known risks for this patient profile.</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}