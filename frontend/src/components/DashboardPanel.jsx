import React, { useState, useEffect } from 'react'
import SafetyResult from './SafetyResult'
import AlertBox from './AlertBox'
import { useSafetyCheck } from '../hooks/useSafetyCheck'
// CHANGED: Removed import { PATIENTS } from '../data/mockData'
// Patients now fetched from GET /api/patients

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'



// CHANGED: ADDENDUM 6 - Override PipelineSteps since original file is untouchable
const FRONTEND_STEPS = [
  'Input normalization & error correction',
  'Brand-to-generic mapping',
  'Patient record retrieval',
  'DDI check',
  'Risk output'
]

function CustomPipelineSteps({ steps, loading, loadingMsg }) {
  const dotClass = (state) => {
    if (state === 'done')   return 'w-2 h-2 rounded-full bg-[#1D9E75] flex-shrink-0'
    if (state === 'active') return 'w-2 h-2 rounded-full flex-shrink-0 dot-active'
    return 'w-2 h-2 rounded-full bg-[#21262d] flex-shrink-0'
  }

  return (
    <div className="bg-[#161b22] border border-[#21262d] rounded-xl p-4 mb-3.5">
      {loading && (
        <div className="flex items-center gap-2.5 mb-3 text-[13px] text-[#8b949e]">
          <div
            className="w-4 h-4 rounded-full border-2 border-[#21262d] border-t-[#1D9E75] flex-shrink-0"
            style={{ animation: 'spin 0.8s linear infinite' }}
          />
          <span>{loadingMsg}</span>
        </div>
      )}
      <div className="text-[11px] font-bold text-[#484f58] uppercase tracking-widest mb-2">
        Processing pipeline
      </div>
      <div className="flex flex-col gap-1">
        {FRONTEND_STEPS.map((label, i) => (
          <div key={i} className="flex items-center gap-2 text-[12px] text-[#8b949e] py-1">
            <div className={dotClass(steps[i] || 'wait')} />
            <span>{label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function DashboardPanel({ onViewPatient, onPatientChange }) {
  const [input, setInput]         = useState('')
  // CHANGED: patientId starts as empty — will be set after patients are fetched
  const [patientId, setPatientId] = useState('')
  const [userRole, setUserRole] = useState('')
  const [userId, setUserId] = useState('')
  const { loading, loadingMsg, steps, showSteps, result, apiError, runCheck, clear } = useSafetyCheck()

  // CHANGED: Fetch patients from Supabase via GET /api/patients
  const [patients, setPatients]     = useState([])
  const [patientsLoading, setPatientsLoading] = useState(true)

  useEffect(() => {
    const fetchPatients = async () => {
      try {
        const savedUser = localStorage.getItem('ag_user')
        const parsed = savedUser ? JSON.parse(savedUser) : null
        const token = parsed ? parsed.token : ''
        // attempt to extract user role/id from saved object
        if (parsed) {
          // support either { user: { id, role } , token } or { id, role, token }
          const maybeUser = parsed.user || parsed
          setUserRole(maybeUser.role || '')
          setUserId(String(maybeUser.id || ''))
        }
        
        const res = await fetch(`${API_BASE}/api/patients`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        const data = await res.json()
        const list = data.patients || []
        setPatients(list)
        // CHANGED: Auto-select first patient if available
        if (list.length > 0) {
          setPatientId(String(list[0].id))
          if (onPatientChange) onPatientChange(String(list[0].id))
        }
      } catch (err) {
        console.error('Failed to fetch patients:', err)
      } finally {
        setPatientsLoading(false)
      }
    }
    fetchPatients()
  }, [])

  // ── Pharmacist: request access to selected patient ──
  const handleRequestAccess = async () => {
    try {
      const savedUser = localStorage.getItem('ag_user')
      const parsed = savedUser ? JSON.parse(savedUser) : null
      const token = parsed ? parsed.token : ''
      // pharmacist id fallback to stored userId
      const pharmacistId = parsed && (parsed.user?.id || parsed.id) ? (parsed.user?.id || parsed.id) : userId
      if (!patientId) return alert('Select a patient first')

      const res = await fetch(`${API_BASE}/api/patients/request-access`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ patient_id: patientId, pharmacist_id: pharmacistId })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed to request access')
      alert(data.status === 'exists' ? 'A request already exists.' : 'Access request sent.')
    } catch (err) {
      alert(err.message || 'Request failed')
    }
  }

  // CHANGED: Pass Supabase patient.id (as string) to the safety check
  const handleCheck = () => runCheck(input, patientId)
  const handleClear = () => { setInput(''); clear() }
  const handleDemo  = (name) => setInput(name)

  const handlePatientChange = (id) => {
    setPatientId(id)
    clear()
    if (onPatientChange) onPatientChange(id)
  }

  // CHANGED: Find selected patient from fetched list instead of PATIENTS constant
  const selectedPatient = patients.find(p => String(p.id) === patientId)

  return (
    <div>
      <div className="card">
        <div className="card-body">

          {/* Medicine search — unchanged */}
          <div className="section-label">Medicine lookup</div>
          <div className="flex gap-2 mb-3.5 flex-wrap">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleCheck()}
              placeholder="Type brand name e.g. Augmentin 625, Allegra 120mg, Ascoril LS…"
              className="flex-1 min-w-0 px-3.5 py-2.5 border border-[#21262d] rounded-lg text-[14px] outline-none
                         bg-[#0d1117] text-[#e2e8f0] placeholder-[#484f58]
                         focus:border-[#1D9E75] focus:ring-2 focus:ring-[#1D9E75]/20 transition-all"
            />
            <button onClick={handleCheck} disabled={loading || selectedPatient?.access_status !== 'ACCEPTED'}
              className="btn btn-primary whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed">
              {loading ? 'Checking…' : 'Run safety check'}
            </button>
            <button onClick={handleClear} className="btn btn-outline">Clear</button>
          </div>

          {/* CHANGED: Patient selector — now fetches from GET /api/patients */}
          <div className="section-label">Select patient</div>
          <div className="flex gap-2 mb-4 items-center flex-wrap">
            {patientsLoading ? (
              <span className="text-[13px] text-[#484f58]">Loading patients…</span>
            ) : (
              <select
                value={patientId}
                onChange={(e) => handlePatientChange(e.target.value)}
                className="px-3.5 py-2.5 border border-[#21262d] rounded-lg text-[14px] outline-none
                           bg-[#0d1117] text-[#e2e8f0]
                           focus:border-[#378ADD] focus:ring-2 focus:ring-[#378ADD]/20 transition-all"
              >
                {patients.length === 0 && <option value="">No patients found</option>}
                {patients.map((p) => (
                  <option key={p.id} value={String(p.id)}>
                    {p.name} — {p.phone || 'No phone'}
                  </option>
                ))}
              </select>
            )}
            <div className="flex gap-2">
              <button onClick={onViewPatient} className="btn btn-blue whitespace-nowrap">
                View patient profile
              </button>
              {userRole === 'pharmacist' && (
                <button onClick={handleRequestAccess} className="btn btn-primary whitespace-nowrap">
                  Request access
                </button>
              )}
            </div>
          </div>

          {/* CHANGED: Patient quick info strip using Supabase fields */}
          {selectedPatient && (
            <div className="bg-[#0d1117] border border-[#21262d] rounded-lg px-3.5 py-2.5 mb-4">
              {selectedPatient.access_status === 'ACCEPTED' ? (
                <div className="flex flex-wrap gap-4 text-[12px]">
                  <span className="text-[#8b949e]">Patient: <span className="text-[#e2e8f0] font-medium">{selectedPatient.name}</span></span>
                  <span className="text-[#8b949e]">Phone: <span className="text-[#e2e8f0] font-medium">{selectedPatient.phone || '—'}</span></span>
                  <span className="text-[#8b949e]">Conditions: <span className="text-amber-400 font-medium">
                    {(selectedPatient.current_conditions || []).join(', ') || 'None'}
                  </span></span>
                  <span className="text-[#8b949e]">Current meds: <span className="text-blue-400 font-medium">
                    {(selectedPatient.current_medications || []).join(', ') || 'None'}
                  </span></span>
                </div>
              ) : (
                <div className="flex items-center gap-2 text-[12px]">
                  <div className="w-2 h-2 rounded-full bg-amber-500"></div>
                  <span className="text-amber-400 font-medium">RESTRICTED ACCESS:</span>
                  <span className="text-[#8b949e]">Full records hidden. Current status: </span>
                  <span className="px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-500 text-[10px] font-bold uppercase tracking-wider">
                    {selectedPatient.access_status || 'NONE'}
                  </span>
                </div>
              )}
            </div>
          )}


        </div>
      </div>

      {/* Pipeline steps — unchanged style but using CustomPipelineSteps */}
      {showSteps && (
        <CustomPipelineSteps steps={steps} loading={loading} loadingMsg={loadingMsg} />
      )}

      {/* API connection error — unchanged */}
      {apiError && (
        <AlertBox variant="critical" title="Backend connection error">
          {apiError}
        </AlertBox>
      )}

      {/* Safety check result — unchanged */}
      {!loading && result && <SafetyResult result={result} />}
    </div>
  )
}
