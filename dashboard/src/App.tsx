import { useState } from 'react'
import Header from './components/Header'
import DeviceList from './components/DeviceList'
import DeviceCard from './components/DeviceCard'
import DecisionLog from './components/DecisionLog'
import ChatBar from './components/ChatBar'
import SettingsPanel from './components/SettingsPanel'
import { useDevices, useDecisions } from './hooks/useApi'

export default function App() {
  const { devices, refresh } = useDevices()
  const { decisions } = useDecisions()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [settingsOpen, setSettingsOpen] = useState(false)

  return (
    <div className="h-screen flex flex-col bg-slate-50">
      <Header
        deviceCount={devices.length}
        onScan={refresh}
        onOpenSettings={() => setSettingsOpen(true)}
      />

      <div className="flex flex-1 overflow-hidden">
        <DeviceList
          devices={devices}
          selectedId={selectedId}
          onSelect={(id) => setSelectedId(id === selectedId ? null : id)}
        />
        <DeviceCard devices={devices} selectedId={selectedId} />
        <DecisionLog decisions={decisions} />
      </div>

      <ChatBar />

      <SettingsPanel
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        onDevicesChanged={refresh}
      />
    </div>
  )
}
