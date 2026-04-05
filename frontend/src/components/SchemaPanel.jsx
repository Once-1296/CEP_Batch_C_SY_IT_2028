import React from 'react'
import { DB_SCHEMA } from '../data/mockData'

const RLS_TAGS = [
  'RLS enabled on all 3 core tables',
  'Public role: SELECT only',
  'No INSERT / UPDATE / DELETE',
  'Deny-by-default on init',
  'PgBouncer connection pooling',
  'PostgREST API layer',
]

function ColKey({ keyType }) {
  if (!keyType) return null
  const styles = keyType === 'PK'
    ? 'bg-amber-950/40 text-amber-400 border border-amber-800/30'
    : 'bg-purple-950/40 text-purple-400 border border-purple-800/30'
  return (
    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${styles}`}>
      {keyType}
    </span>
  )
}

function SchemaTable({ table, source, columns }) {
  return (
    <div className="bg-[#161b22] border border-[#21262d] rounded-xl overflow-hidden">
      {/* Table header */}
      <div className="bg-[#0d1117] px-3.5 py-2.5 border-b border-[#21262d]">
        <div className="text-[13px] font-bold text-[#e2e8f0] font-mono">{table}</div>
        <div className="text-[10px] text-[#484f58] mt-0.5">{source}</div>
      </div>
      {/* Columns */}
      {columns.map((col) => (
        <div
          key={col.name}
          className="flex items-center gap-2 px-3.5 py-[7px] border-b border-[#21262d] last:border-b-0 text-[12px]"
        >
          <span className="flex-1 font-mono text-[#e2e8f0]">{col.name}</span>
          <span className="text-[11px] text-blue-400 bg-blue-950/30 border border-blue-800/25 px-1.5 py-px rounded">
            {col.type}
          </span>
          {col.key && <ColKey keyType={col.key} />}
          {col.note && (
            <span className="text-[10px] text-[#484f58]">{col.note}</span>
          )}
        </div>
      ))}
    </div>
  )
}

export default function SchemaPanel() {
  return (
    <div>
      {/* Schema grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3.5">
        {DB_SCHEMA.map((s) => (
          <SchemaTable key={s.table} {...s} />
        ))}
      </div>

      {/* RLS posture card */}
      <div className="card">
        <div className="card-body">
          <div className="section-label">PostgreSQL row-level security (RLS) posture</div>
          <div className="flex flex-wrap gap-2 mt-2">
            {RLS_TAGS.map((tag) => (
              <span
                key={tag}
                className="bg-[#21262d] px-3 py-1 rounded-full text-[12px] text-[#8b949e] border border-[#30363d]"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
