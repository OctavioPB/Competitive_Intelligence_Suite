import { useState } from 'react'
import { api } from '../services/api'
import type { ChurnAnalysis, ChurnBucket } from '../services/api'
import Eyebrow from '../components/Eyebrow'
import Spinner from '../components/Spinner'
import Toast from '../components/Toast'
import { errorMessage, useToast } from '../hooks/useToast'
import KpiCard from '../components/KpiCard'
import CompetitorSelect from '../components/CompetitorSelect'
import { useAppStore } from '../stores/appStore'
import { heroStyle, btnGold, btnNavy, card } from '../styles/shared'

function trendColor(dir: string): string {
  if (dir === 'worsening') return 'var(--status-red)'
  if (dir === 'improving') return 'var(--status-green)'
  return 'var(--gold)'
}

function trendLabel(dir: string): string {
  if (dir === 'worsening') return 'Worsening'
  if (dir === 'improving') return 'Improving'
  return 'Stable'
}

function BucketBar({ bucket, maxPct }: { bucket: ChurnBucket; maxPct: number }) {
  const barPct  = maxPct > 0 ? (bucket.mention_pct / maxPct) * 100 : 0
  const color   = trendColor(bucket.trend_direction)
  const tLabel  = trendLabel(bucket.trend_direction)

  return (
    <div style={{ marginBottom: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
        <span style={{ fontFamily: 'var(--fb)', fontSize: 13, fontWeight: 500, color: 'var(--dark)' }}>
          {bucket.label}
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{
            fontFamily:      'var(--fb)',
            fontSize:        10,
            fontWeight:      600,
            color,
            backgroundColor: color === 'var(--gold)' ? 'rgba(200,152,42,0.08)' : undefined,
            padding:         '2px 8px',
            borderRadius:    'var(--radius-pill)',
          }}>
            {tLabel}
          </span>
          <span style={{ fontFamily: 'var(--fd)', fontSize: 18, fontWeight: 300, color: 'var(--dark)' }}>
            {bucket.mention_pct.toFixed(1)}%
          </span>
        </div>
      </div>
      <div style={{ height: 8, backgroundColor: 'var(--primary-10)', borderRadius: 4 }}>
        <div style={{
          height:          '100%',
          borderRadius:    4,
          backgroundColor: color,
          width:           `${barPct}%`,
          transition:      'width 0.5s',
          opacity:         0.85,
        }} />
      </div>
    </div>
  )
}

export default function ChurnIntelligencePage() {
  const { competitor } = useAppStore()
  const [analysis, setAnalysis] = useState<ChurnAnalysis | null>(null)
  const [loading,  setLoading]  = useState(false)
  const { toast, showToast } = useToast()

  function handleAnalyse() {
    setLoading(true)
    api.churn.analyse(competitor)
      .then(setAnalysis)
      .catch((err) => showToast(errorMessage(err, 'Churn analysis failed. Check API key and backend.'), 'error'))
      .finally(() => setLoading(false))
  }

  function handleLoadCached() {
    setLoading(true)
    api.churn.getCached(competitor)
      .then((r) => {
        if (r) setAnalysis(r)
        else showToast('No cached analysis for this competitor yet. Click Analyse to create one.', 'warning')
      })
      .catch((err) => showToast(errorMessage(err, 'Failed to load cached analysis.'), 'error'))
      .finally(() => setLoading(false))
  }

  const topBucket   = analysis?.buckets[0]
  const worstBucket = analysis?.buckets.find((b) => b.trend_direction === 'worsening')
  const maxPct      = analysis ? Math.max(0, ...analysis.buckets.map((b) => b.mention_pct)) : 0

  return (
    <div>
      {/* ── Hero ─────────────────────────────────────────────────────────── */}
      <div style={heroStyle}>
        <div style={{ maxWidth: 'var(--max-width-dashboard)', margin: '0 auto' }}>
          <Eyebrow light>Churn Intelligence</Eyebrow>
          <h1 style={{ fontFamily: 'var(--fd)', fontSize: 36, fontWeight: 300, color: '#fff', margin: '0 0 6px', lineHeight: 1.2 }}>
            Why users leave{' '}
            <em style={{ fontStyle: 'italic', color: 'var(--gold-light)' }}>competitors</em>
          </h1>
          <p style={{ fontFamily: 'var(--fb)', fontSize: 13, color: 'rgba(255,255,255,0.45)', maxWidth: 560 }}>
            Categorised churn drivers with mention share, trend direction, and real customer proof quotes — so your team knows exactly what to probe in discovery.
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
          <div style={{ display: 'flex', gap: 16, alignItems: 'flex-end' }}>
            <CompetitorSelect />
            <button style={btnGold} onClick={handleAnalyse} disabled={loading}>
              Analyse with Claude
            </button>
            <button style={btnNavy} onClick={handleLoadCached} disabled={loading}>
              Load Cached
            </button>
          </div>

          {toast && <Toast message={toast.msg} type={toast.type} />}

          {loading && (
            <div>
              <Spinner />
              <p style={{ fontFamily: 'var(--fb)', fontSize: 12, color: 'var(--mid)', marginTop: 8 }}>
                Claude is categorising customer reviews… (~15s)
              </p>
            </div>
          )}

          {!loading && !analysis && (
            <div style={{ ...card, padding: 24, fontFamily: 'var(--fb)', fontSize: 13, color: 'var(--mid)' }}>
              Select a competitor and click <strong>Analyse with Claude</strong> to categorise churn drivers, or load a cached result.
            </div>
          )}

          {!loading && analysis && (
            <>
              {/* KPI row */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
                <KpiCard
                  label="Reviews Analysed"
                  value={analysis.total_reviews_analysed.toLocaleString()}
                  sub="in last 180 days"
                />
                <KpiCard
                  label="Top Churn Driver"
                  value={topBucket ? `${topBucket.mention_pct.toFixed(0)}%` : '—'}
                  sub={topBucket?.label ?? ''}
                  valueColor="var(--status-red)"
                />
                <KpiCard
                  label="Worsening Bucket"
                  value={worstBucket?.label.split(' ')[0] ?? 'None'}
                  sub={worstBucket ? `${worstBucket.mention_pct.toFixed(1)}% of complaints` : 'No worsening signals'}
                  valueColor={worstBucket ? 'var(--status-red)' : undefined}
                />
                <KpiCard
                  label="Generated"
                  value={analysis.generated_at.slice(0, 10)}
                  sub={analysis.competitor}
                />
              </div>

              {/* Churn driver breakdown */}
              <section>
                <Eyebrow>Churn Breakdown</Eyebrow>
                <h2 style={{ fontFamily: 'var(--fd)', fontSize: 22, fontWeight: 300, color: 'var(--dark)', marginBottom: 20 }}>
                  Why {analysis.competitor} users{' '}
                  <em style={{ fontStyle: 'italic', color: 'var(--gold)' }}>leave</em>
                </h2>
                <div style={{ ...card, padding: 28 }}>
                  {analysis.buckets.map((bucket) => (
                    <BucketBar key={bucket.category} bucket={bucket} maxPct={maxPct} />
                  ))}
                </div>
              </section>

              {/* Proof quote library */}
              <section>
                <Eyebrow>Proof Quotes</Eyebrow>
                <h2 style={{ fontFamily: 'var(--fd)', fontSize: 22, fontWeight: 300, color: 'var(--dark)', marginBottom: 20 }}>
                  Real customer{' '}
                  <em style={{ fontStyle: 'italic', color: 'var(--gold)' }}>voice</em>
                </h2>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 16 }}>
                  {analysis.buckets.filter((b) => b.proof_quotes.length > 0).map((bucket) => (
                    <div key={bucket.category} style={{ ...card, padding: 24 }}>
                      <div style={{
                        fontFamily:    'var(--fb)',
                        fontSize:      9,
                        fontWeight:    600,
                        letterSpacing: '3px',
                        textTransform: 'uppercase',
                        color:         trendColor(bucket.trend_direction),
                        marginBottom:  12,
                      }}>
                        {bucket.label}
                      </div>
                      {bucket.proof_quotes.map((q, i) => (
                        <div
                          key={i}
                          style={{
                            fontFamily:  'var(--fb)',
                            fontSize:    13,
                            fontStyle:   'italic',
                            color:       'var(--dark)',
                            lineHeight:  1.7,
                            borderLeft:  '2px solid var(--primary-30)',
                            paddingLeft: 14,
                            marginBottom: i < bucket.proof_quotes.length - 1 ? 12 : 0,
                          }}
                        >
                          "{q}"
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              </section>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
