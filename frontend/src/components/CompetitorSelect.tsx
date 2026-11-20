import { useEffect, useState } from 'react'
import { useAppStore } from '../stores/appStore'
import { api } from '../services/api'

const DEFAULT_OPTIONS = ['Salesforce', 'HubSpot', 'Pipedrive']

// Fetch the competitor list once per session, not on every page mount. A
// failed request is forgotten so the next mount retries; Settings calls
// refreshCompetitors() after an edit.
let competitorsRequest: Promise<string[]> | null = null
const listeners = new Set<() => void>()

export function refreshCompetitors(): void {
  competitorsRequest = null
  listeners.forEach((fn) => fn())
}
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

  const [version, setVersion] = useState(0)
  useEffect(() => {
    const bump = () => setVersion((v) => v + 1)
    listeners.add(bump)
    return () => { listeners.delete(bump) }
  }, [])

  useEffect(() => {
    let cancelled = false
    loadCompetitors()
      .then((names) => {
        if (cancelled || names.length === 0) return
        setOptions(names)
        // The selected competitor may have been removed in Settings.
        if (!names.includes(competitor)) setCompetitor(names[0])
      })
      .catch(() => {/* keep defaults */})
    return () => { cancelled = true }
  }, [version, competitor, setCompetitor])

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
