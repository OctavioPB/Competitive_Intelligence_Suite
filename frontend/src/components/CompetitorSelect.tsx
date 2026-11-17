import { useEffect, useState } from 'react'
import { useAppStore } from '../stores/appStore'
import { api } from '../services/api'

const DEFAULT_OPTIONS = ['Salesforce', 'HubSpot', 'Pipedrive']

// The competitor list is static config — fetch it once per session, not on
// every page mount. A failed request is forgotten so the next mount retries.
let competitorsRequest: Promise<string[]> | null = null
function loadCompetitors(): Promise<string[]> {
  competitorsRequest ??= api.meta
    .competitors()
    .then((r) => r.competitors)
    .catch((err) => {
      competitorsRequest = null
      throw err
    })
  return competitorsRequest
}

export default function CompetitorSelect({ label }: { label?: string }) {
  const { competitor, setCompetitor } = useAppStore()
  const [options, setOptions] = useState<string[]>(DEFAULT_OPTIONS)

  useEffect(() => {
    let cancelled = false
    loadCompetitors()
      .then((names) => { if (!cancelled && names.length > 0) setOptions(names) })
      .catch(() => {/* keep defaults */})
    return () => { cancelled = true }
  }, [])

  return (
    <div>
      <label
        style={{
          fontFamily: 'var(--fb)',
          fontSize: 10,
          fontWeight: 500,
          letterSpacing: '2px',
          textTransform: 'uppercase',
          color: 'var(--mid)',
          display: 'block',
          marginBottom: 6,
        }}
      >
        {label ?? 'Competitor'}
      </label>
      <select
        value={competitor}
        onChange={(e) => setCompetitor(e.target.value)}
        style={{
          fontFamily: 'var(--fb)',
          fontSize: 13,
          color: 'var(--dark)',
          border: '1px solid var(--primary-10)',
          borderRadius: 'var(--radius-sm)',
          padding: '8px 12px',
          backgroundColor: 'var(--white)',
          cursor: 'pointer',
          minWidth: 160,
        }}
      >
        {options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    </div>
  )
}
