import { X, Wifi, ScanLine, Settings, Key, MessageCircle, Brain } from 'lucide-react'

interface HelpPanelProps {
  open: boolean
  onClose: () => void
}

export default function HelpPanel({ open, onClose }: HelpPanelProps) {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[85vh] overflow-y-auto">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <h2 className="text-lg font-semibold text-slate-800">使用帮助</h2>
          <button onClick={onClose} className="p-1 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer">
            <X className="w-5 h-5 text-slate-400" />
          </button>
        </div>

        <div className="p-6 space-y-6 text-sm text-slate-600 leading-relaxed">

          {/* Step 1 */}
          <section>
            <div className="flex items-center gap-2 mb-2">
              <span className="w-6 h-6 rounded-full bg-violet-500 text-white text-xs flex items-center justify-center font-bold">1</span>
              <h3 className="font-semibold text-slate-800">配置 LLM 大脑</h3>
            </div>
            <div className="ml-8 space-y-1">
              <p>点击右上角 <Settings className="w-4 h-4 inline text-slate-400" /> 打开设置面板。</p>
              <p>在「LLM 大脑」区域填入 API Key、模型名和 Base URL。</p>
              <p>支持 OpenAI / DeepSeek / 豆包 / Ollama 等兼容 OpenAI API 的服务。</p>
              <p className="text-slate-400">也可通过项目根目录 .env 文件配置。</p>
            </div>
          </section>

          {/* Step 2 */}
          <section>
            <div className="flex items-center gap-2 mb-2">
              <span className="w-6 h-6 rounded-full bg-violet-500 text-white text-xs flex items-center justify-center font-bold">2</span>
              <h3 className="font-semibold text-slate-800">连接小米设备（扫码登录）</h3>
            </div>
            <div className="ml-8 space-y-1">
              <p>点击 <Settings className="w-4 h-4 inline text-slate-400" /> → 小米/米家区域 → <strong>生成二维码</strong>。</p>
              <p>打开手机上的 <strong>米家 APP</strong>，扫描页面上的二维码。</p>
              <p>扫码成功后，系统自动获取你小米账号下所有设备的信息和 Token。</p>
              <p className="text-slate-400">为什么需要扫码？Token 是设备的控制密钥，小米只提供给已认证的账号主人。局域网扫描能发现设备，但拿不到 Token。</p>
            </div>
          </section>

          {/* Step 3 */}
          <section>
            <div className="flex items-center gap-2 mb-2">
              <span className="w-6 h-6 rounded-full bg-violet-500 text-white text-xs flex items-center justify-center font-bold">3</span>
              <h3 className="font-semibold text-slate-800">查看和管理设备</h3>
            </div>
            <div className="ml-8 space-y-1">
              <p>扫码成功后，左栏会列出所有设备（加湿器、空调、灯光等）。</p>
              <p>点击设备可查看传感器数据和控制能力。</p>
              <p>点击 <ScanLine className="w-4 h-4 inline text-slate-400" /> <strong>扫描设备</strong> 可随时重新扫描局域网。</p>
            </div>
          </section>

          {/* Step 4 */}
          <section>
            <div className="flex items-center gap-2 mb-2">
              <span className="w-6 h-6 rounded-full bg-violet-500 text-white text-xs flex items-center justify-center font-bold">4</span>
              <h3 className="font-semibold text-slate-800">AI 自动决策</h3>
            </div>
            <div className="ml-8 space-y-1">
              <p>设备连接后，Anima 的 AI 大脑会自动根据传感器数据做出决策。</p>
              <p>右栏 <Brain className="w-4 h-4 inline text-slate-400" /> <strong>AI 决策流</strong> 实时展示每一条决策和原因。</p>
              <p>紧急情况（如温度过高）由规则引擎毫秒级响应，无需等待 AI。</p>
            </div>
          </section>

          {/* Step 5 */}
          <section>
            <div className="flex items-center gap-2 mb-2">
              <span className="w-6 h-6 rounded-full bg-violet-500 text-white text-xs flex items-center justify-center font-bold">5</span>
              <h3 className="font-semibold text-slate-800">对话交互</h3>
            </div>
            <div className="ml-8 space-y-1">
              <p>底部 <MessageCircle className="w-4 h-4 inline text-slate-400" /> 聊天栏可以和 Anima 对话，直接下达指令。</p>
              <p className="text-slate-400">完整对话功能将在后续版本中推出。</p>
            </div>
          </section>

          <hr className="border-slate-200" />

          {/* Manual device */}
          <section>
            <div className="flex items-center gap-2 mb-2">
              <Key className="w-4 h-4 text-violet-500" />
              <h3 className="font-semibold text-slate-800">手动添加设备</h3>
            </div>
            <div className="ml-6 space-y-1">
              <p>如果你已经有设备的 IP 和 Token，可以在设置面板的「手动添加设备」区域直接输入。</p>
              <p>Token 获取方式：扫码登录（推荐）、米家 APP 本地日志（Android）、第三方 Token 提取工具。</p>
            </div>
          </section>

          {/* Links */}
          <section>
            <div className="flex items-center gap-2 mb-2">
              <Wifi className="w-4 h-4 text-violet-500" />
              <h3 className="font-semibold text-slate-800">了解更多</h3>
            </div>
            <div className="ml-6 space-y-1">
              <p>
                <a href="https://github.com/fulai-tech/Anima" target="_blank" className="text-violet-500 hover:text-violet-600 underline">
                  GitHub 仓库
                </a>
                {' · '}
                <a href="https://github.com/fulai-tech/Anima/blob/main/README.zh-CN.md" target="_blank" className="text-violet-500 hover:text-violet-600 underline">
                  中文文档
                </a>
              </p>
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}
