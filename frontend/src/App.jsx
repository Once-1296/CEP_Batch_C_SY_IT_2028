import React, { useState, useEffect } from 'react'
import LoginPage from './components/LoginPage'
import Header from './components/Header'
import Tabs from './components/Tabs'
import DashboardPanel from './components/DashboardPanel'
import PatientPanel from './components/PatientPanel'
import SubstitutionPanel from './components/SubstitutionPanel'
// CHANGED: Import new AdminPanel for admin role
import AdminPanel from './components/AdminPanel'

export default function App() {
  // CHANGED: user state is now an object { role, name, username } instead of a plain string
  const [user, setUser]               = useState(null)
  const [activeTab, setActiveTab]     = useState('dashboard')
  const [activePatient, setActivePatient] = useState(null)  // CHANGED: default null, set after fetch

  // CHANGED: Persist login across refresh — parse JSON object from localStorage
  useEffect(() => {
    const savedUser = localStorage.getItem('ag_user')
    if (savedUser) {
      try {
        const parsed = JSON.parse(savedUser)
        setUser(parsed)
        // CHANGED: Route admin to admin panel on restore
        if (parsed.role === 'admin') setActiveTab('admin')
      } catch {
        // If parse fails (old format), clear it
        localStorage.removeItem('ag_user')
      }
    }
  }, [])

  // CHANGED: handleLogin receives full user object from LoginPage
  const handleLogin = (userData) => {
    setUser(userData)
    // CHANGED: Route based on role after login
    if (userData.role === 'admin') {
      setActiveTab('admin')
    } else {
      setActiveTab('dashboard')
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('ag_user')
    setUser(null)
    setActiveTab('dashboard')  // Reset tab
  }

  const handleViewPatient = () => setActiveTab('patient')
  const handlePatientChange = (id) => setActivePatient(id)

  // Show login page if not authenticated
  if (!user) return <LoginPage onLogin={handleLogin} />

  return (
    <div className="min-h-screen bg-[#0d1117] p-5">
      <div className="max-w-[960px] mx-auto">
        {/* CHANGED: Pass user.name and user.role to Header for display */}
        <Header user={user.name || user.username} onLogout={handleLogout} />

        {/* CHANGED: Role-based routing */}
        {user.role === 'admin' ? (
          // CHANGED: Admin sees only AdminPanel — no Tabs component
          <AdminPanel />
        ) : (
          // CHANGED: Pharmacist sees existing tabbed layout (Dashboard, Patient, Schema, Substitution)
          <>
            <Tabs active={activeTab} onChange={setActiveTab} />

            {activeTab === 'dashboard' && (
              <DashboardPanel
                onViewPatient={handleViewPatient}
                onPatientChange={handlePatientChange}
              />
            )}
            {activeTab === 'patient'      && <PatientPanel activePatientId={activePatient} loggedInUser={user} />}
            {activeTab === 'substitution' && <SubstitutionPanel />}
          </>
        )}
      </div>
    </div>
  )
}
