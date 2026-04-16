import React, { useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const ABDM_TEMPLATE = {
  abha_id: "12-3456-7890-1234",
  basic_health_details: { blood_group: "O+", height_cm: 170, weight_kg: 65 },
  pre_existing_conditions: [
    { condition: "Hypertension", diagnosed_date: "2020-01-15", severity: "moderate" }
  ],
  medication_history: [
    { medication_name: "Amlodipine", dosage: "5mg", status: "active", time_period: "current" }
  ],
  allergies: [
    { allergen: "Penicillin", reaction: "Rash", severity: "moderate" }
  ]
}

export default function AdminPanel() {
  // ── Add Pharmacist form state ──
  const [pharmName, setPharmName]       = useState('')
  const [pharmUsername, setPharmUsername] = useState('')
  const [pharmPassword, setPharmPassword] = useState('')
  const [pharmPhone, setPharmPhone]     = useState('')
  const [pharmLicense, setPharmLicense] = useState('')
  const [pharmLoading, setPharmLoading] = useState(false)
  const [pharmMsg, setPharmMsg]         = useState(null)

  // ── Add Admin form state ──
  const [adminName, setAdminName]       = useState('')
  const [adminUsername, setAdminUsername] = useState('')
  const [adminPassword, setAdminPassword] = useState('')
  const [adminLoading, setAdminLoading] = useState(false)
  const [adminMsg, setAdminMsg]         = useState(null)

  // ── Add Patient form state ──
  const [patientName, setPatientName] = useState('')
  const [patientAbhaId, setPatientAbhaId] = useState('')
  const [patientPhone, setPatientPhone] = useState('')
  const [patientPassword, setPatientPassword] = useState('')
  const [patientRegisteredBy, setPatientRegisteredBy] = useState('')
  const [patientLoading, setPatientLoading] = useState(false)
  const [patientMsg, setPatientMsg] = useState(null)

  // ── Upload ABDM Record state ──
  const [abdmJson, setAbdmJson] = useState('')
  const [abdmLoading, setAbdmLoading] = useState(false)
  const [abdmMsg, setAbdmMsg] = useState(null)

  const getToken = () => {
    const savedUser = localStorage.getItem('ag_user')
    return savedUser ? JSON.parse(savedUser).token : ''
  }

  // ── Submit: Add Pharmacist ──
  const handleAddPharmacist = async () => {
    if (!pharmName.trim() || !pharmUsername.trim() || !pharmPassword.trim() || !pharmPhone.trim() || !pharmLicense.trim()) {
      setPharmMsg({ type: 'error', text: 'All fields are required.' })
      return
    }
    setPharmLoading(true)
    setPharmMsg(null)
    try {
      const res = await fetch(`${API_BASE}/api/admin/add-pharmacist`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${getToken()}` },
        body: JSON.stringify({
          name: pharmName.trim(),
          username: pharmUsername.trim(),
          password: pharmPassword.trim(),
          phone: pharmPhone.trim(),
          license_number: pharmLicense.trim(),
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed to add pharmacist')
      setPharmMsg({ type: 'success', text: data.message || 'Pharmacist added successfully!' })
      setPharmName(''); setPharmUsername(''); setPharmPassword(''); setPharmPhone(''); setPharmLicense('')
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
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${getToken()}` },
        body: JSON.stringify({
          name: adminName.trim(),
          username: adminUsername.trim(),
          password: adminPassword.trim(),
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed to add admin')
      setAdminMsg({ type: 'success', text: data.message || 'Admin added successfully!' })
      setAdminName(''); setAdminUsername(''); setAdminPassword('')
    } catch (err) {
      setAdminMsg({ type: 'error', text: err.message })
    } finally {
      setAdminLoading(false)
    }
  }

  // ── Submit: Add Patient (admin only) ──
  const handleAddPatient = async () => {
    if (!patientName.trim() || !patientAbhaId.trim() || !patientPhone.trim() || !patientPassword.trim() || !patientRegisteredBy.trim()) {
      setPatientMsg({ type: 'error', text: 'All fields are required.' })
      return
    }
    setPatientLoading(true)
    setPatientMsg(null)
    try {
      const res = await fetch(`${API_BASE}/api/admin/add-patient`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${getToken()}` },
        body: JSON.stringify({
          name: patientName.trim(),
          abha_id: patientAbhaId.trim(),
          phone: patientPhone.trim(),
          password: patientPassword.trim(),
          registered_by: patientRegisteredBy.trim(),
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed to add patient')
      setPatientMsg({ type: 'success', text: data.message || 'Patient added successfully!' })
      setPatientName(''); setPatientAbhaId(''); setPatientPhone(''); setPatientPassword(''); setPatientRegisteredBy('')
    } catch (err) {
      setPatientMsg({ type: 'error', text: err.message })
    } finally {
      setPatientLoading(false)
    }
  }

  // ── Submit: Upload ABDM Record ──
  const handleUploadAbdm = async () => {
    if (!abdmJson.trim()) {
      setAbdmMsg({ type: 'error', text: 'Please paste or load a JSON document.' })
      return
    }

    let parsed
    try {
      parsed = JSON.parse(abdmJson)
    } catch (e) {
      setAbdmMsg({ type: 'error', text: `Invalid JSON: ${e.message}` })
      return
    }

    if (!parsed.abha_id) {
      setAbdmMsg({ type: 'error', text: 'JSON must contain an "abha_id" field.' })
      return
    }

    setAbdmLoading(true)
    setAbdmMsg(null)
    try {
      const res = await fetch(`${API_BASE}/api/admin/upload-abdm-record`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${getToken()}` },
        body: JSON.stringify(parsed),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Upload failed')
      setAbdmMsg({ type: 'success', text: data.message || 'ABDM record uploaded!' })
      setAbdmJson('')
    } catch (err) {
      setAbdmMsg({ type: 'error', text: err.message })
    } finally {
      setAbdmLoading(false)
    }
  }

  // Handle file upload
  const handleFileUpload = (e) => {
    const file = e.target.files[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (ev) => {
      setAbdmJson(ev.target.result)
      setAbdmMsg(null)
    }
    reader.readAsText(file)
  }

  // Load template
  const handleLoadTemplate = () => {
    setAbdmJson(JSON.stringify(ABDM_TEMPLATE, null, 2))
    setAbdmMsg(null)
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
      {/* Page title */}
      <div className="card">
        <div className="card-head">
          <div>
            <div className="text-[16px] font-bold text-[#e2e8f0]">Admin Panel</div>
            <div className="text-[12px] text-[#8b949e] mt-0.5">
              Manage pharmacists, patients, and medical records
            </div>
          </div>
        </div>
      </div>

      {/* Three side-by-side forms (Admin, Pharmacist, Patient) */}
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
              <Field label="License Number" value={pharmLicense} onChange={e => setPharmLicense(e.target.value)} placeholder="e.g. PH-001" />
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
              <Field label="ABHA ID" value={patientAbhaId} onChange={e => setPatientAbhaId(e.target.value)} placeholder="e.g. 12-3456-7890-1234" />
              <Field label="Phone" value={patientPhone} onChange={e => setPatientPhone(e.target.value)} placeholder="e.g. 9876543210" />
              <Field label="Password" type="password" value={patientPassword} onChange={e => setPatientPassword(e.target.value)} placeholder="Enter password" />
              <Field label="Registered By (Pharmacist UUID)" value={patientRegisteredBy} onChange={e => setPatientRegisteredBy(e.target.value)} placeholder="Enter pharmacist UUID" />
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

      {/* ── Upload ABDM Record Card ── */}
      <div className="card mt-3.5">
        <div className="card-body">
          <div className="section-label">Upload ABDM Medical Record</div>
          <p className="text-[12px] text-[#8b949e] mb-3">
            Paste or upload a JSON file containing patient medical data compliant with the
            <span className="text-[#e2e8f0] font-medium"> abdm_mock_records</span> schema.
            Invalid JSON will be rejected.
          </p>

          <div className="flex gap-2 mb-3">
            <button onClick={handleLoadTemplate}
              className="btn btn-outline text-[12px]">
              Load template
            </button>
            <label className="btn btn-outline text-[12px] cursor-pointer">
              Upload JSON file
              <input type="file" accept=".json" onChange={handleFileUpload} className="hidden" />
            </label>
          </div>

          {/* Template preview */}
          <details className="mb-3">
            <summary className="text-[11px] text-[#484f58] cursor-pointer hover:text-[#8b949e] transition-colors">
              View expected JSON format
            </summary>
            <pre className="mt-2 bg-[#0d1117] border border-[#21262d] rounded-lg p-3
                            text-[11px] text-[#7ee787] font-mono overflow-auto max-h-48">
              {JSON.stringify(ABDM_TEMPLATE, null, 2)}
            </pre>
          </details>

          <textarea
            value={abdmJson}
            onChange={(e) => setAbdmJson(e.target.value)}
            placeholder='Paste JSON here...'
            rows={8}
            className="w-full px-3.5 py-2.5 border border-[#21262d] rounded-lg text-[13px] outline-none
                       bg-[#0d1117] text-[#e2e8f0] placeholder-[#484f58] font-mono
                       focus:border-[#1D9E75] focus:ring-2 focus:ring-[#1D9E75]/20 transition-all resize-y"
          />

          <button
            onClick={handleUploadAbdm}
            disabled={abdmLoading}
            className="w-full btn btn-primary py-3 text-[14px] disabled:opacity-50 disabled:cursor-not-allowed mt-3"
          >
            {abdmLoading ? 'Uploading…' : 'Upload ABDM Record'}
          </button>
          <MsgBanner msg={abdmMsg} />
        </div>
      </div>
    </div>
  )
}
