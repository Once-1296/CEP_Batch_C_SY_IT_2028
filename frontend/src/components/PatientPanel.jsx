import React, { useState, useEffect } from 'react'
import Badge from './Badge'
import AlertBox from './AlertBox'
// CHANGED: Removed import { PATIENTS } from '../data/mockData'
// Patient data now comes from Supabase via API

const API_BASE = 'http://localhost:8000'

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
  const [editMeds, setEditMeds]           = useState('')
  const [editConditions, setEditConditions] = useState('')
  const [editName, setEditName]           = useState('')
  const [editPhone, setEditPhone]         = useState('')
  const [editLoading, setEditLoading]     = useState(false)
  const [editMsg, setEditMsg]             = useState(null)

  // ── Add new patient state ──
  const [showAddForm, setShowAddForm]     = useState(false)
  const [newName, setNewName]             = useState('')
  const [newPhone, setNewPhone]           = useState('')
  const [newPassword, setNewPassword]     = useState('')
  const [newMeds, setNewMeds]             = useState('')
  const [newConditions, setNewConditions] = useState('')
  const [addLoading, setAddLoading]       = useState(false)
  const [addMsg, setAddMsg]               = useState(null)

  // ── Fetch patients on mount ──
  const fetchPatients = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/patients`)
      const data = await res.json()
      const list = data.patients || []
      setPatients(list)
      // CHANGED: Auto-select first patient or keep active
      if (activePatientId) {
        setSelectedId(String(activePatientId))
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
  const handleSelectPatient = (id) => {
    setSelectedId(id)
    setConsentVerified(false)
    setConsentPassword('')
    setConsentError(null)
    setEditMode(false)
    setEditMsg(null)
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
      const res = await fetch(`${API_BASE}/api/patients/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patient_id: parseInt(selectedId), password: consentPassword }),
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

  // ── Enter edit mode ──
  const enterEditMode = () => {
    if (!patient) return
    setEditName(patient.name || '')
    setEditPhone(patient.phone || '')
    setEditMeds((patient.current_medications || []).join(', '))
    setEditConditions((patient.current_conditions || []).join(', '))
    setEditMode(true)
    setEditMsg(null)
  }

  // ── Save edits ──
  const handleSaveEdit = async () => {
    setEditLoading(true)
    setEditMsg(null)
    try {
      const res = await fetch(`${API_BASE}/api/patients/${selectedId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: editName.trim(),
          phone: editPhone.trim(),
          // CHANGED: Split comma-separated string into array before sending
          current_medications: editMeds.split(',').map(s => s.trim()).filter(Boolean),
          current_conditions: editConditions.split(',').map(s => s.trim()).filter(Boolean),
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Update failed')
      setEditMsg({ type: 'success', text: 'Patient updated successfully!' })
      setEditMode(false)
      // CHANGED: Refresh patient list to reflect changes
      await fetchPatients()
    } catch (err) {
      setEditMsg({ type: 'error', text: err.message })
    } finally {
      setEditLoading(false)
    }
  }

  // ── Add new patient ──
  const handleAddPatient = async () => {
    if (!newName.trim() || !newPhone.trim() || !newPassword.trim()) {
      setAddMsg({ type: 'error', text: 'Name, phone, and password are required.' })
      return
    }
    setAddLoading(true)
    setAddMsg(null)
    try {
      const res = await fetch(`${API_BASE}/api/patients`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newName.trim(),
          phone: newPhone.trim(),
          password: newPassword.trim(),
          // CHANGED: Split comma-separated string into array before sending
          current_medications: newMeds.split(',').map(s => s.trim()).filter(Boolean),
          current_conditions: newConditions.split(',').map(s => s.trim()).filter(Boolean),
          // CHANGED: Auto-fill added_by from logged-in pharmacist
          added_by: loggedInUser?.username || 'unknown',
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed to add patient')
      setAddMsg({ type: 'success', text: 'Patient added successfully!' })
      // CHANGED: Clear form and refresh list
      setNewName(''); setNewPhone(''); setNewPassword(''); setNewMeds(''); setNewConditions('')
      setShowAddForm(false)
      await fetchPatients()
    } catch (err) {
      setAddMsg({ type: 'error', text: err.message })
    } finally {
      setAddLoading(false)
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
                  <option key={p.id} value={String(p.id)}>{p.name} — {p.phone || 'No phone'}</option>
                ))}
              </select>
            )}
            {/* CHANGED: Add New Patient button */}
            <button onClick={() => { setShowAddForm(!showAddForm); setAddMsg(null) }}
              className="btn btn-primary whitespace-nowrap">
              {showAddForm ? 'Cancel' : '+ Add New Patient'}
            </button>
          </div>
        </div>
      </div>

      {/* ── Add New Patient Form ── */}
      {showAddForm && (
        <div className="card">
          <div className="card-body">
            <div className="section-label">Add New Patient</div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <Field label="Full Name" value={newName} onChange={e => setNewName(e.target.value)} placeholder="e.g. Rajesh Kumar" />
              <Field label="Phone" value={newPhone} onChange={e => setNewPhone(e.target.value)} placeholder="e.g. 9876543210" />
              <Field label="Password (for consent)" type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} placeholder="Patient password" />
              <div>{/* spacer */}</div>
              <Field label="Current Medications (comma separated)" value={newMeds} onChange={e => setNewMeds(e.target.value)} placeholder="e.g. Amlodipine, Methotrexate" />
              <Field label="Current Conditions (comma separated)" value={newConditions} onChange={e => setNewConditions(e.target.value)} placeholder="e.g. Kidney Disease, Hypertension" />
            </div>
            {/* CHANGED: Auto-fill added_by from logged-in pharmacist */}
            <div className="text-[12px] text-[#484f58] mt-2">
              Added by: <span className="text-[#e2e8f0] font-medium">{loggedInUser?.username || 'unknown'}</span>
            </div>
            <button onClick={handleAddPatient} disabled={addLoading}
              className="btn btn-primary mt-3 disabled:opacity-50 disabled:cursor-not-allowed">
              {addLoading ? 'Adding…' : 'Add Patient'}
            </button>
            <MsgBanner msg={addMsg} />
          </div>
        </div>
      )}

      {/* ── Consent Verification ── */}
      {patient && !consentVerified && !showAddForm && (
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
      {patient && consentVerified && !showAddForm && (
        <div className="card">
          <div className="card-head">
            <div className="flex items-center gap-3.5">
              {/* CHANGED: Initials derived from patient name */}
              <div className="w-12 h-12 rounded-full bg-emerald-950/40 border border-emerald-800/30
                              flex items-center justify-center text-[16px] font-bold text-emerald-400">
                {patient.name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()}
              </div>
              <div>
                <div className="text-[16px] font-bold text-[#e2e8f0]">{patient.name}</div>
                <div className="text-[12px] text-[#8b949e] mt-0.5">
                  Phone: {patient.phone || '—'}&nbsp;|&nbsp;Added by: {patient.added_by || '—'}
                </div>
              </div>
            </div>
            <div className="flex gap-2">
              {/* CHANGED: Edit Patient toggle */}
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
              // ── Edit Mode ──
              <div className="space-y-3">
                <Field label="Name" value={editName} onChange={e => setEditName(e.target.value)} placeholder="Patient name" />
                <Field label="Phone" value={editPhone} onChange={e => setEditPhone(e.target.value)} placeholder="Phone number" />
                <Field label="Current Medications (comma separated)" value={editMeds} onChange={e => setEditMeds(e.target.value)} placeholder="e.g. Amlodipine, Methotrexate" />
                <Field label="Current Conditions (comma separated)" value={editConditions} onChange={e => setEditConditions(e.target.value)} placeholder="e.g. Kidney Disease, Hypertension" />
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
              // ── Display Mode ──
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  {/* CHANGED: Use current_medications from Supabase */}
                  <div className="section-label">Active medications</div>
                  {(patient.current_medications || []).length > 0 ? (
                    (patient.current_medications || []).map((med) => (
                      <div key={med} className="info-row">
                        <span className="text-[#8b949e]">{med}</span>
                        <Badge variant="warn">Active</Badge>
                      </div>
                    ))
                  ) : (
                    <p className="text-[13px] text-[#484f58]">No medications recorded</p>
                  )}

                  {/* CHANGED: Use current_conditions from Supabase */}
                  <div className="section-label mt-4">Diagnosed conditions</div>
                  <div className="mt-1 flex flex-wrap">
                    {(patient.current_conditions || []).length > 0 ? (
                      (patient.current_conditions || []).map((c) => (
                        <span key={c} className="tag-pill">{c}</span>
                      ))
                    ) : (
                      <p className="text-[13px] text-[#484f58]">No conditions recorded</p>
                    )}
                  </div>
                </div>

                <div>
                  {/* CHANGED: Consent status — verified via password */}
                  <div className="section-label">Consent status</div>
                  <AlertBox variant="safe" title="Consent granted">
                    Patient verified their identity via password at the counter.
                  </AlertBox>

                  {/* CHANGED: Patient metadata */}
                  <div className="section-label mt-4">Record information</div>
                  <div className="space-y-1 text-[12px]">
                    <div className="text-[#8b949e]">Patient ID: <span className="text-[#e2e8f0] font-medium">{patient.id}</span></div>
                    <div className="text-[#8b949e]">Phone: <span className="text-[#e2e8f0] font-medium">{patient.phone || '—'}</span></div>
                    <div className="text-[#8b949e]">Added by: <span className="text-[#e2e8f0] font-medium">{patient.added_by || '—'}</span></div>
                  </div>
                </div>
              </div>
            )}
            {/* Show edit message outside of edit mode too */}
            {!editMode && <MsgBanner msg={editMsg} />}
          </div>
        </div>
      )}
    </div>
  )
}
