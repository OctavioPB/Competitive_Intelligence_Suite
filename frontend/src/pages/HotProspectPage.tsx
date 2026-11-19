import { useCallback, useEffect, useState } from 'react'
import { api } from '../services/api'
import type { CrmStatus, CrmTarget, Lead, LeadStage, Pipeline } from '../services/api'
import type { Page } from '../App'
import Eyebrow from '../components/Eyebrow'
import Spinner from '../components/Spinner'
import Toast from '../components/Toast'
import { errorMessage, useToast } from '../hooks/useToast'
import { csvCell, downloadTextFile } from '../utils/download'
import KpiCard from '../components/KpiCard'
import StatusBadge from '../components/StatusBadge'
import { useAppStore } from '../stores/appStore'
import { heroStyle, btnGold, btnNavy, thStyle } from '../styles/shared'

const CRM_LABELS: Record<CrmTarget, string> = { hubspot: 'HubSpot', salesforce: 'Salesforce' }
const CRM_ENV_HINT: Record<CrmTarget, string> = {
  hubspot:    'Add HUBSPOT_ACCESS_TOKEN to .env to enable',
  salesforce: 'Add SALESFORCE_INSTANCE_URL and a token (or client id/secret) to .env to enable',
}

const STAGES: { id: LeadStage; label: string }[] = [
  { id: 'new',         label: 'New' },
  { id: 'contacted',   label: 'Contacted' },
  { id: 'replied',     label: 'Replied' },
  { id: 'opportunity', label: 'Opportunity' },
  { id: 'dismissed',   label: 'Not a fit' },
]

const STAGE_COLOR: Record<LeadStage, string> = {
  new:         'var(--mid)',
  contacted:   'var(--primary-60)',
  replied:     'var(--gold)',
  opportunity: 'var(--status-green)',
  dismissed:   'var(--mid)',
}

function StageCell({ lead, onSaved, onError }: {
  lead:    Lead
  onSaved: (l: Lead) => void
  onError: (msg: string) => void
}) {
  const [note, setNote] = useState(lead.note ?? '')
  const [saving, setSaving] = useState(false)
  useEffect(() => setNote(lead.note ?? ''), [lead.note])

  if (!lead.status) return <span style={{ fontFamily: 'var(--fb)', fontSize: 11, color: 'var(--mid)' }}>—</span>

  function save(status: LeadStage, newNote?: string) {
    setSaving(true)
    api.prospects
      .setStage(lead.post_url, status, newNote)
      .then(onSaved)
      .catch((err) => onError(errorMessage(err, 'Could not update the lead.')))
      .finally(() => setSaving(false))
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6, minWidth: 130 }}>
      <select
        value={lead.status}
        disabled={saving}
        onChange={(e) => save(e.target.value as LeadStage)}
        aria-label={`Pipeline stage for ${lead.username}`}
        style={{
          fontFamily: 'var(--fb)', fontSize: 12, fontWeight: 600, color: STAGE_COLOR[lead.status],
          border: '1px solid var(--primary-10)', borderRadius: 'var(--radius-sm)', padding: '4px 6px',
          backgroundColor: 'var(--white)', cursor: 'pointer',
        }}
      >
        {STAGES.map((s) => <option key={s.id} value={s.id}>{s.label}</option>)}
      </select>
      <input
        value={note}
        placeholder="Add a note…"
        maxLength={2000}
        aria-label={`Note for ${lead.username}`}
        onChange={(e) => setNote(e.target.value)}
        onBlur={() => { if (note !== (lead.note ?? '')) save(lead.status as LeadStage, note) }}
        onKeyDown={(e) => { if (e.key === 'Enter') (e.target as HTMLInputElement).blur() }}
        style={{
          fontFamily: 'var(--fb)', fontSize: 11, color: 'var(--dark)', border: '1px solid var(--primary-10)',
          borderRadius: 'var(--radius-sm)', padding: '3px 6px', backgroundColor: 'var(--light)',
        }}
      />
    </div>
  )
}

function StageFunnel({ stages, active, onSelect }: {
  stages:   Pipeline['stages']
  active:   LeadStage | 'all'
  onSelect: (s: LeadStage | 'all') => void
}) {
  // "All" lists every lead except the ones marked as not a fit.
  const total = stages.reduce((n, s) => n + (s.id === 'dismissed' ? 0 : s.count), 0)
  return (
    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'stretch' }}>
      {[{ id: 'all' as const, label: 'All', count: total }, ...stages].map((s, i) => {
        const on = active === s.id
        return (
          <button
            key={s.id}
            onClick={() => onSelect(s.id)}
            style={{
              display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 2,
              padding: '10px 16px', minWidth: 110, cursor: 'pointer',
              backgroundColor: on ? 'var(--primary)' : 'var(--white)',
              border: `1px solid ${on ? 'var(--primary)' : 'var(--primary-10)'}`,
              borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-card)',
            }}
          >
            <span style={{ fontFamily: 'var(--fd)', fontSize: 22, fontWeight: 300, color: on ? '#fff' : 'var(--dark)' }}>
              {s.count}
            </span>
            <span style={{ fontFamily: 'var(--fb)', fontSize: 9, letterSpacing: '2px', textTransform: 'uppercase', color: on ? 'rgba(255,255,255,0.75)' : 'var(--mid)' }}>
              {i > 1 && s.id !== 'dismissed' ? '→ ' : ''}{s.label}
            </span>
          </button>
        )
      })}
    </div>
  )
}

function urgencyBadgeProps(score: number) {
  if (score >= 0.7)
    return { label: `High ${score.toFixed(2)}`, color: 'var(--status-red)', bg: 'var(--status-red-bg)' }
  if (score >= 0.4)
    return { label: `Med ${score.toFixed(2)}`, color: 'var(--status-orange)', bg: 'var(--status-orange-bg)' }
  return { label: `Low ${score.toFixed(2)}`, color: 'var(--status-green)', bg: 'var(--status-green-bg)' }
}

export default function HotProspectPage({ onNavigate }: { onNavigate?: (p: Page) => void }) {
  const { setOutreachPrefill } = useAppStore()
  const [leads, setLeads] = useState<Lead[]>([])
  const [loading, setLoading] = useState(false)
  const { toast, showToast } = useToast()
  const [crm, setCrm] = useState<CrmStatus | null>(null)
  const [pushing, setPushing] = useState<CrmTarget | null>(null)

  useEffect(() => {
    let cancelled = false
    api.crm
      .status()
      .then((s) => { if (!cancelled) setCrm(s) })
      .catch(() => {/* buttons stay disabled */})
    return () => { cancelled = true }
  }, [])

  // ── Pipeline ──────────────────────────────────────────────────────────────
  const [view, setView] = useState<'scan' | 'pipeline'>('scan')
  const [pipeline, setPipeline] = useState<Pipeline | null>(null)
  const [stageFilter, setStageFilter] = useState<LeadStage | 'all'>('all')

  const loadPipeline = useCallback(() => {
    return api.prospects.pipeline(true).then(setPipeline).catch(() => {/* pipeline is optional */})
  }, [])
  useEffect(() => { loadPipeline() }, [loadPipeline])

  function handleStageSaved(updated: Lead) {
    setLeads((list) => list.map((l) => (l.post_url === updated.post_url ? { ...l, ...updated } : l)))
    loadPipeline()
  }

  const pipelineLeads = (pipeline?.leads ?? []).filter((l) =>
    stageFilter === 'all' ? l.status !== 'dismissed' : l.status === stageFilter,
  )
  const shown = view === 'scan' ? leads : pipelineLeads
  const pipelineTotal = pipeline?.stages.reduce((n, st) => n + st.count, 0) ?? 0

  const realLeads = shown.filter((l) => !l.is_synthetic)

  function crmDisabledReason(target: CrmTarget): string | null {
    if (!crm) return 'Checking CRM configuration…'
    if (crm.demo_mode) return 'Disabled in demo mode: these are sample leads'
    if (!crm[target]) return CRM_ENV_HINT[target]
    if (realLeads.length === 0) return 'Only sample leads loaded: nothing to send'
    return null
  }

  function handlePush(target: CrmTarget) {
    const name = CRM_LABELS[target]
    // Creates records in an external system, so ask first.
    if (!window.confirm(`Create up to ${realLeads.length} lead(s) in ${name}? Leads already there are skipped.`)) return
    setPushing(target)
    api.crm
      .push(target, realLeads)
      .then((r) => {
        const parts = [`${r.created} created`, `${r.exists} already in ${name}`]
        if (r.skipped) parts.push(`${r.skipped} sample skipped`)
        if (r.failed) {
          const firstError = r.results.find((x) => x.status === 'failed')?.error ?? 'unknown error'
          showToast(`${name}: ${parts.join(', ')}, ${r.failed} failed (${firstError})`, 'error')
        } else {
          showToast(`${name}: ${parts.join(', ')}.`, 'success')
        }
      })
      .catch((err) => showToast(errorMessage(err, `Could not send leads to ${name}.`), 'error'))
      .finally(() => setPushing(null))
  }

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
      .then((found) => { setLeads(found); setView('scan'); return loadPipeline() })
      .catch((err) => showToast(errorMessage(err, 'Reddit scan failed. Is the backend running?'), 'error'))
      .finally(() => setLoading(false))
  }

  function handleDemo() {
    setLoading(true)
    api.prospects
      .demo()
      .then((found) => { setLeads(found); setView('scan'); return loadPipeline() })
      .catch((err) => showToast(errorMessage(err, 'Could not load demo leads.'), 'error'))
      .finally(() => setLoading(false))
  }

  function handleDownloadCSV() {
    if (shown.length === 0) return
    const headers = [
      'username',
      'post_url',
      'created_at',
      'competitor_name',
      'urgency_score',
      'complaint_summary',
      'company_signals',
      'suggested_angle',
      'stage',
      'note',
    ]
    const rows = shown.map((l) =>
      // Every field is scraped, user-authored text — quote and neutralise all of them.
      [
        l.username,
        l.post_url,
        l.created_at,
        l.competitor_name,
        l.urgency_score.toFixed(3),
        l.complaint_summary,
        l.company_signals.join('; '),
        l.suggested_angle,
        l.status ?? '',
        l.note ?? '',
      ]
        .map(csvCell)
        .join(','),
    )
    downloadTextFile('hot_prospects.csv', [headers.join(','), ...rows].join('\n'), 'text/csv')
  }

  const highUrgency = shown.filter((l) => l.urgency_score >= 0.7).length
  const medUrgency = shown.filter(
    (l) => l.urgency_score >= 0.4 && l.urgency_score < 0.7,
  ).length
  const competitorCount = new Set(shown.map((l) => l.competitor_name)).size

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
            <div style={{ flex: 1 }} />
            {(['scan', 'pipeline'] as const).map((v) => (
              <button
                key={v}
                onClick={() => setView(v)}
                style={{
                  fontFamily: 'var(--fb)', fontSize: 11, cursor: 'pointer', padding: '4px 12px',
                  borderRadius: 'var(--radius-sm)', border: '1px solid',
                  fontWeight: view === v ? 600 : 400,
                  color: view === v ? '#fff' : 'var(--link)',
                  backgroundColor: view === v ? 'var(--primary)' : 'transparent',
                  borderColor: view === v ? 'var(--primary)' : 'var(--primary-10)',
                }}
              >
                {v === 'scan' ? 'This scan' : `Pipeline (${pipelineTotal})`}
              </button>
            ))}
          </div>

          {view === 'pipeline' && pipeline && (
            <StageFunnel stages={pipeline.stages} active={stageFilter} onSelect={setStageFilter} />
          )}

          {toast && <Toast message={toast.msg} type={toast.type} />}

          {loading && <Spinner />}

          {!loading && view === 'pipeline' && shown.length === 0 && (
            <div style={{ fontFamily: 'var(--fb)', fontSize: 13, color: 'var(--mid)', padding: 24, backgroundColor: 'var(--white)', borderRadius: 'var(--radius-md)', border: '1px solid var(--primary-10)' }}>
              {pipelineTotal === 0
                ? 'The pipeline is empty. Every lead a scan finds is kept here with its stage.'
                : 'No leads in this stage.'}
            </div>
          )}

          {!loading && view === 'scan' && leads.length === 0 && (
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

          {!loading && shown.length > 0 && (
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
                  label={view === 'scan' ? 'Total Prospects' : 'In Pipeline'}
                  value={String(shown.length)}
                  sub={view === 'scan' ? 'switching-intent posts' : stageFilter === 'all' ? 'active leads' : `stage: ${stageFilter}`}
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
                <Eyebrow>{view === 'scan' ? 'Top Prospects' : 'Pipeline'}</Eyebrow>
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
                        <th style={thStyle}>Stage</th>
                        <th style={{ ...thStyle, textAlign: 'center' }}>
                          Link
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {(view === 'scan' ? shown.slice(0, 10) : shown).map((lead, i) => {
                        const badge = urgencyBadgeProps(lead.urgency_score)
                        return (
                          <tr
                            key={lead.post_url || lead.username + i}
                            style={{
                              backgroundColor:
                                i % 2 === 0 ? 'var(--white)' : 'rgba(0,51,102,0.02)',
                              borderBottom: '1px solid var(--primary-10)',
                              opacity: lead.status === 'dismissed' ? 0.55 : 1,
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
                              {lead.is_synthetic && (
                                <div style={{ margin: '4px 0' }}>
                                  <StatusBadge label="Sample" color="var(--status-orange)" bg="var(--status-orange-bg)" />
                                </div>
                              )}
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
                            <td style={{ padding: '12px 14px', verticalAlign: 'top' }}>
                              <StageCell lead={lead} onSaved={handleStageSaved} onError={(m) => showToast(m, 'error')} />
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

              {/* Export */}
              <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
                {(['hubspot', 'salesforce'] as const).map((target) => {
                  const reason = crmDisabledReason(target)
                  const disabled = reason !== null || pushing !== null
                  return (
                    <button
                      key={target}
                      style={{ ...btnGold, opacity: disabled ? 0.45 : 1, cursor: disabled ? 'not-allowed' : 'pointer' }}
                      onClick={() => handlePush(target)}
                      disabled={disabled}
                      title={reason ?? `Create these leads in ${CRM_LABELS[target]}`}
                    >
                      {pushing === target ? 'Sending…' : `Send to ${CRM_LABELS[target]}`}
                    </button>
                  )
                })}
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
