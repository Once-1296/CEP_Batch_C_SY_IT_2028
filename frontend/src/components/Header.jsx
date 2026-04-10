import React from 'react'

export default function Header({ user, onLogout }) {
  return (
    <header className="bg-[#161b22] border border-[#21262d] rounded-xl px-5 py-4 flex items-center justify-between mb-4">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 bg-[#1D9E75] rounded-[10px] flex items-center justify-center flex-shrink-0">
          <svg viewBox="0 0 24 24" className="w-5 h-5 fill-white">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 15v-4H7l5-8v4h4l-5 8z" />
          </svg>
        </div>
        <div>
          <div className="text-[17px] font-semibold text-[#e2e8f0] tracking-tight">Ayush-Guard</div>
          <div className="text-[11px] text-[#484f58]">Point-of-Sale Clinical Decision Support System</div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* ABDM status (Hidden as per user request since not currently connected) */}
        {/*
        <div className="flex items-center gap-1.5 text-[12px] font-medium text-emerald-400
                        bg-emerald-950/40 border border-emerald-800/30 px-3 py-1.5 rounded-full">
          <span className="w-1.5 h-1.5 rounded-full bg-[#1D9E75]"
            style={{ animation: 'pulse-dot 2s infinite' }} />
          ABDM Sandbox Connected
        </div>
        */}

        {/* Logged in user */}
        {user && (
          <div className="flex items-center gap-2">
            <span className="text-[12px] text-[#8b949e]">
              Pharmacist: <span className="text-[#e2e8f0] font-medium">{user}</span>
            </span>
            <button onClick={onLogout}
              className="text-[12px] text-red-400 hover:text-red-300 border border-red-900/40
                         hover:border-red-700/40 px-2.5 py-1 rounded-lg transition-all">
              Logout
            </button>
          </div>
        )}
      </div>
    </header>
  )
}
