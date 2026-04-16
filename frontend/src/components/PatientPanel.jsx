import React, { useState, useEffect } from 'react'
import Badge from './Badge'
import AlertBox from './AlertBox'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Helper to extract readable items from ABDM JSONB arrays
function extractMedNames(medHistory) {
  if (!Array.isArray(medHistory)) return []
  return medHistory
    .map(m => typeof m === 'string' ? m : (m?.medication_name || ''))
    .filter(Boolean)
}

function extractConditions(conditions) {
  if (!Array.isArray(conditions)) return []
  return conditions
    .map(c => typeof c === 'string' ? c : (c?.condition || ''))
    .filter(Boolean)
}

function extractAllergies(allergies) {
  if (!Array.isArray(allergies)) return []
  return allergies
    .map(a => typeof a === 'string' ? a : (a?.allergen || ''))
    .filter(Boolean)
}

export default function PatientPanel({ activePatientId, loggedInUser }) {
  // ── Patient list state ──
  const [patients, setPatients]           = useState([])
  const [patientsLoading, setPatientsLoading] = useState(true)
  const [selectedId, setSelectedId]       = useState(activePatientId || '')

  // ── Consent verification state ──
  const [consentPassword, setConsentPassword] = useState('')
  const [consentVerified, setConsentVerified] = useState(false)
  const [consentLoading, setConsentLoading]   = useState(false)
  const [consentError, setConsentError]       = useState(null)

  // ── Edit mode state ──
  const [editMode, setEditMode]           = useState(false)
  const [editName, setEditName]           = useState('')
  const [editPhone, setEditPhone]         = useState('')
  const [editLoading, setEditLoading]     = useState(false)
  const [editMsg, setEditMsg]             = useState(null)

  // ── Fetch patients on mount ──
  const fetchPatients = async () => {
    try {
      const savedUser = localStorage.getItem('ag_user')
      const token = savedUser ? JSON.parse(savedUser).token : ''

      const res = await fetch(`${API_BASE}/api/patients`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      const data = await res.json()
      const list = data.patients || []
      setPatients(list)
      if (activePatientId) {
        setSelectedId(String(activePatientId))
        await fetchFullDetails(String(activePatientId))
      } else if (list.length > 0) {
        setSelectedId(String(list[0].id))
      }
    } catch (err) {
      console.error('Failed to fetch patients:', err)
    } finally {
      setPatientsLoading(false)
    }
  }

  useEffect(() => { fetchPatients() }, [])

  // ── Reset consent when patient changes ──
  const handleSelectPatient = async (id) => {
    setSelectedId(id)
    setConsentVerified(false)
    setConsentPassword('')
    setConsentError(null)
    setEditMode(false)
    setEditMsg(null)
    
    if (id) {
      await fetchFullDetails(id)
    }
  }

  // ── Fetch full details (including medical data from abdm_mock_records) ──
  const fetchFullDetails = async (id) => {
    try {
      const savedUser = localStorage.getItem('ag_user')
      const token = savedUser ? JSON.parse(savedUser).token : ''

      const res = await fetch(`${API_BASE}/api/patients/${id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      const data = await res.json()
      
      if (data.access === 'granted') {
        setConsentVerified(true)
        setPatients(prev => prev.map(p => String(p.id) === id ? data.patient : p))
      }
    } catch (err) {
      console.error('fetchFullDetails error:', err)
    }
  }

  // ── Consent verification ──
  const handleVerifyConsent = async () => {
    if (!consentPassword.trim()) {
      setConsentError('Please enter the patient password.')
      return
    }
    setConsentLoading(true)
    setConsentError(null)
    try {
      const savedUser = localStorage.getItem('ag_user')
      const token = savedUser ? JSON.parse(savedUser).token : ''

      const res = await fetch(`${API_BASE}/api/patients/verify`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ patient_id: selectedId, password: consentPassword }),
      })
      const data = await res.json()
      if (data.verified) {
        setConsentVerified(true)
      } else {
        setConsentError('Incorrect password. Consent not granted.')
      }
    } catch (err) {
      setConsentError('Verification failed. Is the backend running?')
    } finally {
      setConsentLoading(false)
    }
  }

  // ── Find selected patient from list ──
  const patient = patients.find(p => String(p.id) === selectedId)

  // ── Extract medical data from abdm_record (JSONB) ──
  const abdmRecord = patient?.abdm_record || {}
  const medNames = extractMedNames(abdmRecord.medication_history)
  const condNames = extractConditions(abdmRecord.pre_existing_conditions)
  const allergyNames = extractAllergies(abdmRecord.allergies)

  // ── Enter edit mode ──
  const enterEditMode = () => {
    if (!patient) return
    setEditName(patient.name || '')
    setEditPhone(patient.phone || '')
    setEditMode(true)
    setEditMsg(null)
  }

  // ── Save edits ──
  const handleSaveEdit = async () => {
    setEditLoading(true)
    setEditMsg(null)
    try {
      const savedUser = localStorage.getItem('ag_user')
      const token = savedUser ? JSON.parse(savedUser).token : ''

      const res = await fetch(`${API_BASE}/api/patients/${selectedId}`, {
        method: 'PUT',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: editName.trim(),
          phone: editPhone.trim(),
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Update failed')
      setEditMsg({ type: 'success', text: 'Patient updated successfully!' })
      setEditMode(false)
      await fetchPatients()
    } catch (err) {
      setEditMsg({ type: 'error', text: err.message })
    } finally {
      setEditLoading(false)
    }
  }

  // ── Reusable message banner ──
  const MsgBanner = ({ msg }) => {
    if (!msg) return null
    const isErr = msg.type === 'error'
    return (
      <div className={`rounded-lg px-3 py-2.5 text-[12px] mt-3 ${
        isErr ? 'bg-red-950/40 border border-red-800/40 text-red-400'
              : 'bg-emerald-950/40 border border-emerald-800/40 text-emerald-400'
      }`}>{msg.text}</div>
    )
  }

  // ── Reusable input field ──
  const Field = ({ label, type = 'text', value, onChange, placeholder }) => (
    <div>
      <label className="text-[11px] font-bold text-[#484f58] uppercase tracking-widest block mb-1.5">{label}</label>
      <input type={type} value={value} onChange={onChange} placeholder={placeholder}
        className="w-full px-3.5 py-2.5 border border-[#21262d] rounded-lg text-[14px] outline-none
                   bg-[#0d1117] text-[#e2e8f0] placeholder-[#484f58]
                   focus:border-[#1D9E75] focus:ring-2 focus:ring-[#1D9E75]/20 transition-all" />
    </div>
  )

  return (
    <div>
      {/* ── Patient selector dropdown ── */}
      <div className="card">
        <div className="card-body">
          <div className="section-label">Select patient</div>
          <div className="flex gap-2 items-center flex-wrap">
            {patientsLoading ? (
              <span className="text-[13px] text-[#484f58]">Loading patients…</span>
            ) : (
              <select
                value={selectedId}
                onChange={(e) => handleSelectPatient(e.target.value)}
                className="flex-1 px-3.5 py-2.5 border border-[#21262d] rounded-lg text-[14px] outline-none
                           bg-[#0d1117] text-[#e2e8f0]
                           focus:border-[#378ADD] focus:ring-2 focus:ring-[#378ADD]/20 transition-all"
              >
                {patients.length === 0 && <option value="">No patients found</option>}
                {patients.map((p) => (
                  <option key={p.id} value={String(p.id)}>{p.name} — {p.abha_id || 'No ABHA'}</option>
                ))}
              </select>
            )}
          </div>
        </div>
      </div>


      {/* ── Consent Verification ── */}
      {patient && !consentVerified && (
        <div className="card">
          <div className="card-body">
            <div className="section-label">Patient Consent Required</div>
            <p className="text-[13px] text-[#8b949e] mb-3">
              Patient <span className="text-[#e2e8f0] font-medium">{patient.name}</span> must enter their password to grant access to their records.
            </p>
            <div className="flex gap-2 items-center">
              <input
                type="password"
                value={consentPassword}
                onChange={(e) => setConsentPassword(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleVerifyConsent()}
                placeholder="Enter patient password"
                className="flex-1 px-3.5 py-2.5 border border-[#21262d] rounded-lg text-[14px] outline-none
                           bg-[#0d1117] text-[#e2e8f0] placeholder-[#484f58]
                           focus:border-[#1D9E75] focus:ring-2 focus:ring-[#1D9E75]/20 transition-all"
              />
              <button onClick={handleVerifyConsent} disabled={consentLoading}
                className="btn btn-primary whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed">
                {consentLoading ? 'Verifying…' : 'Verify Consent'}
              </button>
            </div>
            {consentError && (
              <div className="bg-red-950/40 border border-red-800/40 rounded-lg px-3 py-2.5 text-[12px] text-red-400 mt-3">
                {consentError}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Patient Record (shown only after consent verified) ── */}
      {patient && consentVerified && (
        <div className="card">
          <div className="card-head">
            <div className="flex items-center gap-3.5">
              <div className="w-12 h-12 rounded-full bg-emerald-950/40 border border-emerald-800/30
                              flex items-center justify-center text-[16px] font-bold text-emerald-400">
                {patient.name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()}
              </div>
              <div>
                <div className="text-[16px] font-bold text-[#e2e8f0]">{patient.name}</div>
                <div className="text-[12px] text-[#8b949e] mt-0.5">
                  ABHA: {patient.abha_id || '—'}&nbsp;|&nbsp;Phone: {patient.phone || '—'}
                </div>
              </div>
            </div>
            <div className="flex gap-2">
              {!editMode && (
                <button onClick={enterEditMode} className="btn btn-outline text-[12px]">
                  Edit Patient
                </button>
              )}
              <Badge variant="safe">Consent Verified</Badge>
            </div>
          </div>

          <div className="card-body">
            {editMode ? (
              // ── Edit Mode (only name & phone) ──
              <div className="space-y-3">
                <Field label="Name" value={editName} onChange={e => setEditName(e.target.value)} placeholder="Patient name" />
                <Field label="Phone" value={editPhone} onChange={e => setEditPhone(e.target.value)} placeholder="Phone number" />
                <div className="flex gap-2 mt-2">
                  <button onClick={handleSaveEdit} disabled={editLoading}
                    className="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed">
                    {editLoading ? 'Saving…' : 'Save Changes'}
                  </button>
                  <button onClick={() => { setEditMode(false); setEditMsg(null) }}
                    className="btn btn-outline">Cancel</button>
                </div>
                <MsgBanner msg={editMsg} />
              </div>
            ) : (
              // ── Display Mode — reads from abdm_mock_records ──
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  {/* Active medications from abdm_mock_records */}
                  <div className="section-label">Active medications</div>
                  {medNames.length > 0 ? (
                    medNames.map((med) => (
                      <div key={med} className="info-row">
                        <span className="text-[#8b949e]">{med}</span>
                        <Badge variant="warn">Active</Badge>
                      </div>
                    ))
                  ) : (
                    <p className="text-[13px] text-[#484f58]">No medications recorded</p>
                  )}

                  {/* Pre-existing conditions */}
                  <div className="section-label mt-4">Diagnosed conditions</div>
                  <div className="mt-1 flex flex-wrap">
                    {condNames.length > 0 ? (
                      condNames.map((c) => (
                        <span key={c} className="tag-pill">{c}</span>
                      ))
                    ) : (
                      <p className="text-[13px] text-[#484f58]">No conditions recorded</p>
                    )}
                  </div>

                  {/* Allergies */}
                  <div className="section-label mt-4">Allergies</div>
                  <div className="mt-1 flex flex-wrap">
                    {allergyNames.length > 0 ? (
                      allergyNames.map((a) => (
                        <span key={a} className="tag-pill bg-red-950/30 border-red-800/30 text-red-400">{a}</span>
                      ))
                    ) : (
                      <p className="text-[13px] text-[#484f58]">No allergies recorded</p>
                    )}
                  </div>
                </div>

                <div>
                  {/* Consent status */}
                  <div className="section-label">Consent status</div>
                  <AlertBox variant="safe" title="Consent granted">
                    Patient verified their identity via password at the counter.
                  </AlertBox>

                  {/* Patient metadata */}
                  <div className="section-label mt-4">Record information</div>
                  <div className="space-y-1 text-[12px]">
                    <div className="text-[#8b949e]">Patient ID: <span className="text-[#e2e8f0] font-medium">{patient.id}</span></div>
                    <div className="text-[#8b949e]">ABHA ID: <span className="text-[#e2e8f0] font-medium">{patient.abha_id || '—'}</span></div>
                    <div className="text-[#8b949e]">Phone: <span className="text-[#e2e8f0] font-medium">{patient.phone || '—'}</span></div>
                    <div className="text-[#8b949e]">Registered by: <span className="text-[#e2e8f0] font-medium">{patient.registered_by || '—'}</span></div>
                  </div>
                </div>
              </div>
            )}
            {!editMode && <MsgBanner msg={editMsg} />}
          </div>
        </div>
      )}
    </div>
  )
}
