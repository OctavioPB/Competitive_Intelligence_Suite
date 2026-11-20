import { useEffect, useRef, useState } from 'react'
import type { CSSProperties, FormEvent, ReactNode } from 'react'
import { api } from '../services/api'
import type { AskAnswer, AskSource } from '../services/api'
import Eyebrow from '../components/Eyebrow'
import Spinner from '../components/Spinner'
import StatusBadge from '../components/StatusBadge'
import { errorMessage } from '../hooks/useToast'
import { btnGold, card, heroStyle, inputStyle } from '../styles/shared'

type Message =
  | { role: 'user'; content: string }
  | { role: 'assistant'; content: string; result: AskAnswer }
  | { role: 'error'; content: string }

const EXAMPLES = [
  'Why do customers say they are leaving Salesforce?',
  'What do HubSpot users say about pricing tiers?',
  'Which integrations do people complain about?',
  'What do reviewers like about Pipedrive?',
]

const muted: CSSProperties = { fontFamily: 'var(--fb)', fontSize: 12, color: 'var(--mid)' }

function Citation({ n, onClick }: { n: number; onClick: (n: number) => void }) {
  return (
    <button
      onClick={() => onClick(n)}
      aria-label={`Show source ${n}`}
      style={{
        fontFamily: 'var(--fb)', fontSize: 10, fontWeight: 700, color: 'var(--gold)', cursor: 'pointer',
        background: 'rgba(200,152,42,0.12)', border: 'none', borderRadius: 4, padding: '0 4px', margin: '0 1px',
        verticalAlign: 'super', lineHeight: 1.4,
      }}
    >
      {n}
    </button>
  )
}

/** Answer text with [n] markers turned into clickable citations. */
function AnswerText({ text, onCite }: { text: string; onCite: (n: number) => void }) {
  const parts: ReactNode[] = []
  text.split(/(\[\d{1,3}\])/).forEach((part, i) => {
    const m = /^\[(\d{1,3})\]$/.exec(part)
    parts.push(m ? <Citation key={i} n={Number(m[1])} onClick={onCite} /> : <span key={i}>{part}</span>)
  })
  return (
    <div style={{ fontFamily: 'var(--fb)', fontSize: 14, color: 'var(--dark)', lineHeight: 1.65, whiteSpace: 'pre-wrap' }}>
      {parts}
    </div>
  )
}

function SourceCard({ s, highlighted, cited }: { s: AskSource; highlighted: boolean; cited: boolean }) {
  return (
    <li id={`source-${s.review_id}`} style={{
      listStyle: 'none', padding: '10px 12px', borderRadius: 'var(--radius-sm)',
      border: `1px solid ${highlighted ? 'var(--gold)' : 'var(--primary-10)'}`,
      backgroundColor: highlighted ? 'rgba(200,152,42,0.06)' : 'var(--white)',
      opacity: cited || highlighted ? 1 : 0.75, transition: 'border-color 0.2s, background-color 0.2s',
    }}>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap', marginBottom: 4 }}>
        <strong style={{ fontFamily: 'var(--fb)', fontSize: 11, color: 'var(--gold)' }}>[{s.n}]</strong>
        <span style={{ ...muted, fontSize: 11, textTransform: 'uppercase', letterSpacing: '1px' }}>
          {s.competitor} · {s.source} · {s.date ?? 'no date'}{s.rating !== null ? ` · ${s.rating.toFixed(0)}★` : ''}
        </span>
        {s.is_synthetic && <StatusBadge label="Sample" color="var(--status-orange)" bg="var(--status-orange-bg)" />}
      </div>
      <div style={{ fontFamily: 'var(--fb)', fontSize: 12, color: 'var(--dark)', lineHeight: 1.55 }}>“{s.text}”</div>
    </li>
  )
}

function AssistantMessage({ result }: { result: AskAnswer }) {
  const [highlight, setHighlight] = useState<number | null>(null)
  const [showAll, setShowAll] = useState(false)
  const listRef = useRef<HTMLUListElement>(null)

  function cite(n: number) {
    setHighlight(n)
    setShowAll(true)
    const src = result.sources.find((s) => s.n === n)
    if (src) setTimeout(() => document.getElementById(`source-${src.review_id}`)?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 50)
  }

  const cited = new Set(result.cited)
  const ordered = [...result.sources].sort((a, b) => Number(cited.has(b.n)) - Number(cited.has(a.n)) || a.n - b.n)
  const visible = showAll || result.mode !== 'claude' ? ordered : ordered.filter((s) => cited.has(s.n))

  return (
    <div style={{ ...card, padding: '18px 22px', display: 'flex', flexDirection: 'column', gap: 14, borderLeft: '3px solid var(--gold)' }}>
      {result.mode === 'claude' && result.answer ? (
        <AnswerText text={result.answer} onCite={cite} />
      ) : result.mode === 'retrieval' ? (
        <div style={{ ...muted, fontSize: 13 }}>
          Claude is not configured (no ANTHROPIC_API_KEY), so here are the reviews that best match your question.
        </div>
      ) : (
        <div style={{ ...muted, fontSize: 13 }}>{result.answer}</div>
      )}
      {result.sources.length > 0 && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <span style={{ ...muted, fontSize: 10, letterSpacing: '2px', textTransform: 'uppercase' }}>
              Sources · {result.retrieval === 'semantic' ? 'semantic search' : 'keyword search'}
            </span>
            {result.mode === 'claude' && result.sources.length > visible.length && (
              <button onClick={() => setShowAll(true)} style={{ background: 'none', border: 'none', color: 'var(--link)', cursor: 'pointer', fontFamily: 'var(--fb)', fontSize: 11 }}>
                Show all {result.sources.length} retrieved
              </button>
            )}
          </div>
          <ul ref={listRef} style={{ margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: 8 }}>
            {visible.map((s) => <SourceCard key={s.review_id} s={s} highlighted={highlight === s.n} cited={cited.has(s.n)} />)}
          </ul>
        </div>
      )}
    </div>
  )
}

export default function AskPage() {
  const [competitors, setCompetitors] = useState<string[]>([])
  const [scope, setScope] = useState<string>('')
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [busy, setBusy] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => { api.meta.competitors().then((r) => setCompetitors(r.competitors)).catch(() => {}) }, [])
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }) }, [messages, busy])

  function send(text: string) {
    const q = text.trim()
    if (q.length < 3 || busy) return
    const history = messages
      .filter((m): m is Exclude<Message, { role: 'error' }> => m.role !== 'error')
      .slice(-8)
      .map((m) => ({ role: m.role, content: m.role === 'assistant' ? (m.result.answer ?? '') : m.content }))
    setMessages((list) => [...list, { role: 'user', content: q }])
    setQuestion('')
    setBusy(true)
    api.ask(q, scope || null, history)
      .then((result) => setMessages((list) => [...list, { role: 'assistant', content: result.answer ?? '', result }]))
      .catch((err) => setMessages((list) => [...list, { role: 'error', content: errorMessage(err, 'Could not answer.') }]))
      .finally(() => setBusy(false))
  }

  function submit(e: FormEvent) {
    e.preventDefault()
    send(question)
  }

  return (
    <div>
      <div style={heroStyle}>
        <div style={{ maxWidth: 'var(--max-width-dashboard)', margin: '0 auto' }}>
          <Eyebrow light>Ask RivalSense</Eyebrow>
          <h1 style={{ fontFamily: 'var(--fd)', fontSize: 36, fontWeight: 300, color: '#fff', margin: '0 0 6px' }}>
            Ask the <em style={{ fontStyle: 'italic', color: 'var(--gold-light)' }}>reviews</em>
          </h1>
          <p style={{ fontFamily: 'var(--fb)', fontSize: 13, color: 'rgba(255,255,255,0.45)', maxWidth: 620 }}>
            Questions answered from every stored review, with the reviews behind each claim cited.
          </p>
        </div>
      </div>

      <div style={{ backgroundColor: 'var(--light)', minHeight: '60vh' }}>
        <div style={{ maxWidth: 860, margin: '0 auto', padding: '36px 24px 48px', display: 'flex', flexDirection: 'column', gap: 18 }}>
          {messages.length === 0 && (
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {EXAMPLES.map((ex) => (
                <button key={ex} onClick={() => send(ex)} style={{
                  fontFamily: 'var(--fb)', fontSize: 12, color: 'var(--link)', cursor: 'pointer', padding: '8px 12px',
                  border: '1px solid var(--primary-10)', borderRadius: 'var(--radius-pill)', backgroundColor: 'var(--white)',
                }}>{ex}</button>
              ))}
            </div>
          )}

          {messages.map((m, i) => (
            m.role === 'user' ? (
              <div key={i} style={{ alignSelf: 'flex-end', maxWidth: '80%', backgroundColor: 'var(--primary)', color: '#fff',
                                    fontFamily: 'var(--fb)', fontSize: 14, padding: '10px 14px', borderRadius: 'var(--radius-md)' }}>
                {m.content}
              </div>
            ) : m.role === 'assistant' ? (
              <AssistantMessage key={i} result={m.result} />
            ) : (
              <div key={i} role="alert" style={{ ...card, padding: '12px 16px', fontFamily: 'var(--fb)', fontSize: 13, color: 'var(--status-red)' }}>{m.content}</div>
            )
          ))}
          {busy && <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}><Spinner /><span style={muted}>Searching reviews…</span></div>}
          <div ref={endRef} />

          <form onSubmit={submit} style={{ ...card, padding: 12, display: 'flex', gap: 10, alignItems: 'center', position: 'sticky', bottom: 16 }}>
            <select value={scope} onChange={(e) => setScope(e.target.value)} aria-label="Competitor scope"
                    style={{ ...inputStyle, width: 'auto', minWidth: 150 }}>
              <option value="">All competitors</option>
              {competitors.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
            <input value={question} onChange={(e) => setQuestion(e.target.value)} maxLength={500} aria-label="Question"
                   placeholder="Ask about pricing, churn reasons, missing features…" style={{ ...inputStyle, flex: 1 }} />
            <button type="submit" style={{ ...btnGold, opacity: busy || question.trim().length < 3 ? 0.5 : 1 }}
                    disabled={busy || question.trim().length < 3}>Ask</button>
          </form>
        </div>
      </div>
    </div>
  )
}
