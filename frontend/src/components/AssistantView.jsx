import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import '../assistant.css'

const SUGGESTIONS = [
  'What are the evacuation rules for Ganjam?',
  'What does a red alert mean?',
  "What's the weather in Ganjam today?",
  'Are there any current cyclone warnings for Odisha?',
]

// --- tiny, safe formatter: **bold** and "- " bullets (no HTML injection) ---
function inline(text) {
  return text.split(/(\*\*[^*]+\*\*)/g).map((p, i) =>
    p.startsWith('**') && p.endsWith('**') ? <strong key={i}>{p.slice(2, -2)}</strong> : p)
}

function Answer({ text }) {
  const blocks = []
  let list = []
  const flush = () => {
    if (list.length) { blocks.push(<ul key={`u${blocks.length}`}>{list}</ul>); list = [] }
  }
  const highlight = (line) => {
    const low = line.toLowerCase()
    if (/\b(no|not|could not verify|unable to verify)\b.{0,32}\b(red alert|cyclone|warning|alert status|severe thunderstorms?)\b/.test(low)) return ''
    if (/\bred alert\b|\bred message\b|\bcyclone warning\b|\bsevere cyclonic storm\b|\bextremely heavy rain\b|\bstorm surge warning\b|\bsevere thunderstorms?\b/.test(low)) return 'rag-alert-danger'
    if (/\borange alert\b|\byellow alert\b|\bheavy rain\b|\bstrong winds?\b|\bthunderstorms?\b|\b(upcoming|tropical) cyclone\b|\bcyclone (outlook|forecast|expected|likely)\b/.test(low)) return 'rag-alert-caution'
    if (/\bfollow official|\bstay indoors\b|\bmove to (a )?(designated )?shelter\b|\bavoid travel\b|\bkeep .* (ready|charged)\b/.test(low)) return 'rag-alert-safety'
    return ''
  }
  text.split('\n').forEach((line, i) => {
    const m = line.match(/^\s*[-*•]\s+(.*)/)
    if (m) list.push(<li key={i} className={highlight(m[1])}>{inline(m[1])}</li>)
    else { flush(); if (line.trim()) blocks.push(<p key={`p${i}`} className={highlight(line)}>{inline(line)}</p>) }
  })
  flush()
  return <div className="agent-a">{blocks}</div>
}

export default function AssistantView() {
  const [question, setQuestion] = useState('')
  const [history, setHistory] = useState([]) // [{role:'user'|'model', text}]
  const [turns, setTurns] = useState([])     // [{q, a, mode, sources, tools_used, llm_error, log_id, rated}]
  const [pending, setPending] = useState('') // question currently being answered
  const [asking, setAsking] = useState(false)
  const endRef = useRef(null)

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }) }, [turns, pending])

  const ask = async (text) => {
    const q = (text ?? question).trim()
    if (!q || asking) return
    setAsking(true)
    setPending(q)
    setQuestion('')
    try {
      const data = await api.ask(q, history)
      setTurns((t) => [...t, {
        q, a: data.answer, mode: data.mode, model: data.model, warning: data.warning, sources: data.sources || [],
        tools_used: data.tools_used || [], llm_error: data.llm_error, log_id: data.log_id,
      }])
      setHistory((h) => [...h, { role: 'user', text: q }, { role: 'model', text: data.answer }])
    } catch {
      setTurns((t) => [...t, {
        q, mode: 'error', sources: [], tools_used: [],
        a: 'Could not reach the IDMAP assistant. Start the project from the IDMAP folder with: npm run dev',
      }])
    }
    setPending('')
    setAsking(false)
  }

  const rate = async (i, rating) => {
    const t = turns[i]
    if (!t.log_id || t.rated) return
    setTurns((all) => all.map((x, j) => (j === i ? { ...x, rated: rating } : x)))
    try { await api.feedback(t.log_id, rating) } catch { /* feedback is best-effort */ }
  }

  const clearHistory = () => { setHistory([]); setTurns([]) }

  return (
    <div className="assistant-view">
      <div className="view-header">
        <div className="view-header-row">
          <div>
            <h1>Assistant</h1>
            <p className="view-subtitle">
              Evidence-grounded (RAG) -- answers come from IMD / OSDMA knowledge documents and IDMAP data,
              with sources shown. If nothing relevant is found, it says so. Multi-turn: follow-up questions
              see prior turns.
            </p>
          </div>
          {turns.length > 0 && <button className="chip" onClick={clearHistory}>clear conversation</button>}
        </div>
      </div>

      <div className="suggestion-row">
        {SUGGESTIONS.map((s) => (
          <button key={s} className="chip" onClick={() => ask(s)} disabled={asking}>{s}</button>
        ))}
      </div>

      <div className="agent-history">
        {turns.length === 0 && !pending && <p className="loading">Ask a question or click a suggestion above.</p>}
        {turns.map((t, i) => (
          <div key={i} className="agent-turn">
            <div className="agent-q">{t.q}</div>
            <Answer text={t.a} />

            {t.sources.length > 0 && (
              <details className="rag-sources">
                <summary>{t.sources.length} source{t.sources.length > 1 ? 's' : ''} used</summary>
                {t.sources.map((s, k) => (
                  <div key={k} className="rag-source" title={s.snippet}>
                    {s.kind === 'web' ? (
                      <><span className="rag-kind">web</span>
                        <a href={s.url} target="_blank" rel="noreferrer">{s.source}</a></>
                    ) : s.kind === 'live' ? (
                      <><span className="rag-kind live">live</span> {s.source} &rsaquo; {s.section}</>
                    ) : (
                      <><code>[{s.n}]</code> {s.source} &rsaquo; {s.section}
                        {typeof s.score === 'number' && <span className="rag-score">{Math.round(s.score * 100)}% match</span>}</>
                    )}
                  </div>
                ))}
              </details>
            )}

            {t.llm_error && <div className="rag-error">Gemini error: {t.llm_error}</div>}
            {t.warning && <div className="rag-error">Note: {t.warning}</div>}

            <div className="agent-meta">
              {t.mode === 'rag' && <span className="mode-tag mode-llm" title={t.model}>Gemini + RAG</span>}
              {t.mode === 'curated' && <span className="mode-tag mode-llm">reviewed answer</span>}
              {t.mode === 'live' && <span className="mode-tag mode-llm" title={t.model}>Live data + Gemini</span>}
              {t.mode === 'rag_web' && <span className="mode-tag mode-llm" title={t.model}>Gemini + RAG + Web search</span>}
              {t.mode === 'web' && <span className="mode-tag mode-llm" title={t.model}>Web search + Gemini</span>}
              {t.mode === 'general' && <span className="mode-tag mode-fallback" title={t.model}>general knowledge (not from IDMAP data)</span>}
              {t.mode === 'fallback' && <span className="mode-tag mode-fallback">retrieval only (Gemini unavailable)</span>}
              {t.mode === 'no_context' && <span className="mode-tag mode-fallback">no source found</span>}
              {t.mode === 'error' && <span className="mode-tag mode-fallback">connection error</span>}
              {t.tools_used?.length > 0 && (
                <span className="tools-used">tools called: {t.tools_used.map((n) => <code key={n}>{n}</code>)}</span>
              )}
              {t.llm_error && <span className="tools-used">Gemini call failed, showing sources</span>}
              {t.log_id && (
                <span className="rag-rate">
                  <button className="chip" disabled={!!t.rated} onClick={() => rate(i, 1)}>{t.rated === 1 ? 'helpful ✓' : 'helpful'}</button>
                  <button className="chip" disabled={!!t.rated} onClick={() => rate(i, -1)}>{t.rated === -1 ? 'not helpful ✓' : 'not helpful'}</button>
                </span>
              )}
            </div>
          </div>
        ))}

        {pending && (
          <div className="agent-turn">
            <div className="agent-q">{pending}</div>
            <p className="loading rag-thinking">Searching the knowledge base…</p>
          </div>
        )}
        <div ref={endRef} />
      </div>

      <div className="agent-input-row">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && ask()}
          placeholder="Ask about cyclone procedures, districts, or past events…"
        />
        <button onClick={() => ask()} disabled={asking}>{asking ? '…' : 'Ask'}</button>
      </div>
    </div>
  )
}
