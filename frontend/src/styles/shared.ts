// Style objects shared by every page — defined once so pages stay in sync.
import type { CSSProperties } from 'react'

/** Navy hero band with the faint 48px grid. */
export const heroStyle: CSSProperties = {
  backgroundColor: 'var(--primary)',
  backgroundImage:
    'linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)',
  backgroundSize: '48px 48px',
  padding: '56px 48px',
}

/** Primary action button. */
export const btnGold: CSSProperties = {
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

/** Secondary action button. */
export const btnNavy: CSSProperties = {
  ...btnGold,
  backgroundColor: 'var(--primary)',
}

/** Table header cell on a navy header row. */
export const thStyle: CSSProperties = {
  fontFamily: 'var(--fb)',
  fontSize: 10,
  fontWeight: 600,
  letterSpacing: '2px',
  textTransform: 'uppercase',
  color: '#fff',
  padding: '10px 14px',
  textAlign: 'left',
}

/** White content card surface (add padding per use). */
export const card: CSSProperties = {
  backgroundColor: 'var(--white)',
  borderRadius: 'var(--radius-md)',
  boxShadow: 'var(--shadow-card)',
  border: '1px solid var(--primary-10)',
}

/** Form field label: small caps text above its control. */
export const labelStyle: CSSProperties = {
  fontFamily: 'var(--fb)',
  fontSize: 10,
  fontWeight: 500,
  letterSpacing: '2px',
  textTransform: 'uppercase',
  color: 'var(--mid)',
  display: 'flex',
  flexDirection: 'column',
  gap: 6,
}

/** Text input / select / textarea. */
export const inputStyle: CSSProperties = {
  fontFamily: 'var(--fb)',
  fontSize: 13,
  color: 'var(--dark)',
  border: '1px solid var(--primary-10)',
  borderRadius: 'var(--radius-sm)',
  padding: '8px 10px',
  backgroundColor: 'var(--white)',
  textTransform: 'none',
  letterSpacing: 0,
  width: '100%',
}

/** Small outlined button for secondary row actions. */
export const btnGhost: CSSProperties = {
  background: 'none',
  border: '1px solid var(--primary-10)',
  borderRadius: 'var(--radius-sm)',
  fontFamily: 'var(--fb)',
  fontSize: 11,
  color: 'var(--link)',
  cursor: 'pointer',
  padding: '5px 12px',
}
