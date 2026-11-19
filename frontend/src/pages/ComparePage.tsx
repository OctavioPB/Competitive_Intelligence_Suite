import { useEffect, useState } from 'react'
import type { CSSProperties, ReactNode } from 'react'
import { api } from '../services/api'
import type { CompetitorComparison, Comparison } from '../services/api'
import type { Page } from '../App'
import Eyebrow from '../components/Eyebrow'
import Spinner from '../components/Spinner'
import Toast from '../components/Toast'
import StatusBadge from '../components/StatusBadge'
import { errorMessage, useToast } from '../hooks/useToast'
import { heroStyle, card, thStyle } from '../styles/shared'

// One colour per competitor, used by both the chart and the table header.
const SERIES = ['var(--chart-line)', 'var(--gold)', 'var(--status-purple)', 'var(--status-orange)', 'var(--status-green)']

const muted: CSSProperties = { fontFamily: 'var(--fb)', fontSize: 12, color: 'var(--mid)' }
const cellText: CSSProperties = { fontFamily: 'var(--fb)', fontSize: 13, color: 'var(--dark)' }

function signed(v: number | null, digits = 2) {
  if (v === null) return '—'
  // -0.001 must not print as "-0.00".
  if (Math.abs(v) < 0.5 * 10 ** -digits) return (0).toFixed(digits)
  return `${v > 0 ? '+' : ''}${v.toFixed(digits)}`
}

function SentimentOverlay({ competitors }: { competitors: CompetitorComparison[] }) {
  const months = Array.from(new Set(competitors.flatMap((c) => c.timeline.map((t) => t.month)))).sort()
  const values = competitors.flatMap((c) => c.timeline.map((t) => t.avg_sentiment))
  if (months.length < 2 || values.length === 0) return <div style={muted}>Not enough monthly data to chart.</div>

  const W = 760, H = 230, padL = 44, padR = 16, padT = 14, padB = 28
  const plotW = W - padL - padR, plotH = H - padT - padB
  const lo = Math.min(0, ...values) - 0.1
  const hi = Math.max(0, ...values) + 0.1
  const toY = (s: number) => padT + plotH * (1 - (s - lo) / (hi - lo))
  const toX = (m: string) => padL + (months.indexOf(m) / (months.length - 1)) * plotW
  const ticks = [hi, (hi + lo) / 2, lo].map((v) => Math.round(v * 10) / 10)

  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" style={{ display: 'block' }} role="img"
         aria-label="Monthly average sentiment per competitor">
      <line x1={padL} x2={W - padR} y1={toY(0)} y2={toY(0)} stroke="#9ca3af" strokeWidth={1} strokeDasharray="4 3" />
      {ticks.map((v) => (
        <text key={v} x={padL - 6} y={toY(v) + 4} textAnchor="end" fill="#6b7280" fontSize={9}
              fontFamily="'Plus Jakarta Sans', sans-serif">
          {v > 0 ? `+${v}` : v}
        </text>
      ))}
      {competitors.map((c, ci) => (
        <g key={c.name}>
          <polyline
            points={c.timeline.map((t) => `${toX(t.month).toFixed(1)},${toY(t.avg_sentiment).toFixed(1)}`).join(' ')}
            fill="none" style={{ stroke: SERIES[ci % SERIES.length] }} strokeWidth={2}
            strokeLinecap="round" strokeLinejoin="round"
          />
          {c.timeline.map((t) => (
            <circle key={t.month} cx={toX(t.month)} cy={toY(t.avg_sentiment)} r={3}
                    style={{ fill: SERIES[ci % SERIES.length] }}>
              <title>{`${c.name} · ${t.month}: ${signed(t.avg_sentiment)}`}</title>
            </circle>
          ))}
        </g>
      ))}
      {months.map((m, i) => (i % 2 === 0 || i === months.length - 1 ? (
        <text key={m} x={toX(m)} y={H - 6} textAnchor="middle" fill="#6b7280" fontSize={8}
              fontFamily="'Plus Jakarta Sans', sans-serif">{m}</text>
      ) : null))}
    </svg>
  )
}

/** Index of the min / max of a numeric row, ignoring nulls (null when < 2 values). */
function extremes(values: (number | null)[]) {
  const present = values.map((v, i) => [v, i] as const).filter(([v]) => v !== null) as [number, number][]
  if (present.length < 2) return { min: null, max: null }
  present.sort((a, b) => a[0] - b[0])
  return { min: present[0][1], max: present[present.length - 1][1] }
}

export default function ComparePage({ onNavigate }: { onNavigate?: (p: Page) => void }) {
  const [data, setData] = useState<Comparison | null>(null)
  const [loading, setLoading] = useState(true)
  const { toast, showToast } = useToast()

  useEffect(() => {
    api.insights
      .compare()
      .then(setData)
      .catch((err) => showToast(errorMessage(err, 'Could not load the comparison.'), 'error'))
      .finally(() => setLoading(false))
  }, [showToast])

  const cs = data?.competitors ?? []
  const sentiment = extremes(cs.map((c) => c.sentiment_30d))
  const change = extremes(cs.map((c) => c.sentiment_change))
  const rating = extremes(cs.map((c) => c.rating_30d))

  // Lowest sentiment / biggest drop / lowest rating = most vulnerable = most opportunity.
  const weak = (i: number, idx: number | null) =>
    idx === i ? { color: 'var(--status-red)', fontWeight: 600 } : {}

  const rows: { label: string; hint?: string; cell: (c: CompetitorComparison, i: number) => ReactNode }[] = [
    { label: 'Reviews (30 days)', cell: (c) => `${c.reviews_30d} of ${c.reviews_total}` },
    {
      label: 'Avg sentiment', hint: 'last 30 days',
      cell: (c, i) => <span style={weak(i, sentiment.min)}>{signed(c.sentiment_30d)}</span>,
    },
    {
      label: 'Sentiment change', hint: 'vs the 30 days before',
      cell: (c, i) => <span style={weak(i, change.min)}>{signed(c.sentiment_change)}</span>,
    },
    {
      label: 'Avg rating', hint: 'out of 5',
      cell: (c, i) => <span style={weak(i, rating.min)}>{c.rating_30d === null ? '—' : c.rating_30d.toFixed(2)}</span>,
    },
    {
      label: 'Top pain points',
      cell: (c) => c.pain_points.length === 0 ? <span style={muted}>—</span> : (
        <ol style={{ margin: 0, paddingLeft: 16 }}>
          {c.pain_points.map((p) => (
            <li key={p.topic} style={{ ...cellText, fontSize: 12, padding: '2px 0' }}>
              {p.topic} <span style={muted}>· {(p.severity * 100).toFixed(0)}% sev{p.trend === 'rising' ? ' · ↑' : ''}</span>
            </li>
          ))}
        </ol>
      ),
    },
    {
      label: 'Churn reasons', hint: 'from Churn Intel',
      cell: (c) => c.churn ? (
        <ol style={{ margin: 0, paddingLeft: 16 }}>
          {c.churn.map((b) => (
            <li key={b.label} style={{ ...cellText, fontSize: 12, padding: '2px 0' }}>
              {b.label} <span style={muted}>· {b.mention_pct.toFixed(0)}%</span>
            </li>
          ))}
        </ol>
      ) : (
        <span style={muted}>
          Not analysed yet
          {onNavigate && (
            <> — <button onClick={() => onNavigate('churn')} style={{ background: 'none', border: 'none', padding: 0, color: 'var(--link)', cursor: 'pointer', fontFamily: 'var(--fb)', fontSize: 12, textDecoration: 'underline' }}>run it</button></>
          )}
        </span>
      ),
    },
    { label: 'Active alerts', cell: (c) => String(c.active_alerts) },
    { label: 'Last price change', cell: (c) => c.last_price_change ?? <span style={muted}>none seen</span> },
    {
      label: 'Support share of new roles',
      cell: (c) => c.support_share === null ? <span style={muted}>no job data</span> : (
        <span style={c.support_share >= 0.25 ? { color: 'var(--status-red)', fontWeight: 600 } : {}}>
          {(c.support_share * 100).toFixed(0)}% <span style={muted}>of {c.new_roles}</span>
        </span>
      ),
    },
  ]

  return (
    <div>
      <div style={heroStyle}>
        <div style={{ maxWidth: 'var(--max-width-dashboard)', margin: '0 auto' }}>
          <Eyebrow light>Compare</Eyebrow>
          <h1 style={{ fontFamily: 'var(--fd)', fontSize: 36, fontWeight: 300, color: '#fff', margin: '0 0 6px', lineHeight: 1.2 }}>
            Competitors <em style={{ fontStyle: 'italic', color: 'var(--gold-light)' }}>side by side</em>
          </h1>
          <p style={{ fontFamily: 'var(--fb)', fontSize: 13, color: 'rgba(255,255,255,0.45)', maxWidth: 600 }}>
            Sentiment, pain points, churn reasons and market signals for every competitor in one
            view. The weakest value in each row is red — that is where the opening is.
          </p>
        </div>
      </div>

      <div style={{ backgroundColor: 'var(--light)', minHeight: '60vh' }}>
        <div style={{ maxWidth: 'var(--max-width-dashboard)', margin: '0 auto', padding: '44px 48px', display: 'flex', flexDirection: 'column', gap: 24 }}>
          {toast && <Toast message={toast.msg} type={toast.type} />}
          {loading && <Spinner />}

          {data && (
            <>
              <div style={{ ...card, padding: '22px 26px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', marginBottom: 12 }}>
                  <span style={{ fontFamily: 'var(--fb)', fontSize: 14, fontWeight: 600, color: 'var(--link)' }}>
                    Monthly sentiment
                  </span>
                  <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                    {cs.map((c, i) => (
                      <span key={c.name} style={{ ...muted, display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                        <span style={{ width: 14, height: 3, borderRadius: 2, backgroundColor: SERIES[i % SERIES.length] }} />
                        {c.name}
                      </span>
                    ))}
                  </div>
                </div>
                <SentimentOverlay competitors={cs} />
              </div>

              <div style={{ ...card, overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 720 }}>
                  <thead>
                    <tr style={{ backgroundColor: 'var(--primary)' }}>
                      <th style={{ ...thStyle, width: 190 }}>Metric</th>
                      {cs.map((c, i) => (
                        <th key={c.name} style={thStyle}>
                          {/* White ring: a navy series colour would vanish on the navy header. */}
                          <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', backgroundColor: SERIES[i % SERIES.length], boxShadow: '0 0 0 1.5px #fff', marginRight: 8 }} />
                          {c.name}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((row) => (
                      <tr key={row.label} style={{ borderTop: '1px solid var(--primary-10)' }}>
                        <td style={{ padding: '12px 14px', verticalAlign: 'top' }}>
                          <div style={{ ...cellText, fontWeight: 600, fontSize: 12 }}>{row.label}</div>
                          {row.hint && <div style={{ ...muted, fontSize: 11 }}>{row.hint}</div>}
                        </td>
                        {cs.map((c, i) => (
                          <td key={c.name} style={{ padding: '12px 14px', verticalAlign: 'top', ...cellText }}>
                            {row.cell(c, i)}
                          </td>
                        ))}
                      </tr>
                    ))}
                    <tr style={{ borderTop: '1px solid var(--primary-10)' }}>
                      <td style={{ padding: '12px 14px', ...cellText, fontWeight: 600, fontSize: 12 }}>Data</td>
                      {cs.map((c) => (
                        <td key={c.name} style={{ padding: '12px 14px' }}>
                          {c.synthetic_share > 0 ? (
                            <StatusBadge label={`${Math.round(c.synthetic_share * 100)}% sample`} color="var(--status-orange)" bg="var(--status-orange-bg)" />
                          ) : (
                            <span style={muted}>live · to {c.latest_date ?? '—'}</span>
                          )}
                        </td>
                      ))}
                    </tr>
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
