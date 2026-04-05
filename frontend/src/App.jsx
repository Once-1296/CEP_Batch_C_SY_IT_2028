import React, { useState, useEffect } from 'react'
import LoginPage from './components/LoginPage'
import Header from './components/Header'
import Tabs from './components/Tabs'
import DashboardPanel from './components/DashboardPanel'
import PatientPanel from './components/PatientPanel'
import SchemaPanel from './components/SchemaPanel'
import SubstitutionPanel from './components/SubstitutionPanel'

export default function App() {
  const [user, setUser]               = useState(null)
  const [activeTab, setActiveTab]     = useState('dashboard')
  const [activePatient, setActivePatient] = useState('ABHA-1234-5678')

  // Persist login across refresh
  useEffect(() => {
    const savedUser = localStorage.getItem('ag_user')
    if (savedUser) setUser(savedUser)
  }, [])

  const handleLogin = (username) => setUser(username)

  const handleLogout = () => {
    localStorage.removeItem('ag_token')
    localStorage.removeItem('ag_user')
    setUser(null)
  }

  const handleViewPatient = () => setActiveTab('patient')
  const handlePatientChange = (id) => setActivePatient(id)

  if (!user) return <LoginPage onLogin={handleLogin} />

  return (
    <div className="min-h-screen bg-[#0d1117] p-5">
      <div className="max-w-[960px] mx-auto">
        <Header user={user} onLogout={handleLogout} />
        <Tabs active={activeTab} onChange={setActiveTab} />

        {activeTab === 'dashboard' && (
          <DashboardPanel
            onViewPatient={handleViewPatient}
            onPatientChange={handlePatientChange}
          />
        )}
        {activeTab === 'patient'      && <PatientPanel activePatientId={activePatient} />}
        {activeTab === 'schema'       && <SchemaPanel />}
        {activeTab === 'substitution' && <SubstitutionPanel />}
      </div>
    </div>
  )
}
