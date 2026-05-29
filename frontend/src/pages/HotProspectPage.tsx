import { useState } from 'react'
import type React from 'react'
import { api } from '../services/api'
import type { Lead } from '../services/api'
import type { Page } from '../App'
import Eyebrow from '../components/Eyebrow'
import Spinner from '../components/Spinner'
import KpiCard from '../components/KpiCard'
import StatusBadge from '../components/StatusBadge'
import { useAppStore } from '../stores/appStore'

const heroStyle: React.CSSProperties = {
  backgroundColor: 'var(--primary)',
  backgroundImage:
    'linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)',
  backgroundSize: '48px 48px',
  padding: '56px 48px',
}

const btnNavy: React.CSSProperties = {
  fontFamily: 'var(--fb)',
  fontSize: 10,
  fontWeight: 700,
  letterSpacing: '2px',
  textTransform: 'uppercase',
  backgroundColor: 'var(--primary)',
  color: '#fff',
  border: 'none',
  borderRadius: 'var(--radius-sm)',
  padding: '10px 22px',
  cursor: 'pointer',
}

const btnGold: React.CSSProperties = {
  ...btnNavy,
  backgroundColor: 'var(--gold)',
}

function urgencyBadgeProps(score: number) {
  if (score >= 0.7)
    return { label: `High ${score.toFixed(2)}`, color: 'var(--status-red)', bg: 'var(--status-red-bg)' }
  if (score >= 0.4)
    return { label: `Med ${score.toFixed(2)}`, color: 'var(--status-orange)', bg: 'var(--status-orange-bg)' }
  return { label: `Low ${score.toFixed(2)}`, color: 'var(--status-green)', bg: 'var(--status-green-bg)' }
}

const thStyle: React.CSSProperties = {
  fontFamily: 'var(--fb)',
  fontSize: 10,
  fontWeight: 600,
  letterSpacing: '2px',
  textTransform: 'uppercase',
  color: '#fff',
  padding: '10px 14px',
  textAlign: 'left',
}

export default function HotProspectPage({ onNavigate }: { onNavigate?: (p: Page) => void }) {
  const { setOutreachPrefill } = useAppStore()
  const [leads, setLeads] = useState<Lead[]>([])
  const [loading, setLoading] = useState(false)

  function handleCompose(lead: Lead) {
    setOutreachPrefill({
      competitor: lead.competitor_name,
      complaint:  lead.complaint_summary,
      username:   lead.username,
    })
    onNavigate?.('outreach')
  }

  function handleScan() {
    setLoading(true)
    api.prospects
      .scan()
      .then(setLeads)
      .catch(() => setLeads([]))
      .finally(() => setLoading(false))
  }

  function handleDemo() {
    setLoading(true)
    api.prospects
      .demo()
      .then(setLeads)
      .catch(() => setLeads([]))
      .finally(() => setLoading(false))
  }

  function handleDownloadCSV() {
    if (leads.length === 0) return
    const headers = [
      'username',
      'post_url',
      'created_at',
      'competitor_name',
      'urgency_score',
      'complaint_summary',
      'company_signals',
      'suggested_angle',
    ]
    const rows = leads.map((l) =>
      [
        l.username,
        l.post_url,
        l.created_at,
        l.competitor_name,
        l.urgency_score.toFixed(3),
        `"${l.complaint_summary.replace(/"/g, '""')}"`,
        `"${l.company_signals.join('; ')}"`,
        `"${l.suggested_angle.replace(/"/g, '""')}"`,
      ].join(','),
    )
    const csv = [headers.join(','), ...rows].join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'hot_prospects.csv'
    a.click()
    URL.revokeObjectURL(url)
  }

  const highUrgency = leads.filter((l) => l.urgency_score >= 0.7).length
  const medUrgency = leads.filter(
    (l) => l.urgency_score >= 0.4 && l.urgency_score < 0.7,
  ).length
  const competitorCount = new Set(leads.map((l) => l.competitor_name)).size

  return (
    <div>
      {/* ── Hero ─────────────────────────────────────────────────────────── */}
      <div style={heroStyle}>
        <div style={{ maxWidth: 'var(--max-width-dashboard)', margin: '0 auto' }}>
          <Eyebrow light>Hot Prospect Finder</Eyebrow>
          <h1
            style={{
              fontFamily: 'var(--fd)',
              fontSize: 36,
              fontWeight: 300,
              color: '#ffffff',
              margin: '0 0 6px',
            }}
          >
            Hot Prospect{' '}
            <em style={{ fontStyle: 'italic', color: 'var(--gold-light)' }}>
              Finder
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
            Reddit users actively expressing intent to switch from competitors —
            ranked by urgency and enriched with suggested outreach angles.
          </p>
        </div>
      </div>

      {/* ── Body ─────────────────────────────────────────────────────────── */}
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
              Scan Reddit
            </button>
            <button style={btnGold} onClick={handleDemo} disabled={loading}>
              Load Demo Leads
            </button>
          </div>

          {loading && <Spinner />}

          {!loading && leads.length === 0 && (
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
              No leads loaded yet. Click <strong>Scan Reddit</strong> for live
              data or <strong>Load Demo Leads</strong> to preview fixture
              prospects.
            </div>
          )}

          {!loading && leads.length > 0 && (
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
                  label="Total Prospects"
                  value={String(leads.length)}
                  sub="switching-intent posts"
                />
                <KpiCard
                  label="High Urgency ≥0.7"
                  value={String(highUrgency)}
                  sub="act now"
                  valueColor="var(--status-red)"
                />
                <KpiCard
                  label="Medium Urgency"
                  value={String(medUrgency)}
                  sub="follow up this week"
                  valueColor="var(--status-orange)"
                />
                <KpiCard
                  label="Competitors Flagged"
                  value={String(competitorCount)}
                  sub="unique competitors"
                  valueColor="var(--status-green)"
                />
              </div>

              {/* Table */}
              <section>
                <Eyebrow>Top Prospects</Eyebrow>
                <h2
                  style={{
                    fontFamily: 'var(--fd)',
                    fontSize: 22,
                    fontWeight: 300,
                    color: 'var(--dark)',
                    marginBottom: 20,
                  }}
                >
                  Switching-intent leads ranked by <em style={{ fontStyle: 'italic', color: 'var(--gold)' }}>urgency</em>
                </h2>
                <div
                  style={{
                    overflowX: 'auto',
                    borderRadius: 'var(--radius-md)',
                    boxShadow: 'var(--shadow-card)',
                    border: '1px solid var(--primary-10)',
                  }}
                >
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ backgroundColor: 'var(--primary)' }}>
                        <th style={thStyle}>User</th>
                        <th style={thStyle}>Complaint</th>
                        <th style={thStyle}>Company Signals</th>
                        <th style={thStyle}>Angle</th>
                        <th style={{ ...thStyle, textAlign: 'center' }}>
                          Urgency
                        </th>
                        <th style={{ ...thStyle, textAlign: 'center' }}>
                          Link
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {leads.slice(0, 10).map((lead, i) => {
                        const badge = urgencyBadgeProps(lead.urgency_score)
                        return (
                          <tr
                            key={lead.username + i}
                            style={{
                              backgroundColor:
                                i % 2 === 0 ? 'var(--white)' : 'rgba(0,51,102,0.02)',
                              borderBottom: '1px solid var(--primary-10)',
                            }}
                          >
                            <td style={{ padding: '12px 14px', verticalAlign: 'top' }}>
                              <div
                                style={{
                                  fontFamily: 'var(--fb)',
                                  fontWeight: 600,
                                  fontSize: 12,
                                  color: 'var(--primary)',
                                }}
                              >
                                {lead.username}
                              </div>
                              <div
                                style={{
                                  fontFamily: 'var(--fb)',
                                  fontSize: 11,
                                  color: 'var(--mid)',
                                }}
                              >
                                {lead.created_at}
                              </div>
                            </td>
                            <td
                              style={{
                                padding: '12px 14px',
                                verticalAlign: 'top',
                                fontFamily: 'var(--fb)',
                                fontSize: 12,
                                color: 'var(--dark)',
                                lineHeight: 1.5,
                                maxWidth: 260,
                              }}
                            >
                              {lead.complaint_summary.slice(0, 100)}
                            </td>
                            <td
                              style={{
                                padding: '12px 14px',
                                verticalAlign: 'top',
                                fontFamily: 'var(--fb)',
                                fontSize: 12,
                                color: 'var(--mid)',
                              }}
                            >
                              {lead.company_signals.slice(0, 3).join(', ') || '—'}
                            </td>
                            <td
                              style={{
                                padding: '12px 14px',
                                verticalAlign: 'top',
                                fontFamily: 'var(--fb)',
                                fontSize: 12,
                                color: 'var(--dark)',
                                lineHeight: 1.5,
                                maxWidth: 200,
                              }}
                            >
                              {lead.suggested_angle.slice(0, 100)}
                            </td>
                            <td
                              style={{
                                padding: '12px 14px',
                                textAlign: 'center',
                                verticalAlign: 'top',
                              }}
                            >
                              <StatusBadge {...badge} />
                            </td>
                            <td
                              style={{
                                padding: '12px 14px',
                                textAlign: 'center',
                                verticalAlign: 'middle',
                              }}
                            >
                              <div style={{ display: 'flex', flexDirection: 'column', gap: 6, alignItems: 'center' }}>
                                <a
                                  href={lead.post_url}
                                  target="_blank"
                                  rel="noreferrer"
                                  style={{ color: 'var(--primary)', fontFamily: 'var(--fb)', fontSize: 12, textDecoration: 'none' }}
                                >
                                  View
                                </a>
                                {onNavigate && (
                                  <button
                                    onClick={() => handleCompose(lead)}
                                    style={{
                                      fontFamily:      'var(--fb)',
                                      fontSize:        8,
                                      fontWeight:      700,
                                      letterSpacing:   '1.5px',
                                      textTransform:   'uppercase',
                                      backgroundColor: 'var(--gold)',
                                      color:           '#fff',
                                      border:          'none',
                                      borderRadius:    'var(--radius-sm)',
                                      padding:         '4px 8px',
                                      cursor:          'pointer',
                                      whiteSpace:      'nowrap',
                                    }}
                                  >
                                    Compose
                                  </button>
                                )}
                              </div>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </section>

              {/* Download */}
              <div>
                <button style={btnNavy} onClick={handleDownloadCSV}>
                  Download CSV
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
