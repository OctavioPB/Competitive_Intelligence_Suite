import { useEffect, useState } from 'react'
import type React from 'react'
import { useAppStore } from '../stores/appStore'
import { api } from '../services/api'
import type { TimelineEntry } from '../services/api'
import Eyebrow from '../components/Eyebrow'
import Spinner from '../components/Spinner'
import KpiCard from '../components/KpiCard'
import CompetitorSelect from '../components/CompetitorSelect'

const heroStyle: React.CSSProperties = {
  backgroundColor: 'var(--primary)',
  backgroundImage:
    'linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)',
  backgroundSize: '48px 48px',
  padding: '56px 48px',
}

function SentimentChart({ timeline }: { timeline: TimelineEntry[] }) {
  if (timeline.length === 0) return null

  const W = 720
  const H = 200
  const padL = 40
  const padR = 20
  const padT = 16
  const padB = 30
  const plotW = W - padL - padR
  const plotH = H - padT - padB

  // y: sentiment in [-1, 1]
  const toY = (s: number) => padT + plotH * (1 - (s + 1) / 2)
  const toX = (i: number) =>
    padL + (i / Math.max(timeline.length - 1, 1)) * plotW

  const pts = timeline
    .map((e, i) => `${toX(i).toFixed(1)},${toY(e.avg_sentiment).toFixed(1)}`)
    .join(' ')

  const zeroY = toY(0)

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      width="100%"
      style={{ display: 'block' }}
    >
      {/* Zero line */}
      <line
        x1={padL}
        y1={zeroY}
        x2={W - padR}
        y2={zeroY}
        stroke="#9ca3af"
        strokeWidth={1}
        strokeDasharray="4 3"
      />
      {/* Y-axis labels */}
      {[1, 0.5, 0, -0.5, -1].map((v) => (
        <text
          key={v}
          x={padL - 6}
          y={toY(v) + 4}
          textAnchor="end"
          fill="#6b7280"
          fontSize={9}
          fontFamily="'Plus Jakarta Sans', sans-serif"
        >
          {v > 0 ? `+${v}` : v}
        </text>
      ))}
      {/* Line */}
      <polyline
        points={pts}
        fill="none"
        stroke="#003366"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Data points */}
      {timeline.map((e, i) => (
        <circle
          key={e.month}
          cx={toX(i)}
          cy={toY(e.avg_sentiment)}
          r={3}
          fill={e.avg_sentiment >= 0 ? '#27b97c' : '#e03448'}
        />
      ))}
      {/* Event stars */}
      {timeline.map((e, i) =>
        e.top_event ? (
          <text
            key={`star-${e.month}`}
            x={toX(i)}
            y={toY(e.avg_sentiment) - 10}
            textAnchor="middle"
            fontSize={12}
            fill="#c8982a"
          >
            â˜…
          </text>
        ) : null,
      )}
      {/* X-axis labels â€” show every 3rd */}
      {timeline.map((e, i) =>
        i % 3 === 0 ? (
          <text
            key={`lbl-${e.month}`}
            x={toX(i)}
            y={H - 4}
            textAnchor="middle"
            fill="#6b7280"
            fontSize={8}
            fontFamily="'Plus Jakarta Sans', sans-serif"
          >
            {e.month.slice(0, 7)}
          </text>
        ) : null,
      )}
    </svg>
  )
}

export default function SentimentTimelinePage() {
  const { competitor } = useAppStore()
  const [months, setMonths] = useState(18)
  const [timeline, setTimeline] = useState<TimelineEntry[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setLoading(true)
    api.sentiment
      .get(competitor, months)
      .then((r) => setTimeline(r.timeline))
      .catch(() => setTimeline([]))
      .finally(() => setLoading(false))
  }, [competitor, months])

  const overallSentiment =
    timeline.length > 0
      ? timeline.reduce((s, e) => s + e.avg_sentiment, 0) / timeline.length
      : 0

  const latestSentiment = timeline.length > 0 ? timeline[timeline.length - 1].avg_sentiment : 0
  const firstSentiment = timeline.length > 0 ? timeline[0].avg_sentiment : 0
  const trendDelta = latestSentiment - firstSentiment

  const totalReviews = timeline.reduce((s, e) => s + e.review_count, 0)

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
      {/* â”€â”€ Hero â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
      <div style={heroStyle}>
        <div style={{ maxWidth: 'var(--max-width-dashboard)', margin: '0 auto' }}>
          <Eyebrow light>Sentiment Analysis</Eyebrow>
          <h1
            style={{
              fontFamily: 'var(--fd)',
              fontSize: 36,
              fontWeight: 300,
              color: '#ffffff',
              margin: '0 0 6px',
            }}
          >
            Sentiment{' '}
            <em style={{ fontStyle: 'italic', color: 'var(--gold-light)' }}>
              Timeline
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
            18-month rolling competitor sentiment with news event overlay â€” spot
            drops before your competitors recover.
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
          <div style={{ display: 'flex', gap: 32, alignItems: 'flex-end' }}>
            <CompetitorSelect />
            <div style={{ flex: 1, maxWidth: 280 }}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  marginBottom: 6,
                }}
              >
                <span
                  style={{
                    fontFamily: 'var(--fb)',
                    fontSize: 10,
                    fontWeight: 500,
                    letterSpacing: '2px',
                    textTransform: 'uppercase',
                    color: 'var(--mid)',
                  }}
                >
                  Months
                </span>
                <span
                  style={{
                    fontFamily: 'var(--fd)',
                    fontSize: 16,
                    fontWeight: 300,
                    color: 'var(--gold)',
                  }}
                >
                  {months}
                </span>
              </div>
              <input
                type="range"
                min={1}
                max={18}
                step={1}
                value={months}
                onChange={(e) => setMonths(Number(e.target.value))}
                style={{ width: '100%', accentColor: 'var(--gold)', cursor: 'pointer' }}
              />
            </div>
          </div>

          {loading && <Spinner />}

          {!loading && timeline.length === 0 && (
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
              No sentiment data found for <strong>{competitor}</strong>. Run the
              ingestion pipeline to populate the database.
            </div>
          )}

          {!loading && timeline.length > 0 && (
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
                  label="Overall Sentiment"
                  value={overallSentiment.toFixed(2)}
                  sub="period average"
                  valueColor={
                    overallSentiment >= 0
                      ? 'var(--status-green)'
                      : 'var(--status-red)'
                  }
                />
                <KpiCard
                  label="Latest Month"
                  value={latestSentiment.toFixed(2)}
                  sub={timeline[timeline.length - 1]?.month ?? ''}
                  valueColor={
                    latestSentiment >= 0
                      ? 'var(--status-green)'
                      : 'var(--status-red)'
                  }
                />
                <KpiCard
                  label="Trend"
                  value={`${trendDelta > 0 ? '+' : ''}${trendDelta.toFixed(2)}`}
                  sub="first â†’ last month"
                  valueColor={
                    trendDelta >= 0 ? 'var(--status-green)' : 'var(--status-red)'
                  }
                />
                <KpiCard
                  label="Reviews Analysed"
                  value={totalReviews.toLocaleString()}
                  sub="total across period"
                />
              </div>

              {/* Chart */}
              <section>
                <Eyebrow>Sentiment Over Time</Eyebrow>
                <h2
                  style={{
                    fontFamily: 'var(--fd)',
                    fontSize: 22,
                    fontWeight: 300,
                    color: 'var(--dark)',
                    marginBottom: 20,
                  }}
                >
                  Monthly average <em style={{ fontStyle: 'italic', color: 'var(--gold)' }}>sentiment</em> — ★ marks news events
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
                  <SentimentChart timeline={timeline} />
                </div>
              </section>

              {/* News events table */}
              {timeline.some((e) => e.top_event) && (
                <section>
                  <Eyebrow>News Events</Eyebrow>
                  <h2
                    style={{
                      fontFamily: 'var(--fd)',
                      fontSize: 22,
                      fontWeight: 300,
                      color: 'var(--dark)',
                      marginBottom: 20,
                    }}
                  >
                    Months with notable <em style={{ fontStyle: 'italic', color: 'var(--gold)' }}>news headlines</em>
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
                          <th style={thStyle}>Month</th>
                          <th style={thStyle}>Top News Headline</th>
                          <th style={{ ...thStyle, textAlign: 'right' }}>
                            Sentiment
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {timeline
                          .filter((e) => e.top_event)
                          .map((e, i) => (
                            <tr
                              key={e.month}
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
                                  whiteSpace: 'nowrap',
                                }}
                              >
                                {e.month}
                              </td>
                              <td
                                style={{
                                  fontFamily: 'var(--fb)',
                                  fontSize: 13,
                                  color: 'var(--dark)',
                                  padding: '10px 14px',
                                }}
                              >
                                {e.top_event}
                              </td>
                              <td
                                style={{
                                  fontFamily: 'var(--fd)',
                                  fontSize: 15,
                                  fontWeight: 300,
                                  color:
                                    e.avg_sentiment >= 0
                                      ? 'var(--status-green)'
                                      : 'var(--status-red)',
                                  padding: '10px 14px',
                                  textAlign: 'right',
                                }}
                              >
                                {e.avg_sentiment.toFixed(2)}
                              </td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
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
