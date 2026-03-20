import { useState, useEffect } from 'react'
import { Activity, RefreshCw, Wifi, WifiOff } from 'lucide-react'
import { api } from '../hooks/useApi'

interface HeaderProps {
  deviceCount: number
  onScan: () => void
}

export default function Header({ deviceCount, onScan }: HeaderProps) {
  const [connected, setConnected] = useState(false)
  const [scanning, setScanning] = useState(false)

  useEffect(() => {
    api.getHealth().then(() => setConnected(true)).catch(() => setConnected(false))
    const id = setInterval(() => {
      api.getHealth().then(() => setConnected(true)).catch(() => setConnected(false))
    }, 10000)
    return () => clearInterval(id)
  }, [])

  const handleScan = async () => {
    setScanning(true)
    try {
      await api.scan()
      onScan()
    } finally {
      setTimeout(() => setScanning(false), 1000)
    }
  }

  return (
    <header className="flex items-center justify-between px-6 py-4 bg-slate-800/50 border-b border-slate-700">
      <div className="flex items-center gap-3">
        <Activity className="w-6 h-6 text-violet-400" />
        <h1 className="text-xl font-semibold text-white">Anima</h1>
        <span className="text-sm text-slate-400">Make Every Hardware Intelligent</span>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-sm">
          {connected ? (
            <><Wifi className="w-4 h-4 text-green-400" /><span className="text-green-400">在线</span></>
          ) : (
            <><WifiOff className="w-4 h-4 text-red-400" /><span className="text-red-400">离线</span></>
          )}
        </div>

        <span className="text-sm text-slate-400">
          {deviceCount} 台设备
        </span>

        <button
          onClick={handleScan}
          disabled={scanning}
          className="flex items-center gap-2 px-3 py-1.5 text-sm bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white rounded-lg transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${scanning ? 'animate-spin' : ''}`} />
          扫描设备
        </button>
      </div>
    </header>
  )
}
