import { useCallback, useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { api } from '../services/api'
import type { HiringOverview, JobRole, PricingOverview, PricingPage, RoleCategory } from '../services/api'
import Eyebrow from '../components/Eyebrow'
import Spinner from '../components/Spinner'
import Toast from '../components/Toast'
import KpiCard from '../components/KpiCard'
import StatusBadge from '../components/StatusBadge'
import CompetitorSelect from '../components/CompetitorSelect'
import { errorMessage, useToast } from '../hooks/useToast'
import { useAppStore } from '../stores/appStore'
import { heroStyle, btnGold, card, thStyle } from '../styles/shared'

const POINTS_PREVIEW = 10

const CATEGORY_COLOR: Record<RoleCategory, string> = {
  support:     'var(--status-red)',
  engineering: 'var(--primary-60)',
  sales:       'var(--gold)',
  product:     'var(--status-purple)',
  marketing:   'var(--status-orange)',
  other:       'var(--mid)',
}

const SAMPLE_BADGE = { label: 'Sample', color: 'var(--status-orange)', bg: 'var(--status-orange-bg)' }

const muted = { fontFamily: 'var(--fb)', fontSize: 12, color: 'var(--mid)' } as const
const sectionTitle = {
  fontFamily: 'var(--fd)', fontSize: 22, fontWeight: 300, color: 'var(--dark)', margin: '0 0 16px',
} as const

function shortUrl(url: string): string {
  return url.replace(/^https?:\/\/(www\.)?/, '').replace(/\/$/, '')
}

function EmptyNote({ children }: { children: ReactNode }) {
  return <div style={{ ...card, padding: 24, ...muted, fontSize: 13, lineHeight: 1.6 }}>{children}</div>
}

// ── Pricing ─────────────────────────────────────────────────────────────────

function ChangeLine({ text }: { text: string }) {
  const arrow = text.indexOf('→')
  const [label, rest] = arrow >= 0 ? [text.slice(0, arrow), text.slice(arrow + 1)] : [text, null]
  return (
    <li style={{ fontFamily: 'var(--fb)', fontSize: 13, color: 'var(--dark)', padding: '4px 0', listStyle: 'none' }}>
      {rest === null ? text : (
        <>
          <span style={{ color: 'var(--mid)' }}>{label}</span>
          <span style={{ color: 'var(--gold)', fontWeight: 600 }}>→</span>
          <strong style={{ fontWeight: 600 }}>{rest}</strong>
        </>
      )}
    </li>
  )
}

function PricingCard({ page }: { page: PricingPage }) {
  const [showAll, setShowAll] = useState(false)
  const points = showAll ? page.price_points : page.price_points.slice(0, POINTS_PREVIEW)

  return (
    <div style={{ ...card, padding: '22px 26px', borderLeft: '3px solid var(--gold)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
        <a href={page.url} target="_blank" rel="noreferrer"
           style={{ fontFamily: 'var(--fb)', fontSize: 14, fontWeight: 600, color: 'var(--link)' }}>
          {shortUrl(page.url)}
        </a>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          {page.is_synthetic && <StatusBadge {...SAMPLE_BADGE} />}
          <span style={muted}>
            Checked {page.last_checked} · monitored since {page.monitored_since} · {page.versions} version{page.versions === 1 ? '' : 's'}
          </span>
        </div>
      </div>

      <div style={{ marginTop: 16, padding: '14px 16px', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--light)' }}>
        {page.last_change ? (
          <>
            <div style={{ fontFamily: 'var(--fb)', fontSize: 10, fontWeight: 600, letterSpacing: '2px', textTransform: 'uppercase', color: 'var(--status-green)', marginBottom: 6 }}>
              Changed on {page.last_change.date}
            </div>
            <ul style={{ margin: 0, padding: 0 }}>
              {page.last_change.changes.map((c) => <ChangeLine key={c} text={c} />)}
            </ul>
          </>
        ) : (
          <span style={muted}>No change since monitoring started.</span>
        )}
      </div>

      <div style={{ marginTop: 16 }}>
        <div style={{ ...muted, fontSize: 10, letterSpacing: '2px', textTransform: 'uppercase', marginBottom: 8 }}>
          Current price points ({page.price_points.length})
        </div>
        <ul style={{ margin: 0, padding: 0, columns: '2 280px', columnGap: 28 }}>
          {points.map((p) => (
            <li key={p} style={{ listStyle: 'none', fontFamily: 'var(--fb)', fontSize: 12, color: 'var(--dark)', padding: '3px 0', breakInside: 'avoid' }}>
              {p}
            </li>
          ))}
        </ul>
        {page.price_points.length > POINTS_PREVIEW && (
          <button onClick={() => setShowAll((s) => !s)}
                  style={{ background: 'none', border: 'none', color: 'var(--gold)', cursor: 'pointer', fontFamily: 'var(--fb)', fontSize: 12, padding: '6px 0 0' }}>
            {showAll ? 'Show fewer' : `Show all ${page.price_points.length}`}
          </button>
        )}
      </div>
    </div>
  )
}

// ── Hiring ──────────────────────────────────────────────────────────────────

function CategoryBars({ hiring }: { hiring: HiringOverview }) {
  const max = Math.max(1, ...hiring.by_category.map((c) => (hiring.board?.recent_only ? c.new : c.open)))
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {hiring.by_category.map((c) => {
        const value = hiring.board?.recent_only ? c.new : c.open
        return (
          <div key={c.category}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontFamily: 'var(--fb)', fontSize: 13, color: 'var(--dark)', marginBottom: 4 }}>
              <span>{c.label}</span>
              <span style={muted}>
                {hiring.board?.recent_only ? `${c.new} new` : `${c.open} open · ${c.new} new`}
              </span>
            </div>
            <div style={{ height: 8, borderRadius: 4, backgroundColor: 'var(--primary-10)' }}>
              <div style={{ height: '100%', borderRadius: 4, width: `${(value / max) * 100}%`, backgroundColor: CATEGORY_COLOR[c.category], opacity: 0.85 }} />
            </div>
          </div>
        )
      })}
    </div>
  )
}

function RolesTable({ roles, labels }: { roles: JobRole[]; labels: HiringOverview['category_labels'] }) {
  return (
    <div style={{ ...card, overflow: 'hidden' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ backgroundColor: 'var(--primary)' }}>
            <th style={thStyle}>Role</th>
            <th style={thStyle}>Function</th>
            <th style={thStyle}>Location</th>
            <th style={thStyle}>Posted</th>
          </tr>
        </thead>
        <tbody>
          {roles.map((r, i) => (
            <tr key={`${r.title}-${i}`} style={{ borderTop: '1px solid var(--primary-10)' }}>
              <td style={{ padding: '10px 14px', fontFamily: 'var(--fb)', fontSize: 13, color: 'var(--dark)' }}>
                {r.url ? <a href={r.url} target="_blank" rel="noreferrer" style={{ color: 'var(--link)' }}>{r.title}</a> : r.title}
              </td>
              <td style={{ padding: '10px 14px', fontFamily: 'var(--fb)', fontSize: 12, color: CATEGORY_COLOR[r.category] }}>
                {labels[r.category]}
              </td>
              <td style={{ padding: '10px 14px', ...muted }}>{r.location ?? '—'}</td>
              <td style={{ padding: '10px 14px', ...muted, whiteSpace: 'nowrap' }}>{r.posted_date}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ── Page ────────────────────────────────────────────────────────────────────

export default function MarketSignalsPage() {
  const { competitor } = useAppStore()
  const [pricing, setPricing] = useState<PricingOverview | null>(null)
  const [hiring, setHiring] = useState<HiringOverview | null>(null)
  const [loading, setLoading] = useState(false)
  const [checking, setChecking] = useState(false)
  const [demoMode, setDemoMode] = useState<boolean | null>(null)
  const { toast, showToast } = useToast()

  // Switching competitor while a load is in flight must not let the older
  // response overwrite the newer one — only the latest request may set state.
  const latestRequest = useRef(0)
  const load = useCallback((name: string) => {
    const id = ++latestRequest.current
    setLoading(true)
    return Promise.all([api.signals.pricing(name), api.signals.hiring(name)])
      .then(([p, h]) => {
        if (id === latestRequest.current) { setPricing(p); setHiring(h) }
      })
      .catch((err) => {
        if (id === latestRequest.current) showToast(errorMessage(err, 'Could not load market signals.'), 'error')
      })
      .finally(() => { if (id === latestRequest.current) setLoading(false) })
  }, [showToast])

  useEffect(() => { load(competitor) }, [competitor, load])

  useEffect(() => {
    api.meta.dataStatus().then((s) => setDemoMode(s.demo_mode)).catch(() => setDemoMode(false))
  }, [])

  function handleCheck() {
    setChecking(true)
    api.signals
      .refresh(competitor)
      .then((r) => {
        const parts: string[] = []
        for (const p of r.pricing) {
          parts.push(p.status === 'changed' ? `pricing changed (${p.changes.length} edits)` : `pricing ${p.status === 'first' ? 'captured' : 'unchanged'}`)
        }
        if (r.jobs) parts.push(`${r.jobs.seen} roles (${r.jobs.new} new since last check)`)
        if (r.errors.length) {
          showToast(`${competitor}: ${parts.join(', ') || 'nothing fetched'}. ${r.errors[0]}`, 'warning')
        } else {
          showToast(`${competitor}: ${parts.join(', ') || 'nothing configured'}.`, 'success')
        }
        return load(competitor)
      })
      .catch((err) => showToast(errorMessage(err, 'Check failed.'), 'error'))
      .finally(() => setChecking(false))
  }

  const changeDates = (pricing?.pages ?? [])
    .map((p) => p.last_change?.date)
    .filter((d): d is string => Boolean(d))
    .sort()
  const lastChange = changeDates.length ? changeDates[changeDates.length - 1] : undefined
  const support = hiring?.by_category.find((c) => c.category === 'support')
  const supportShare = hiring && hiring.new_roles ? Math.round(((support?.new ?? 0) / hiring.new_roles) * 100) : null
  const checkDisabledReason = demoMode ? 'Disabled in demo mode: market signals are sample data' : null

  return (
    <div>
      {/* ── Hero ─────────────────────────────────────────────────────────── */}
      <div style={heroStyle}>
        <div style={{ maxWidth: 'var(--max-width-dashboard)', margin: '0 auto' }}>
          <Eyebrow light>Market Signals</Eyebrow>
          <h1 style={{ fontFamily: 'var(--fd)', fontSize: 36, fontWeight: 300, color: '#fff', margin: '0 0 6px', lineHeight: 1.2 }}>
            Pricing &amp; hiring{' '}
            <em style={{ fontStyle: 'italic', color: 'var(--gold-light)' }}>signals</em>
          </h1>
          <p style={{ fontFamily: 'var(--fb)', fontSize: 13, color: 'rgba(255,255,255,0.45)', maxWidth: 600 }}>
            Every change to a competitor&apos;s pricing page, and what their job board says about where
            they hurt — a wave of support hires, or engineers hired to fix integrations.
          </p>
        </div>
      </div>

      {/* ── Body ─────────────────────────────────────────────────────────── */}
      <div style={{ backgroundColor: 'var(--light)', minHeight: '60vh' }}>
        <div style={{ maxWidth: 'var(--max-width-dashboard)', margin: '0 auto', padding: '44px 48px', display: 'flex', flexDirection: 'column', gap: 32 }}>
          <div style={{ display: 'flex', gap: 16, alignItems: 'flex-end', flexWrap: 'wrap' }}>
            <CompetitorSelect />
            <button
              style={{ ...btnGold, opacity: checkDisabledReason || checking ? 0.5 : 1, cursor: checkDisabledReason ? 'not-allowed' : 'pointer' }}
              onClick={handleCheck}
              disabled={checking || loading || checkDisabledReason !== null}
              title={checkDisabledReason ?? 'Fetch the pricing pages and job board now'}
            >
              {checking ? 'Checking…' : 'Check now'}
            </button>
            {checking && <span style={muted}>Large job boards take up to a minute.</span>}
          </div>

          {toast && <Toast message={toast.msg} type={toast.type} />}
          {loading && !pricing && <Spinner />}

          {pricing && hiring && (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
                <KpiCard label="Last price change" value={lastChange ?? 'None'} sub={lastChange ? 'on a monitored page' : 'since monitoring began'}
                         valueColor={lastChange ? 'var(--status-green)' : undefined} />
                <KpiCard label={hiring.board?.recent_only ? 'Roles (30 days)' : 'Open roles'} value={String(hiring.open_roles)}
                         sub={hiring.crawled_on ? `crawled ${hiring.crawled_on}` : 'no crawl yet'} />
                <KpiCard label="New roles" value={String(hiring.new_roles)} sub={`posted in the last ${hiring.window_days} days`} />
                <KpiCard label="Support share" value={supportShare === null ? '—' : `${supportShare}%`} sub="of new roles"
                         valueColor={supportShare !== null && supportShare >= 25 ? 'var(--status-red)' : undefined} />
              </div>

              {/* Pricing */}
              <section>
                <Eyebrow>Pricing Pages</Eyebrow>
                <h2 style={sectionTitle}>What they <em style={{ fontStyle: 'italic', color: 'var(--gold)' }}>charge</em></h2>
                {pricing.pages.length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                    {pricing.pages.map((p) => <PricingCard key={p.url} page={p} />)}
                  </div>
                ) : pricing.monitored_urls.length > 0 ? (
                  <EmptyNote>
                    {shortUrl(pricing.monitored_urls[0])} has not been checked yet. Click <strong>Check now</strong>, or
                    run <code>python ingestion/run_signals.py</code> — the daily scheduler job does it automatically.
                  </EmptyNote>
                ) : (
                  <EmptyNote>No pricing page configured for {competitor}. Add <code>pricing_urls</code> in <code>config.py</code>.</EmptyNote>
                )}
              </section>

              {/* Hiring */}
              <section>
                <Eyebrow>Job Board</Eyebrow>
                <h2 style={sectionTitle}>Where they <em style={{ fontStyle: 'italic', color: 'var(--gold)' }}>hire</em></h2>
                {!hiring.board ? (
                  <EmptyNote>
                    No public job board configured for {competitor}. Add <code>careers</code> in <code>config.py</code>
                    (Greenhouse, Lever, Ashby or Workday).
                  </EmptyNote>
                ) : !hiring.crawled_on ? (
                  <EmptyNote>The {hiring.board.provider} board has not been crawled yet. Click <strong>Check now</strong>.</EmptyNote>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 20 }}>
                      <div style={{ ...card, padding: '22px 26px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, gap: 10 }}>
                          <span style={{ ...muted, textTransform: 'capitalize' }}>
                            {hiring.board.provider} · {hiring.board.recent_only ? `roles posted in the last ${hiring.window_days} days` : 'all open roles'}
                          </span>
                          {hiring.is_synthetic && <StatusBadge {...SAMPLE_BADGE} />}
                        </div>
                        <CategoryBars hiring={hiring} />
                      </div>
                      <div style={{ ...card, padding: '22px 26px' }}>
                        <div style={{ fontFamily: 'var(--fb)', fontSize: 14, fontWeight: 600, color: 'var(--link)', marginBottom: 4 }}>
                          Integration &amp; API engineering
                        </div>
                        <div style={{ ...muted, marginBottom: 12 }}>
                          {hiring.integration_new} new role{hiring.integration_new === 1 ? '' : 's'} in the last {hiring.window_days} days
                        </div>
                        {hiring.integration_roles.length ? (
                          <ul style={{ margin: 0, padding: 0 }}>
                            {hiring.integration_roles.map((r, i) => (
                              <li key={`${r.title}-${i}`} style={{ listStyle: 'none', fontFamily: 'var(--fb)', fontSize: 13, color: 'var(--dark)', padding: '6px 0', borderTop: i ? '1px solid var(--primary-10)' : 'none' }}>
                                {r.title} <span style={muted}>· {r.posted_date}</span>
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <span style={muted}>None — no sign of an integration push.</span>
                        )}
                      </div>
                    </div>
                    {hiring.recent_roles.length > 0 && (
                      <div>
                        <div style={{ ...muted, fontSize: 10, letterSpacing: '2px', textTransform: 'uppercase', marginBottom: 8 }}>
                          Most recent roles
                        </div>
                        <RolesTable roles={hiring.recent_roles} labels={hiring.category_labels} />
                      </div>
                    )}
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
