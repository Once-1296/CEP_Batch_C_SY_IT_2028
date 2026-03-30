import React, { useState } from 'react'
import Header from './components/Header'
import Tabs from './components/Tabs'
import DashboardPanel from './components/DashboardPanel'
import PatientPanel from './components/PatientPanel'
import SchemaPanel from './components/SchemaPanel'
import SubstitutionPanel from './components/SubstitutionPanel'

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard')

  const handleViewPatient = () => setActiveTab('patient')

  return (
    <div className="min-h-screen bg-[#0d1117] p-5">
      <div className="max-w-[960px] mx-auto">
        <Header />
        <Tabs active={activeTab} onChange={setActiveTab} />

        {activeTab === 'dashboard'    && <DashboardPanel onViewPatient={handleViewPatient} />}
        {activeTab === 'patient'      && <PatientPanel />}
        {activeTab === 'schema'       && <SchemaPanel />}
        {activeTab === 'substitution' && <SubstitutionPanel />}
      </div>
    </div>
  )
}
