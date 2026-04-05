import React from 'react'

/**
 * Badge — inline status pill
 * variant: 'safe' | 'warn' | 'danger' | 'info' | 'neutral'
 */
export default function Badge({ variant = 'neutral', children }) {
  const variants = {
    safe:    'bg-emerald-900/30 text-emerald-400 border border-emerald-700/30',
    warn:    'bg-amber-900/30 text-amber-400 border border-amber-700/30',
    danger:  'bg-red-900/30 text-red-400 border border-red-700/30',
    info:    'bg-blue-900/30 text-blue-400 border border-blue-700/30',
    neutral: 'bg-[#21262d] text-[#8b949e] border border-[#30363d]',
    green:   'bg-emerald-950/40 text-emerald-400 border border-emerald-800/30',
    red:     'bg-red-950/40 text-red-400 border border-red-800/30',
  }

  return (
    <span className={`inline-block px-2.5 py-0.5 rounded-full text-[11px] font-semibold tracking-wide ${variants[variant]}`}>
      {children}
    </span>
  )
}
