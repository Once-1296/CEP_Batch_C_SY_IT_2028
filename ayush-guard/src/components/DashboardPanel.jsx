import React, { useState } from 'react'
import PipelineSteps from './PipelineSteps'
import SafetyResult from './SafetyResult'
import { useSafetyCheck } from '../hooks/useSafetyCheck'

const DEMO_DRUGS = ['Dolo 650', 'Brufen', 'Combiflam', 'Metformin', 'Ecosprin']

export default function DashboardPanel({ onViewPatient }) {
  const [input, setInput]   = useState('')
  const [abhaId, setAbhaId] = useState('27-3456-7890-1234')
  const { loading, loadingMsg, steps, showSteps, result, runCheck, clear } = useSafetyCheck()

  const handleCheck = () => runCheck(input)
  const handleClear = () => { setInput(''); clear() }
  const handleDemo  = (name) => setInput(name)

  return (
    <div>
      <div className="card">
        <div className="card-body">
          {/* Medicine search */}
          <div className="section-label">Medicine lookup</div>
          <div className="flex gap-2 mb-3.5">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleCheck()}
              placeholder="Type brand name e.g. Dolo 650, Crocin, Brufen, Combiflam, Ecosprin…"
              className="flex-1 px-3.5 py-2.5 border border-[#21262d] rounded-lg text-[14px] outline-none
                         bg-[#0d1117] text-[#e2e8f0] placeholder-[#484f58]
                         focus:border-[#1D9E75] focus:ring-2 focus:ring-[#1D9E75]/20 transition-all"
            />
            <button onClick={handleCheck} className="btn btn-primary whitespace-nowrap">
              Run safety check
            </button>
            <button onClick={handleClear} className="btn btn-outline">
              Clear
            </button>
          </div>

          {/* ABHA ID row */}
          <div className="section-label">Patient ABHA ID</div>
          <div className="flex gap-2 mb-4 items-center">
            <input
              type="text"
              value={abhaId}
              onChange={(e) => setAbhaId(e.target.value)}
              className="w-52 px-3.5 py-2.5 border border-[#21262d] rounded-lg text-[14px] outline-none
                         bg-[#0d1117] text-[#e2e8f0]
                         focus:border-[#378ADD] focus:ring-2 focus:ring-[#378ADD]/20 transition-all"
            />
            <button onClick={onViewPatient} className="btn btn-blue whitespace-nowrap">
              View patient records
            </button>
          </div>

          {/* Demo quick links */}
          <p className="text-[12px] text-[#484f58]">
            Try:{' '}
            {DEMO_DRUGS.map((name, i) => (
              <React.Fragment key={name}>
                <button
                  onClick={() => handleDemo(name)}
                  className="text-emerald-400 underline hover:text-emerald-300 transition-colors"
                >
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

      {/* Safety check result */}
      {!loading && result && (
        <SafetyResult result={result} />
      )}
    </div>
  )
}
