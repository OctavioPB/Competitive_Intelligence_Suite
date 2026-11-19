import { useCallback, useEffect, useState } from 'react'
import type { CSSProperties } from 'react'
import { api } from '../services/api'
import type { Alert, AlertStatus } from '../services/api'
import Eyebrow from '../components/Eyebrow'
import Spinner from '../components/Spinner'
import Toast from '../components/Toast'
import { errorMessage, useToast } from '../hooks/useToast'
import KpiCard from '../components/KpiCard'
import StatusBadge from '../components/StatusBadge'
import { heroStyle, btnGold, btnNavy } from '../styles/shared'

// Badge uses semantic status tokens. Alert card border is always gold (structural rule).
const BADGE_MAP: Record<string, { label: string; color: string; bg: string }> = {
  sentiment_drop: { label: 'Sentiment Drop', color: 'var(--status-red)', bg: 'var(--status-red-bg)' },
  negative_news: { label: 'Negative News', color: 'var(--status-orange)', bg: 'var(--status-orange-bg)' },
  review_spike: { label: 'Review Spike', color: 'var(--status-purple)', bg: 'var(--status-purple-bg)' },
  pricing_change: { label: 'Pricing Change', color: 'var(--status-green)', bg: 'var(--status-green-bg)' },
  hiring_signal: { label: 'Hiring Signal', color: 'var(--primary-60)', bg: 'var(--primary-10)' },
}

const STATUS_LABEL: Record<AlertStatus, string> = { new: 'New', seen: 'Seen', dismissed: 'Dismissed' }

type View = 'active' | 'history'

const smallBtn: CSSProperties = {
  background: 'none',
  border: '1px solid var(--primary-10)',
  borderRadius: 'var(--radius-sm)',
  fontFamily: 'var(--fb)',
  fontSize: 11,
  color: 'var(--link)',
  cursor: 'pointer',
  padding: '4px 12px',
}

function chip(active: boolean): CSSProperties {
  return {
    ...smallBtn,
    fontWeight: active ? 600 : 400,
    color: active ? '#fff' : 'var(--link)',
    backgroundColor: active ? 'var(--primary)' : 'transparent',
    borderColor: active ? 'var(--primary)' : 'var(--primary-10)',
  }
}

function StatusPill({ status }: { status: AlertStatus }) {
  const style: Record<AlertStatus, CSSProperties> = {
    new: { color: '#fff', backgroundColor: 'var(--gold)' },
    seen: { color: 'var(--mid)', backgroundColor: 'var(--primary-10)' },
    dismissed: { color: 'var(--mid)', backgroundColor: 'transparent', border: '1px dashed var(--mid)' },
  }
  return (
    <span style={{
      fontFamily: 'var(--fb)', fontSize: 9, fontWeight: 700, letterSpacing: '1.5px',
      textTransform: 'uppercase', padding: '2px 8px', borderRadius: 'var(--radius-pill)', ...style[status],
    }}>
      {STATUS_LABEL[status]}
    </span>
  )
}

function AlertCard({ alert, onChange }: { alert: Alert; onChange: (a: Alert) => void }) {
  const [draft, setDraft] = useState<string | null>(alert.outreach_draft)
  const [expanded, setExpanded] = useState(false)
  const [loadingDraft, setLoadingDraft] = useState(false)
  const [saving, setSaving] = useState(false)
  const { toast, showToast } = useToast()

  const badge = BADGE_MAP[alert.trigger_type] ?? {
    label: alert.trigger_type,
    color: 'var(--primary-60)',
    bg: 'var(--primary-10)',
  }
  const stored = typeof alert.id === 'number' && alert.status
  const dismissed = alert.status === 'dismissed'

  function setStatus(status: AlertStatus) {
    if (typeof alert.id !== 'number') return
    setSaving(true)
    api.alerts
      .setStatus(alert.id, status)
      .then((updated) => onChange({ ...alert, ...updated, timestamp: alert.timestamp }))
      .catch((err) => showToast(errorMessage(err, 'Could not update the alert.'), 'error'))
      .finally(() => setSaving(false))
  }

  function requestDraft(useLlm: boolean) {
    setLoadingDraft(true)
    api.alerts
      .outreach(alert, useLlm)
      .then((r) => {
        setDraft(r.draft)
        setExpanded(true)
        if (alert.status === 'new') setStatus('seen')   // drafting outreach means it was read
      })
      .catch((err) => showToast(errorMessage(err, 'Could not draft outreach.'), 'error'))
      .finally(() => setLoadingDraft(false))
  }

  const seenText = stored && alert.first_seen
    ? alert.first_seen === alert.last_seen
      ? `First seen ${alert.first_seen}`
      : `First seen ${alert.first_seen} · still active ${alert.last_seen} (${alert.times_seen} checks)`
    : `${alert.timestamp.replace('T', ' ').slice(0, 16)} UTC`

  return (
    <div
      style={{
        backgroundColor: 'var(--white)',
        borderRadius: 'var(--radius-md)',
        padding: '20px 24px',
        marginBottom: 14,
        boxShadow: 'var(--shadow-card)',
        border: '1px solid var(--primary-10)',
        borderLeft: '3px solid var(--gold)',
        opacity: dismissed ? 0.6 : 1,
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10, gap: 12, flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <StatusBadge label={badge.label} color={badge.color} bg={badge.bg} />
          {stored && <StatusPill status={alert.status as AlertStatus} />}
        </div>
        <span style={{ fontFamily: 'var(--fb)', fontSize: 11, color: 'var(--mid)' }}>{seenText}</span>
      </div>

      {/* Competitor */}
      <div style={{ fontFamily: 'var(--fb)', fontWeight: 600, fontSize: 14, color: 'var(--link)', marginBottom: 6 }}>
        {alert.competitor}
      </div>

      {/* Evidence */}
      <div style={{ fontFamily: 'var(--fb)', fontSize: 13, color: 'var(--dark)', lineHeight: 1.5, marginBottom: 14 }}>
        {alert.evidence_summary}
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', alignItems: 'flex-start' }}>
        {/* Outreach section */}
        {draft ? (
          <div style={{ flex: 1, minWidth: 260 }}>
            <button onClick={() => setExpanded((o) => !o)} style={{ ...smallBtn, marginBottom: expanded ? 10 : 0 }}>
              {expanded ? 'Hide' : 'View'} outreach draft ▾
            </button>
            {expanded && (
              <textarea
                value={draft}
                readOnly
                rows={7}
                style={{
                  width: '100%',
                  fontFamily: 'var(--fb)',
                  fontSize: 12,
                  color: 'var(--dark)',
                  border: '1px solid var(--primary-10)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '10px 12px',
                  backgroundColor: 'var(--light)',
                  resize: 'vertical',
                }}
              />
            )}
          </div>
        ) : (
          <div style={{ display: 'flex', gap: 10 }}>
            {loadingDraft ? (
              <Spinner />
            ) : (
              <>
                <button style={btnNavy} onClick={() => requestDraft(false)}>Template Draft</button>
                <button style={btnGold} onClick={() => requestDraft(true)}>Claude Draft</button>
              </>
            )}
          </div>
        )}

        {/* Workflow */}
        {stored && (
          <div style={{ display: 'flex', gap: 8 }}>
            {alert.status === 'new' && (
              <button style={smallBtn} disabled={saving} onClick={() => setStatus('seen')}>Mark seen</button>
            )}
            {dismissed ? (
              <button style={smallBtn} disabled={saving} onClick={() => setStatus('seen')}>Restore</button>
            ) : (
              <button style={smallBtn} disabled={saving} onClick={() => setStatus('dismissed')}
                      title="Hide this alert while the signal lasts">
                Dismiss
              </button>
            )}
          </div>
        )}
      </div>
      {toast && <Toast message={toast.msg} type={toast.type} />}
    </div>
  )
}

export default function TriggerAlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [view, setView] = useState<View>('active')
  const [historyFilter, setHistoryFilter] = useState<AlertStatus | 'all'>('all')
  const [history, setHistory] = useState<Alert[]>([])
  const [counts, setCounts] = useState<Record<AlertStatus, number>>({ new: 0, seen: 0, dismissed: 0 })
  const [showDismissed, setShowDismissed] = useState(false)
  const [isDemoScenario, setIsDemoScenario] = useState(false)
  const [loading, setLoading] = useState(false)
  const { toast, showToast } = useToast()

  const refreshHistory = useCallback(() => {
    return api.alerts
      .history(historyFilter === 'all' ? {} : { status: historyFilter })
      .then((h) => { setHistory(h.alerts); setCounts(h.counts) })
      .catch(() => {/* history is optional — the feed still works */})
  }, [historyFilter])

  // On open, show what is already active instead of an empty page.
  useEffect(() => {
    setLoading(true)
    api.alerts
      .history({ active: true })
      .then((h) => { setAlerts(h.alerts); setCounts(h.counts) })
      .catch(() => {/* no history yet */})
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { if (view === 'history') refreshHistory() }, [view, refreshHistory])

  function handleScan() {
    setLoading(true)
    setIsDemoScenario(false)
    api.alerts
      .scan()
      .then((found) => {
        setAlerts(found)
        const fresh = found.filter((a) => a.is_new).length
        showToast(
          fresh ? `${fresh} new alert${fresh === 1 ? '' : 's'} — ${found.length - fresh} already known.`
                : `No new alerts — ${found.length} still active.`,
          'success',
        )
        return refreshHistory()
      })
      .catch((err) => showToast(errorMessage(err, 'Alert scan failed. Is the backend running?'), 'error'))
      .finally(() => setLoading(false))
  }

  function handleDemo() {
    setLoading(true)
    setIsDemoScenario(true)
    setView('active')
    api.alerts
      .demo()
      .then(setAlerts)
      .catch((err) => showToast(errorMessage(err, 'Could not load demo alerts.'), 'error'))
      .finally(() => setLoading(false))
  }

  function handleMarkAllSeen() {
    api.alerts
      .markAllSeen()
      .then((r) => {
        setAlerts((list) => list.map((a) => (a.status === 'new' ? { ...a, status: 'seen' } : a)))
        showToast(`${r.updated} alert${r.updated === 1 ? '' : 's'} marked as seen.`, 'success')
        return refreshHistory()
      })
      .catch((err) => showToast(errorMessage(err, 'Could not update alerts.'), 'error'))
  }

  function handleChange(updated: Alert) {
    const swap = (list: Alert[]) => list.map((a) => (a.id === updated.id ? { ...a, ...updated } : a))
    setAlerts(swap)
    setHistory(swap)
    api.alerts.history({ active: true }).then((h) => setCounts(h.counts)).catch(() => {})
  }

  const visible = alerts.filter((a) => showDismissed || a.status !== 'dismissed')
  const hiddenCount = alerts.length - visible.length
  const live = alerts.filter((a) => a.status !== 'dismissed')
  const count = (t: string) => live.filter((a) => a.trigger_type === t).length
  const newCount = live.filter((a) => a.status === 'new').length

  const sorted = [...visible].sort((a, b) =>
    Number(b.status === 'new') - Number(a.status === 'new') || b.timestamp.localeCompare(a.timestamp),
  )

  return (
    <div>
      {/* ── Hero ─────────────────────────────────────────────────────────── */}
      <div style={heroStyle}>
        <div style={{ maxWidth: 'var(--max-width-dashboard)', margin: '0 auto' }}>
          <Eyebrow light>Trigger Alerts</Eyebrow>
          <h1 style={{ fontFamily: 'var(--fd)', fontSize: 36, fontWeight: 300, color: '#ffffff', margin: '0 0 6px' }}>
            Trigger{' '}
            <em style={{ fontStyle: 'italic', color: 'var(--gold-light)' }}>Alerts</em>
          </h1>
          <p style={{ fontFamily: 'var(--fb)', fontSize: 13, color: 'rgba(255,255,255,0.45)', maxWidth: 560 }}>
            Real-time competitor vulnerability signals — sentiment drops, negative
            news, review spikes, pricing changes and hiring waves — with
            pre-drafted outreach ready to send. Every alert is kept with its status,
            so an ongoing signal is reported once, not every day.
          </p>
        </div>
      </div>

      {/* ── Body ─────────────────────────────────────────────────────────── */}
      <div style={{ backgroundColor: 'var(--light)', minHeight: '60vh' }}>
        <div style={{ maxWidth: 'var(--max-width-dashboard)', margin: '0 auto', padding: '44px 48px', display: 'flex', flexDirection: 'column', gap: 32 }}>
          {/* Controls */}
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
            <button style={btnNavy} onClick={handleScan} disabled={loading}>Scan All Competitors</button>
            <button style={btnGold} onClick={handleDemo} disabled={loading}>Simulate Bad Week</button>
            <div style={{ flex: 1 }} />
            <button style={chip(view === 'active')} onClick={() => setView('active')}>
              Active{newCount ? ` · ${newCount} new` : ''}
            </button>
            <button style={chip(view === 'history')} onClick={() => setView('history')}>
              History ({counts.new + counts.seen + counts.dismissed})
            </button>
          </div>

          {toast && <Toast message={toast.msg} type={toast.type} />}
          {loading && <Spinner />}

          {view === 'active' && !loading && alerts.length === 0 && (
            <div style={{ fontFamily: 'var(--fb)', fontSize: 13, color: 'var(--mid)', padding: '24px', backgroundColor: 'var(--white)', borderRadius: 'var(--radius-md)', border: '1px solid var(--primary-10)' }}>
              No active alerts. Click <strong>Scan All Competitors</strong> to check
              for live signals, or <strong>Simulate Bad Week</strong> to preview a
              demo scenario.
            </div>
          )}

          {view === 'active' && !loading && alerts.length > 0 && (
            <>
              {/* KPIs */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
                <KpiCard label="Active Alerts" value={String(live.length)}
                         sub={isDemoScenario ? 'demo scenario (not stored)' : `${newCount} new · ${counts.dismissed} dismissed`} />
                <KpiCard label="Sentiment Drops" value={String(count('sentiment_drop'))} sub="competitors declining" valueColor="var(--status-red)" />
                <KpiCard label="Negative News" value={String(count('negative_news'))} sub="press events flagged" valueColor="var(--status-orange)" />
                <KpiCard label="Review Spikes" value={String(count('review_spike'))} sub="unusual volume" valueColor="var(--gold)" />
                <KpiCard label="Pricing Changes" value={String(count('pricing_change'))} sub="pricing pages edited" valueColor="var(--status-green)" />
                <KpiCard label="Hiring Signals" value={String(count('hiring_signal'))} sub="support / integration waves" />
              </div>

              {/* Alert feed */}
              <section>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', gap: 12, flexWrap: 'wrap', marginBottom: 20 }}>
                  <div>
                    <Eyebrow>Alert Feed</Eyebrow>
                    <h2 style={{ fontFamily: 'var(--fd)', fontSize: 22, fontWeight: 300, color: 'var(--dark)', margin: 0 }}>
                      Latest <em style={{ fontStyle: 'italic', color: 'var(--gold)' }}>vulnerability signals</em>
                    </h2>
                  </div>
                  <div style={{ display: 'flex', gap: 8 }}>
                    {hiddenCount > 0 && (
                      <button style={smallBtn} onClick={() => setShowDismissed((s) => !s)}>
                        {showDismissed ? 'Hide' : 'Show'} dismissed ({hiddenCount})
                      </button>
                    )}
                    {newCount > 0 && <button style={smallBtn} onClick={handleMarkAllSeen}>Mark all seen</button>}
                  </div>
                </div>
                {sorted.map((alert, i) => (
                  <AlertCard key={alert.id ?? `${alert.competitor}-${alert.trigger_type}-${i}`} alert={alert} onChange={handleChange} />
                ))}
              </section>
            </>
          )}

          {view === 'history' && (
            <section>
              <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
                {(['all', 'new', 'seen', 'dismissed'] as const).map((f) => (
                  <button key={f} style={chip(historyFilter === f)} onClick={() => setHistoryFilter(f)}>
                    {f === 'all' ? 'All' : STATUS_LABEL[f]} ({f === 'all' ? counts.new + counts.seen + counts.dismissed : counts[f]})
                  </button>
                ))}
              </div>
              {history.length === 0 ? (
                <div style={{ fontFamily: 'var(--fb)', fontSize: 13, color: 'var(--mid)', padding: 24, backgroundColor: 'var(--white)', borderRadius: 'var(--radius-md)', border: '1px solid var(--primary-10)' }}>
                  Nothing here yet. Alerts are stored the first time a scan detects them.
                </div>
              ) : (
                history.map((alert) => <AlertCard key={alert.id ?? alert.evidence_summary} alert={alert} onChange={handleChange} />)
              )}
            </section>
          )}
        </div>
      </div>
    </div>
  )
}
