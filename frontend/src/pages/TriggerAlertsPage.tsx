import { useState } from 'react'
import type React from 'react'
import { api } from '../services/api'
import type { Alert } from '../services/api'
import Eyebrow from '../components/Eyebrow'
import Spinner from '../components/Spinner'
import KpiCard from '../components/KpiCard'
import StatusBadge from '../components/StatusBadge'

const heroStyle: React.CSSProperties = {
  backgroundColor: 'var(--primary)',
  backgroundImage:
    'linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)',
  backgroundSize: '48px 48px',
  padding: '56px 48px',
}

const btnGold: React.CSSProperties = {
  fontFamily: 'var(--fb)',
  fontSize: 10,
  fontWeight: 700,
  letterSpacing: '2px',
  textTransform: 'uppercase',
  backgroundColor: 'var(--gold)',
  color: '#fff',
  border: 'none',
  borderRadius: 'var(--radius-sm)',
  padding: '10px 22px',
  cursor: 'pointer',
}

const btnNavy: React.CSSProperties = {
  ...btnGold,
  backgroundColor: 'var(--primary)',
}

// Badge uses semantic status tokens. Alert card border is always gold (structural rule).
const BADGE_MAP: Record<string, { label: string; color: string; bg: string }> = {
  sentiment_drop: { label: 'Sentiment Drop', color: 'var(--status-red)', bg: 'var(--status-red-bg)' },
  negative_news: { label: 'Negative News', color: 'var(--status-orange)', bg: 'var(--status-orange-bg)' },
  review_spike: { label: 'Review Spike', color: 'var(--status-purple)', bg: 'var(--status-purple-bg)' },
}

function AlertCard({ alert }: { alert: Alert }) {
  const [draft, setDraft] = useState<string | null>(alert.outreach_draft)
  const [expanded, setExpanded] = useState(false)
  const [loadingDraft, setLoadingDraft] = useState(false)

  const badge = BADGE_MAP[alert.trigger_type] ?? {
    label: alert.trigger_type,
    color: 'var(--primary-60)',
    bg: 'var(--primary-10)',
  }

  function requestDraft(useLlm: boolean) {
    setLoadingDraft(true)
    api.alerts
      .outreach(alert, useLlm)
      .then((r) => {
        setDraft(r.draft)
        setExpanded(true)
      })
      .catch(() => {/* silently fail */})
      .finally(() => setLoadingDraft(false))
  }

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
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          marginBottom: 10,
        }}
      >
        <StatusBadge label={badge.label} color={badge.color} bg={badge.bg} />
        <span
          style={{
            fontFamily: 'var(--fb)',
            fontSize: 11,
            color: 'var(--mid)',
          }}
        >
          {alert.timestamp.replace('T', ' ').slice(0, 16)} UTC
        </span>
      </div>

      {/* Competitor */}
      <div
        style={{
          fontFamily: 'var(--fb)',
          fontWeight: 600,
          fontSize: 14,
          color: 'var(--primary)',
          marginBottom: 6,
        }}
      >
        {alert.competitor}
      </div>

      {/* Evidence */}
      <div
        style={{
          fontFamily: 'var(--fb)',
          fontSize: 13,
          color: 'var(--dark)',
          lineHeight: 1.5,
          marginBottom: 14,
        }}
      >
        {alert.evidence_summary}
      </div>

      {/* Outreach section */}
      {draft ? (
        <div>
          <button
            onClick={() => setExpanded((o) => !o)}
            style={{
              background: 'none',
              border: '1px solid var(--primary-10)',
              borderRadius: 'var(--radius-sm)',
              fontFamily: 'var(--fb)',
              fontSize: 11,
              color: 'var(--primary)',
              cursor: 'pointer',
              padding: '4px 12px',
              marginBottom: expanded ? 10 : 0,
            }}
          >
            {expanded ? 'Hide' : 'View'} outreach draft â–¾
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
              <button style={btnNavy} onClick={() => requestDraft(false)}>
                Template Draft
              </button>
              <button style={btnGold} onClick={() => requestDraft(true)}>
                Claude Draft
              </button>
            </>
          )}
        </div>
      )}
    </div>
  )
}

export default function TriggerAlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(false)

  function handleScan() {
    setLoading(true)
    api.alerts
      .scan()
      .then(setAlerts)
      .catch(() => setAlerts([]))
      .finally(() => setLoading(false))
  }

  function handleDemo() {
    setLoading(true)
    api.alerts
      .demo()
      .then(setAlerts)
      .catch(() => setAlerts([]))
      .finally(() => setLoading(false))
  }

  const nDrop = alerts.filter((a) => a.trigger_type === 'sentiment_drop').length
  const nNews = alerts.filter((a) => a.trigger_type === 'negative_news').length
  const nSpike = alerts.filter((a) => a.trigger_type === 'review_spike').length

  const sorted = [...alerts]
    .sort((a, b) => b.timestamp.localeCompare(a.timestamp))
    .slice(0, 10)

  return (
    <div>
      {/* â”€â”€ Hero â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
      <div style={heroStyle}>
        <div style={{ maxWidth: 'var(--max-width-dashboard)', margin: '0 auto' }}>
          <Eyebrow light>Trigger Alerts</Eyebrow>
          <h1
            style={{
              fontFamily: 'var(--fd)',
              fontSize: 36,
              fontWeight: 300,
              color: '#ffffff',
              margin: '0 0 6px',
            }}
          >
            Trigger{' '}
            <em style={{ fontStyle: 'italic', color: 'var(--gold-light)' }}>
              Alerts
            </em>
          </h1>
          <p
            style={{
              fontFamily: 'var(--fb)',
              fontSize: 13,
              color: 'rgba(255,255,255,0.45)',
              maxWidth: 560,
            }}
          >
            Real-time competitor vulnerability signals â€” sentiment drops, negative
            news, and review spikes â€” with pre-drafted outreach ready to send.
          </p>
        </div>
      </div>

      {/* â”€â”€ Body â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
      <div style={{ backgroundColor: 'var(--light)', minHeight: '60vh' }}>
        <div
          style={{
            maxWidth: 'var(--max-width-dashboard)',
            margin: '0 auto',
            padding: '44px 48px',
            display: 'flex',
            flexDirection: 'column',
            gap: 32,
          }}
        >
          {/* Controls */}
          <div style={{ display: 'flex', gap: 12 }}>
            <button style={btnNavy} onClick={handleScan} disabled={loading}>
              Scan All Competitors
            </button>
            <button style={btnGold} onClick={handleDemo} disabled={loading}>
              Simulate Bad Week
            </button>
          </div>

          {loading && <Spinner />}

          {!loading && alerts.length === 0 && (
            <div
              style={{
                fontFamily: 'var(--fb)',
                fontSize: 13,
                color: 'var(--mid)',
                padding: '24px',
                backgroundColor: 'var(--white)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--primary-10)',
              }}
            >
              No alerts yet. Click <strong>Scan All Competitors</strong> to check
              for live signals, or <strong>Simulate Bad Week</strong> to preview a
              demo scenario.
            </div>
          )}

          {!loading && alerts.length > 0 && (
            <>
              {/* KPIs */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(4, 1fr)',
                  gap: 16,
                }}
              >
                <KpiCard
                  label="Total Alerts"
                  value={String(alerts.length)}
                  sub="detected this scan"
                />
                <KpiCard
                  label="Sentiment Drops"
                  value={String(nDrop)}
                  sub="competitors declining"
                  valueColor="var(--status-red)"
                />
                <KpiCard
                  label="Negative News"
                  value={String(nNews)}
                  sub="press events flagged"
                  valueColor="var(--status-orange)"
                />
                <KpiCard
                  label="Review Spikes"
                  value={String(nSpike)}
                  sub="unusual volume"
                  valueColor="var(--gold)"
                />
              </div>

              {/* Alert feed */}
              <section>
                <Eyebrow>Alert Feed</Eyebrow>
                <h2
                  style={{
                    fontFamily: 'var(--fd)',
                    fontSize: 22,
                    fontWeight: 300,
                    color: 'var(--dark)',
                    marginBottom: 20,
                  }}
                >
                  Latest <em style={{ fontStyle: 'italic', color: 'var(--gold)' }}>vulnerability signals</em>
                </h2>
                {sorted.map((alert, i) => (
                  <AlertCard key={`${alert.competitor}-${alert.trigger_type}-${i}`} alert={alert} />
                ))}
              </section>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
