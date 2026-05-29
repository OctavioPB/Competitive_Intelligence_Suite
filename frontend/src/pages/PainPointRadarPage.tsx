import { useEffect, useState } from 'react'
import type React from 'react'
import { useAppStore } from '../stores/appStore'
import { api } from '../services/api'
import type { PainPoint } from '../services/api'
import Eyebrow from '../components/Eyebrow'
import Spinner from '../components/Spinner'
import KpiCard from '../components/KpiCard'
import CompetitorSelect from '../components/CompetitorSelect'
import StatusBadge from '../components/StatusBadge'

const heroStyle: React.CSSProperties = {
  backgroundColor: 'var(--primary)',
  backgroundImage:
    'linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)',
  backgroundSize: '48px 48px',
  padding: '56px 48px',
}

const BAR_COLORS = ['#003366', '#1a4d80', '#336699', '#99bbdd', '#c8982a']

function severityBadgeProps(sev: number) {
  if (sev >= 0.65)
    return { label: 'High', color: 'var(--status-red)', bg: 'var(--status-red-bg)' }
  if (sev >= 0.40)
    return { label: 'Medium', color: 'var(--status-orange)', bg: 'var(--status-orange-bg)' }
  return { label: 'Low', color: 'var(--status-green)', bg: 'var(--status-green-bg)' }
}

function trendBadgeProps(dir: string) {
  if (dir === 'rising')
    return { label: 'Rising', color: 'var(--status-green)', bg: 'var(--status-green-bg)' }
  if (dir === 'declining')
    return { label: 'Declining', color: 'var(--status-red)', bg: 'var(--status-red-bg)' }
  return { label: 'Stable', color: 'var(--primary-60)', bg: 'var(--primary-10)' }
}

function PainBarChart({ points }: { points: PainPoint[] }) {
  if (points.length === 0) return null
  const maxMentions = Math.max(...points.map((p) => p.mention_count), 1)
  const svgW     = 720
  const rowH     = 24
  const labelW   = 160
  const barAreaW = svgW - labelW - 48
  const svgH     = points.length * rowH + 12

  return (
    <svg
      viewBox={`0 0 ${svgW} ${svgH}`}
      width="100%"
      style={{ display: 'block' }}
    >
      {points.map((p, i) => {
        const barW  = Math.max(4, Math.round((p.mention_count / maxMentions) * barAreaW))
        const y     = i * rowH + 2
        const color = BAR_COLORS[i % BAR_COLORS.length]
        const raw   = p.topic_label.replace(/_/g, ' ')
        const label = raw.length > 24 ? raw.slice(0, 22) + '…' : raw
        return (
          <g key={p.topic_label}>
            <text
              x={labelW - 10}
              y={y + 14}
              textAnchor="end"
              fill="#6b7280"
              fontSize={10}
              fontFamily="'Plus Jakarta Sans', sans-serif"
            >
              {label}
            </text>
            <rect
              x={labelW}
              y={y + 4}
              width={barW}
              height={rowH - 9}
              fill={color}
              rx={3}
            />
            <text
              x={labelW + barW + 7}
              y={y + 14}
              fill="#1c1c2e"
              fontSize={10}
              fontFamily="'Plus Jakarta Sans', sans-serif"
            >
              {p.mention_count}
            </text>
          </g>
        )
      })}
    </svg>
  )
}

export default function PainPointRadarPage() {
  const { competitor } = useAppStore()
  const [points, setPoints] = useState<PainPoint[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setLoading(true)
    api.painPoints
      .get(competitor, 10)
      .then((r) => setPoints(r.points))
      .catch(() => setPoints([]))
      .finally(() => setLoading(false))
  }, [competitor])

  const totalMentions = points.reduce((s, p) => s + p.mention_count, 0)
  const avgSeverity =
    points.length > 0
      ? points.reduce((s, p) => s + p.avg_severity, 0) / points.length
      : 0
  const risingCount = points.filter((p) => p.trend_direction === 'rising').length

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

  return (
    <div>
      {/* ── Hero ─────────────────────────────────────────────────────────── */}
      <div style={heroStyle}>
        <div style={{ maxWidth: 'var(--max-width-dashboard)', margin: '0 auto' }}>
          <Eyebrow light>Pain Point Radar</Eyebrow>
          <h1
            style={{
              fontFamily: 'var(--fd)',
              fontSize: 36,
              fontWeight: 300,
              color: '#ffffff',
              margin: '0 0 6px',
            }}
          >
            Pain Point{' '}
            <em style={{ fontStyle: 'italic', color: 'var(--gold-light)' }}>
              Radar
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
            Rank competitor pain points by mention frequency, severity, and trend
            direction — so you know exactly where to position your product.
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
          <div>
            <CompetitorSelect />
          </div>

          {loading && <Spinner />}

          {!loading && points.length === 0 && (
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
              No pain point data found for <strong>{competitor}</strong>. Run the
              ingestion pipeline to populate the database.
            </div>
          )}

          {!loading && points.length > 0 && (
            <>
              {/* KPI row */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(4, 1fr)',
                  gap: 16,
                }}
              >
                <KpiCard
                  label="Total Mentions"
                  value={totalMentions.toLocaleString()}
                  sub="across all pain points"
                />
                <KpiCard
                  label="Avg Severity"
                  value={`${Math.round(avgSeverity * 100)}%`}
                  sub="pain intensity score"
                />
                <KpiCard
                  label="Rising Topics"
                  value={String(risingCount)}
                  sub="trending upward"
                  valueColor="var(--status-red)"
                />
                <KpiCard
                  label="Pain Clusters"
                  value={String(points.length)}
                  sub="unique topic groups"
                />
              </div>

              {/* Bar chart */}
              <section>
                <Eyebrow>Mention Volume</Eyebrow>
                <h2
                  style={{
                    fontFamily: 'var(--fd)',
                    fontSize: 22,
                    fontWeight: 300,
                    color: 'var(--dark)',
                    marginBottom: 20,
                  }}
                >
                  Pain points by <em style={{ fontStyle: 'italic', color: 'var(--gold)' }}>mention count</em>
                </h2>
                <div
                  style={{
                    backgroundColor: 'var(--white)',
                    borderRadius: 'var(--radius-md)',
                    padding: '24px',
                    boxShadow: 'var(--shadow-card)',
                    border: '1px solid var(--primary-10)',
                  }}
                >
                  <PainBarChart points={points} />
                </div>
              </section>

              {/* Table */}
              <section>
                <Eyebrow>Detail View</Eyebrow>
                <h2
                  style={{
                    fontFamily: 'var(--fd)',
                    fontSize: 22,
                    fontWeight: 300,
                    color: 'var(--dark)',
                    marginBottom: 20,
                  }}
                >
                  Pain point <em style={{ fontStyle: 'italic', color: 'var(--gold)' }}>breakdown</em>
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
                        <th style={thStyle}>Pain Point</th>
                        <th style={{ ...thStyle, textAlign: 'right' }}>
                          Mentions
                        </th>
                        <th style={thStyle}>Severity</th>
                        <th style={thStyle}>Trend</th>
                      </tr>
                    </thead>
                    <tbody>
                      {points.map((p, i) => {
                        const sev = severityBadgeProps(p.avg_severity)
                        const trend = trendBadgeProps(p.trend_direction)
                        return (
                          <tr
                            key={p.topic_label}
                            style={{
                              backgroundColor:
                                i % 2 === 0 ? 'var(--white)' : 'rgba(0,51,102,0.02)',
                              borderBottom: '1px solid var(--primary-10)',
                            }}
                          >
                            <td
                              style={{
                                fontFamily: 'var(--fb)',
                                fontSize: 13,
                                color: 'var(--dark)',
                                padding: '10px 14px',
                                fontWeight: 500,
                              }}
                            >
                              {p.topic_label.replace(/_/g, ' ')}
                            </td>
                            <td
                              style={{
                                fontFamily: 'var(--fd)',
                                fontSize: 15,
                                fontWeight: 300,
                                color: 'var(--dark)',
                                padding: '10px 14px',
                                textAlign: 'right',
                              }}
                            >
                              {p.mention_count}
                            </td>
                            <td style={{ padding: '10px 14px' }}>
                              <StatusBadge {...sev} />
                            </td>
                            <td style={{ padding: '10px 14px' }}>
                              <StatusBadge {...trend} />
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </section>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
