import React from 'react'

/**
 * AlertBox — reusable alert/notification component
 * variant: 'critical' | 'warn' | 'safe' | 'info'
 */
export default function AlertBox({ variant = 'info', title, children }) {
  const styles = {
    critical: {
      wrap:  'bg-red-950/40 border-red-800/40',
      icon:  'bg-red-500 text-white',
      title: 'text-red-400',
      sym:   '!',
    },
    warn: {
      wrap:  'bg-amber-950/40 border-amber-800/40',
      icon:  'bg-amber-500 text-white',
      title: 'text-amber-400',
      sym:   '!',
    },
    safe: {
      wrap:  'bg-emerald-950/40 border-emerald-800/40',
      icon:  'bg-[#1D9E75] text-white',
      title: 'text-emerald-400',
      sym:   '✓',
    },
    info: {
      wrap:  'bg-blue-950/40 border-blue-800/40',
      icon:  'bg-blue-500 text-white',
      title: 'text-blue-400',
      sym:   'i',
    },
  }

  const s = styles[variant]

  return (
    <div className={`rounded-xl p-3 mb-2.5 flex gap-2.5 items-start border ${s.wrap}`}>
      <div className={`w-5 h-5 rounded-full flex-shrink-0 flex items-center justify-center text-[11px] font-bold mt-px ${s.icon}`}>
        {s.sym}
      </div>
      <div className="flex-1 min-w-0">
        {title && (
          <div className={`font-semibold text-[13px] mb-0.5 ${s.title}`}>{title}</div>
        )}
        <div className="text-[12px] text-[#8b949e] leading-relaxed">{children}</div>
      </div>
    </div>
  )
}
