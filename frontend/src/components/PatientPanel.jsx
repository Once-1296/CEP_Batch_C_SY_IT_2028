import React, { useState } from 'react'
import { PATIENTS } from '../data/mockData'
import Badge from './Badge'
import AlertBox from './AlertBox'

const FHIR_TEMPLATE = (patient) => `{
  "resourceType": "Bundle",
  "type": "collection",
  "entry": [
    {
      "resource": {
        "resourceType": "Patient",
        "name": "${patient.name}",
        "gender": "${patient.gender.toLowerCase()}",
        "identifier": { "value": "${patient.abha}" }
      }
    },
    ${patient.meds.map(med => `{
      "resource": {
        "resourceType": "MedicationStatement",
        "status": "active",
        "medicationCodeableConcept": { "text": "${med}" }
      }
    }`).join(',\n    ')},
    ${patient.conditions.map(c => `{
      "resource": {
        "resourceType": "Condition",
        "code": { "text": "${c}" },
        "clinicalStatus": "active"
      }
    }`).join(',\n    ')}
  ]
}`

export default function PatientPanel({ activePatientId }) {
  const [selectedId, setSelectedId] = useState(activePatientId || 'ABHA-1234-5678')
  const patient = PATIENTS[selectedId]

  return (
    <div>
      {/* Patient selector */}
      <div className="card">
        <div className="card-body">
          <div className="section-label">Select patient</div>
          <div className="flex gap-2">
            {Object.entries(PATIENTS).map(([id, p]) => (
              <button
                key={id}
                onClick={() => setSelectedId(id)}
                className={`flex-1 px-3.5 py-2.5 rounded-lg text-[13px] font-medium border transition-all
                  ${selectedId === id
                    ? 'bg-[#1D9E75] text-white border-[#1D9E75]'
                    : 'bg-[#0d1117] text-[#8b949e] border-[#21262d] hover:border-[#484f58]'
                  }`}
              >
                {p.name}
                <span className="block text-[10px] opacity-70 mt-0.5">{id}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Patient record card */}
      <div className="card">
        <div className="card-head">
          <div className="flex items-center gap-3.5">
            <div className="w-12 h-12 rounded-full bg-emerald-950/40 border border-emerald-800/30
                            flex items-center justify-center text-[16px] font-bold text-emerald-400">
              {patient.initials}
            </div>
            <div>
              <div className="text-[16px] font-bold text-[#e2e8f0]">{patient.name}</div>
              <div className="text-[12px] text-[#8b949e] mt-0.5">
                ABHA: {patient.abha}&nbsp;|&nbsp;Age: {patient.age} yrs&nbsp;|&nbsp;{patient.gender}
              </div>
            </div>
          </div>
          <Badge variant="info">FHIR R4</Badge>
        </div>

        <div className="card-body grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Left column */}
          <div>
            <div className="section-label">Active medications (MedicationStatement)</div>
            {patient.meds.map((med) => (
              <div key={med} className="info-row">
                <span className="text-[#8b949e]">{med}</span>
                <Badge variant="warn">Active</Badge>
              </div>
            ))}

            <div className="section-label mt-4">Diagnosed conditions (Condition)</div>
            <div className="mt-1 flex flex-wrap">
              {patient.conditions.map((c) => (
                <span key={c} className="tag-pill">{c}</span>
              ))}
            </div>

            <div className="section-label mt-4">Consent status</div>
            <AlertBox variant="safe" title="Consent granted">
              Patient approved HIU request at {patient.consentTime} via ABDM sandbox app
            </AlertBox>
          </div>

          {/* Right column */}
          <div>
            <div className="section-label">Simulated FHIR bundle (ABDM sandbox)</div>
            <pre className="fhir-text bg-[#0d1117] border border-[#21262d] rounded-lg p-3
                            text-[11px] leading-relaxed overflow-auto max-h-52 whitespace-pre-wrap">
              {FHIR_TEMPLATE(patient)}
            </pre>

            <div className="section-label mt-4">ABDM HIU request flow</div>
            <ol className="text-[12px] text-[#8b949e] leading-loose list-none space-y-0.5">
              {[
                'Chemist enters ABHA ID',
                'Consent request sent to patient\'s phone',
                'Patient approves via ABDM sandbox app',
                'System fetches FHIR bundle via HIU API',
                'Parser extracts MedicationStatement + Condition blocks',
              ].map((step, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-[#1D9E75] font-bold flex-shrink-0">{i + 1}.</span>
                  <span>{step}</span>
                </li>
              ))}
            </ol>
          </div>
        </div>
      </div>
    </div>
  )
}
