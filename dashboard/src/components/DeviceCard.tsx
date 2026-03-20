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
    <div className="flex items-center gap-2 px-3 py-2 bg-slate-50 rounded-lg border border-slate-100">
      <Icon className="w-4 h-4 text-slate-400" />
      <div>
        <p className="text-xs text-slate-400 capitalize">{name}</p>
        <p className="text-sm font-mono text-slate-700">{display}</p>
      </div>
    </div>
  )
}

function SingleCard({ device }: { device: Device }) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-medium text-slate-800">{device.name}</h3>
          <p className="text-sm text-slate-400">{device.device_id}</p>
        </div>
        <span className={`px-2 py-1 text-xs rounded-full ${
          device.online ? 'bg-emerald-50 text-emerald-600 border border-emerald-200' : 'bg-slate-100 text-slate-400'
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
            <span key={c.name} className="px-2 py-0.5 text-xs bg-violet-50 text-violet-600 rounded border border-violet-100">
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
    <div className="flex-1 overflow-y-auto p-5 bg-slate-50">
      {shown.length === 0 ? (
        <div className="flex items-center justify-center h-full text-slate-400">
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
