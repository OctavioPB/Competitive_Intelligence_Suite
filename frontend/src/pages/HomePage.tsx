import type React from 'react'
import type { Page } from '../App'
import Eyebrow from '../components/Eyebrow'

const MODULES: { page: Page; title: string; desc: string }[] = [
  {
    page: 'pain-radar',
    title: 'Pain Point Radar',
    desc: 'Rank competitor pain points by severity and trend direction.',
  },
  {
    page: 'sentiment',
    title: 'Sentiment Timeline',
    desc: '18-month competitor sentiment with news event overlay.',
  },
  {
    page: 'wish-miner',
    title: 'Feature Wish Miner',
    desc: "Cluster feature requests and flag your product's advantages.",
  },
  {
    page: 'battlecard',
    title: 'Battlecard Generator',
    desc: 'AI-powered sales battlecards from live competitor data.',
  },
  {
    page: 'alerts',
    title: 'Trigger Alerts',
    desc: 'Detect vulnerability signals and draft outreach instantly.',
  },
  {
    page: 'prospects',
    title: 'Hot Prospect Finder',
    desc: 'Surface Reddit users actively switching away from competitors.',
  },
]

const heroStyle: React.CSSProperties = {
  backgroundColor: 'var(--primary)',
  backgroundImage:
    'linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)',
  backgroundSize: '48px 48px',
  padding: '56px 48px',
}

export default function HomePage({
  onNavigate,
}: {
  onNavigate: (p: Page) => void
}) {
  return (
    <div>
      {/* ── Hero ─────────────────────────────────────────────────────────── */}
      <div style={heroStyle}>
        <div
          style={{
            maxWidth: 'var(--max-width-dashboard)',
            margin: '0 auto',
          }}
        >
          <Eyebrow light>Competitive Intelligence Suite</Eyebrow>
          <h1
            style={{
              fontFamily: 'var(--fd)',
              fontSize: 36,
              fontWeight: 300,
              color: '#ffffff',
              margin: '0 0 6px',
              lineHeight: 1.2,
            }}
          >
            Competitive intelligence that{' '}
            <em style={{ fontStyle: 'italic', color: 'var(--gold-light)' }}>
              decides.
            </em>
          </h1>
          <p
            style={{
              fontFamily: 'var(--fb)',
              fontSize: 13,
              color: 'rgba(255,255,255,0.45)',
              maxWidth: 560,
              lineHeight: 1.7,
            }}
          >
            Six AI-powered modules that transform raw competitor signals — reviews,
            Reddit posts, news — into revenue-ready sales intelligence.
          </p>
        </div>
      </div>

      {/* ── Module grid ──────────────────────────────────────────────────── */}
      <div style={{ backgroundColor: 'var(--light)', minHeight: '60vh' }}>
        <div
          style={{
            maxWidth: 'var(--max-width-dashboard)',
            margin: '0 auto',
            padding: '44px 48px',
          }}
        >
          <Eyebrow>Intelligence Modules</Eyebrow>
          <h2
            style={{
              fontFamily: 'var(--fd)',
              fontSize: 22,
              fontWeight: 300,
              color: 'var(--dark)',
              marginBottom: 32,
            }}
          >
            Choose your intelligence{' '}
            <em style={{ fontStyle: 'italic', color: 'var(--gold)' }}>workflow</em>
          </h2>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: 20,
            }}
          >
            {MODULES.map(({ page, title, desc }) => (
              <div
                key={page}
                style={{
                  backgroundColor: 'var(--white)',
                  borderRadius: 'var(--radius-md)',
                  boxShadow: 'var(--shadow-card)',
                  border: '1px solid var(--primary-10)',
                  borderTop: '3px solid var(--gold)',
                  padding: '24px 24px 20px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 12,
                }}
              >
                <div
                  style={{
                    fontFamily: 'var(--fb)',
                    fontSize: 14,
                    fontWeight: 600,
                    color: 'var(--primary)',
                  }}
                >
                  {title}
                </div>
                <p
                  style={{
                    fontFamily: 'var(--fb)',
                    fontSize: 13,
                    color: 'var(--mid)',
                    lineHeight: 1.6,
                    flex: 1,
                  }}
                >
                  {desc}
                </p>
                <button
                  onClick={() => onNavigate(page)}
                  style={{
                    fontFamily: 'var(--fb)',
                    fontSize: 10,
                    fontWeight: 700,
                    letterSpacing: '2px',
                    textTransform: 'uppercase',
                    backgroundColor: 'var(--primary)',
                    color: '#fff',
                    border: 'none',
                    borderRadius: 'var(--radius-sm)',
                    padding: '9px 18px',
                    cursor: 'pointer',
                    alignSelf: 'flex-start',
                  }}
                >
                  Open →
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
