import { useState, useCallback } from 'react'
import { PIPELINE_STEPS } from '../data/mockData'

// ── FastAPI backend URL ───────────────────────────────────────────────────────
const API_BASE = 'http://localhost:8000'

const delay = (ms) => new Promise((r) => setTimeout(r, ms))

/**
 * useSafetyCheck
 * Calls the real FastAPI backend:
 *   POST /api/check-drug  →  { pharmacist_query, patient_id }
 *
 * Backend response shape:
 *   { severity_tier, message, resolved_data, suggested_alternative }
 *
 * severity_tier values from backend: "Green" | "Yellow" | "Red"
 */
export function useSafetyCheck() {
  const [loading, setLoading]       = useState(false)
  const [loadingMsg, setLoadingMsg] = useState('')
  const [steps, setSteps]           = useState([])
  const [result, setResult]         = useState(null)
  const [showSteps, setShowSteps]   = useState(false)
  const [apiError, setApiError]     = useState(null)

  const runCheck = useCallback(async (rawInput, patientId) => {
    if (!rawInput.trim()) return
    // console.log(rawInput.trim())
    // Reset state
    setResult(null)
    setApiError(null)
    setShowSteps(true)
    setSteps(PIPELINE_STEPS.map(() => 'wait'))
    setLoading(true)

    const updateStep = (i, state) =>
      setSteps((prev) => prev.map((s, idx) => (idx === i ? state : s)))

    // Animate first 5 steps while API call is in flight
    const stepMsgs = [
      'Normalizing input with SciSpacy NLP…',
      'Mapping brand to generic salt via FuzzyWuzzy…',
      'Fetching ABDM FHIR records via HIU API…',
      'Running DDI cross-reference query…',
      'Checking drug-condition contraindications…',
    ]

    // Animate steps 0-4 with delays
    for (let i = 0; i < 5; i++) {
      setLoadingMsg(stepMsgs[i])
      updateStep(i, 'active')
      await delay(400)
      updateStep(i, 'done')
    }

    // Step 5 — actual API call happens here
    setLoadingMsg('Stratifying risk & preparing output…')
    updateStep(5, 'active')

    try {
      const response = await fetch(`${API_BASE}/api/check-drug`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pharmacist_query: rawInput.trim(),
          patient_id: patientId,
        }),
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || 'Backend error')
      }

      const data = await response.json()
      updateStep(5, 'done')
      setLoading(false)

      // Map backend severity_tier → frontend severity
      // Backend uses: "Green" | "Yellow" | "Red"
      const severityMap = {
        Red:    'critical',
        Yellow: 'moderate',
        Green:  'safe',
      }

      setResult({
        // resolved drug info from backend
        drug: {
          brand:  data.resolved_data?.brand_matched  || rawInput,
          salt:   data.resolved_data?.generic_salt   || 'Unknown',
          cat:    data.resolved_data?.therapeutic_class || 'Unknown',
          score:  data.resolved_data?.match_score    || 0,
        },
        severity:    severityMap[data.severity_tier] || 'safe',
        message:     data.message,
        substitute:  data.suggested_alternative
          ? { name: data.suggested_alternative, brands: data.suggested_alternative, reason: data.message }
          : null,
        // raw backend response for debugging
        raw: data,
      })

    } catch (err) {
      updateStep(5, 'done')
      setLoading(false)

      // Check if it's a network error (backend not running)
      if (err.message === 'Failed to fetch') {
        setApiError('Cannot connect to backend. Make sure FastAPI is running on port 8000 (uvicorn main:app --reload)')
      } else {
        setApiError(err.message)
      }
    }
  }, [])

  const clear = useCallback(() => {
    setResult(null)
    setApiError(null)
    setShowSteps(false)
    setSteps([])
    setLoading(false)
  }, [])

  return { loading, loadingMsg, steps, showSteps, result, apiError, runCheck, clear }
}
