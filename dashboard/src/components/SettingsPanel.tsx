import { useState, useEffect } from 'react'
import { Settings, Wifi, WifiOff, Brain, Eye, EyeOff, X, Check, Loader2 } from 'lucide-react'

interface SettingsPanelProps {
  open: boolean
  onClose: () => void
  onDevicesChanged: () => void
}

export default function SettingsPanel({ open, onClose, onDevicesChanged }: SettingsPanelProps) {
  // Xiaomi state
  const [xiaomiUser, setXiaomiUser] = useState('')
  const [xiaomiPass, setXiaomiPass] = useState('')
  const [xiaomiCountry, setXiaomiCountry] = useState('cn')
  const [xiaomiConnected, setXiaomiConnected] = useState(false)
  const [xiaomiConnecting, setXiaomiConnecting] = useState(false)
  const [xiaomiError, setXiaomiError] = useState('')
  const [xiaomiResult, setXiaomiResult] = useState('')

  // LLM state
  const [llmKey, setLlmKey] = useState('')
  const [llmModel, setLlmModel] = useState('gpt-4o')
  const [llmBaseUrl, setLlmBaseUrl] = useState('')
  const [llmDisableThinking, setLlmDisableThinking] = useState(false)
  const [llmConfigured, setLlmConfigured] = useState(false)
  const [llmSource, setLlmSource] = useState('')
  const [llmSaving, setLlmSaving] = useState(false)
  const [llmSaved, setLlmSaved] = useState(false)

  const [showPass, setShowPass] = useState(false)
  const [showKey, setShowKey] = useState(false)

  useEffect(() => {
    if (!open) return
    // Load current status
    fetch('/api/settings/xiaomi/status').then(r => r.json()).then(data => {
      setXiaomiConnected(data.configured)
      if (data.username) setXiaomiUser(data.username)
      if (data.country) setXiaomiCountry(data.country)
    }).catch(() => {})

    fetch('/api/settings/llm/status').then(r => r.json()).then(data => {
      setLlmConfigured(data.configured)
      setLlmModel(data.model || 'gpt-4o')
      setLlmBaseUrl(data.base_url || '')
      setLlmSource(data.source || '')
    }).catch(() => {})
  }, [open])

  const handleXiaomiConnect = async () => {
    if (!xiaomiUser || !xiaomiPass) return
    setXiaomiConnecting(true)
    setXiaomiError('')
    setXiaomiResult('')

    try {
      const res = await fetch('/api/settings/xiaomi/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: xiaomiUser, password: xiaomiPass, country: xiaomiCountry }),
      })
      const data = await res.json()
      if (data.success) {
        setXiaomiConnected(true)
        setXiaomiResult(`连接成功！发现 ${data.cloud_devices} 台云端设备，已添加 ${data.discovered} 台新设备。`)
        setXiaomiPass('')
        onDevicesChanged()
      } else {
        setXiaomiError(data.error || '连接失败')
      }
    } catch {
      setXiaomiError('网络错误，请检查后端是否运行')
    } finally {
      setXiaomiConnecting(false)
    }
  }

  const handleXiaomiDisconnect = async () => {
    await fetch('/api/settings/xiaomi/disconnect', { method: 'POST' })
    setXiaomiConnected(false)
    setXiaomiUser('')
    setXiaomiResult('')
  }

  const handleLlmSave = async () => {
    if (!llmKey) return
    setLlmSaving(true)
    setLlmSaved(false)

    try {
      await fetch('/api/settings/llm/configure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          api_key: llmKey,
          model: llmModel,
          base_url: llmBaseUrl,
          disable_thinking: llmDisableThinking,
        }),
      })
      setLlmConfigured(true)
      setLlmSaved(true)
      setLlmSource('dashboard')
      setLlmKey('')
      setTimeout(() => setLlmSaved(false), 3000)
    } catch {
      /* ignore */
    } finally {
      setLlmSaving(false)
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[85vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <div className="flex items-center gap-2">
            <Settings className="w-5 h-5 text-violet-500" />
            <h2 className="text-lg font-semibold text-slate-800">设置</h2>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer">
            <X className="w-5 h-5 text-slate-400" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Xiaomi Section */}
          <section>
            <div className="flex items-center gap-2 mb-3">
              {xiaomiConnected ? <Wifi className="w-4 h-4 text-emerald-500" /> : <WifiOff className="w-4 h-4 text-slate-400" />}
              <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wider">小米 / 米家</h3>
              {xiaomiConnected && <span className="text-xs bg-emerald-50 text-emerald-600 px-2 py-0.5 rounded-full">已连接</span>}
            </div>

            {xiaomiConnected ? (
              <div>
                <p className="text-sm text-slate-500 mb-2">已登录: {xiaomiUser}</p>
                {xiaomiResult && <p className="text-sm text-emerald-600 mb-2">{xiaomiResult}</p>}
                <button onClick={handleXiaomiDisconnect} className="text-sm text-red-500 hover:text-red-600 cursor-pointer">断开连接</button>
              </div>
            ) : (
              <div className="space-y-3">
                <p className="text-sm text-slate-500">登录小米账号，自动获取所有绑定的智能设备和 token。</p>
                <input
                  type="text"
                  placeholder="小米账号（手机号或邮箱）"
                  value={xiaomiUser}
                  onChange={e => setXiaomiUser(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg bg-slate-50 focus:outline-none focus:border-violet-400"
                />
                <div className="relative">
                  <input
                    type={showPass ? 'text' : 'password'}
                    placeholder="密码"
                    value={xiaomiPass}
                    onChange={e => setXiaomiPass(e.target.value)}
                    className="w-full px-3 py-2 pr-10 text-sm border border-slate-200 rounded-lg bg-slate-50 focus:outline-none focus:border-violet-400"
                  />
                  <button onClick={() => setShowPass(!showPass)} className="absolute right-2 top-1/2 -translate-y-1/2 p-1 cursor-pointer">
                    {showPass ? <EyeOff className="w-4 h-4 text-slate-400" /> : <Eye className="w-4 h-4 text-slate-400" />}
                  </button>
                </div>
                <select
                  value={xiaomiCountry}
                  onChange={e => setXiaomiCountry(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg bg-slate-50 focus:outline-none focus:border-violet-400"
                >
                  <option value="cn">中国大陆</option>
                  <option value="tw">台湾</option>
                  <option value="de">欧洲</option>
                  <option value="us">美国</option>
                  <option value="sg">新加坡</option>
                  <option value="in">印度</option>
                  <option value="ru">俄罗斯</option>
                </select>

                {xiaomiError && <p className="text-sm text-red-500">{xiaomiError}</p>}
                {xiaomiResult && <p className="text-sm text-emerald-600">{xiaomiResult}</p>}

                <button
                  onClick={handleXiaomiConnect}
                  disabled={xiaomiConnecting || !xiaomiUser || !xiaomiPass}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm bg-violet-500 hover:bg-violet-600 disabled:opacity-40 text-white rounded-lg transition-colors cursor-pointer"
                >
                  {xiaomiConnecting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wifi className="w-4 h-4" />}
                  {xiaomiConnecting ? '连接中...' : '连接小米云服务'}
                </button>
              </div>
            )}
          </section>

          <hr className="border-slate-200" />

          {/* LLM Section */}
          <section>
            <div className="flex items-center gap-2 mb-3">
              <Brain className="w-4 h-4 text-violet-500" />
              <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wider">LLM 大脑</h3>
              {llmConfigured && <span className="text-xs bg-emerald-50 text-emerald-600 px-2 py-0.5 rounded-full">已配置 ({llmSource})</span>}
            </div>

            <p className="text-sm text-slate-500 mb-3">
              配置 AI 大脑，支持 OpenAI / DeepSeek / 豆包 / Ollama 等兼容 OpenAI API 的服务。
              也可通过 .env 文件配置。
            </p>

            <div className="space-y-3">
              <div className="relative">
                <input
                  type={showKey ? 'text' : 'password'}
                  placeholder="API Key"
                  value={llmKey}
                  onChange={e => setLlmKey(e.target.value)}
                  className="w-full px-3 py-2 pr-10 text-sm border border-slate-200 rounded-lg bg-slate-50 focus:outline-none focus:border-violet-400"
                />
                <button onClick={() => setShowKey(!showKey)} className="absolute right-2 top-1/2 -translate-y-1/2 p-1 cursor-pointer">
                  {showKey ? <EyeOff className="w-4 h-4 text-slate-400" /> : <Eye className="w-4 h-4 text-slate-400" />}
                </button>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <input
                  type="text"
                  placeholder="模型名称 (如 gpt-4o)"
                  value={llmModel}
                  onChange={e => setLlmModel(e.target.value)}
                  className="px-3 py-2 text-sm border border-slate-200 rounded-lg bg-slate-50 focus:outline-none focus:border-violet-400"
                />
                <input
                  type="text"
                  placeholder="Base URL（留空=OpenAI）"
                  value={llmBaseUrl}
                  onChange={e => setLlmBaseUrl(e.target.value)}
                  className="px-3 py-2 text-sm border border-slate-200 rounded-lg bg-slate-50 focus:outline-none focus:border-violet-400"
                />
              </div>
              <label className="flex items-center gap-2 text-sm text-slate-600 cursor-pointer">
                <input
                  type="checkbox"
                  checked={llmDisableThinking}
                  onChange={e => setLlmDisableThinking(e.target.checked)}
                  className="rounded"
                />
                关闭深度思考（豆包必选）
              </label>

              {llmSaved && <p className="text-sm text-emerald-600 flex items-center gap-1"><Check className="w-4 h-4" />已保存</p>}

              <button
                onClick={handleLlmSave}
                disabled={llmSaving || !llmKey}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm bg-violet-500 hover:bg-violet-600 disabled:opacity-40 text-white rounded-lg transition-colors cursor-pointer"
              >
                {llmSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Brain className="w-4 h-4" />}
                保存 LLM 配置
              </button>
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}
