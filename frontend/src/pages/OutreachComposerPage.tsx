import { useEffect, useState } from 'react'
import type React from 'react'
import { api } from '../services/api'
import type { OutreachBundle } from '../services/api'
import Eyebrow from '../components/Eyebrow'
import Spinner from '../components/Spinner'
import CompetitorSelect from '../components/CompetitorSelect'
import { useAppStore } from '../stores/appStore'

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

const TABS = ['Email', 'LinkedIn', 'Call'] as const
type Tab = (typeof TABS)[number]

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  function handleCopy() {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }
  return (
    <button
      onClick={handleCopy}
      style={{
        fontFamily:      'var(--fb)',
        fontSize:        9,
        fontWeight:      700,
        letterSpacing:   '2px',
        textTransform:   'uppercase',
        backgroundColor: copied ? 'rgba(39,185,124,0.12)' : 'var(--primary-10)',
        color:           copied ? 'var(--status-green)' : 'var(--primary)',
        border:          'none',
        borderRadius:    'var(--radius-sm)',
        padding:         '6px 14px',
        cursor:          'pointer',
        transition:      'background-color 0.2s, color 0.2s',
      }}
    >
      {copied ? 'Copied ✓' : 'Copy'}
    </button>
  )
}

export default function OutreachComposerPage() {
  const { competitor, outreachPrefill, setOutreachPrefill } = useAppStore()

  const [complaint, setComplaint] = useState('')
  const [username,  setUsername]  = useState('')
  const [bundle,    setBundle]    = useState<OutreachBundle | null>(null)
  const [loading,   setLoading]   = useState(false)
  const [activeTab, setActiveTab] = useState<Tab>('Email')

  // Apply prefill from HotProspectPage "Compose Outreach" button
  useEffect(() => {
    if (outreachPrefill) {
      setComplaint(outreachPrefill.complaint)
      setUsername(outreachPrefill.username)
      setOutreachPrefill(null)
    }
  }, [outreachPrefill, setOutreachPrefill])

  function handleCompose() {
    if (!complaint.trim()) return
    setLoading(true)
    setBundle(null)
    api.outreach.compose(competitor, complaint, username || 'Prospect')
      .then(setBundle)
      .catch(() => setBundle(null))
      .finally(() => setLoading(false))
  }

  const linkedinCount = bundle?.linkedin_dm.length ?? 0

  return (
    <div>
      {/* ── Hero ─────────────────────────────────────────────────────────── */}
      <div style={heroStyle}>
        <div style={{ maxWidth: 'var(--max-width-dashboard)', margin: '0 auto' }}>
          <Eyebrow light>Outreach Composer</Eyebrow>
          <h1 style={{ fontFamily: 'var(--fd)', fontSize: 36, fontWeight: 300, color: '#fff', margin: '0 0 6px', lineHeight: 1.2 }}>
            From signal to{' '}
            <em style={{ fontStyle: 'italic', color: 'var(--gold-light)' }}>sent</em>
          </h1>
          <p style={{ fontFamily: 'var(--fb)', fontSize: 13, color: 'rgba(255,255,255,0.45)', maxWidth: 560 }}>
            Paste a prospect's complaint, pick their competitor, and get three personalised outreach variants — email, LinkedIn DM, and cold call bullets — in under 60 seconds.
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
          {/* Input panel */}
          <section>
            <Eyebrow>Prospect Details</Eyebrow>
            <div style={{ ...card, padding: 28, borderTop: '3px solid var(--gold)', display: 'flex', flexDirection: 'column', gap: 20 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
                <CompetitorSelect label="Competitor being left" />
                <div>
                  <label style={{ fontFamily: 'var(--fb)', fontSize: 10, fontWeight: 500, letterSpacing: '2px', textTransform: 'uppercase', color: 'var(--mid)', display: 'block', marginBottom: 6 }}>
                    Username / Name (optional)
                  </label>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="e.g. frustrated_admin_sf"
                    style={{
                      fontFamily:   'var(--fb)',
                      fontSize:     13,
                      color:        'var(--dark)',
                      border:       '1px solid var(--primary-10)',
                      borderRadius: 'var(--radius-sm)',
                      padding:      '8px 12px',
                      backgroundColor: 'var(--white)',
                      width:        '100%',
                      outline:      'none',
                    }}
                  />
                </div>
              </div>

              <div>
                <label style={{ fontFamily: 'var(--fb)', fontSize: 10, fontWeight: 500, letterSpacing: '2px', textTransform: 'uppercase', color: 'var(--mid)', display: 'block', marginBottom: 6 }}>
                  Prospect's complaint — paste from Reddit, G2, or type directly
                </label>
                <textarea
                  value={complaint}
                  onChange={(e) => setComplaint(e.target.value)}
                  placeholder="e.g. Switching from Salesforce after 3 years. The pricing keeps going up and support is terrible. Looking for alternative CRM recommendations."
                  rows={4}
                  style={{
                    fontFamily:      'var(--fb)',
                    fontSize:        13,
                    color:           'var(--dark)',
                    border:          '1px solid var(--primary-10)',
                    borderRadius:    'var(--radius-sm)',
                    padding:         '10px 14px',
                    backgroundColor: 'var(--white)',
                    width:           '100%',
                    resize:          'vertical',
                    outline:         'none',
                    lineHeight:      1.7,
                  }}
                />
              </div>

              <div>
                <button
                  style={{ ...btnGold, opacity: complaint.trim() ? 1 : 0.5 }}
                  onClick={handleCompose}
                  disabled={loading || !complaint.trim()}
                >
                  Compose Outreach
                </button>
              </div>
            </div>
          </section>

          {loading && (
            <div>
              <Spinner />
              <p style={{ fontFamily: 'var(--fb)', fontSize: 12, color: 'var(--mid)', marginTop: 8 }}>
                Claude is composing your outreach variants… (~10s)
              </p>
            </div>
          )}

          {!loading && bundle && (
            <section>
              <Eyebrow>Outreach Variants</Eyebrow>
              <h2 style={{ fontFamily: 'var(--fd)', fontSize: 22, fontWeight: 300, color: 'var(--dark)', marginBottom: 20 }}>
                Three ready-to-send{' '}
                <em style={{ fontStyle: 'italic', color: 'var(--gold)' }}>variants</em>
              </h2>

              {/* Tab bar */}
              <div style={{ ...card, overflow: 'hidden' }}>
                <div style={{
                  display:      'flex',
                  borderBottom: '1px solid var(--primary-10)',
                  backgroundColor: 'var(--primary-10)',
                }}>
                  {TABS.map((tab) => (
                    <button
                      key={tab}
                      onClick={() => setActiveTab(tab)}
                      style={{
                        background:    'none',
                        border:        'none',
                        borderBottom:  `2px solid ${activeTab === tab ? 'var(--gold)' : 'transparent'}`,
                        cursor:        'pointer',
                        fontFamily:    'var(--fb)',
                        fontSize:      11,
                        fontWeight:    500,
                        letterSpacing: '1.5px',
                        textTransform: 'uppercase',
                        padding:       '12px 24px',
                        marginBottom:  -1,
                        color:         activeTab === tab ? 'var(--primary)' : 'var(--mid)',
                        transition:    'color 0.15s',
                      }}
                    >
                      {tab}
                    </button>
                  ))}
                </div>

                <div style={{ padding: 28 }}>
                  {/* Email tab */}
                  {activeTab === 'Email' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                      <div>
                        <div style={{ fontFamily: 'var(--fb)', fontSize: 9, letterSpacing: '3px', textTransform: 'uppercase', color: 'var(--mid)', marginBottom: 6 }}>
                          Subject line
                        </div>
                        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                          <div style={{ fontFamily: 'var(--fd)', fontSize: 16, fontWeight: 300, color: 'var(--dark)', flex: 1 }}>
                            {bundle.email.subject}
                          </div>
                          <CopyButton text={bundle.email.subject} />
                        </div>
                      </div>
                      <div style={{ borderTop: '1px solid var(--primary-10)', paddingTop: 16 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                          <div style={{ fontFamily: 'var(--fb)', fontSize: 9, letterSpacing: '3px', textTransform: 'uppercase', color: 'var(--mid)' }}>
                            Email body
                          </div>
                          <CopyButton text={bundle.email.body} />
                        </div>
                        <textarea
                          value={bundle.email.body}
                          readOnly
                          rows={10}
                          style={{
                            width:           '100%',
                            fontFamily:      'var(--fb)',
                            fontSize:        13,
                            color:           'var(--dark)',
                            lineHeight:      1.75,
                            border:          '1px solid var(--primary-10)',
                            borderRadius:    'var(--radius-sm)',
                            padding:         '12px 16px',
                            backgroundColor: 'var(--light)',
                            resize:          'vertical',
                            outline:         'none',
                          }}
                        />
                      </div>
                    </div>
                  )}

                  {/* LinkedIn tab */}
                  {activeTab === 'LinkedIn' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ fontFamily: 'var(--fb)', fontSize: 9, letterSpacing: '3px', textTransform: 'uppercase', color: 'var(--mid)' }}>
                          LinkedIn DM
                        </div>
                        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                          <span style={{
                            fontFamily: 'var(--fb)',
                            fontSize:   11,
                            color:      linkedinCount > 280 ? 'var(--status-red)' : 'var(--mid)',
                            fontWeight: linkedinCount > 280 ? 600 : 400,
                          }}>
                            {linkedinCount}/280 chars
                          </span>
                          <CopyButton text={bundle.linkedin_dm} />
                        </div>
                      </div>
                      <textarea
                        value={bundle.linkedin_dm}
                        readOnly
                        rows={5}
                        style={{
                          width:           '100%',
                          fontFamily:      'var(--fb)',
                          fontSize:        13,
                          color:           'var(--dark)',
                          lineHeight:      1.75,
                          border:          `1px solid ${linkedinCount > 280 ? 'var(--status-red)' : 'var(--primary-10)'}`,
                          borderRadius:    'var(--radius-sm)',
                          padding:         '12px 16px',
                          backgroundColor: 'var(--light)',
                          resize:          'none',
                          outline:         'none',
                        }}
                      />
                    </div>
                  )}

                  {/* Call tab */}
                  {activeTab === 'Call' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ fontFamily: 'var(--fb)', fontSize: 9, letterSpacing: '3px', textTransform: 'uppercase', color: 'var(--mid)' }}>
                          Cold call talk track
                        </div>
                        <CopyButton text={bundle.call_bullets.map((b, i) => `${i + 1}. ${b}`).join('\n')} />
                      </div>
                      {bundle.call_bullets.map((bullet, i) => (
                        <div key={i} style={{
                          display:         'flex',
                          gap:             16,
                          alignItems:      'flex-start',
                          backgroundColor: 'var(--light)',
                          borderRadius:    'var(--radius-sm)',
                          padding:         '14px 16px',
                          border:          '1px solid var(--primary-10)',
                        }}>
                          <div style={{
                            fontFamily:    'var(--fd)',
                            fontSize:      20,
                            fontWeight:    300,
                            color:         'var(--primary-30)',
                            lineHeight:    1,
                            flexShrink:    0,
                            minWidth:      24,
                          }}>
                            {i + 1}
                          </div>
                          <p style={{ fontFamily: 'var(--fb)', fontSize: 13, color: 'var(--dark)', lineHeight: 1.7, margin: 0 }}>
                            {bullet}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Meta */}
              <div style={{ fontFamily: 'var(--fb)', fontSize: 11, color: 'var(--mid)', marginTop: 8 }}>
                Generated for <strong>{bundle.username}</strong> leaving <strong>{bundle.competitor}</strong> · {bundle.generated_at.slice(0, 16).replace('T', ' ')} UTC
              </div>
            </section>
          )}
        </div>
      </div>
    </div>
  )
}
