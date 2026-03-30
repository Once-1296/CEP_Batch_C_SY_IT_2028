import React from 'react'
import AlertBox from './AlertBox'
import Badge from './Badge'

export default function SafetyResult({ result }) {
  if (!result) return null

  // Unresolved brand
  if (result.error) {
    return (
      <AlertBox variant="warn" title="Brand not resolved">
        Could not match <strong className="text-[#e2e8f0]">"{result.error}"</strong> to
        a known salt in the medicines master table. Try one of the demo links above.
      </AlertBox>
    )
  }

  const { drug, ddis, conflicts, isDuplicate, substitute, severity } = result

  const sevBadge  = severity === 'critical' ? 'danger' : severity === 'moderate' ? 'warn' : 'safe'
  const sevLabel  = severity === 'critical' ? 'Critical Risk' : severity === 'moderate' ? 'Moderate Risk' : 'Safe to Dispense'

  return (
    <div className="card">
      {/* Card header */}
      <div className="card-head">
        <div>
          <div className="text-[15px] font-bold text-[#e2e8f0]">{drug.brand}</div>
          <div className="text-[12px] text-[#8b949e] mt-0.5">
            Generic salt: <span className="text-[#e2e8f0] font-medium">{drug.salt}</span>
            &nbsp;|&nbsp;{drug.cat}
          </div>
        </div>
        <Badge variant={sevBadge}>{sevLabel}</Badge>
      </div>

      {/* Card body */}
      <div className="card-body space-y-0">
        {/* Duplicate therapy */}
        {isDuplicate && (
          <AlertBox variant="critical" title="Duplicate therapy detected">
            Patient is already prescribed <strong className="text-[#e2e8f0]">{drug.salt}</strong>.
            Dispensing under a different brand risks overdose. Transaction blocked.
          </AlertBox>
        )}

        {/* Drug-condition contraindication */}
        {conflicts.length > 0 && (
          <AlertBox variant="critical" title="Drug-condition contraindication">
            <strong className="text-[#e2e8f0]">{drug.salt}</strong> is contraindicated in:{' '}
            <strong className="text-[#e2e8f0]">{conflicts.join(', ')}</strong>. Risk of serious
            adverse event. Do not dispense.
          </AlertBox>
        )}

        {/* DDI alerts */}
        {ddis.map((d, i) => {
          const other   = d.a === drug.salt ? d.b : d.a
          const variant = d.severity === 'Critical' ? 'critical' : d.severity === 'Moderate' ? 'warn' : 'info'
          return (
            <AlertBox key={i} variant={variant} title={`${d.severity} DDI — ${drug.salt} + ${other}`}>
              {d.effect}
            </AlertBox>
          )
        })}

        {/* All clear */}
        {!isDuplicate && conflicts.length === 0 && ddis.length === 0 && (
          <AlertBox variant="safe" title="No conflicts found">
            {drug.salt} is safe to dispense for this patient. No DDIs or contraindications
            detected against current medications or conditions.
          </AlertBox>
        )}

        {/* Safer alternative */}
        {substitute && severity === 'critical' && (
          <div className="mt-3 bg-emerald-950/30 border border-emerald-800/25 rounded-xl p-4">
            <div className="text-[11px] font-bold text-emerald-500 uppercase tracking-widest mb-1.5">
              Safer alternative computed
            </div>
            <div className="text-[14px] font-bold text-[#e2e8f0]">
              {substitute.name}{' '}
              <span className="text-[12px] text-[#8b949e] font-normal">({substitute.brands})</span>
            </div>
            <div className="text-[12px] text-emerald-400 mt-1 leading-relaxed">
              {substitute.reason}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
