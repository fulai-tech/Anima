import { useState } from 'react'
import { Send, MessageCircle } from 'lucide-react'
import { api } from '../hooks/useApi'

export default function ChatBar() {
  const [message, setMessage] = useState('')
  const [reply, setReply] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSend = async () => {
    const text = message.trim()
    if (!text || loading) return

    setLoading(true)
    setReply('')
    try {
      const res = await api.chat(text)
      setReply(res.reply)
      setMessage('')
    } catch {
      setReply('连接失败，请检查后端是否运行')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="border-t border-slate-700 bg-slate-800/50 px-6 py-3">
      {reply && (
        <div className="mb-2 px-3 py-2 bg-slate-700/40 rounded-lg text-sm text-slate-300">
          <span className="text-violet-400 font-medium">Anima: </span>{reply}
        </div>
      )}
      <div className="flex items-center gap-3">
        <MessageCircle className="w-5 h-5 text-slate-500" />
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="和 Anima 对话..."
          className="flex-1 bg-slate-700/40 border border-slate-600 rounded-lg px-4 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-violet-500 transition-colors"
        />
        <button
          onClick={handleSend}
          disabled={loading || !message.trim()}
          className="flex items-center gap-2 px-4 py-2 text-sm bg-violet-600 hover:bg-violet-500 disabled:opacity-40 text-white rounded-lg transition-colors"
        >
          <Send className="w-4 h-4" />
          发送
        </button>
      </div>
    </div>
  )
}
