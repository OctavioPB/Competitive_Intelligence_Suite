import { useEffect, useState } from 'react'
import { api } from '../services/api'
import type { DataStatus } from '../services/api'

// Live ingestion silently falls back to sample reviews when a scraper is
// blocked. This strip makes that visible on every page so nobody presents
// sample data as real competitor intelligence.
export default function DataSourceBanner() {
  const [status, setStatus] = useState<DataStatus | null>(null)

  useEffect(() => {
    let cancelled = false
    api.meta
      .dataStatus()
      .then((s) => { if (!cancelled) setStatus(s) })
      .catch(() => {/* backend down — pages show their own errors */})
    return () => { cancelled = true }
  }, [])

  if (!status) return null

  const affected = status.competitors.filter((c) => c.synthetic > 0)
  const allSynthetic =
    affected.length > 0 && status.competitors.every((c) => c.reviews === 0 || c.synthetic === c.reviews)

  let message: string
  if (status.demo_mode) {
    message = 'Demo mode: every review and insight in this app is generated from sample data.'
  } else if (affected.length === 0) {
    return null
  } else if (allSynthetic) {
    message = 'All data is sample data: live scraping fell back to synthetic reviews. Treat insights as illustrative.'
  } else {
    const parts = affected.map((c) => `${c.name} ${Math.round((c.synthetic / c.reviews) * 100)}%`)
    message = `Part of the data is synthetic sample data (${parts.join(' · ')}) because live scraping was blocked. Treat those competitors' insights as illustrative.`
  }

  return (
    <div
      role="status"
      style={{
        backgroundColor: 'var(--status-orange-bg)',
        borderBottom:    '1px solid rgba(240,112,32,0.25)',
        color:           'var(--status-orange)',
        fontFamily:      'var(--fb)',
        fontSize:        12,
        fontWeight:      500,
        padding:         '8px 48px',
        textAlign:       'center',
      }}
    >
      {message}
    </div>
  )
}
