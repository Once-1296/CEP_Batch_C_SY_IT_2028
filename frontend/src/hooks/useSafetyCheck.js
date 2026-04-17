import { useState, useCallback } from 'react'

// ── FastAPI backend URL ───────────────────────────────────────────────────────
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'


/**
 * useSafetyCheck
 * Calls the real FastAPI backend:
 *   POST /api/check-drug  →  { pharmacist_query, patient_id, abha_id }
 *
 * Backend response shape:
 *   { severity_tier, message, resolved_data, suggested_alternative, risk_probability, ml_details }
 *
 * severity_tier values from backend: "Green" | "Yellow" | "Red"
 */
export function useSafetyCheck() {
  const [loading, setLoading] = useState(false)
  const [loadingMsg, setLoadingMsg] = useState('')
  const [steps, setSteps] = useState([])
  const [result, setResult] = useState(null)
  const [showSteps, setShowSteps] = useState(false)
  const [apiError, setApiError] = useState(null)

  const runCheck = useCallback(async (rawInput, patientId, abhaId) => {
    if (!rawInput.trim()) return
    // Reset state
    setResult(null)
    setApiError(null)
    setShowSteps(true)

    setSteps(['active'])
    setLoading(true)
    setLoadingMsg('Querying Evidence Database...')

    try {
      const savedUser = localStorage.getItem('ag_user')
      const token = savedUser ? JSON.parse(savedUser).token : ''

      const response = await fetch(`${API_BASE}/api/check-drug`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          pharmacist_query: rawInput.trim(),
          patient_id: patientId,
          abha_id: abhaId || '',
        }),
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || 'Backend error')
      }

      const data = await response.json()
      setSteps(['done'])
      setLoading(false)

      // Map backend severity_tier → frontend severity
      const severityMap = {
        Red: 'critical',
        Yellow: 'moderate',
        Green: 'safe',
      }

      setResult({
        drug: {
          brand: rawInput,
          salt: (data.resolved_salts && data.resolved_salts.length > 0) ? data.resolved_salts.join(', ') : 'Unknown',
        },
        severity: severityMap[data.severity_tier] || 'safe',
        message: data.message,
        riskProbability: data.risk_probability || 0,
        substitute: data.suggested_alternative
          ? { name: data.suggested_alternative, brands: data.suggested_alternative, reason: data.message }
          : null,
        raw: data,
      })

    } catch (err) {
      updateStep(4, 'done')
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
