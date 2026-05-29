import { useState } from 'react'
import type React from 'react'
import type { Page } from '../App'

type NavGroupDef = {
  label: string
  pages: { id: Page; label: string }[]
}

const GROUPS: NavGroupDef[] = [
  {
    label: 'Intelligence',
    pages: [
      { id: 'pain-radar', label: 'Pain Radar'   },
      { id: 'sentiment',  label: 'Sentiment'    },
      { id: 'wish-miner', label: 'Wish Miner'   },
      { id: 'churn',      label: 'Churn Intel'  },
      { id: 'digest',     label: 'Digest'       },
    ],
  },
  {
    label: 'Revenue',
    pages: [
      { id: 'battlecard', label: 'Battlecard'   },
      { id: 'alerts',     label: 'Alerts'       },
      { id: 'prospects',  label: 'Prospects'    },
      { id: 'outreach',   label: 'Outreach'     },
    ],
  },
  {
    label: 'Platform',
    pages: [
      { id: 'info', label: 'Overview' },
    ],
  },
]

function NavGroup({ group, currentPage, onNavigate }: {
  group:       NavGroupDef
  currentPage: Page
  onNavigate:  (p: Page) => void
}) {
  const [open, setOpen]               = useState(false)
  const [hoveredPage, setHoveredPage] = useState<Page | null>(null)
  const isActive = group.pages.some((p) => p.id === currentPage)

  const btnStyle: React.CSSProperties = {
    background:      'none',
    border:          'none',
    cursor:          'pointer',
    fontFamily:      'var(--fb)',
    fontSize:        9,
    fontWeight:      500,
    letterSpacing:   '2px',
    textTransform:   'uppercase',
    padding:         '5px 10px',
    borderRadius:    'var(--radius-sm)',
    color:           isActive ? 'var(--gold-light)' : open ? 'rgba(255,255,255,0.8)' : 'rgba(255,255,255,0.45)',
    backgroundColor: isActive ? 'rgba(201,168,76,0.12)' : open ? 'rgba(255,255,255,0.05)' : 'transparent',
    display:         'flex',
    alignItems:      'center',
    gap:             5,
    transition:      'color 0.15s, background-color 0.15s',
    whiteSpace:      'nowrap',
  }

  return (
    <div
      style={{
        position:  'relative',
        alignSelf: 'stretch',
        display:   'flex',
        alignItems:'center',
      }}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button style={btnStyle}>
        {group.label}
        <span style={{
          fontSize:   7,
          opacity:    0.55,
          display:    'inline-block',
          transform:  open ? 'rotate(180deg)' : 'none',
          transition: 'transform 0.15s',
        }}>▾</span>
      </button>

      {open && (
        <div style={{
          position:        'absolute',
          top:             'calc(100% + 1px)',
          left:            0,
          backgroundColor: 'rgba(0,32,76,0.98)',
          backdropFilter:  'blur(16px)',
          border:          '1px solid rgba(255,255,255,0.1)',
          borderRadius:    'var(--radius-md)',
          boxShadow:       '0 8px 32px rgba(0,0,0,0.45)',
          padding:         '6px',
          minWidth:        156,
          zIndex:          1000,
          display:         'flex',
          flexDirection:   'column',
          gap:             2,
        }}>
          {group.pages.map((p) => {
            const isPageActive = currentPage === p.id
            const isHovered    = hoveredPage === p.id
            return (
              <button
                key={p.id}
                onClick={() => { onNavigate(p.id); setOpen(false) }}
                onMouseEnter={() => setHoveredPage(p.id)}
                onMouseLeave={() => setHoveredPage(null)}
                style={{
                  background:      'none',
                  border:          'none',
                  cursor:          'pointer',
                  width:           '100%',
                  textAlign:       'left',
                  fontFamily:      'var(--fb)',
                  fontSize:        11,
                  fontWeight:      isPageActive ? 600 : 400,
                  letterSpacing:   '0.5px',
                  color:           isPageActive ? 'var(--gold-light)' : isHovered ? '#fff' : 'rgba(255,255,255,0.65)',
                  backgroundColor: isPageActive ? 'rgba(201,168,76,0.10)' : isHovered ? 'rgba(255,255,255,0.06)' : 'transparent',
                  padding:         '7px 12px',
                  borderRadius:    6,
                  transition:      'background-color 0.1s, color 0.1s',
                  whiteSpace:      'nowrap',
                }}
              >
                {p.label}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default function Nav({
  currentPage,
  onNavigate,
  theme,
  onToggleTheme,
}: {
  currentPage:   Page
  onNavigate:    (p: Page) => void
  theme:         'light' | 'dark'
  onToggleTheme: () => void
}) {
  return (
    <nav
      style={{
        backgroundColor: 'rgba(0,51,102,0.97)',
        backdropFilter:  'blur(12px)',
        height:          'var(--nav-height)',
        position:        'sticky',
        top:             0,
        zIndex:          999,
        borderBottom:    '1px solid rgba(255,255,255,0.08)',
        padding:         '0 40px',
        display:         'flex',
        alignItems:      'center',
        justifyContent:  'space-between',
      }}
    >
      {/* Left — OPB monogram + app title */}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, flexShrink: 0, flex: 1 }}>
        <div
          style={{
            display:    'flex',
            alignItems: 'baseline',
            gap:        1,
            cursor:     'pointer',
            userSelect: 'none',
          }}
          onClick={() => onNavigate('home')}
        >
          <span style={{ fontFamily: 'var(--fd)', fontSize: 20, fontWeight: 300, color: '#fff', lineHeight: 1 }}>
            O
          </span>
          <em style={{ fontFamily: 'var(--fd)', fontSize: 20, fontWeight: 300, fontStyle: 'italic', color: 'var(--gold-light)', lineHeight: 1 }}>
            PB
          </em>
        </div>
        <span style={{
          fontFamily:    'var(--fb)',
          fontSize:      9,
          letterSpacing: '3px',
          textTransform: 'uppercase',
          color:         'rgba(255,255,255,0.4)',
        }}>
          RivalSense
        </span>
      </div>

      {/* Right — home + grouped nav + theme toggle */}
      <div style={{ display: 'flex', alignItems: 'stretch', gap: 4 }}>
        <button
          onClick={() => onNavigate('home')}
          style={{
            background:      'none',
            border:          'none',
            cursor:          'pointer',
            fontFamily:      'var(--fb)',
            fontSize:        9,
            fontWeight:      500,
            letterSpacing:   '2px',
            textTransform:   'uppercase',
            padding:         '5px 10px',
            borderRadius:    'var(--radius-sm)',
            color:           currentPage === 'home' ? 'var(--gold-light)' : 'rgba(255,255,255,0.45)',
            backgroundColor: currentPage === 'home' ? 'rgba(201,168,76,0.12)' : 'transparent',
            alignSelf:       'center',
            transition:      'color 0.15s, background-color 0.15s',
            whiteSpace:      'nowrap',
          }}
        >
          Home
        </button>
        {GROUPS.map((group) => (
          <NavGroup
            key={group.label}
            group={group}
            currentPage={currentPage}
            onNavigate={onNavigate}
          />
        ))}

        <button
          style={{
            background:      'none',
            backgroundColor: 'transparent',
            border:          'none',
            color:           'rgba(255,255,255,0.45)',
            cursor:          'pointer',
            fontSize:        14,
            padding:         '3px 8px',
            borderRadius:    'var(--radius-sm)',
            marginLeft:      8,
            alignSelf:       'center',
          }}
          onClick={onToggleTheme}
          title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {theme === 'dark' ? '☀' : '◑'}
        </button>
      </div>
    </nav>
  )
}
