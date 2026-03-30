import React from 'react'
import { PATIENT } from '../data/mockData'
import Badge from './Badge'
import AlertBox from './AlertBox'

const FHIR_PREVIEW = `{
  "resourceType": "Bundle",
  "type": "collection",
  "entry": [
    {
      "resource": {
        "resourceType": "MedicationStatement",
        "status": "active",
        "medicationCodeableConcept": {
          "text": "Metformin 500mg"
        },
        "subject": {
          "reference": "Patient/ravi-verma-001"
        }
      }
    },
    {
      "resource": {
        "resourceType": "Condition",
        "code": {
          "text": "Hypertension"
        },
        "clinicalStatus": "active"
      }
    }
  ]
}`

export default function PatientPanel() {
  return (
    <div>
      <div className="card">
        {/* Card header */}
        <div className="card-head">
          <div className="flex items-center gap-3.5">
            {/* Avatar */}
            <div className="w-12 h-12 rounded-full bg-emerald-950/40 border border-emerald-800/30
                            flex items-center justify-center text-[16px] font-bold text-emerald-400">
              {PATIENT.initials}
            </div>
            <div>
              <div className="text-[16px] font-bold text-[#e2e8f0]">{PATIENT.name}</div>
              <div className="text-[12px] text-[#8b949e] mt-0.5">
                ABHA: {PATIENT.abha}&nbsp;|&nbsp;DOB: {PATIENT.dob} ({PATIENT.age} yrs)&nbsp;|&nbsp;{PATIENT.gender}
              </div>
            </div>
          </div>
          <Badge variant="info">FHIR R4</Badge>
        </div>

        {/* Card body — two column */}
        <div className="card-body grid grid-cols-1 md:grid-cols-2 gap-4">

          {/* Left column */}
          <div>
            <div className="section-label">Active medications (MedicationStatement)</div>
            {PATIENT.meds.map((med) => (
              <div key={med} className="info-row">
                <span className="text-[#8b949e]">{med}</span>
                <Badge variant="warn">Active</Badge>
              </div>
            ))}

            <div className="section-label mt-4">Diagnosed conditions (Condition)</div>
            <div className="mt-1 flex flex-wrap">
              {PATIENT.conditions.map((c) => (
                <span key={c} className="tag-pill">{c}</span>
              ))}
            </div>

            <div className="section-label mt-4">Consent status</div>
            <AlertBox variant="safe" title="Consent granted">
              Patient approved HIU request at {PATIENT.consentTime} via ABDM app
            </AlertBox>
          </div>

          {/* Right column */}
          <div>
            <div className="section-label">Raw FHIR bundle preview</div>
            <pre className="fhir-text bg-[#0d1117] border border-[#21262d] rounded-lg p-3
                            text-[11px] leading-relaxed overflow-auto max-h-48 whitespace-pre-wrap">
              {FHIR_PREVIEW}
            </pre>

            <div className="section-label mt-4">ABDM HIU request flow</div>
            <ol className="text-[12px] text-[#8b949e] leading-loose list-none space-y-0.5">
              {[
                'Chemist enters ABHA ID',
                'Consent request sent to patient\'s phone',
                'Patient approves via ABDM app',
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
