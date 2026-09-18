import { useEffect, useState } from 'react'
import './App.css'
import { api } from './api'
import Sidebar from './components/Sidebar'
import Overview from './components/Overview'
import EventsView from './components/EventsView'
import AnomaliesView from './components/AnomaliesView'
import EvaluationView from './components/EvaluationView'
import AssistantView from './components/AssistantView'
import AdvisoryView from './components/AdvisoryView'
import EventDrawer from './components/EventDrawer'
import DistrictGraphView from './components/DistrictGraphView'
import ShapView from './components/ShapView'
import WhatIfView from './components/WhatIfView'
import ResourcePlanningView from './components/ResourcePlanningView'
import LiveMonitorView from './components/LiveMonitorView'

function App() {
  const [activeTab, setActiveTab] = useState('overview')
  const [selectedEvent, setSelectedEvent] = useState(null)
  const [phasesDone, setPhasesDone] = useState(0)
  const [phasesTotal, setPhasesTotal] = useState(0)

  useEffect(() => {
    api.status().then((status) => {
      const entries = Object.values(status)
      setPhasesDone(entries.filter((s) => s.status === 'done').length)
      setPhasesTotal(entries.length)
    }).catch(() => {})
  }, [])

  return (
    <div id="app-shell">
      <Sidebar
        activeTab={activeTab}
        onNavigateTab={setActiveTab}
        phasesDone={phasesDone}
        phasesTotal={phasesTotal}
      />
      <main className="main-content">
        {activeTab === 'overview' && <Overview onSelectEvent={setSelectedEvent} onNavigateTab={setActiveTab} />}
        {activeTab === 'liveMonitor' && <LiveMonitorView />}
        {activeTab === 'advisory' && <AdvisoryView />}
        {activeTab === 'events' && <EventsView onSelectEvent={setSelectedEvent} />}
        {activeTab === 'anomalies' && <AnomaliesView onSelectEvent={setSelectedEvent} />}
        {activeTab === 'shap' && <ShapView onSelectEvent={setSelectedEvent} />}
        {activeTab === 'whatif' && <WhatIfView />}
        {activeTab === 'resources' && <ResourcePlanningView />}
        {activeTab === 'evaluation' && <EvaluationView />}
        {activeTab === 'districtGraph' && <DistrictGraphView />}
        {activeTab === 'assistant' && <AssistantView />}
      </main>

      <EventDrawer baseId={selectedEvent} onClose={() => setSelectedEvent(null)} />
    </div>
  )
}

export default App


