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
    <div className="border-t border-slate-200 bg-white px-6 py-3">
      {reply && (
        <div className="mb-2 px-3 py-2 bg-violet-50 rounded-lg text-sm text-slate-600 border border-violet-100">
          <span className="text-violet-600 font-medium">Anima: </span>{reply}
        </div>
      )}
      <div className="flex items-center gap-3">
        <MessageCircle className="w-5 h-5 text-slate-400" />
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="和 Anima 对话..."
          className="flex-1 bg-slate-50 border border-slate-200 rounded-lg px-4 py-2 text-sm text-slate-700 placeholder-slate-400 focus:outline-none focus:border-violet-400 focus:ring-1 focus:ring-violet-400 transition-colors"
        />
        <button
          onClick={handleSend}
          disabled={loading || !message.trim()}
          className="flex items-center gap-2 px-4 py-2 text-sm bg-violet-500 hover:bg-violet-600 disabled:opacity-40 text-white rounded-lg transition-colors cursor-pointer"
        >
          <Send className="w-4 h-4" />
          发送
        </button>
      </div>
    </div>
  )
}
