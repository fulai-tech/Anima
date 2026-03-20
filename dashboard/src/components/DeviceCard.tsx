import { Droplets, Thermometer, Lightbulb, Zap, Power, Gauge } from 'lucide-react'
import type { Device } from '../hooks/useApi'

const SENSOR_ICONS: Record<string, typeof Gauge> = {
  humidity: Droplets,
  temperature: Thermometer,
  brightness: Lightbulb,
  power: Power,
  water_level: Gauge,
  color_temp: Zap,
}

interface DeviceCardProps {
  devices: Device[]
  selectedId: string | null
}

function SensorBadge({ name, value, unit }: { name: string; value: unknown; unit: string }) {
  const Icon = SENSOR_ICONS[name] || Gauge
  const display = value !== null && value !== undefined ? `${value}${unit}` : '--'

  return (
    <div className="flex items-center gap-2 px-3 py-2 bg-slate-700/40 rounded-lg">
      <Icon className="w-4 h-4 text-slate-400" />
      <div>
        <p className="text-xs text-slate-500 capitalize">{name}</p>
        <p className="text-sm font-mono text-slate-200">{display}</p>
      </div>
    </div>
  )
}

function SingleCard({ device }: { device: Device }) {
  return (
    <div className="bg-slate-800/60 border border-slate-700 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-medium text-white">{device.name}</h3>
          <p className="text-sm text-slate-400">{device.device_id}</p>
        </div>
        <span className={`px-2 py-1 text-xs rounded-full ${
          device.online ? 'bg-green-500/20 text-green-400' : 'bg-slate-600/30 text-slate-500'
        }`}>
          {device.online ? '在线' : '离线'}
        </span>
      </div>

      {device.sensors.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mb-4">
          {device.sensors.map((s) => (
            <SensorBadge key={s.name} name={s.name} value={s.value} unit={s.unit} />
          ))}
        </div>
      )}

      {device.capabilities.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {device.capabilities.map((c) => (
            <span key={c.name} className="px-2 py-0.5 text-xs bg-violet-500/15 text-violet-300 rounded">
              {c.name}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

export default function DeviceCard({ devices, selectedId }: DeviceCardProps) {
  const selected = selectedId ? devices.find(d => d.device_id === selectedId) : null
  const shown = selected ? [selected] : devices

  return (
    <div className="flex-1 overflow-y-auto p-5">
      {shown.length === 0 ? (
        <div className="flex items-center justify-center h-full text-slate-500">
          <div className="text-center">
            <Lightbulb className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>暂无设备</p>
            <p className="text-sm mt-1">扫描局域网以发现智能设备</p>
          </div>
        </div>
      ) : (
        <div className="grid gap-4">
          {shown.map((d) => (
            <SingleCard key={d.device_id} device={d} />
          ))}
        </div>
      )}
    </div>
  )
}
