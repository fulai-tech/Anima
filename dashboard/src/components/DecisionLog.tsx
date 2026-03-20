import { Brain, Clock } from 'lucide-react'
import type { Decision } from '../hooks/useApi'

interface DecisionLogProps {
  decisions: Decision[]
}

function formatTime(ts?: string) {
  if (!ts) return '--:--'
  try {
    const d = new Date(ts)
    return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch {
    return '--:--'
  }
}

export default function DecisionLog({ decisions }: DecisionLogProps) {
  const recent = [...decisions].reverse().slice(0, 50)

  return (
    <aside className="w-72 min-w-[288px] bg-white border-l border-slate-200 flex flex-col">
      <div className="px-4 py-3 border-b border-slate-200 flex items-center gap-2">
        <Brain className="w-4 h-4 text-violet-500" />
        <h2 className="text-sm font-medium text-slate-500 uppercase tracking-wider">AI 决策流</h2>
      </div>

      <div className="flex-1 overflow-y-auto">
        {recent.length === 0 ? (
          <div className="p-4 text-sm text-slate-400 text-center">
            <p>暂无决策记录</p>
            <p className="mt-1 text-xs">AI 做出决策后会实时显示在这里</p>
          </div>
        ) : (
          <ul className="divide-y divide-slate-100">
            {recent.map((d, i) => (
              <li key={i} className="px-4 py-3 hover:bg-slate-50 transition-colors">
                <div className="flex items-center gap-2 mb-1">
                  <Clock className="w-3 h-3 text-slate-300" />
                  <span className="text-xs text-slate-400 font-mono">{formatTime(d.timestamp)}</span>
                </div>
                <p className="text-sm text-slate-700">
                  <span className="text-violet-600 font-medium">{d.action}</span>
                  {d.device_id && <span className="text-slate-400"> → {d.device_id}</span>}
                </p>
                {d.reason && (
                  <p className="text-xs text-slate-400 mt-1">{d.reason}</p>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </aside>
  )
}
