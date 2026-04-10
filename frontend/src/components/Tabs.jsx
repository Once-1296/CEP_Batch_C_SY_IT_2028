import React from 'react'

const TABS = [
  { id: 'dashboard',    label: 'Pharmacist Dashboard' },
  { id: 'patient',      label: 'Patient Profile' },
  { id: 'substitution', label: 'Safety Swap' },
]

export default function Tabs({ active, onChange }) {
  return (
    <nav className="flex bg-[#161b22] border border-[#21262d] rounded-xl p-1 mb-4 gap-1">
      {TABS.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={`
            flex-1 py-2 px-2 rounded-lg text-[13px] font-medium transition-all duration-150
            ${active === tab.id
              ? 'bg-[#1D9E75] text-white'
              : 'text-[#8b949e] hover:bg-[#21262d] hover:text-[#e2e8f0]'
            }
          `}
        >
          {tab.label}
        </button>
      ))}
    </nav>
  )
}
