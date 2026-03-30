import React from 'react'
import { PIPELINE_STEPS } from '../data/mockData'

export default function PipelineSteps({ steps, loading, loadingMsg }) {
  const dotClass = (state) => {
    if (state === 'done')   return 'w-2 h-2 rounded-full bg-[#1D9E75] flex-shrink-0'
    if (state === 'active') return 'w-2 h-2 rounded-full flex-shrink-0 dot-active'
    return 'w-2 h-2 rounded-full bg-[#21262d] flex-shrink-0'
  }

  return (
    <div className="bg-[#161b22] border border-[#21262d] rounded-xl p-4 mb-3.5">
      {/* Spinner row */}
      {loading && (
        <div className="flex items-center gap-2.5 mb-3 text-[13px] text-[#8b949e]">
          <div
            className="w-4 h-4 rounded-full border-2 border-[#21262d] border-t-[#1D9E75] flex-shrink-0"
            style={{ animation: 'spin 0.8s linear infinite' }}
          />
          <span>{loadingMsg}</span>
        </div>
      )}

      <div className="text-[11px] font-bold text-[#484f58] uppercase tracking-widest mb-2">
        Processing pipeline
      </div>

      <div className="flex flex-col gap-1">
        {PIPELINE_STEPS.map((label, i) => (
          <div key={i} className="flex items-center gap-2 text-[12px] text-[#8b949e] py-1">
            <div className={dotClass(steps[i] || 'wait')} />
            <span>{label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
