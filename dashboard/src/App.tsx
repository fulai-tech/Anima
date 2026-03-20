import { useState } from 'react'
import Header from './components/Header'
import DeviceList from './components/DeviceList'
import DeviceCard from './components/DeviceCard'
import DecisionLog from './components/DecisionLog'
import ChatBar from './components/ChatBar'
import { useDevices, useDecisions } from './hooks/useApi'

export default function App() {
  const { devices, refresh } = useDevices()
  const { decisions } = useDecisions()
  const [selectedId, setSelectedId] = useState<string | null>(null)

  return (
    <div className="h-screen flex flex-col bg-slate-900">
      <Header deviceCount={devices.length} onScan={refresh} />

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
    </div>
  )
}
