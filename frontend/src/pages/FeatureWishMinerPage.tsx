import { useEffect, useState } from 'react'
import type React from 'react'
import { useAppStore } from '../stores/appStore'
import { api } from '../services/api'
import type { WishCluster } from '../services/api'
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

export default function FeatureWishMinerPage() {
  const { competitor } = useAppStore()
  const [clusters, setClusters] = useState<WishCluster[]>([])
  const [gapsOnly, setGapsOnly] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setLoading(true)
    api.wishes
      .get(competitor, gapsOnly)
      .then((r) => setClusters(r.clusters))
      .catch(() => setClusters([]))
      .finally(() => setLoading(false))
  }, [competitor, gapsOnly])

  const covered = clusters.filter((c) => c.your_product_has_it).length
  const gaps = clusters.filter((c) => !c.your_product_has_it).length
  const totalMentions = clusters.reduce((s, c) => s + c.count, 0)

  return (
    <div>
      {/* â”€â”€ Hero â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
      <div style={heroStyle}>
        <div style={{ maxWidth: 'var(--max-width-dashboard)', margin: '0 auto' }}>
          <Eyebrow light>Feature Wish Miner</Eyebrow>
          <h1
            style={{
              fontFamily: 'var(--fd)',
              fontSize: 36,
              fontWeight: 300,
              color: '#ffffff',
              margin: '0 0 6px',
            }}
          >
            Feature Wish{' '}
            <em style={{ fontStyle: 'italic', color: 'var(--gold-light)' }}>
              Miner
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
            Cluster competitor feature requests and automatically flag which ones
            your product already solves â€” your unfair advantage, quantified.
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
            <label
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                fontFamily: 'var(--fb)',
                fontSize: 13,
                color: 'var(--dark)',
                cursor: 'pointer',
              }}
            >
              <input
                type="checkbox"
                checked={gapsOnly}
                onChange={(e) => setGapsOnly(e.target.checked)}
                style={{ accentColor: 'var(--gold)', width: 14, height: 14 }}
              />
              Show gaps only
            </label>
          </div>

          {loading && <Spinner />}

          {!loading && clusters.length === 0 && (
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
              No feature wish data found for <strong>{competitor}</strong>. Run
              the ingestion pipeline to populate the database.
            </div>
          )}

          {!loading && clusters.length > 0 && (
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
                  label="Feature Clusters"
                  value={String(clusters.length)}
                  sub="unique request themes"
                />
                <KpiCard
                  label="Already Covered"
                  value={String(covered)}
                  sub="your product has it"
                  valueColor="var(--status-green)"
                />
                <KpiCard
                  label="Gaps"
                  value={String(gaps)}
                  sub="missing from your product"
                  valueColor="var(--status-red)"
                />
                <KpiCard
                  label="Total Mentions"
                  value={totalMentions.toLocaleString()}
                  sub="across all clusters"
                />
              </div>

              {/* Clusters table */}
              <section>
                <Eyebrow>Feature Requests</Eyebrow>
                <h2
                  style={{
                    fontFamily: 'var(--fd)',
                    fontSize: 22,
                    fontWeight: 300,
                    color: 'var(--dark)',
                    marginBottom: 20,
                  }}
                >
                  What {competitor} users are <em style={{ fontStyle: 'italic', color: 'var(--gold)' }}>asking for</em>
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
                        <th style={thStyle}>Request Theme</th>
                        <th style={{ ...thStyle, textAlign: 'right' }}>
                          Mentions
                        </th>
                        <th style={{ ...thStyle, textAlign: 'center' }}>
                          Coverage
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {clusters.map((c, i) => (
                        <tr
                          key={c.wish_phrase_cluster}
                          style={{
                            backgroundColor:
                              i % 2 === 0 ? 'var(--white)' : 'rgba(0,51,102,0.02)',
                            borderBottom: '1px solid var(--primary-10)',
                          }}
                        >
                          <td style={{ padding: '12px 14px' }}>
                            <div
                              style={{
                                fontFamily: 'var(--fb)',
                                fontSize: 13,
                                fontWeight: 500,
                                color: 'var(--dark)',
                                marginBottom: 4,
                              }}
                            >
                              {c.wish_phrase_cluster}
                            </div>
                            {c.sample_quotes.slice(0, 2).map((q, qi) => (
                              <div
                                key={qi}
                                style={{
                                  fontFamily: 'var(--fb)',
                                  fontSize: 11,
                                  fontStyle: 'italic',
                                  color: 'var(--mid)',
                                  lineHeight: 1.5,
                                }}
                              >
                                "{q.slice(0, 90)}{q.length > 90 ? 'â€¦' : ''}"
                              </div>
                            ))}
                          </td>
                          <td
                            style={{
                              fontFamily: 'var(--fd)',
                              fontSize: 15,
                              fontWeight: 300,
                              color: 'var(--dark)',
                              padding: '12px 14px',
                              textAlign: 'right',
                              verticalAlign: 'top',
                            }}
                          >
                            {c.count}
                          </td>
                          <td
                            style={{
                              padding: '12px 14px',
                              textAlign: 'center',
                              verticalAlign: 'top',
                            }}
                          >
                            {c.your_product_has_it ? (
                              <span
                                style={{
                                  backgroundColor: 'var(--status-green-bg)',
                                  color:           'var(--status-green)',
                                  fontFamily:      'var(--fb)',
                                  fontSize:        10,
                                  fontWeight:      600,
                                  letterSpacing:   '1.5px',
                                  textTransform:   'uppercase',
                                  padding:         '3px 10px',
                                  borderRadius:    'var(--radius-pill)',
                                }}
                              >
                                We have this
                              </span>
                            ) : (
                              <span
                                style={{
                                  backgroundColor: 'var(--status-orange-bg)',
                                  color:           'var(--status-orange)',
                                  fontFamily:      'var(--fb)',
                                  fontSize:        10,
                                  fontWeight:      600,
                                  letterSpacing:   '1.5px',
                                  textTransform:   'uppercase',
                                  padding:         '3px 10px',
                                  borderRadius:    'var(--radius-pill)',
                                }}
                              >
                                Gap
                              </span>
                            )}
                            {c.matched_feature && (
                              <div
                                style={{
                                  fontFamily: 'var(--fb)',
                                  fontSize: 10,
                                  color: 'var(--mid)',
                                  marginTop: 4,
                                }}
                              >
                                {c.matched_feature}
                              </div>
                            )}
                          </td>
                        </tr>
                      ))}
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
