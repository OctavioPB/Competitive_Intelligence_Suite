import { useEffect, useState } from 'react'
import { useAppStore } from '../stores/appStore'
import { api } from '../services/api'

export default function CompetitorSelect({ label }: { label?: string }) {
  const { competitor, setCompetitor } = useAppStore()
  const [options, setOptions] = useState<string[]>(['Salesforce', 'HubSpot', 'Pipedrive'])

  useEffect(() => {
    api.meta
      .competitors()
      .then((r) => setOptions(r.competitors))
      .catch(() => {/* keep defaults */})
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
