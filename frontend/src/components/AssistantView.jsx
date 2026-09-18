import { useState } from 'react'
import { api } from '../api'

const SUGGESTIONS = [
  'what is the project status?',
  'top 5 anomalies',
  'tell me about event 46',
  'how many events are there?',
]

export default function AssistantView() {
  const [question, setQuestion] = useState('')
  const [history, setHistory] = useState([]) // [{role:'user'|'model', text}]
  const [turns, setTurns] = useState([]) // [{q, a, mode, tools_used, llm_error}]
  const [asking, setAsking] = useState(false)

  const ask = async (text) => {
    const q = (text ?? question).trim()
    if (!q) return
    setAsking(true)
    setQuestion('')
    try {
      const data = await api.ask(q, history)
      setTurns((t) => [...t, {
        q, a: data.answer, mode: data.mode,
        tools_used: data.tools_used || [], llm_error: data.llm_error,
      }])
      setHistory((h) => [...h, { role: 'user', text: q }, { role: 'model', text: data.answer }])
    } catch {
      setTurns((t) => [...t, { q, a: 'Could not reach the backend at localhost:8000.', mode: 'error', tools_used: [] }])
    }
    setAsking(false)
  }

  const clearHistory = () => {
    setHistory([])
    setTurns([])
  }

  return (
    <div className="assistant-view">
      <div className="view-header">
        <div className="view-header-row">
          <div>
            <h1>Assistant</h1>
            <p className="view-subtitle">
              Tool-grounded -- every answer comes from the tools in src/agent/tools.py,
              never invented. Multi-turn: follow-up questions see prior turns.
            </p>
          </div>
          {turns.length > 0 && (
            <button className="chip" onClick={clearHistory}>clear conversation</button>
          )}
        </div>
      </div>

      <div className="suggestion-row">
        {SUGGESTIONS.map((s) => (
          <button key={s} className="chip" onClick={() => ask(s)}>{s}</button>
        ))}
      </div>

      <div className="agent-history">
        {turns.length === 0 && (
          <p className="loading">Ask a question or click a suggestion above.</p>
        )}
        {turns.map((t, i) => (
          <div key={i} className="agent-turn">
            <div className="agent-q">{t.q}</div>
            <pre className="agent-a">{t.a}</pre>
            <div className="agent-meta">
              {t.mode === 'llm' && <span className="mode-tag mode-llm">Gemini</span>}
              {t.mode === 'fallback' && <span className="mode-tag mode-fallback">rule-based fallback</span>}
              {t.mode === 'error' && <span className="mode-tag mode-fallback">connection error</span>}
              {t.tools_used?.length > 0 && (
                <span className="tools-used">
                  tools called: {t.tools_used.map((tn) => <code key={tn}>{tn}</code>)}
                </span>
              )}
              {t.llm_error && (
                <span className="tools-used" title={t.llm_error}>Gemini call failed, used fallback</span>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="agent-input-row">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && ask()}
          placeholder="Ask about project status, anomalies, or a specific event…"
        />
        <button onClick={() => ask()} disabled={asking}>{asking ? '…' : 'Ask'}</button>
      </div>
    </div>
  )
}
