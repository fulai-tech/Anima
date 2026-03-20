import { useState } from 'react'
import { Droplets, Thermometer, Lightbulb, Zap, Power, Gauge, Key, Loader2, Check } from 'lucide-react'
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
  onDevicesChanged?: () => void
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

function NeedsTokenCard({ device, onActivated }: { device: Device; onActivated: () => void }) {
  const [token, setToken] = useState('')
  const [activating, setActivating] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const handleActivate = async () => {
    if (!token || token.length < 16) {
      setError('Token 格式不正确（应为 32 位十六进制）')
      return
    }
    setActivating(true)
    setError('')
    try {
      const res = await fetch(`/api/devices/${device.device_id}/activate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token }),
      })
      const data = await res.json()
      if (data.success) {
        setSuccess(`已激活: ${data.name} (${data.type})`)
        setToken('')
        onActivated()
      } else {
        setError(data.error || '激活失败')
      }
    } catch {
      setError('网络错误')
    } finally {
      setActivating(false)
    }
  }

  const [showTokenInput, setShowTokenInput] = useState(false)

  return (
    <div className="bg-white border border-amber-200 rounded-xl p-5 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-lg font-medium text-slate-800">{device.name}</h3>
          <p className="text-sm text-slate-400">{device.ip || device.device_id}</p>
        </div>
        <span className="px-2 py-1 text-xs rounded-full bg-amber-50 text-amber-600 border border-amber-200">
          需要激活
        </span>
      </div>

      <div className="bg-amber-50 border border-amber-100 rounded-lg p-3 mb-3 text-sm text-slate-600 space-y-2">
        <p className="font-medium text-slate-700">已在局域网发现此设备，但缺少 Token（设备控制密钥）。</p>
        <p className="text-slate-500">请按以下方法获取 Token：</p>
        <ol className="list-decimal ml-4 space-y-1 text-slate-500">
          <li><strong>扫码登录</strong>（推荐）— 点击右上角 ⚙ 设置 → 小米/米家 → 生成二维码 → 用绑定了此设备的米家 APP 扫码</li>
          <li><strong>多账号？</strong> — 如果扫码后此设备仍需 Token，说明它绑在另一个小米账号下。用那个账号重新扫码即可</li>
          <li><strong>手动输入</strong> — 如果你已有 Token，点击下方「输入 Token」直接填入</li>
        </ol>
      </div>

      {showTokenInput ? (
        <div className="space-y-2">
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="输入 32 位 Token"
              value={token}
              onChange={e => setToken(e.target.value)}
              className="flex-1 px-3 py-2 text-sm font-mono border border-slate-200 rounded-lg bg-slate-50 focus:outline-none focus:border-violet-400"
            />
            <button
              onClick={handleActivate}
              disabled={activating || !token}
              className="flex items-center gap-1.5 px-3 py-2 text-sm bg-violet-500 hover:bg-violet-600 disabled:opacity-40 text-white rounded-lg transition-colors cursor-pointer"
            >
              {activating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Key className="w-4 h-4" />}
              激活
            </button>
          </div>
          <button onClick={() => setShowTokenInput(false)} className="text-xs text-slate-400 hover:text-slate-500 cursor-pointer">收起</button>
        </div>
      ) : (
        <button
          onClick={() => setShowTokenInput(true)}
          className="text-sm text-violet-500 hover:text-violet-600 cursor-pointer"
        >
          输入 Token
        </button>
      )}
      {error && <p className="text-sm text-red-500 mt-2">{error}</p>}
      {success && <p className="text-sm text-emerald-600 mt-2 flex items-center gap-1"><Check className="w-4 h-4" />{success}</p>}
    </div>
  )
}

function ActiveCard({ device }: { device: Device }) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-medium text-slate-800">{device.name}</h3>
          <p className="text-sm text-slate-400">{device.ip || device.device_id}</p>
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

export default function DeviceCard({ devices, selectedId, onDevicesChanged }: DeviceCardProps) {
  const selected = selectedId ? devices.find(d => d.device_id === selectedId) : null
  const shown = selected ? [selected] : devices

  // Sort: active devices first, needs-token devices after
  const sorted = [...shown].sort((a, b) => {
    if (a.needs_token === b.needs_token) return 0
    return a.needs_token ? 1 : -1
  })

  return (
    <div className="flex-1 overflow-y-auto p-5 bg-slate-50">
      {sorted.length === 0 ? (
        <div className="flex items-center justify-center h-full text-slate-400">
          <div className="text-center">
            <Lightbulb className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>暂无设备</p>
            <p className="text-sm mt-1">点击右上角「扫描设备」发现局域网中的智能设备</p>
          </div>
        </div>
      ) : (
        <div className="grid gap-4">
          {sorted.map((d) =>
            d.needs_token ? (
              <NeedsTokenCard key={d.device_id} device={d} onActivated={onDevicesChanged || (() => {})} />
            ) : (
              <ActiveCard key={d.device_id} device={d} />
            )
          )}
        </div>
      )}
    </div>
  )
}
