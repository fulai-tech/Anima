import { Droplets, Thermometer, Lightbulb, Cpu, HelpCircle } from 'lucide-react'
import type { Device } from '../hooks/useApi'

const TYPE_ICONS: Record<string, typeof Cpu> = {
  humidifier: Droplets,
  air_conditioner: Thermometer,
  light: Lightbulb,
  air_purifier: Cpu,
}

const TYPE_LABELS: Record<string, string> = {
  humidifier: '加湿器',
  air_conditioner: '空调',
  light: '灯光',
  air_purifier: '净化器',
  vacuum: '扫地机',
  curtain: '窗帘',
}

interface DeviceListProps {
  devices: Device[]
  selectedId: string | null
  onSelect: (id: string) => void
}

export default function DeviceList({ devices, selectedId, onSelect }: DeviceListProps) {
  const Icon = ({ type }: { type: string }) => {
    const Comp = TYPE_ICONS[type] || HelpCircle
    return <Comp className="w-5 h-5" />
  }

  return (
    <aside className="w-64 min-w-[256px] bg-slate-800/30 border-r border-slate-700 flex flex-col">
      <div className="px-4 py-3 border-b border-slate-700">
        <h2 className="text-sm font-medium text-slate-300 uppercase tracking-wider">设备列表</h2>
      </div>

      <div className="flex-1 overflow-y-auto">
        {devices.length === 0 ? (
          <div className="p-4 text-sm text-slate-500 text-center">
            <p>暂无设备</p>
            <p className="mt-1 text-xs">点击右上角「扫描设备」</p>
          </div>
        ) : (
          <ul>
            {devices.map((d) => (
              <li key={d.device_id}>
                <button
                  onClick={() => onSelect(d.device_id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-slate-700/50 ${
                    selectedId === d.device_id ? 'bg-slate-700/70 border-l-2 border-violet-400' : 'border-l-2 border-transparent'
                  }`}
                >
                  <span className={`${d.online ? 'text-violet-400' : 'text-slate-600'}`}>
                    <Icon type={d.type} />
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-200 truncate">{d.name}</p>
                    <p className="text-xs text-slate-500">
                      {TYPE_LABELS[d.type] || d.type} · {d.adapter}
                    </p>
                  </div>
                  <span className={`w-2 h-2 rounded-full ${d.online ? 'bg-green-400' : 'bg-slate-600'}`} />
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="px-4 py-3 border-t border-slate-700 text-xs text-slate-500">
        共 {devices.length} 台设备 · {devices.filter(d => d.online).length} 在线
      </div>
    </aside>
  )
}
