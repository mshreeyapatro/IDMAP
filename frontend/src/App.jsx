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
import ForecastView from './components/ForecastView'

function App() {
  const [activeTab, setActiveTab] = useState('forecast')
  const [selectedEvent, setSelectedEvent] = useState(null)
  const [phasesDone, setPhasesDone] = useState(0)
  const [phasesTotal, setPhasesTotal] = useState(0)
  const [telemetryMode, setTelemetryMode] = useState('simulated') // 'simulated' | 'live'
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    return localStorage.getItem('idmap_sidebar_collapsed') === 'true'
  })

  const toggleSidebar = () => {
    setSidebarCollapsed(prev => {
      const next = !prev
      localStorage.setItem('idmap_sidebar_collapsed', String(next))
      return next
    })
  }

  const toggleTelemetryMode = () => {
    setTelemetryMode(prev => prev === 'simulated' ? 'live' : 'simulated')
  }

  useEffect(() => {
    api.status().then((status) => {
      const entries = Object.values(status)
      setPhasesDone(entries.filter((s) => s.status === 'done').length)
      setPhasesTotal(entries.length)
    }).catch(() => {})
  }, [])

  return (
    <div id="app-shell" className={sidebarCollapsed ? 'sidebar-collapsed' : ''}>
      <Sidebar
        activeTab={activeTab}
        onNavigateTab={setActiveTab}
        phasesDone={phasesDone}
        phasesTotal={phasesTotal}
        telemetryMode={telemetryMode}
        onToggleTelemetryMode={toggleTelemetryMode}
        collapsed={sidebarCollapsed}
        onToggleCollapse={toggleSidebar}
      />
      <main className={`main-content ${activeTab === 'forecast' ? 'forecast-mode' : ''}`}>
        {activeTab === 'overview' && <Overview onSelectEvent={setSelectedEvent} onNavigateTab={setActiveTab} telemetryMode={telemetryMode} onToggleTelemetryMode={toggleTelemetryMode} />}
        {activeTab === 'forecast' && <ForecastView telemetryMode={telemetryMode} onToggleTelemetryMode={toggleTelemetryMode} />}
        {activeTab === 'liveMonitor' && <LiveMonitorView telemetryMode={telemetryMode} onToggleTelemetryMode={toggleTelemetryMode} />}
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


