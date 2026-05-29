import { useState } from 'react'
import type React from 'react'
import Eyebrow from '../components/Eyebrow'

const heroStyle: React.CSSProperties = {
  backgroundColor: 'var(--primary)',
  backgroundImage:
    'linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)',
  backgroundSize: '48px 48px',
  padding: '52px 48px 0',
}

const TABS = ['Business View', 'Engineering View'] as const
type Tab = (typeof TABS)[number]

const MODULE_LIST = [
  {
    name: 'Pain Point Radar',
    desc: 'Ranks competitor pain points by mention frequency, severity score (0â€“1), and trend direction. Surfaces the specific friction categories â€” pricing, support, UX â€” where your product can win.',
  },
  {
    name: 'Sentiment Timeline',
    desc: '18-month rolling sentiment analysis with news event overlay. Spot sentiment drops before competitors recover and time your outreach to the most vulnerable window.',
  },
  {
    name: 'Feature Wish Miner',
    desc: 'Clusters competitor user feature requests from review data and automatically flags which ones your product already solves. Quantifies your unfair advantage by request volume.',
  },
  {
    name: 'Battlecard Generator',
    desc: 'Generates AI-powered sales battlecards from live competitor data. Each card includes a recommended pitch, objection counters with evidence, and feature gap analysis.',
  },
  {
    name: 'Trigger Alerts',
    desc: 'Detects vulnerability signals â€” sentiment drops, negative news articles, and review spikes â€” and generates personalised outreach drafts using Claude or template substitution.',
  },
  {
    name: 'Hot Prospect Finder',
    desc: 'Surfaces Reddit users actively expressing switching intent from competitors. Each lead is enriched with a complaint summary, company signals, and a suggested outreach angle.',
  },
]

const TECH_STACK = [
  { layer: 'Frontend', tech: 'React 18 + TypeScript 5.5 + Vite 5' },
  { layer: 'State management', tech: 'Zustand 4' },
  { layer: 'Styling', tech: 'Inline React.CSSProperties + OPB design tokens' },
  { layer: 'Charts', tech: 'Hand-coded SVG (no charting library)' },
  { layer: 'Backend API', tech: 'FastAPI + Uvicorn (Python 3.12)' },
  { layer: 'Database', tech: 'SQLite via custom db.py wrapper' },
  { layer: 'AI / LLM', tech: 'Claude claude-sonnet-4-6 via Anthropic SDK' },
  { layer: 'Sentiment scoring', tech: 'VADER (NLTK) + custom pipeline' },
  { layer: 'Data ingestion', tech: 'G2, Trustpilot, Reddit (PRAW), NewsAPI' },
  { layer: 'Scheduling', tech: 'APScheduler (daily scrape, weekly digest)' },
  { layer: 'Alerts / export', tech: 'Slack Webhooks · SendGrid · CSV/JSON' },
]

const card: React.CSSProperties = {
  backgroundColor: 'var(--white)',
  borderRadius: 'var(--radius-md)',
  padding: '20px 24px',
  boxShadow: 'var(--shadow-card)',
  border: '1px solid var(--primary-10)',
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

export default function InfoPage() {
  const [tab, setTab] = useState<Tab>('Business View')

  return (
    <div>
      {/* â”€â”€ Hero â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
      <div style={heroStyle}>
        <div style={{ maxWidth: 'var(--max-width-dashboard)', margin: '0 auto' }}>
          <Eyebrow light>Platform Info</Eyebrow>
          <h1
            style={{
              fontFamily: 'var(--fd)',
              fontSize: 36,
              fontWeight: 300,
              color: '#ffffff',
              margin: '0 0 6px',
            }}
          >
            Platform{' '}
            <em style={{ fontStyle: 'italic', color: 'var(--gold-light)' }}>
              Information
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
            How RivalSense works â€” business capabilities and engineering
            architecture for the Competitive Intelligence Suite.
          </p>

          {/* Tab bar — sits flush at bottom of hero */}
          <div style={{ display: 'flex', gap: 4, marginTop: 36, borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
            {TABS.map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                style={{
                  background: 'none',
                  border: 'none',
                  borderBottom: `2px solid ${t === tab ? 'var(--gold-light)' : 'transparent'}`,
                  cursor: 'pointer',
                  fontFamily: 'var(--fb)',
                  fontSize: 11,
                  fontWeight: 500,
                  letterSpacing: '1.5px',
                  textTransform: 'uppercase',
                  padding: '10px 20px',
                  marginBottom: -1,
                  color: t === tab ? 'var(--gold-light)' : 'rgba(255,255,255,0.4)',
                  transition: 'color 0.15s',
                }}
              >
                {t}
              </button>
            ))}
          </div>
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
          {tab === 'Business View' && (
            <>
              {/* What it does */}
              <section>
                <Eyebrow>Overview</Eyebrow>
                <h2
                  style={{
                    fontFamily: 'var(--fd)',
                    fontSize: 22,
                    fontWeight: 300,
                    color: 'var(--dark)',
                    marginBottom: 16,
                  }}
                >
                  What RivalSense <em style={{ fontStyle: 'italic', color: 'var(--gold)' }}>does</em>
                </h2>
                <div style={card}>
                  <p
                    style={{
                      fontFamily: 'var(--fb)',
                      fontSize: 14,
                      color: 'var(--dark)',
                      lineHeight: 1.75,
                      marginBottom: 12,
                    }}
                  >
                    RivalSense is a competitive intelligence platform that
                    continuously monitors your competitors â€” Salesforce, HubSpot,
                    and Pipedrive â€” across review sites, Reddit, and news sources.
                    It transforms raw customer signals into actionable sales
                    intelligence that your team can act on immediately.
                  </p>
                  <p
                    style={{
                      fontFamily: 'var(--fb)',
                      fontSize: 14,
                      color: 'var(--dark)',
                      lineHeight: 1.75,
                    }}
                  >
                    Instead of manually reading thousands of reviews or setting up
                    alerts for competitor news, RivalSense surfaces the highest-value
                    signals automatically â€” ranked by urgency, enriched with context,
                    and paired with ready-to-use outreach drafts.
                  </p>
                </div>
              </section>

              {/* Modules */}
              <section>
                <Eyebrow>Intelligence Modules</Eyebrow>
                <h2
                  style={{
                    fontFamily: 'var(--fd)',
                    fontSize: 22,
                    fontWeight: 300,
                    color: 'var(--dark)',
                    marginBottom: 20,
                  }}
                >
                  Six modules, one revenue <em style={{ fontStyle: 'italic', color: 'var(--gold)' }}>workflow</em>
                </h2>
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(2, 1fr)',
                    gap: 16,
                  }}
                >
                  {MODULE_LIST.map((m) => (
                    <div key={m.name} style={card}>
                      <div
                        style={{
                          fontFamily: 'var(--fb)',
                          fontSize: 13,
                          fontWeight: 600,
                          color: 'var(--primary)',
                          marginBottom: 8,
                        }}
                      >
                        {m.name}
                      </div>
                      <p
                        style={{
                          fontFamily: 'var(--fb)',
                          fontSize: 13,
                          color: 'var(--mid)',
                          lineHeight: 1.65,
                        }}
                      >
                        {m.desc}
                      </p>
                    </div>
                  ))}
                </div>
              </section>

              {/* Advantages */}
              <section>
                <Eyebrow>Key Advantages</Eyebrow>
                <h2
                  style={{
                    fontFamily: 'var(--fd)',
                    fontSize: 22,
                    fontWeight: 300,
                    color: 'var(--dark)',
                    marginBottom: 16,
                  }}
                >
                  Why teams <em style={{ fontStyle: 'italic', color: 'var(--gold)' }}>choose</em> RivalSense
                </h2>
                <div style={card}>
                  {[
                    'Signals are ranked by urgency â€” not just recency â€” so your team knows exactly where to focus.',
                    'Outreach drafts are generated automatically, cutting from signal to email in under 60 seconds.',
                    'All data is structured and stored locally â€” no vendor lock-in, no per-seat pricing on data.',
                    'Battlecards and prospect lists export as Markdown and CSV for immediate use in your existing workflow.',
                  ].map((point, i) => (
                    <div
                      key={i}
                      style={{
                        display: 'flex',
                        gap: 12,
                        alignItems: 'flex-start',
                        marginBottom: i < 3 ? 12 : 0,
                      }}
                    >
                      <div
                        style={{
                          width: 6,
                          height: 6,
                          borderRadius: '50%',
                          backgroundColor: 'var(--gold)',
                          flexShrink: 0,
                          marginTop: 7,
                        }}
                      />
                      <p
                        style={{
                          fontFamily: 'var(--fb)',
                          fontSize: 14,
                          color: 'var(--dark)',
                          lineHeight: 1.65,
                        }}
                      >
                        {point}
                      </p>
                    </div>
                  ))}
                </div>
              </section>
            </>
          )}

          {tab === 'Engineering View' && (
            <>
              {/* Architecture */}
              <section>
                <Eyebrow>Architecture</Eyebrow>
                <h2
                  style={{
                    fontFamily: 'var(--fd)',
                    fontSize: 22,
                    fontWeight: 300,
                    color: 'var(--dark)',
                    marginBottom: 16,
                  }}
                >
                  System <em style={{ fontStyle: 'italic', color: 'var(--gold)' }}>overview</em>
                </h2>
                <div style={card}>
                  <p
                    style={{
                      fontFamily: 'var(--fb)',
                      fontSize: 14,
                      color: 'var(--dark)',
                      lineHeight: 1.75,
                      marginBottom: 12,
                    }}
                  >
                    The platform uses a decoupled architecture: a FastAPI backend
                    wraps all existing Python analysis modules, and a React 18
                    frontend consumes the REST API via a Vite dev proxy. No
                    server-side rendering â€” the frontend is a pure SPA.
                  </p>
                  <p
                    style={{
                      fontFamily: 'var(--fb)',
                      fontSize: 14,
                      color: 'var(--dark)',
                      lineHeight: 1.75,
                    }}
                  >
                    All chart rendering uses hand-coded SVG inside React components â€”
                    no external charting library. State is managed with Zustand for
                    globally shared values (selected competitor) and React
                    <code style={{ fontSize: 12, backgroundColor: 'var(--primary-10)', padding: '1px 4px', borderRadius: 3 }}>
                      {' '}useState{' '}
                    </code>
                    for page-local state.
                  </p>
                </div>
              </section>

              {/* Tech stack */}
              <section>
                <Eyebrow>Tech Stack</Eyebrow>
                <h2
                  style={{
                    fontFamily: 'var(--fd)',
                    fontSize: 22,
                    fontWeight: 300,
                    color: 'var(--dark)',
                    marginBottom: 20,
                  }}
                >
                  Technologies <em style={{ fontStyle: 'italic', color: 'var(--gold)' }}>used</em>
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
                        <th style={thStyle}>Layer</th>
                        <th style={thStyle}>Technology</th>
                      </tr>
                    </thead>
                    <tbody>
                      {TECH_STACK.map((row, i) => (
                        <tr
                          key={row.layer}
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
                              fontWeight: 600,
                              color: 'var(--primary)',
                              padding: '10px 14px',
                            }}
                          >
                            {row.layer}
                          </td>
                          <td
                            style={{
                              fontFamily: 'var(--fb)',
                              fontSize: 13,
                              color: 'var(--dark)',
                              padding: '10px 14px',
                            }}
                          >
                            {row.tech}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>

              {/* Module descriptions */}
              <section>
                <Eyebrow>Module Details</Eyebrow>
                <h2
                  style={{
                    fontFamily: 'var(--fd)',
                    fontSize: 22,
                    fontWeight: 300,
                    color: 'var(--dark)',
                    marginBottom: 20,
                  }}
                >
                  Backend module <em style={{ fontStyle: 'italic', color: 'var(--gold)' }}>descriptions</em>
                </h2>
                <div
                  style={{ display: 'flex', flexDirection: 'column', gap: 12 }}
                >
                  {[
                    {
                      module: 'modules/pain_point_radar.py',
                      fn: 'get_pain_points(competitor, top_n)',
                      desc: 'Queries the SQLite DB for topic-labelled reviews, aggregates mention counts and sentiment deltas, and computes trend direction by comparing recent vs baseline windows.',
                    },
                    {
                      module: 'modules/sentiment_timeline.py',
                      fn: 'build_timeline(competitor, months)',
                      desc: 'Builds a monthly YYYY-MM bucketed DataFrame of avg_sentiment, stddev, review count, and the most-mentioned news headline per month.',
                    },
                    {
                      module: 'modules/feature_wish_miner.py',
                      fn: 'extract_wishes() + flag_own_features()',
                      desc: 'Clusters feature request phrases from reviews using keyword matching, then cross-references against OWN_FEATURES to flag coverage.',
                    },
                    {
                      module: 'modules/battlecard_generator.py',
                      fn: 'generate_battlecard(competitor)',
                      desc: 'Calls Claude claude-sonnet-4-6 with a structured prompt built from live pain point and sentiment data to produce JSON battlecard output. Supports caching.',
                    },
                    {
                      module: 'modules/trigger_alerts.py',
                      fn: 'check_triggers(competitor_list)',
                      desc: 'Runs three detectors per competitor: sentiment delta < -0.5 in last 7 days, negative keyword in recent news, and 2Ã— review spike vs 30-day baseline.',
                    },
                    {
                      module: 'modules/hot_prospect_finder.py',
                      fn: 'scan_reddit() + enrich_lead()',
                      desc: 'Uses PRAW to search subreddits for switching-intent phrases. Scores each post on a 0â€“1 urgency scale and enriches with complaint summary and outreach angle.',
                    },
                  ].map((m) => (
                    <div key={m.module} style={card}>
                      <div
                        style={{
                          fontFamily: 'var(--fb)',
                          fontSize: 11,
                          color: 'var(--mid)',
                          marginBottom: 4,
                          letterSpacing: '0.5px',
                        }}
                      >
                        <code
                          style={{
                            backgroundColor: 'var(--primary-10)',
                            padding: '1px 6px',
                            borderRadius: 4,
                            fontSize: 11,
                          }}
                        >
                          {m.module}
                        </code>
                      </div>
                      <div
                        style={{
                          fontFamily: 'var(--fb)',
                          fontSize: 12,
                          fontWeight: 600,
                          color: 'var(--primary)',
                          marginBottom: 8,
                        }}
                      >
                        {m.fn}
                      </div>
                      <p
                        style={{
                          fontFamily: 'var(--fb)',
                          fontSize: 13,
                          color: 'var(--mid)',
                          lineHeight: 1.65,
                        }}
                      >
                        {m.desc}
                      </p>
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
