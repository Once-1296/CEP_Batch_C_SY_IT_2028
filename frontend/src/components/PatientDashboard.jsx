import React, { useState, useEffect } from 'react'
import Badge from './Badge'
import AlertBox from './AlertBox'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export default function PatientDashboard({ user }) {
  const [requests, setRequests] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [actionLoading, setActionLoading] = useState(null) // ID of request being processed

  const fetchRequests = async () => {
    try {
      const savedUser = localStorage.getItem('ag_user')
      const token = savedUser ? JSON.parse(savedUser).token : ''

      const res = await fetch(`${API_BASE}/api/patients/access-requests`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      // Treat 204/404 as "no requests" rather than an error
      if (!res.ok) {
        if (res.status === 204 || res.status === 404) {
          setRequests([])
          return
        }
        throw new Error('Failed to fetch requests')
      }
      const data = await res.json()
      const allRequests = data.requests || []
      const pendingOnly = allRequests.filter(r => r.status === 'PENDING')
      setRequests(pendingOnly)
    } catch (err) {
      // If backend unreachable or other error, show friendly message but fall back to no requests
      console.error('fetchRequests error:', err)
      setError(err.message || 'Failed to fetch access requests')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchRequests()
  }, [])

  const handleResponse = async (requestId, status) => {
    if (status === 'ACCEPTED') {
      const confirmed = window.confirm(
        "By accepting this request, you are granting access to your sensitive medical records and your family's medical history. Only proceed if you trust this pharmacist. Continue?"
      )
      if (!confirmed) return
    }

    setActionLoading(requestId)
    try {
      const savedUser = localStorage.getItem('ag_user')
      const token = savedUser ? JSON.parse(savedUser).token : ''

      const res = await fetch(`${API_BASE}/api/patients/respond-access`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ request_id: requestId, status }),
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Action failed')
      }
      // Refresh list
      await fetchRequests()
    } catch (err) {
      alert(err.message)
    } finally {
      setActionLoading(null)
    }
  }

  return (
    <div className="space-y-6">
      <div className="card">
        <div className="card-body">
          <div className="section-label">Your Dashboard</div>
          <h2 className="text-[20px] font-bold text-[#e2e8f0]">Welcome, {user.name || user.username}</h2>
          <p className="text-[13px] text-[#8b949e] mt-1">Manage who can access your medical records below.</p>
        </div>
      </div>

      <div className="card">
        <div className="card-head">
          <div className="text-[14px] font-bold text-[#e2e8f0]">Pending Access Requests</div>
          <Badge variant="blue">{requests.length} Pending</Badge>
        </div>
        <div className="card-body">
          {loading ? (
            <div className="text-center py-8 text-[#484f58] text-[14px]">Loading requests...</div>
          ) : error ? (
            <AlertBox variant="critical" title="Error">{error}</AlertBox>
          ) : requests.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-[#484f58] text-[14px]">No pending requests.</div>
              <p className="text-[12px] text-[#484f58] mt-1">Pharmacists will appear here when they request access.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {requests.map((req) => (
                <div key={req.id} className="bg-[#0d1117] border border-[#21262d] rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="flex items-center gap-3.5">
                    <div className="w-10 h-10 rounded-full bg-blue-950/40 border border-blue-800/30
                                    flex items-center justify-center text-[14px] font-bold text-blue-400">
                      PH
                    </div>
                    <div>
                      <div className="text-[14px] font-bold text-[#e2e8f0]">Pharmacist: {req.pharmacist_username}</div>
                      <div className="text-[12px] text-[#8b949e] mt-0.5">
                        Requested on: {new Date(req.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={() => handleResponse(req.id, 'ACCEPTED')}
                      disabled={actionLoading === req.id}
                      className="btn btn-primary text-[12px] py-1.5 px-4 disabled:opacity-50"
                    >
                      {actionLoading === req.id ? 'Processing...' : 'Accept'}
                    </button>
                    <button
                      onClick={() => handleResponse(req.id, 'REJECTED')}
                      disabled={actionLoading === req.id}
                      className="btn btn-outline text-[12px] py-1.5 px-4 disabled:opacity-50"
                    >
                      Reject
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <AlertBox variant="warn" title="Data Privacy Notice">
        Accepting a request allows the pharmacist to see your full medical history, active medications, and family relationships to ensure safe dispensing. Always verify the identity of the pharmacist before granting access.
      </AlertBox>
    </div>
  )
}
