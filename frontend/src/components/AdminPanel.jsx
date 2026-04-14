import React, { useState } from 'react'

// ── CHANGED: Admin Panel — only visible to admin role ──────────────────────
// Two side-by-side forms: Add Pharmacist and Add Admin
// No table/list of existing users — prototype only

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export default function AdminPanel() {
  // ── Add Pharmacist form state ──
  const [pharmName, setPharmName]       = useState('')
  const [pharmUsername, setPharmUsername] = useState('')
  const [pharmPassword, setPharmPassword] = useState('')
  const [pharmPhone, setPharmPhone]     = useState('')
  const [pharmLoading, setPharmLoading] = useState(false)
  const [pharmMsg, setPharmMsg]         = useState(null)   // { type: 'success'|'error', text }

  // ── Add Admin form state ──
  const [adminName, setAdminName]       = useState('')
  const [adminUsername, setAdminUsername] = useState('')
  const [adminPassword, setAdminPassword] = useState('')
  const [adminLoading, setAdminLoading] = useState(false)
  const [adminMsg, setAdminMsg]         = useState(null)

  // ── Add Patient form state ──
  const [patientName, setPatientName] = useState('')
  const [patientPhone, setPatientPhone] = useState('')
  const [patientPassword, setPatientPassword] = useState('')
  const [patientAddedBy, setPatientAddedBy] = useState('') // pharmacist id
  const [patientMedications, setPatientMedications] = useState('') // comma-separated
  const [patientConditions, setPatientConditions] = useState('') // comma-separated
  const [patientLoading, setPatientLoading] = useState(false)
  const [patientMsg, setPatientMsg] = useState(null)

  // ── Submit: Add Pharmacist ──
  const handleAddPharmacist = async () => {
    if (!pharmName.trim() || !pharmUsername.trim() || !pharmPassword.trim() || !pharmPhone.trim()) {
      setPharmMsg({ type: 'error', text: 'All fields are required.' })
      return
    }
    setPharmLoading(true)
    setPharmMsg(null)
    try {
      const res = await fetch(`${API_BASE}/api/admin/add-pharmacist`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: pharmName.trim(),
          username: pharmUsername.trim(),
          password: pharmPassword.trim(),
          phone: pharmPhone.trim(),
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed to add pharmacist')
      setPharmMsg({ type: 'success', text: data.message || 'Pharmacist added successfully!' })
      // CHANGED: Clear form on success
      setPharmName(''); setPharmUsername(''); setPharmPassword(''); setPharmPhone('')
    } catch (err) {
      setPharmMsg({ type: 'error', text: err.message })
    } finally {
      setPharmLoading(false)
    }
  }

  // ── Submit: Add Admin ──
  const handleAddAdmin = async () => {
    if (!adminName.trim() || !adminUsername.trim() || !adminPassword.trim()) {
      setAdminMsg({ type: 'error', text: 'All fields are required.' })
      return
    }
    setAdminLoading(true)
    setAdminMsg(null)
    try {
      const res = await fetch(`${API_BASE}/api/admin/add-admin`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: adminName.trim(),
          username: adminUsername.trim(),
          password: adminPassword.trim(),
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed to add admin')
      setAdminMsg({ type: 'success', text: data.message || 'Admin added successfully!' })
      // CHANGED: Clear form on success
      setAdminName(''); setAdminUsername(''); setAdminPassword('')
    } catch (err) {
      setAdminMsg({ type: 'error', text: err.message })
    } finally {
      setAdminLoading(false)
    }
  }

  // ── Submit: Add Patient ──
  const handleAddPatient = async () => {
    if (!patientName.trim() || !patientPhone.trim() || !patientPassword.trim() || !patientAddedBy.trim()) {
      setPatientMsg({ type: 'error', text: 'Name, phone, password and registered-by (pharmacist id) are required.' })
      return
    }
    setPatientLoading(true)
    setPatientMsg(null)
    try {
      const meds = patientMedications.split(',').map(s => s.trim()).filter(Boolean)
      const conds = patientConditions.split(',').map(s => s.trim()).filter(Boolean)
      const addedByVal = Number(patientAddedBy.trim())

      const res = await fetch(`${API_BASE}/api/admin/add-patient`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: patientName.trim(),
          phone: patientPhone.trim(),
          password: patientPassword.trim(),
          current_medications: meds,
          current_conditions: conds,
          added_by: isNaN(addedByVal) ? patientAddedBy.trim() : addedByVal,
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed to add patient')
      setPatientMsg({ type: 'success', text: data.message || 'Patient added successfully!' })
      // Clear form on success
      setPatientName('')
      setPatientPhone('')
      setPatientPassword('')
      setPatientAddedBy('')
      setPatientMedications('')
      setPatientConditions('')
    } catch (err) {
      setPatientMsg({ type: 'error', text: err.message })
    } finally {
      setPatientLoading(false)
    }
  }

  // ── Reusable message banner ──
  const MsgBanner = ({ msg }) => {
    if (!msg) return null
    const isErr = msg.type === 'error'
    return (
      <div className={`rounded-lg px-3 py-2.5 text-[12px] mt-3 ${
        isErr
          ? 'bg-red-950/40 border border-red-800/40 text-red-400'
          : 'bg-emerald-950/40 border border-emerald-800/40 text-emerald-400'
      }`}>
        {msg.text}
      </div>
    )
  }

  // ── Reusable input field ──
  const Field = ({ label, type = 'text', value, onChange, placeholder }) => (
    <div>
      <label className="text-[11px] font-bold text-[#484f58] uppercase tracking-widest block mb-1.5">
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className="w-full px-3.5 py-2.5 border border-[#21262d] rounded-lg text-[14px] outline-none
                   bg-[#0d1117] text-[#e2e8f0] placeholder-[#484f58]
                   focus:border-[#1D9E75] focus:ring-2 focus:ring-[#1D9E75]/20 transition-all"
      />
    </div>
  )

  return (
    <div>
      {/* CHANGED: Page title for admin context */}
      <div className="card">
        <div className="card-head">
          <div>
            <div className="text-[16px] font-bold text-[#e2e8f0]">Admin Panel</div>
            <div className="text-[12px] text-[#8b949e] mt-0.5">
              Manage pharmacists and admin accounts
            </div>
          </div>
        </div>
      </div>

  {/* CHANGED: Three side-by-side forms (Admin, Pharmacist, Patient) */}
  <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">

        {/* ── Add Pharmacist Card ── */}
        <div className="card">
          <div className="card-body">
            <div className="section-label">Add New Pharmacist</div>
            <div className="space-y-3">
              <Field label="Full Name" value={pharmName} onChange={e => setPharmName(e.target.value)} placeholder="e.g. Dr. Sharma" />
              <Field label="Username" value={pharmUsername} onChange={e => setPharmUsername(e.target.value)} placeholder="e.g. sharma_pharm" />
              <Field label="Password" type="password" value={pharmPassword} onChange={e => setPharmPassword(e.target.value)} placeholder="Enter password" />
              <Field label="Phone" value={pharmPhone} onChange={e => setPharmPhone(e.target.value)} placeholder="e.g. 9876543210" />
              <button
                onClick={handleAddPharmacist}
                disabled={pharmLoading}
                className="w-full btn btn-primary py-3 text-[14px] disabled:opacity-50 disabled:cursor-not-allowed mt-1"
              >
                {pharmLoading ? 'Adding…' : 'Add Pharmacist'}
              </button>
              <MsgBanner msg={pharmMsg} />
            </div>
          </div>
        </div>

        {/* ── Add Admin Card ── */}
        <div className="card">
          <div className="card-body">
            <div className="section-label">Add New Admin</div>
            <div className="space-y-3">
              <Field label="Full Name" value={adminName} onChange={e => setAdminName(e.target.value)} placeholder="e.g. Admin Two" />
              <Field label="Username" value={adminUsername} onChange={e => setAdminUsername(e.target.value)} placeholder="e.g. admin2" />
              <Field label="Password" type="password" value={adminPassword} onChange={e => setAdminPassword(e.target.value)} placeholder="Enter password" />
              <button
                onClick={handleAddAdmin}
                disabled={adminLoading}
                className="w-full btn btn-primary py-3 text-[14px] disabled:opacity-50 disabled:cursor-not-allowed mt-1"
              >
                {adminLoading ? 'Adding…' : 'Add Admin'}
              </button>
              <MsgBanner msg={adminMsg} />
            </div>
          </div>
        </div>

        {/* ── Add Patient Card ── */}
        <div className="card">
          <div className="card-body">
            <div className="section-label">Add New Patient</div>
            <div className="space-y-3">
              <Field label="Full Name" value={patientName} onChange={e => setPatientName(e.target.value)} placeholder="e.g. Ravi Kumar" />
              <Field label="Phone" value={patientPhone} onChange={e => setPatientPhone(e.target.value)} placeholder="e.g. 9876543210" />
              <Field label="Password" type="password" value={patientPassword} onChange={e => setPatientPassword(e.target.value)} placeholder="Enter password" />
              <Field label="Registered By (Pharmacist ID)" value={patientAddedBy} onChange={e => setPatientAddedBy(e.target.value)} placeholder="Enter pharmacist id (numeric)" />
              <Field label="Current Medications" value={patientMedications} onChange={e => setPatientMedications(e.target.value)} placeholder="Comma-separated, e.g. aspirin, metformin" />
              <Field label="Current Conditions" value={patientConditions} onChange={e => setPatientConditions(e.target.value)} placeholder="Comma-separated, e.g. diabetes, hypertension" />
              <button
                onClick={handleAddPatient}
                disabled={patientLoading}
                className="w-full btn btn-primary py-3 text-[14px] disabled:opacity-50 disabled:cursor-not-allowed mt-1"
              >
                {patientLoading ? 'Adding…' : 'Add Patient'}
              </button>
              <MsgBanner msg={patientMsg} />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
