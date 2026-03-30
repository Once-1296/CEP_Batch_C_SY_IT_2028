import { useState, useCallback } from 'react'
import { DRUGS, PATIENT, DDI, CONTRAINDICATIONS, SUBSTITUTES, PIPELINE_STEPS } from '../data/mockData'

const delay = (ms) => new Promise((r) => setTimeout(r, ms))

/**
 * useSafetyCheck
 * Simulates the FastAPI backend pipeline:
 *   1. NLP normalization  →  2. Brand-to-salt mapping  →
 *   3. ABDM FHIR fetch   →  4. DDI check  →
 *   5. Contraindication check  →  6. Risk stratification
 */
export function useSafetyCheck() {
  const [loading, setLoading]       = useState(false)
  const [loadingMsg, setLoadingMsg] = useState('')
  const [steps, setSteps]           = useState([]) // 'wait' | 'active' | 'done'
  const [result, setResult]         = useState(null)
  const [showSteps, setShowSteps]   = useState(false)

  const runCheck = useCallback(async (rawInput) => {
    if (!rawInput.trim()) return

    // reset
    setResult(null)
    setShowSteps(true)
    setSteps(PIPELINE_STEPS.map(() => 'wait'))
    setLoading(true)

    const updateStep = (i, state) =>
      setSteps((prev) => prev.map((s, idx) => (idx === i ? state : s)))

    // Simulate each pipeline stage
    for (let i = 0; i < PIPELINE_STEPS.length; i++) {
      setLoadingMsg(PIPELINE_STEPS[i] + '…')
      updateStep(i, 'active')
      await delay(480)
      updateStep(i, 'done')
    }

    setLoading(false)

    // ── Core logic (mirrors FastAPI backend) ──────────────────────────────────
    const normalized = rawInput.trim().toLowerCase()
    const matchedKey = Object.keys(DRUGS).find((k) => normalized.includes(k))
    const drug = matchedKey ? DRUGS[matchedKey] : null

    if (!drug) {
      setResult({ error: rawInput.trim() })
      return
    }

    const ddis = DDI.filter((d) => d.a === drug.salt || d.b === drug.salt)
    const conflicts = (CONTRAINDICATIONS[drug.salt] || []).filter((c) =>
      PATIENT.conditions.includes(c)
    )
    const isDuplicate = PATIENT.meds.includes(drug.salt)
    const substitute  = SUBSTITUTES[drug.salt] || null

    // Risk stratification
    let severity = 'safe'
    if (conflicts.length > 0 || ddis.some((d) => d.severity === 'Critical')) {
      severity = 'critical'
    } else if (isDuplicate || ddis.some((d) => d.severity === 'Moderate')) {
      severity = 'moderate'
    }

    setResult({ drug, ddis, conflicts, isDuplicate, substitute, severity })
  }, [])

  const clear = useCallback(() => {
    setResult(null)
    setShowSteps(false)
    setSteps([])
    setLoading(false)
  }, [])

  return { loading, loadingMsg, steps, showSteps, result, runCheck, clear }
}
