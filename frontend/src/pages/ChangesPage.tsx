import { useCallback, useEffect, useRef, useState } from 'react'
import type { CSSProperties, ReactNode } from 'react'
import { api } from '../services/api'
import type { Changes, TopicMove, WindowStats } from '../services/api'
import Eyebrow from '../components/Eyebrow'
import Spinner from '../components/Spinner'
import Toast from '../components/Toast'
import CompetitorSelect from '../components/CompetitorSelect'
import { errorMessage, useToast } from '../hooks/useToast'
import { useAppStore } from '../stores/appStore'
import { heroStyle, card } from '../styles/shared'

const WINDOWS = [7, 14, 30] as const

const muted: CSSProperties = { fontFamily: 'var(--fb)', fontSize: 12, color: 'var(--mid)' }
const label: CSSProperties = { ...muted, fontSize: 10, letterSpacing: '2px', textTransform: 'uppercase' }
const body: CSSProperties = { fontFamily: 'var(--fb)', fontSize: 13, color: 'var(--dark)', lineHeight: 1.55 }

function Card({ title, children, note }: { title: string; children: ReactNode; note?: string }) {
  return (
    <div style={{ ...card, padding: '22px 26px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, marginBottom: 14, flexWrap: 'wrap' }}>
        <span style={{ fontFamily: 'var(--fb)', fontSize: 14, fontWeight: 600, color: 'var(--link)' }}>{title}</span>
        {note && <span style={muted}>{note}</span>}
      </div>
      {children}
    </div>
  )
}

/** "before → after" with the change coloured; higherIsBetter decides red/green. */
function Delta({ before, after, digits = 2, higherIsBetter = true, signed = false }: {
  before: number | null; after: number | null; digits?: number; higherIsBetter?: boolean; signed?: boolean
}) {
  const fmt = (v: number | null) =>
    v === null ? '—' : signed && v > 0 ? `+${v.toFixed(digits)}` : v.toFixed(digits)
  const diff = before !== null && after !== null ? after - before : null
  const good = diff !== null && (higherIsBetter ? diff > 0 : diff < 0)
  const color = diff === null || Math.abs(diff) < 10 ** -digits ? 'var(--mid)' : good ? 'var(--status-green)' : 'var(--status-red)'
  return (
    <span style={{ fontFamily: 'var(--fb)', fontSize: 13 }}>
      <span style={{ color: 'var(--mid)' }}>{fmt(before)}</span>
      <span style={{ color: 'var(--gold)', margin: '0 6px' }}>→</span>
      <strong style={{ color: 'var(--dark)', fontWeight: 600 }}>{fmt(after)}</strong>
      {diff !== null && (
        <span style={{ color, marginLeft: 8, fontSize: 12 }}>
          ({diff > 0 ? '+' : ''}{diff.toFixed(digits)})
        </span>
      )}
    </span>
  )
}

function ReviewStats({ current, previous }: { current: WindowStats; previous: WindowStats }) {
  const rows: [string, ReactNode][] = [
    ['Reviews', <Delta key="n" before={previous.reviews} after={current.reviews} digits={0} higherIsBetter={false} />],
    ['Avg sentiment', <Delta key="s" before={previous.sentiment} after={current.sentiment} signed />],
    ['Avg rating', <Delta key="r" before={previous.rating} after={current.rating} />],
  ]
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {rows.map(([name, value]) => (
        <div key={name} style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
          <span style={muted}>{name}</span>
          {value}
        </div>
      ))}
      <span style={{ ...muted, fontSize: 11 }}>
        More reviews is shown in red: for a competitor, a jump in reviews is usually a jump in complaints.
      </span>
    </div>
  )
}

function TopicList({ title, items, color }: { title: string; items: TopicMove[]; color: string }) {
  return (
    <div>
      <div style={{ ...label, color, marginBottom: 6 }}>{title}</div>
      {items.length === 0 ? (
        <span style={muted}>None</span>
      ) : (
        <ul style={{ margin: 0, padding: 0 }}>
          {items.map((t) => (
            <li key={t.topic} style={{ listStyle: 'none', ...body, fontSize: 12, padding: '3px 0' }}>
              {t.topic} <span style={muted}>· {t.previous} → {t.current}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function DiffList({ added, removed, what }: { added: string[]; removed: string[]; what: string }) {
  if (!added.length && !removed.length) return <div style={muted}>No {what} added or removed.</div>
  return (
    <ul style={{ margin: 0, padding: 0 }}>
      {added.map((x) => (
        <li key={`+${x}`} style={{ listStyle: 'none', ...body, fontSize: 12, padding: '3px 0' }}>
          <strong style={{ color: 'var(--status-green)', marginRight: 6 }}>+</strong>{x}
        </li>
      ))}
      {removed.map((x) => (
        <li key={`-${x}`} style={{ listStyle: 'none', ...body, fontSize: 12, padding: '3px 0', color: 'var(--mid)', textDecoration: 'line-through' }}>
          <strong style={{ color: 'var(--status-red)', marginRight: 6, textDecoration: 'none', display: 'inline-block' }}>−</strong>{x}
        </li>
      ))}
    </ul>
  )
}

export default function ChangesPage() {
  const { competitor } = useAppStore()
  const [days, setDays] = useState<number>(7)
  const [data, setData] = useState<Changes | null>(null)
  const [loading, setLoading] = useState(false)
  const { toast, showToast } = useToast()
  const latest = useRef(0)

  const load = useCallback((name: string, window: number) => {
    const id = ++latest.current
    setLoading(true)
    api.insights
      .changes(name, window)
      .then((d) => { if (id === latest.current) setData(d) })
      .catch((err) => { if (id === latest.current) showToast(errorMessage(err, 'Could not load changes.'), 'error') })
      .finally(() => { if (id === latest.current) setLoading(false) })
  }, [showToast])

  useEffect(() => { load(competitor, days) }, [competitor, days, load])

  const r = data?.reviews
  const bc = data?.battlecard
  const dg = data?.digest

  return (
    <div>
      <div style={heroStyle}>
        <div style={{ maxWidth: 'var(--max-width-dashboard)', margin: '0 auto' }}>
          <Eyebrow light>What Changed</Eyebrow>
          <h1 style={{ fontFamily: 'var(--fd)', fontSize: 36, fontWeight: 300, color: '#fff', margin: '0 0 6px', lineHeight: 1.2 }}>
            Since <em style={{ fontStyle: 'italic', color: 'var(--gold-light)' }}>last week</em>
          </h1>
          <p style={{ fontFamily: 'var(--fb)', fontSize: 13, color: 'rgba(255,255,255,0.45)', maxWidth: 600 }}>
            Reviews, battlecard, digest, alerts, pricing and hiring — this period against the
            one before, so the Monday meeting starts from what is new.
          </p>
        </div>
      </div>

      <div style={{ backgroundColor: 'var(--light)', minHeight: '60vh' }}>
        <div style={{ maxWidth: 'var(--max-width-dashboard)', margin: '0 auto', padding: '44px 48px', display: 'flex', flexDirection: 'column', gap: 24 }}>
          <div style={{ display: 'flex', gap: 16, alignItems: 'flex-end', flexWrap: 'wrap' }}>
            <CompetitorSelect />
            <div>
              <div style={{ ...label, marginBottom: 6 }}>Compare windows</div>
              <div style={{ display: 'flex', gap: 6 }}>
                {WINDOWS.map((w) => (
                  <button
                    key={w}
                    onClick={() => setDays(w)}
                    style={{
                      fontFamily: 'var(--fb)', fontSize: 12, padding: '7px 12px', cursor: 'pointer',
                      borderRadius: 'var(--radius-sm)', border: '1px solid',
                      borderColor: days === w ? 'var(--primary)' : 'var(--primary-10)',
                      backgroundColor: days === w ? 'var(--primary)' : 'var(--white)',
                      color: days === w ? '#fff' : 'var(--dark)', fontWeight: days === w ? 600 : 400,
                    }}
                  >
                    {w} days
                  </button>
                ))}
              </div>
            </div>
          </div>

          {toast && <Toast message={toast.msg} type={toast.type} />}
          {loading && !data && <Spinner />}

          {data && r && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20, opacity: loading ? 0.6 : 1, transition: 'opacity 0.2s' }}>
              {/* Highlights */}
              <div style={{ ...card, padding: '22px 26px', borderLeft: '3px solid var(--gold)' }}>
                <div style={{ ...label, color: 'var(--gold)', marginBottom: 10 }}>
                  {data.competitor} · last {data.window_days} days{r.anchor_date ? ` to ${r.anchor_date}` : ''}
                </div>
                {data.highlights.length ? (
                  <ul style={{ margin: 0, padding: 0 }}>
                    {data.highlights.map((h) => (
                      <li key={h} style={{ listStyle: 'none', ...body, padding: '4px 0 4px 16px', position: 'relative' }}>
                        <span style={{ position: 'absolute', left: 0, color: 'var(--gold)' }}>•</span>{h}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <span style={muted}>Nothing notable changed in this period.</span>
                )}
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: 20 }}>
                <Card title="Reviews" note={`${data.window_days} days vs the ${data.window_days} before`}>
                  <ReviewStats current={r.current} previous={r.previous} />
                </Card>
                <Card title="Complaint topics">
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14 }}>
                    <TopicList title="New" items={r.topics.new} color="var(--status-red)" />
                    <TopicList title="Rising" items={r.topics.rising} color="var(--status-orange)" />
                    <TopicList title="Fading" items={r.topics.fading} color="var(--status-green)" />
                  </div>
                </Card>
              </div>

              <Card
                title="Battlecard"
                note={bc ? (bc.previous_date ? `${bc.current_date} vs ${bc.previous_date}` : `Only version: ${bc.current_date}`) : undefined}
              >
                {!bc ? (
                  <span style={muted}>No battlecard generated yet for {data.competitor}.</span>
                ) : !bc.previous_date ? (
                  <span style={muted}>Only one version so far — the next generated battlecard will be compared with this one.</span>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                    <div>
                      <div style={{ ...label, marginBottom: 6 }}>Recommended pitch {bc.pitch_changed ? '— changed' : '— unchanged'}</div>
                      {bc.pitch_changed ? (
                        <>
                          <p style={{ ...body, fontSize: 12, color: 'var(--mid)', textDecoration: 'line-through', margin: '0 0 6px' }}>{bc.pitch_before}</p>
                          <p style={{ ...body, margin: 0 }}>{bc.pitch_after}</p>
                        </>
                      ) : (
                        <p style={{ ...body, margin: 0 }}>{bc.pitch_after}</p>
                      )}
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 16 }}>
                      <div>
                        <div style={{ ...label, marginBottom: 6 }}>Objections</div>
                        <DiffList added={bc.objections_added} removed={bc.objections_removed} what="objections" />
                      </div>
                      <div>
                        <div style={{ ...label, marginBottom: 6 }}>Feature gaps</div>
                        <DiffList added={bc.gaps_added} removed={bc.gaps_removed} what="feature gaps" />
                      </div>
                    </div>
                  </div>
                )}
              </Card>

              <Card
                title="Weekly digest"
                note={dg ? (dg.previous_at ? `${dg.current_at.slice(0, 10)} vs ${dg.previous_at.slice(0, 10)}` : `Only digest: ${dg.current_at.slice(0, 10)}`) : undefined}
              >
                {!dg ? (
                  <span style={muted}>No digest stored yet.</span>
                ) : !dg.previous_at || !dg.before || !dg.after ? (
                  <span style={muted}>One digest so far — next week's will be compared with it.</span>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                      <span style={muted}>Top pain</span>
                      <span style={{ fontFamily: 'var(--fb)', fontSize: 13 }}>
                        <span style={{ color: 'var(--mid)' }}>{dg.before.top_pain}</span>
                        <span style={{ color: 'var(--gold)', margin: '0 6px' }}>→</span>
                        <strong style={{ fontWeight: 600, color: 'var(--dark)' }}>{dg.after.top_pain}</strong>
                      </span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                      <span style={muted}>Sentiment delta</span>
                      <Delta before={dg.before.sentiment_delta} after={dg.after.sentiment_delta} signed />
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                      <span style={muted}>Signal</span>
                      <span style={{ fontFamily: 'var(--fb)', fontSize: 13, color: 'var(--dark)' }}>
                        {dg.before.sentiment_signal} → <strong style={{ fontWeight: 600 }}>{dg.after.sentiment_signal}</strong>
                      </span>
                    </div>
                    {dg.after.summary && <p style={{ ...body, fontSize: 12, margin: 0, color: 'var(--mid)' }}>{dg.after.summary}</p>}
                  </div>
                )}
              </Card>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 20 }}>
                <Card title="New alerts" note={`first detected in the last ${data.window_days} days`}>
                  {data.alerts.length === 0 ? (
                    <span style={muted}>None. Alerts appear here once a scan has detected them.</span>
                  ) : (
                    <ul style={{ margin: 0, padding: 0 }}>
                      {data.alerts.map((a) => (
                        <li key={a.id ?? a.evidence_summary} style={{ listStyle: 'none', ...body, fontSize: 12, padding: '5px 0', borderTop: '1px solid var(--primary-10)' }}>
                          <strong style={{ fontWeight: 600 }}>{a.trigger_type.replace('_', ' ')}</strong>
                          <span style={muted}> · {a.first_seen} · {a.status}</span>
                          <div style={{ color: 'var(--mid)' }}>{a.evidence_summary.slice(0, 140)}</div>
                        </li>
                      ))}
                    </ul>
                  )}
                </Card>
                <Card title="Pricing & hiring">
                  {data.pricing.length === 0 && !data.hiring ? (
                    <span style={muted}>No pricing change and no new roles in this period.</span>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                      {data.pricing.map((p) => (
                        <div key={p.url}>
                          <div style={{ ...label, color: 'var(--status-green)', marginBottom: 4 }}>Price change · {p.date}</div>
                          {p.changes.map((c) => <div key={c} style={{ ...body, fontSize: 12 }}>{c}</div>)}
                        </div>
                      ))}
                      {data.hiring && (
                        <div style={{ ...body, fontSize: 12 }}>
                          <strong style={{ fontWeight: 600 }}>{data.hiring.new_roles}</strong> new roles posted ·{' '}
                          {data.hiring.support} support · {data.hiring.integration} integration engineering
                        </div>
                      )}
                    </div>
                  )}
                </Card>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
