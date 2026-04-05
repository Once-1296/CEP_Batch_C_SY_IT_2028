import React, { useState } from 'react'
import PipelineSteps from './PipelineSteps'
import SafetyResult from './SafetyResult'
import AlertBox from './AlertBox'
import { useSafetyCheck } from '../hooks/useSafetyCheck'
import { PATIENTS } from '../data/mockData'

// Demo drugs that work with backend medicines_cleaned.csv
const DEMO_DRUGS = ['Augmentin 625', 'Allegra 120mg', 'Ascoril LS', 'Azithral 500', 'Ambroxol']

export default function DashboardPanel({ onViewPatient, onPatientChange }) {
  const [input, setInput]         = useState('')
  const [patientId, setPatientId] = useState('ABHA-1234-5678')
  const { loading, loadingMsg, steps, showSteps, result, apiError, runCheck, clear } = useSafetyCheck()

  const handleCheck = () => runCheck(input, patientId)
  const handleClear = () => { setInput(''); clear() }
  const handleDemo  = (name) => setInput(name)

  const handlePatientChange = (id) => {
    setPatientId(id)
    clear()
    if (onPatientChange) onPatientChange(id)
  }

  const selectedPatient = PATIENTS[patientId]

  return (
    <div>
      <div className="card">
        <div className="card-body">

          {/* Medicine search */}
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
            <button onClick={handleCheck} disabled={loading}
              className="btn btn-primary whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed">
              {loading ? 'Checking…' : 'Run safety check'}
            </button>
            <button onClick={handleClear} className="btn btn-outline">Clear</button>
          </div>

          {/* Patient selector */}
          <div className="section-label">Select patient (ABHA ID)</div>
          <div className="flex gap-2 mb-4 items-center flex-wrap">
            <select
              value={patientId}
              onChange={(e) => handlePatientChange(e.target.value)}
              className="px-3.5 py-2.5 border border-[#21262d] rounded-lg text-[14px] outline-none
                         bg-[#0d1117] text-[#e2e8f0]
                         focus:border-[#378ADD] focus:ring-2 focus:ring-[#378ADD]/20 transition-all"
            >
              {Object.entries(PATIENTS).map(([id, p]) => (
                <option key={id} value={id}>{id} — {p.name}</option>
              ))}
            </select>
            <button onClick={onViewPatient} className="btn btn-blue whitespace-nowrap">
              View patient profile
            </button>
          </div>

          {/* Selected patient quick info strip */}
          {selectedPatient && (
            <div className="bg-[#0d1117] border border-[#21262d] rounded-lg px-3.5 py-2.5 mb-4">
              <div className="flex flex-wrap gap-4 text-[12px]">
                <span className="text-[#8b949e]">Patient: <span className="text-[#e2e8f0] font-medium">{selectedPatient.name}</span></span>
                <span className="text-[#8b949e]">Age: <span className="text-[#e2e8f0] font-medium">{selectedPatient.age}</span></span>
                <span className="text-[#8b949e]">Conditions: <span className="text-amber-400 font-medium">{selectedPatient.conditions.join(', ')}</span></span>
                <span className="text-[#8b949e]">Current meds: <span className="text-blue-400 font-medium">{selectedPatient.meds.join(', ')}</span></span>
              </div>
            </div>
          )}

          {/* Demo quick links */}
          <p className="text-[12px] text-[#484f58]">
            Try with <span className="text-amber-400 font-medium">Rajesh Kumar</span>:{' '}
            {DEMO_DRUGS.map((name, i) => (
              <React.Fragment key={name}>
                <button onClick={() => handleDemo(name)}
                  className="text-emerald-400 underline hover:text-emerald-300 transition-colors">
                  {name}
                </button>
                {i < DEMO_DRUGS.length - 1 && <span className="mx-1 text-[#30363d]">·</span>}
              </React.Fragment>
            ))}
          </p>
        </div>
      </div>

      {/* Pipeline steps */}
      {showSteps && (
        <PipelineSteps steps={steps} loading={loading} loadingMsg={loadingMsg} />
      )}

      {/* API connection error */}
      {apiError && (
        <AlertBox variant="critical" title="Backend connection error">
          {apiError}
        </AlertBox>
      )}

      {/* Safety check result */}
      {!loading && result && <SafetyResult result={result} />}
    </div>
  )
}
