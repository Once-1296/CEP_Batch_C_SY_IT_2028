import React from 'react'
import AlertBox from './AlertBox'
import Badge from './Badge'

const BLOCKED_DRUG = {
  name:     'Ibuprofen 400mg',
  salt:     'Ibuprofen',
  class:    'NSAID',
  severity: 'Critical',
  conflicts: 'CKD Stage 2, Hypertension',
  ddiConflict: 'Amlodipine (antihypertensive)',
  habit:    'No',
}

const RECOMMENDED_DRUG = {
  name:      'Paracetamol 500mg',
  salt:      'Paracetamol',
  class:     'Analgesic / Antipyretic',
  severity:  'Safe',
  conflicts: 'None detected',
  outcome:   'Fever / Mild pain relief',
  brands:    'Crocin, Dolo 500',
  reason:    'Safe for CKD Stage 2 and Hypertension. Achieves the same analgesic and antipyretic outcome. Max 4g/day — advise patient to take after food.',
}

function InfoRow({ label, children }) {
  return (
    <div className="flex justify-between items-center text-[13px] py-1.5 border-b border-[#21262d] last:border-b-0">
      <span className="text-[#8b949e]">{label}</span>
      <span className="text-[#e2e8f0] font-medium">{children}</span>
    </div>
  )
}

export default function SubstitutionPanel() {
  return (
    <div>
      {/* Scenario alert */}
      <AlertBox variant="critical" title="Scenario: Ibuprofen requested — patient has CKD Stage 2 + Hypertension">
        NSAIDs are contraindicated in CKD and Hypertension. Risk: acute kidney injury,
        elevated BP, fluid retention. Transaction blocked. Alternative computed below.
      </AlertBox>

      {/* Side-by-side cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 my-3.5">

        {/* Blocked drug */}
        <div className="bg-[#161b22] border border-dashed border-[#30363d] rounded-xl p-4 opacity-60">
          <span className="inline-block bg-red-950/40 text-red-400 border border-red-800/30
                           text-[11px] font-bold px-2.5 py-0.5 rounded-full mb-2.5">
            Blocked
          </span>
          <div className="text-[14px] font-bold text-[#e2e8f0] mb-1">{BLOCKED_DRUG.name}</div>
          <div className="text-[12px] text-[#8b949e] mb-3">
            Salt: {BLOCKED_DRUG.salt}&nbsp;|&nbsp;Class: {BLOCKED_DRUG.class}
          </div>
          <InfoRow label="DDI severity">
            <Badge variant="danger">Critical</Badge>
          </InfoRow>
          <InfoRow label="Conflicts with">{BLOCKED_DRUG.conflicts}</InfoRow>
          <InfoRow label="DDI conflict">{BLOCKED_DRUG.ddiConflict}</InfoRow>
          <InfoRow label="Habit forming">{BLOCKED_DRUG.habit}</InfoRow>
        </div>

        {/* Recommended drug */}
        <div className="bg-[#161b22] border-2 border-[#1D9E75] rounded-xl p-4">
          <span className="inline-block bg-emerald-950/40 text-emerald-400 border border-emerald-800/30
                           text-[11px] font-bold px-2.5 py-0.5 rounded-full mb-2.5">
            Recommended swap
          </span>
          <div className="text-[14px] font-bold text-[#e2e8f0] mb-1">{RECOMMENDED_DRUG.name}</div>
          <div className="text-[12px] text-[#8b949e] mb-3">
            Salt: {RECOMMENDED_DRUG.salt}&nbsp;|&nbsp;Class: {RECOMMENDED_DRUG.class}
          </div>
          <InfoRow label="DDI severity">
            <Badge variant="safe">Safe</Badge>
          </InfoRow>
          <InfoRow label="Conflicts with patient">{RECOMMENDED_DRUG.conflicts}</InfoRow>
          <InfoRow label="Therapeutic outcome">{RECOMMENDED_DRUG.outcome}</InfoRow>
          <InfoRow label="Available brands">{RECOMMENDED_DRUG.brands}</InfoRow>

          {/* Reason box */}
          <div className="mt-3 bg-emerald-950/30 border border-emerald-800/25 rounded-lg px-3 py-2.5
                          text-[12px] text-emerald-400 leading-relaxed">
            {RECOMMENDED_DRUG.reason}
          </div>
        </div>
      </div>

      {/* How it works */}
      <AlertBox variant="info" title="How the substitution engine works">
        System identifies the risky drug's therapeutic category → searches{' '}
        <span className="font-mono text-[#e2e8f0]">drug_interactions</span> for a proven{' '}
        <span className="font-mono text-[#e2e8f0]">safe_substitute</span> in the same category →
        filters against the patient's condition profile → returns a safe brand the chemist
        can recommend immediately.
      </AlertBox>
    </div>
  )
}
