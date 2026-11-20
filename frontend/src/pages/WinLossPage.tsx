import { useCallback, useEffect, useRef, useState } from 'react'
import type { CSSProperties, FormEvent } from 'react'
import { api } from '../services/api'
import type { DealOutcome, WinLoss, WinLossCategory } from '../services/api'
import Eyebrow from '../components/Eyebrow'
import Spinner from '../components/Spinner'
import Toast from '../components/Toast'
import KpiCard from '../components/KpiCard'
import StatusBadge from '../components/StatusBadge'
import CompetitorSelect from '../components/CompetitorSelect'
import { errorMessage, useToast } from '../hooks/useToast'
import { useAppStore } from '../stores/appStore'
import { btnGhost, btnGold, card, heroStyle, inputStyle, labelStyle, thStyle } from '../styles/shared'

const READING: Record<NonNullable<WinLossCategory['reading']>, { label: string; color: string; bg: string }> = {
  contested: { label: 'Contested', color: 'var(--status-orange)', bg: 'var(--status-orange-bg)' },
  strength:  { label: 'Their strength', color: 'var(--status-red)', bg: 'var(--status-red-bg)' },
  proven:    { label: 'Proven angle', color: 'var(--status-green)', bg: 'var(--status-green-bg)' },
  untapped:  { label: 'Untapped', color: 'var(--status-purple)', bg: 'var(--status-purple-bg)' },
}

const muted: CSSProperties = { fontFamily: 'var(--fb)', fontSize: 12, color: 'var(--mid)' }
const today = () => new Date().toISOString().slice(0, 10)

function Bar({ share, color, label }: { share: number; color: string; label: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 140 }} title={label}>
      <div style={{ flex: 1, height: 8, borderRadius: 4, backgroundColor: 'var(--primary-10)' }}>
        <div style={{ width: `${Math.round(share * 100)}%`, height: '100%', borderRadius: 4, backgroundColor: color }} />
      </div>
      <span style={{ ...muted, width: 34, textAlign: 'right' }}>{Math.round(share * 100)}%</span>
    </div>
  )
}

function DealForm({ competitor, labels, onSaved, onError }: {
  competitor: string; labels: Record<string, string>; onSaved: () => void; onError: (m: string) => void
}) {
  const blank = { outcome: 'lost' as DealOutcome, reason_category: 'pricing', reason_text: '', deal_name: '', amount: '', closed_on: today() }
  const [f, setF] = useState(blank)
  const [busy, setBusy] = useState(false)

  function submit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    api.winloss
      .add({ competitor, ...f, amount: f.amount ? Number(f.amount) : null })
      .then(() => { setF({ ...blank, outcome: f.outcome }); onSaved() })
      .catch((err) => onError(errorMessage(err, 'Could not save the deal.')))
      .finally(() => setBusy(false))
  }

  return (
    <form onSubmit={submit} style={{ ...card, padding: '18px 22px', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12, alignItems: 'end' }}>
      <label style={labelStyle}>Outcome
        <select style={inputStyle} value={f.outcome} onChange={(e) => setF({ ...f, outcome: e.target.value as DealOutcome })}>
          <option value="lost">Lost to {competitor}</option>
          <option value="won">Won against {competitor}</option>
        </select>
      </label>
      <label style={labelStyle}>Main reason
        <select style={inputStyle} value={f.reason_category} onChange={(e) => setF({ ...f, reason_category: e.target.value })}>
          {Object.entries(labels).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
      </label>
      <label style={{ ...labelStyle, gridColumn: 'span 2' }}>In their words
        <input style={inputStyle} value={f.reason_text} maxLength={2000} placeholder="e.g. Needed CPQ out of the box"
               onChange={(e) => setF({ ...f, reason_text: e.target.value })} />
      </label>
      <label style={labelStyle}>Deal
        <input style={inputStyle} value={f.deal_name} maxLength={200} onChange={(e) => setF({ ...f, deal_name: e.target.value })} />
      </label>
      <label style={labelStyle}>Amount
        <input style={inputStyle} value={f.amount} inputMode="decimal" pattern="\d*(\.\d+)?" onChange={(e) => setF({ ...f, amount: e.target.value })} />
      </label>
      <label style={labelStyle}>Closed on
        <input style={inputStyle} type="date" value={f.closed_on} max={today()} required onChange={(e) => setF({ ...f, closed_on: e.target.value })} />
      </label>
      <button type="submit" style={btnGold} disabled={busy}>{busy ? 'Saving…' : 'Log deal'}</button>
    </form>
  )
}

export default function WinLossPage() {
  const { competitor } = useAppStore()
  const [data, setData] = useState<WinLoss | null>(null)
  const { toast, showToast } = useToast()
  const latest = useRef(0)

  const load = useCallback((name: string) => {
    const id = ++latest.current
    api.winloss.get(name)
      .then((d) => { if (id === latest.current) setData(d) })
      .catch((err) => { if (id === latest.current) showToast(errorMessage(err, 'Could not load win/loss.'), 'error') })
  }, [showToast])
  useEffect(() => { load(competitor) }, [competitor, load])

  function remove(id: number) {
    if (!window.confirm('Delete this deal?')) return
    api.winloss.remove(id).then(() => load(competitor)).catch((err) => showToast(errorMessage(err, 'Could not delete.'), 'error'))
  }

  return (
    <div>
      <div style={heroStyle}>
        <div style={{ maxWidth: 'var(--max-width-dashboard)', margin: '0 auto' }}>
          <Eyebrow light>Win / Loss</Eyebrow>
          <h1 style={{ fontFamily: 'var(--fd)', fontSize: 36, fontWeight: 300, color: '#fff', margin: '0 0 6px' }}>
            Why you <em style={{ fontStyle: 'italic', color: 'var(--gold-light)' }}>win and lose</em>
          </h1>
          <p style={{ fontFamily: 'var(--fb)', fontSize: 13, color: 'rgba(255,255,255,0.45)', maxWidth: 620 }}>
            Log why each deal against a competitor was won or lost, and see it next to what that
            competitor's own customers complain about.
          </p>
        </div>
      </div>

      <div style={{ backgroundColor: 'var(--light)', minHeight: '60vh' }}>
        <div style={{ maxWidth: 'var(--max-width-dashboard)', margin: '0 auto', padding: '44px 48px', display: 'flex', flexDirection: 'column', gap: 28 }}>
          <CompetitorSelect />
          {toast && <Toast message={toast.msg} type={toast.type} />}
          {!data ? <Spinner /> : (
            <>
              <DealForm competitor={competitor} labels={data.category_labels}
                        onSaved={() => { showToast('Deal logged.', 'success'); load(competitor) }}
                        onError={(m) => showToast(m, 'error')} />

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
                <KpiCard label="Deals logged" value={String(data.deals)} sub={data.is_synthetic ? 'includes sample deals' : `against ${data.competitor}`} />
                <KpiCard label="Win rate" value={data.win_rate === null ? '—' : `${Math.round(data.win_rate * 100)}%`}
                         sub={`${data.won} won · ${data.lost} lost`}
                         valueColor={data.win_rate !== null && data.win_rate < 0.5 ? 'var(--status-red)' : 'var(--status-green)'} />
                <KpiCard label="Revenue lost" value={data.amount_lost ? `$${Math.round(data.amount_lost).toLocaleString()}` : '—'} sub="sum of lost deal amounts" />
                <KpiCard label="Top loss reason" value={data.categories.slice().sort((a, b) => b.lost - a.lost)[0]?.lost ? data.categories.slice().sort((a, b) => b.lost - a.lost)[0].label : '—'} sub="most frequent" />
              </div>

              <section>
                <Eyebrow>Cross-check</Eyebrow>
                <h2 style={{ fontFamily: 'var(--fd)', fontSize: 22, fontWeight: 300, color: 'var(--dark)', margin: '0 0 6px' }}>
                  Deal reasons vs <em style={{ fontStyle: 'italic', color: 'var(--gold)' }}>review complaints</em>
                </h2>
                <p style={{ ...muted, margin: '0 0 14px' }}>
                  Share of lost and won deals per reason, next to the share of {data.competitor}'s review complaints in the same area.
                </p>
                {data.categories.length === 0 ? (
                  <div style={{ ...card, padding: 24, ...muted }}>No deals logged and no processed reviews yet for {data.competitor}.</div>
                ) : (
                  <div style={{ ...card, overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 820 }}>
                      <thead><tr style={{ backgroundColor: 'var(--primary)' }}>
                        <th style={thStyle}>Area</th><th style={thStyle}>Lost deals</th><th style={thStyle}>Won deals</th>
                        <th style={thStyle}>Their customers complain</th><th style={thStyle}>What it means</th>
                      </tr></thead>
                      <tbody>
                        {data.categories.map((c) => (
                          <tr key={c.category} style={{ borderTop: '1px solid var(--primary-10)', verticalAlign: 'top' }}>
                            <td style={{ padding: '12px 14px', fontFamily: 'var(--fb)', fontSize: 13, fontWeight: 600, color: 'var(--dark)' }}>
                              {c.label}
                              <div style={{ ...muted, fontWeight: 400, fontSize: 11 }}>{c.lost} lost · {c.won} won</div>
                            </td>
                            <td style={{ padding: '12px 14px' }}><Bar share={c.lost_share} color="var(--status-red)" label="share of lost deals" /></td>
                            <td style={{ padding: '12px 14px' }}><Bar share={c.won_share} color="var(--status-green)" label="share of won deals" /></td>
                            <td style={{ padding: '12px 14px' }}>
                              <Bar share={c.review_share} color="var(--gold)" label="share of review complaints" />
                              {c.review_topics.length > 0 && <div style={{ ...muted, fontSize: 11, marginTop: 4 }}>{c.review_topics.join(' · ')}</div>}
                            </td>
                            <td style={{ padding: '12px 14px', maxWidth: 320 }}>
                              {c.reading ? (
                                <>
                                  <StatusBadge {...READING[c.reading]} />
                                  <div style={{ fontFamily: 'var(--fb)', fontSize: 12, color: 'var(--dark)', marginTop: 6, lineHeight: 1.5 }}>{c.reading_text}</div>
                                </>
                              ) : <span style={muted}>—</span>}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </section>

              <section>
                <Eyebrow>Log</Eyebrow>
                <h2 style={{ fontFamily: 'var(--fd)', fontSize: 22, fontWeight: 300, color: 'var(--dark)', margin: '0 0 14px' }}>Recent deals</h2>
                {data.recent.length === 0 ? <div style={{ ...card, padding: 24, ...muted }}>No deals logged yet.</div> : (
                  <div style={{ ...card, overflow: 'hidden' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                      <tbody>
                        {data.recent.map((d) => (
                          <tr key={d.id} style={{ borderTop: '1px solid var(--primary-10)' }}>
                            <td style={{ padding: '10px 14px', width: 90 }}>
                              <StatusBadge label={d.outcome === 'won' ? 'Won' : 'Lost'}
                                           color={d.outcome === 'won' ? 'var(--status-green)' : 'var(--status-red)'}
                                           bg={d.outcome === 'won' ? 'var(--status-green-bg)' : 'var(--status-red-bg)'} />
                            </td>
                            <td style={{ padding: '10px 14px', fontFamily: 'var(--fb)', fontSize: 13, color: 'var(--dark)' }}>
                              <strong style={{ fontWeight: 600 }}>{d.deal_name || 'Unnamed deal'}</strong> · {d.reason_label}
                              {d.reason_text && <div style={muted}>“{d.reason_text}”</div>}
                            </td>
                            <td style={{ padding: '10px 14px', ...muted, whiteSpace: 'nowrap' }}>
                              {d.amount ? `$${Math.round(d.amount).toLocaleString()} · ` : ''}{d.closed_on}
                              {d.is_synthetic && <> · <StatusBadge label="Sample" color="var(--status-orange)" bg="var(--status-orange-bg)" /></>}
                            </td>
                            <td style={{ padding: '10px 14px', textAlign: 'right' }}>
                              <button style={btnGhost} onClick={() => remove(d.id)} aria-label={`Delete deal ${d.deal_name ?? d.id}`}>Delete</button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </section>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
