import { useState } from 'react'
import type React from 'react'
import { api } from '../services/api'
import type { DigestReport, CompetitorBrief } from '../services/api'
import Eyebrow from '../components/Eyebrow'
import Spinner from '../components/Spinner'
import KpiCard from '../components/KpiCard'

const heroStyle: React.CSSProperties = {
  backgroundColor: 'var(--primary)',
  backgroundImage:
    'linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)',
  backgroundSize: '48px 48px',
  padding: '56px 48px',
}

const card: React.CSSProperties = {
  backgroundColor: 'var(--white)',
  borderRadius:    'var(--radius-md)',
  boxShadow:       'var(--shadow-card)',
  border:          '1px solid var(--primary-10)',
}

const btnGold: React.CSSProperties = {
  fontFamily:      'var(--fb)',
  fontSize:        10,
  fontWeight:      700,
  letterSpacing:   '2px',
  textTransform:   'uppercase',
  backgroundColor: 'var(--gold)',
  color:           '#fff',
  border:          'none',
  borderRadius:    'var(--radius-sm)',
  padding:         '10px 22px',
  cursor:          'pointer',
}

const btnNavy: React.CSSProperties = { ...btnGold, backgroundColor: 'var(--primary)' }

function signalColor(signal: string): string {
  if (signal === 'improving') return 'var(--status-green)'
  if (signal === 'declining') return 'var(--status-red)'
  return 'var(--gold)'
}

function CompetitorBriefCard({ brief }: { brief: CompetitorBrief }) {
  const color  = signalColor(brief.sentiment_signal)
  const delta  = brief.sentiment_delta
  const sign   = delta >= 0 ? '+' : ''

  return (
    <div style={{ ...card, padding: 28, display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontFamily: 'var(--fb)', fontSize: 9, letterSpacing: '3px', textTransform: 'uppercase', color: 'var(--mid)', marginBottom: 4 }}>
            Competitor
          </div>
          <div style={{ fontFamily: 'var(--fd)', fontSize: 22, fontWeight: 300, color: 'var(--dark)' }}>
            {brief.name}
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontFamily: 'var(--fb)', fontSize: 9, letterSpacing: '3px', textTransform: 'uppercase', color: 'var(--mid)', marginBottom: 4 }}>
            Sentiment Δ
          </div>
          <div style={{ fontFamily: 'var(--fd)', fontSize: 22, fontWeight: 300, color }}>
            {sign}{delta.toFixed(3)}
          </div>
        </div>
      </div>

      {/* Top pain */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <div style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: 'var(--gold)', flexShrink: 0 }} />
        <span style={{ fontFamily: 'var(--fb)', fontSize: 12, color: 'var(--mid)' }}>
          Top pain: <strong style={{ color: 'var(--dark)' }}>{brief.top_pain}</strong>
        </span>
      </div>

      {/* Summary */}
      <p style={{ fontFamily: 'var(--fb)', fontSize: 13, color: 'var(--dark)', lineHeight: 1.7, margin: 0 }}>
        {brief.summary}
      </p>

      {/* Action bullets */}
      <div style={{ borderTop: '1px solid var(--primary-10)', paddingTop: 16, display: 'flex', flexDirection: 'column', gap: 8 }}>
        <div style={{ fontFamily: 'var(--fb)', fontSize: 9, letterSpacing: '3px', textTransform: 'uppercase', color: 'var(--gold)', marginBottom: 4 }}>
          Act now
        </div>
        {brief.action_bullets.map((bullet, i) => (
          <div key={i} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
            <div style={{ width: 5, height: 5, borderRadius: '50%', backgroundColor: 'var(--primary-30)', flexShrink: 0, marginTop: 6 }} />
            <span style={{ fontFamily: 'var(--fb)', fontSize: 13, color: 'var(--dark)', lineHeight: 1.6 }}>
              {bullet}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

function buildMarkdown(digest: DigestReport): string {
  const lines: string[] = [
    `# Intelligence Digest — ${digest.generated_at.slice(0, 10)}`,
    '',
    `## Overall Theme`,
    digest.overall_theme,
    '',
  ]
  for (const c of digest.per_competitor) {
    lines.push(`## ${c.name}`)
    lines.push(`**Sentiment Δ:** ${c.sentiment_delta >= 0 ? '+' : ''}${c.sentiment_delta.toFixed(3)} (${c.sentiment_signal})`)
    lines.push(`**Top pain:** ${c.top_pain}`)
    lines.push('')
    lines.push(c.summary)
    lines.push('')
    lines.push('**Actions:**')
    for (const b of c.action_bullets) lines.push(`- ${b}`)
    lines.push('')
  }
  if (digest.top_alert) {
    lines.push(`## Top Alert`)
    lines.push(digest.top_alert)
    lines.push('')
  }
  if (digest.top_lead) {
    lines.push(`## Top Prospect Lead`)
    lines.push(digest.top_lead)
  }
  return lines.join('\n')
}

export default function DigestPage() {
  const [digest,  setDigest]  = useState<DigestReport | null>(null)
  const [loading, setLoading] = useState(false)

  function handleGenerate() {
    setLoading(true)
    api.digest.generate()
      .then(setDigest)
      .catch(() => setDigest(null))
      .finally(() => setLoading(false))
  }

  function handleLoadLatest() {
    setLoading(true)
    api.digest.latest()
      .then((r) => { if (r) setDigest(r) })
      .catch(() => {/* silently skip */})
      .finally(() => setLoading(false))
  }

  function handleDownload() {
    if (!digest) return
    const md   = buildMarkdown(digest)
    const blob = new Blob([md], { type: 'text/markdown' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href     = url
    a.download = `digest_${digest.generated_at.slice(0, 10)}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  const competitorCount = digest?.per_competitor.length ?? 0
  const decliningCount  = digest?.per_competitor.filter((c) => c.sentiment_signal === 'declining').length ?? 0

  return (
    <div>
      {/* ── Hero ─────────────────────────────────────────────────────────── */}
      <div style={heroStyle}>
        <div style={{ maxWidth: 'var(--max-width-dashboard)', margin: '0 auto' }}>
          <Eyebrow light>Intelligence Digest</Eyebrow>
          <h1 style={{ fontFamily: 'var(--fd)', fontSize: 36, fontWeight: 300, color: '#fff', margin: '0 0 6px', lineHeight: 1.2 }}>
            Your weekly competitive{' '}
            <em style={{ fontStyle: 'italic', color: 'var(--gold-light)' }}>brief</em>
          </h1>
          <p style={{ fontFamily: 'var(--fb)', fontSize: 13, color: 'rgba(255,255,255,0.45)', maxWidth: 560 }}>
            Claude synthesises all six intelligence modules into one executive-ready narrative — what changed, what it means, and what your team should do this week.
          </p>
        </div>
      </div>

      {/* ── Body ─────────────────────────────────────────────────────────── */}
      <div style={{ backgroundColor: 'var(--light)' }}>
        <div style={{
          maxWidth:      'var(--max-width-dashboard)',
          margin:        '0 auto',
          padding:       '44px 48px',
          display:       'flex',
          flexDirection: 'column',
          gap:           32,
        }}>
          {/* Controls */}
          <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
            <button style={btnGold} onClick={handleGenerate} disabled={loading}>
              Generate Digest
            </button>
            <button style={btnNavy} onClick={handleLoadLatest} disabled={loading}>
              Load Latest
            </button>
            {digest && (
              <button style={btnNavy} onClick={handleDownload}>
                Download Markdown
              </button>
            )}
            {digest && (
              <span style={{ fontFamily: 'var(--fb)', fontSize: 11, color: 'var(--mid)' }}>
                Generated {digest.generated_at.slice(0, 16).replace('T', ' ')} UTC
              </span>
            )}
          </div>

          {loading && (
            <div>
              <Spinner />
              <p style={{ fontFamily: 'var(--fb)', fontSize: 12, color: 'var(--mid)', marginTop: 8 }}>
                Claude is synthesising intelligence across all competitors… (~20s)
              </p>
            </div>
          )}

          {!loading && !digest && (
            <div style={{ ...card, padding: 24, fontFamily: 'var(--fb)', fontSize: 13, color: 'var(--mid)' }}>
              Click <strong>Generate Digest</strong> to create a fresh brief, or <strong>Load Latest</strong> to view the most recent stored digest.
            </div>
          )}

          {!loading && digest && (
            <>
              {/* KPI row */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
                <KpiCard label="Competitors Tracked" value={String(competitorCount)} sub="in this digest" />
                <KpiCard
                  label="Declining Sentiment"
                  value={String(decliningCount)}
                  sub="competitors trending down"
                  valueColor={decliningCount > 0 ? 'var(--status-red)' : undefined}
                />
                <KpiCard
                  label="Top Alert"
                  value={digest.top_alert ? '1' : '0'}
                  sub={digest.top_alert ? 'urgent signal detected' : 'no urgent signals'}
                  valueColor={digest.top_alert ? 'var(--status-orange)' : undefined}
                />
                <KpiCard
                  label="Top Prospect"
                  value={digest.top_lead ? '1' : '0'}
                  sub={digest.top_lead ? 'high-urgency lead' : 'no leads available'}
                  valueColor={digest.top_lead ? 'var(--status-green)' : undefined}
                />
              </div>

              {/* Overall theme */}
              <section>
                <Eyebrow>This Week's Theme</Eyebrow>
                <div style={{
                  ...card,
                  padding:    28,
                  borderLeft: '3px solid var(--gold)',
                  borderRadius: '0 var(--radius-md) var(--radius-md) 0',
                }}>
                  <p style={{ fontFamily: 'var(--fb)', fontSize: 15, color: 'var(--dark)', lineHeight: 1.7, margin: 0 }}>
                    {digest.overall_theme}
                  </p>
                </div>
              </section>

              {/* Per-competitor briefs */}
              <section>
                <Eyebrow>Competitor Briefs</Eyebrow>
                <h2 style={{ fontFamily: 'var(--fd)', fontSize: 22, fontWeight: 300, color: 'var(--dark)', marginBottom: 20 }}>
                  Status by{' '}
                  <em style={{ fontStyle: 'italic', color: 'var(--gold)' }}>competitor</em>
                </h2>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
                  {digest.per_competitor.map((brief) => (
                    <CompetitorBriefCard key={brief.name} brief={brief} />
                  ))}
                </div>
              </section>

              {/* Signals */}
              {(digest.top_alert || digest.top_lead) && (
                <section>
                  <Eyebrow>Priority Signals</Eyebrow>
                  <h2 style={{ fontFamily: 'var(--fd)', fontSize: 22, fontWeight: 300, color: 'var(--dark)', marginBottom: 20 }}>
                    Act on these{' '}
                    <em style={{ fontStyle: 'italic', color: 'var(--gold)' }}>first</em>
                  </h2>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                    {digest.top_alert && (
                      <div style={{ ...card, padding: 24, borderTop: '3px solid var(--status-orange)' }}>
                        <div style={{ fontFamily: 'var(--fb)', fontSize: 9, letterSpacing: '3px', textTransform: 'uppercase', color: 'var(--status-orange)', marginBottom: 10 }}>
                          Top Alert
                        </div>
                        <p style={{ fontFamily: 'var(--fb)', fontSize: 13, color: 'var(--dark)', lineHeight: 1.7, margin: 0 }}>
                          {digest.top_alert}
                        </p>
                      </div>
                    )}
                    {digest.top_lead && (
                      <div style={{ ...card, padding: 24, borderTop: '3px solid var(--status-green)' }}>
                        <div style={{ fontFamily: 'var(--fb)', fontSize: 9, letterSpacing: '3px', textTransform: 'uppercase', color: 'var(--status-green)', marginBottom: 10 }}>
                          Top Prospect Lead
                        </div>
                        <p style={{ fontFamily: 'var(--fb)', fontSize: 13, color: 'var(--dark)', lineHeight: 1.7, margin: 0 }}>
                          {digest.top_lead}
                        </p>
                      </div>
                    )}
                  </div>
                </section>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
