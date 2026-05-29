import { useState } from 'react'
import type React from 'react'
import { useAppStore } from '../stores/appStore'
import { api } from '../services/api'
import type { Battlecard } from '../services/api'
import Eyebrow from '../components/Eyebrow'
import Spinner from '../components/Spinner'
import Toast from '../components/Toast'
import CompetitorSelect from '../components/CompetitorSelect'

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

function buildMarkdown(card: Battlecard): string {
  const lines: string[] = [
    `# Battlecard: ${card.competitor}`,
    `_Generated: ${card.generated_at}_`,
    '',
    '## Recommended Pitch',
    card.recommended_pitch,
    '',
    '## Objections & Counters',
    '',
  ]
  card.objections.forEach((o, i) => {
    lines.push(`### ${i + 1}. ${o.objection}`)
    lines.push(`**Evidence:** ${o.evidence}`)
    lines.push(`**Counter:** ${o.counter}`)
    lines.push(`> ${o.proof_quote}`)
    lines.push('')
  })
  lines.push('## Feature Gaps')
  lines.push('| Gap | Mentions | Our Advantage |')
  lines.push('|-----|---------|---------------|')
  card.feature_gaps.forEach((g) => {
    lines.push(`| ${g.gap} | ${g.frequency} | ${g.your_advantage} |`)
  })
  return lines.join('\n')
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

export default function BattlecardPage() {
  const { competitor } = useAppStore()
  const [card, setCard] = useState<Battlecard | null>(null)
  const [loading, setLoading] = useState(false)
  const [toast, setToast] = useState<{ msg: string; type: 'success' | 'error' | 'warning' } | null>(null)

  function showToast(msg: string, type: 'success' | 'error' | 'warning') {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 4000)
  }

  function handleGenerate() {
    setLoading(true)
    setCard(null)
    api.battlecard
      .generate(competitor)
      .then((c) => {
        setCard(c)
        showToast('Battlecard generated successfully.', 'success')
      })
      .catch(() => showToast('Generation failed. Check API key and backend.', 'error'))
      .finally(() => setLoading(false))
  }

  function handleLoadCached() {
    setLoading(true)
    api.battlecard
      .getCached(competitor)
      .then((c) => {
        if (c) {
          setCard(c)
          showToast('Cached battlecard loaded.', 'success')
        } else {
          showToast('No cached battlecard found. Click Generate to create one.', 'warning')
        }
      })
      .catch(() => showToast('Failed to load cached battlecard.', 'error'))
      .finally(() => setLoading(false))
  }

  function handleDownload() {
    if (!card) return
    const md = buildMarkdown(card)
    const blob = new Blob([md], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `battlecard_${card.competitor.toLowerCase()}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div>
      {/* â”€â”€ Hero â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
      <div style={heroStyle}>
        <div style={{ maxWidth: 'var(--max-width-dashboard)', margin: '0 auto' }}>
          <Eyebrow light>Battlecard Generator</Eyebrow>
          <h1
            style={{
              fontFamily: 'var(--fd)',
              fontSize: 36,
              fontWeight: 300,
              color: '#ffffff',
              margin: '0 0 6px',
            }}
          >
            Battlecard{' '}
            <em style={{ fontStyle: 'italic', color: 'var(--gold-light)' }}>
              Generator
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
            AI-powered sales battlecards generated from live competitor data â€”
            objections, counters, and feature gaps ready for your sales team.
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
          <div style={{ display: 'flex', gap: 16, alignItems: 'flex-end' }}>
            <CompetitorSelect />
            <button style={btnGold} onClick={handleGenerate} disabled={loading}>
              Generate Battlecard
            </button>
            <button style={btnNavy} onClick={handleLoadCached} disabled={loading}>
              Load Cached
            </button>
          </div>

          {loading && (
            <div>
              <Spinner />
              <p
                style={{
                  fontFamily: 'var(--fb)',
                  fontSize: 12,
                  color: 'var(--mid)',
                  marginTop: 8,
                }}
              >
                Claude is generating your battlecard from live dataâ€¦ (~10s)
              </p>
            </div>
          )}

          {toast && <Toast message={toast.msg} type={toast.type} />}

          {card && !loading && (
            <>
              {/* Metadata */}
              <div
                style={{
                  fontFamily: 'var(--fb)',
                  fontSize: 11,
                  color: 'var(--mid)',
                }}
              >
                Generated: {card.generated_at}
              </div>

              {/* Pitch */}
              <section>
                <Eyebrow>Recommended Pitch</Eyebrow>
                <div
                  style={{
                    borderLeft: '3px solid var(--gold)',
                    backgroundColor: 'rgba(200,152,42,0.06)',
                    borderRadius: '0 var(--radius-md) var(--radius-md) 0',
                    padding: '20px 24px',
                    fontFamily: 'var(--fb)',
                    fontSize: 14,
                    color: 'var(--dark)',
                    lineHeight: 1.75,
                  }}
                >
                  {card.recommended_pitch}
                </div>
              </section>

              {/* Objections */}
              {card.objections.length > 0 && (
                <section>
                  <Eyebrow>Objections & Counters</Eyebrow>
                  <h2
                    style={{
                      fontFamily: 'var(--fd)',
                      fontSize: 22,
                      fontWeight: 300,
                      color: 'var(--dark)',
                      marginBottom: 20,
                    }}
                  >
                    Handle every <em style={{ fontStyle: 'italic', color: 'var(--gold)' }}>objection</em> with confidence
                  </h2>
                  <div
                    style={{ display: 'flex', flexDirection: 'column', gap: 16 }}
                  >
                    {card.objections.map((o, i) => (
                      <div
                        key={i}
                        style={{
                          backgroundColor: 'var(--white)',
                          borderRadius: 'var(--radius-md)',
                          padding: '20px 24px',
                          boxShadow: 'var(--shadow-card)',
                          border: '1px solid var(--primary-10)',
                        }}
                      >
                        <div
                          style={{
                            fontFamily: 'var(--fb)',
                            fontSize: 14,
                            fontWeight: 600,
                            color: 'var(--primary)',
                            marginBottom: 12,
                          }}
                        >
                          {o.objection}
                        </div>
                        <div
                          style={{
                            display: 'grid',
                            gridTemplateColumns: '1fr 1fr',
                            gap: 16,
                            marginBottom: 12,
                          }}
                        >
                          <div>
                            <div
                              style={{
                                fontFamily: 'var(--fb)',
                                fontSize: 10,
                                fontWeight: 600,
                                letterSpacing: '2px',
                                textTransform: 'uppercase',
                                color: 'var(--mid)',
                                marginBottom: 4,
                              }}
                            >
                              Evidence
                            </div>
                            <div
                              style={{
                                fontFamily: 'var(--fb)',
                                fontSize: 13,
                                color: 'var(--dark)',
                                lineHeight: 1.6,
                              }}
                            >
                              {o.evidence}
                            </div>
                          </div>
                          <div>
                            <div
                              style={{
                                fontFamily: 'var(--fb)',
                                fontSize: 10,
                                fontWeight: 600,
                                letterSpacing: '2px',
                                textTransform: 'uppercase',
                                color: 'var(--mid)',
                                marginBottom: 4,
                              }}
                            >
                              Counter
                            </div>
                            <div
                              style={{
                                fontFamily: 'var(--fb)',
                                fontSize: 13,
                                color: 'var(--dark)',
                                lineHeight: 1.6,
                              }}
                            >
                              {o.counter}
                            </div>
                          </div>
                        </div>
                        {o.proof_quote && (
                          <div
                            style={{
                              fontFamily: 'var(--fb)',
                              fontSize: 12,
                              fontStyle: 'italic',
                              color: 'var(--mid)',
                              borderLeft: '2px solid var(--primary-30)',
                              paddingLeft: 12,
                              lineHeight: 1.6,
                            }}
                          >
                            "{o.proof_quote}"
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {/* Feature gaps */}
              {card.feature_gaps.length > 0 && (
                <section>
                  <Eyebrow>Feature Gaps</Eyebrow>
                  <h2
                    style={{
                      fontFamily: 'var(--fd)',
                      fontSize: 22,
                      fontWeight: 300,
                      color: 'var(--dark)',
                      marginBottom: 20,
                    }}
                  >
                    Where {card.competitor} <em style={{ fontStyle: 'italic', color: 'var(--gold)' }}>falls short</em>
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
                          <th style={thStyle}>Feature Gap</th>
                          <th style={{ ...thStyle, textAlign: 'right' }}>
                            Mentions
                          </th>
                          <th style={thStyle}>Our Advantage</th>
                        </tr>
                      </thead>
                      <tbody>
                        {card.feature_gaps.map((g, i) => (
                          <tr
                            key={i}
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
                                fontWeight: 500,
                                color: 'var(--dark)',
                                padding: '10px 14px',
                              }}
                            >
                              {g.gap}
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
                              {g.frequency}
                            </td>
                            <td
                              style={{
                                fontFamily: 'var(--fb)',
                                fontSize: 13,
                                color: 'var(--dark)',
                                padding: '10px 14px',
                              }}
                            >
                              {g.your_advantage}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>
              )}

              {/* Download */}
              <div>
                <button style={btnNavy} onClick={handleDownload}>
                  Download Markdown
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
