import React from 'react'
import AlertBox from './AlertBox'
import Badge from './Badge'

/**
 * SafetyResult — renders the output from POST /api/check-drug
 *
 * Backend response shape (via useSafetyCheck):
 * result = {
 *   drug:      { brand, salt, cat, score }
 *   severity:  'critical' | 'moderate' | 'safe'
 *   message:   string  (the alert message from backend)
 *   riskProbability: float 0.0-1.0
 *   mlDetails: [{ item, probability }]
 *   substitute: { name, brands, reason } | null
 *   raw:       original backend JSON
 * }
 */
export default function SafetyResult({ result }) {
  if (!result) return null

  // Unresolved brand error
  if (result.error) {
    return (
      <AlertBox variant="warn" title="Brand not resolved">
        Could not match <strong className="text-[#e2e8f0]">"{result.error}"</strong> to a known
        medicine in the database. Try one of the demo links above.
      </AlertBox>
    )
  }

  const { drug, severity, message, substitute, riskProbability = 0, mlDetails = [] } = result

  const sevBadge = severity === 'critical' ? 'danger' : severity === 'moderate' ? 'warn' : 'safe'
  const sevLabel = severity === 'critical' ? 'Critical Risk' : severity === 'moderate' ? 'Moderate Risk' : 'Safe to Dispense'

  // Map severity to alert variant
  const alertVariant = severity === 'critical' ? 'critical' : severity === 'moderate' ? 'warn' : 'safe'
  const alertTitle   = severity === 'critical' ? 'Critical alert' : severity === 'moderate' ? 'Moderate alert' : 'No conflicts found'

  // Risk probability display
  const riskPercent = Math.round(riskProbability * 100 * 10) / 10
  const riskColor = riskPercent >= 75 ? 'text-red-400' : riskPercent >= 40 ? 'text-amber-400' : 'text-emerald-400'
  const riskBg = riskPercent >= 75 ? 'bg-red-500' : riskPercent >= 40 ? 'bg-amber-500' : 'bg-emerald-500'

  return (
    <div className="card">
      {/* Card header */}
      <div className="card-head">
        <div>
          <div className="text-[15px] font-bold text-[#e2e8f0]">{drug.brand}</div>
          <div className="flex flex-wrap gap-1 mt-1.5">
            {drug.salt && drug.salt !== 'Unknown' ? (
              drug.salt.split(', ').map((s, idx) => (
                <span key={idx} className="px-2 py-0.5 bg-[#21262d] text-[#e2e8f0] text-[11px] rounded uppercase font-medium tracking-wide">
                  {s}
                </span>
              ))
            ) : (
              <span className="text-[#8b949e] text-[12px]">Unknown Salt</span>
            )}
          </div>
        </div>
        <Badge variant={sevBadge}>{sevLabel}</Badge>
      </div>

      {/* Card body */}
      <div className="card-body">
        {/* Risk Probability Bar */}
        <div className="bg-[#0d1117] border border-[#21262d] rounded-xl p-4 mb-3">
          <div className="flex items-center justify-between mb-2">
            <div className="text-[11px] font-bold text-[#484f58] uppercase tracking-widest">
              Evidence Severity Score
            </div>
            <span className={`text-[18px] font-bold ${riskColor}`}>
              {riskPercent}%
            </span>
          </div>
          <div className="w-full h-2.5 bg-[#21262d] rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-700 ease-out ${riskBg}`}
              style={{ width: `${Math.min(riskPercent, 100)}%` }}
            />
          </div>
          <div className="text-[10px] text-[#484f58] mt-1.5">
            Based on active medications, conditions, allergies, and genomic markers
          </div>
        </div>

        {/* Main alert from backend message */}
        <AlertBox variant={alertVariant} title={alertTitle}>
          <ul className="list-disc list-outside ml-4 space-y-1">
            {message ? message.split('|').map(m => m.trim()).filter(Boolean).map((alertItem, idx) => (
              <li key={idx} className="leading-relaxed">{alertItem}</li>
            )) : <li>No details provided.</li>}
          </ul>
        </AlertBox>

        {/* Safer alternative if backend returned one */}
        {substitute && severity === 'critical' && (
          <div className="mt-3 bg-emerald-950/30 border border-emerald-800/25 rounded-xl p-4">
            <div className="text-[11px] font-bold text-emerald-500 uppercase tracking-widest mb-1.5">
              Safer alternative suggested
            </div>
            <div className="text-[14px] font-bold text-[#e2e8f0]">
              {substitute.name}
            </div>
            <div className="text-[12px] text-emerald-400 mt-1 leading-relaxed">
              This alternative is from a safer therapeutic class for this patient's condition profile.
            </div>
          </div>
        )}



        {/* Raw backend response for transparency */}
        <details className="mt-3">
          <summary className="text-[11px] text-[#484f58] cursor-pointer hover:text-[#8b949e] transition-colors">
            View raw backend response
          </summary>
          <pre className="mt-2 bg-[#0d1117] border border-[#21262d] rounded-lg p-3
                          text-[11px] text-[#7ee787] font-mono overflow-auto max-h-40">
            {JSON.stringify(result.raw, null, 2)}
          </pre>
        </details>
      </div>
    </div>
  )
}
