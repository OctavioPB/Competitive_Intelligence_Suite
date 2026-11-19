import { useEffect, useState } from 'react'
import { api } from '../services/api'
import type { ReviewEvidence, ReviewList, ReviewQuery } from '../services/api'
import Spinner from './Spinner'
import StatusBadge from './StatusBadge'
import { card } from '../styles/shared'
import { errorMessage } from '../hooks/useToast'

const PAGE_SIZE = 8
const PREVIEW_CHARS = 320

function sentimentBadge(score: number) {
  if (score <= -0.2)
    return { label: `Negative ${score.toFixed(2)}`, color: 'var(--status-red)', bg: 'var(--status-red-bg)' }
  if (score >= 0.2)
    return { label: `Positive ${score.toFixed(2)}`, color: 'var(--status-green)', bg: 'var(--status-green-bg)' }
  return { label: `Neutral ${score.toFixed(2)}`, color: 'var(--mid)', bg: 'var(--primary-10)' }
}

function ReviewItem({ review }: { review: ReviewEvidence }) {
  const [expanded, setExpanded] = useState(false)
  const long = review.review_text.length > PREVIEW_CHARS
  const text = expanded || !long ? review.review_text : `${review.review_text.slice(0, PREVIEW_CHARS)}…`

  return (
    <li style={{ listStyle: 'none', padding: '14px 0', borderBottom: '1px solid var(--primary-10)' }}>
      <p
        style={{
          fontFamily: 'var(--fb)',
          fontSize: 13,
          lineHeight: 1.6,
          color: 'var(--dark)',
          borderLeft: '2px solid var(--primary-30)',
          paddingLeft: 12,
        }}
      >
        “{text}”
        {long && (
          <button
            onClick={() => setExpanded((e) => !e)}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--gold)',
              cursor: 'pointer',
              fontFamily: 'var(--fb)',
              fontSize: 12,
              marginLeft: 6,
            }}
          >
            {expanded ? 'Show less' : 'Read more'}
          </button>
        )}
      </p>
      <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap', marginTop: 8, paddingLeft: 14 }}>
        <span style={{ fontFamily: 'var(--fb)', fontSize: 11, color: 'var(--mid)', textTransform: 'uppercase', letterSpacing: '1px' }}>
          {review.source} · {review.date ?? 'no date'}
          {review.rating !== null ? ` · ${review.rating.toFixed(1)}★` : ''}
        </span>
        <StatusBadge {...sentimentBadge(review.sentiment_score)} />
        {review.is_synthetic && (
          <StatusBadge label="Sample data" color="var(--status-orange)" bg="var(--status-orange-bg)" />
        )}
      </div>
    </li>
  )
}

/**
 * The individual reviews behind an aggregate (a pain point, a month…).
 * Give it a `key` that changes with the selection so paging restarts at page one.
 */
export default function EvidencePanel({
  competitor,
  query,
  title,
  onClose,
}: {
  competitor: string
  query:      ReviewQuery
  title:      string
  onClose:    () => void
}) {
  const [data, setData] = useState<ReviewList | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [limit, setLimit] = useState(PAGE_SIZE)

  const { topic, month, sort = 'negative' } = query

  useEffect(() => {
    let cancelled = false
    setError(null)
    api.reviews
      .list(competitor, { topic, month, sort, limit })
      .then((r) => { if (!cancelled) setData(r) })
      .catch((err) => { if (!cancelled) setError(errorMessage(err, 'Could not load reviews.')) })
    return () => { cancelled = true }
  }, [competitor, topic, month, sort, limit])

  // Only show a response that belongs to the current selection.
  const current =
    data && data.competitor === competitor && data.topic === (topic ?? null) && data.month === (month ?? null)
      ? data
      : null

  return (
    <section style={{ ...card, padding: '20px 24px' }} aria-live="polite">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 16 }}>
        <div>
          <div style={{ fontFamily: 'var(--fb)', fontSize: 10, letterSpacing: '3px', textTransform: 'uppercase', color: 'var(--gold)' }}>
            Evidence
          </div>
          <h3 style={{ fontFamily: 'var(--fd)', fontSize: 20, fontWeight: 300, color: 'var(--dark)' }}>{title}</h3>
          {current && (
            <div style={{ fontFamily: 'var(--fb)', fontSize: 12, color: 'var(--mid)' }}>
              Showing {current.reviews.length} of {current.total} reviews ·{' '}
              {sort === 'negative' ? 'most negative first' : sort === 'positive' ? 'most positive first' : 'newest first'}
            </div>
          )}
        </div>
        <button
          onClick={onClose}
          aria-label="Close evidence"
          style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--mid)', fontSize: 18, lineHeight: 1 }}
        >
          ×
        </button>
      </div>

      {error && (
        <p style={{ fontFamily: 'var(--fb)', fontSize: 13, color: 'var(--status-red)', marginTop: 12 }}>{error}</p>
      )}
      {!error && !current && <Spinner />}
      {current && current.reviews.length === 0 && (
        <p style={{ fontFamily: 'var(--fb)', fontSize: 13, color: 'var(--mid)', marginTop: 12 }}>No reviews match this selection.</p>
      )}
      {current && current.reviews.length > 0 && (
        <ul style={{ marginTop: 4 }}>
          {current.reviews.map((r) => <ReviewItem key={r.id} review={r} />)}
        </ul>
      )}
      {current && current.reviews.length < current.total && (
        <button
          onClick={() => setLimit((l) => Math.min(l + PAGE_SIZE, 50))}
          disabled={limit >= 50}
          style={{
            marginTop: 14,
            background: 'none',
            border: '1px solid var(--primary-10)',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--primary-60)',
            cursor: 'pointer',
            fontFamily: 'var(--fb)',
            fontSize: 11,
            fontWeight: 600,
            letterSpacing: '1px',
            padding: '7px 14px',
            textTransform: 'uppercase',
          }}
        >
          {limit >= 50 ? 'Showing the first 50' : 'Show more'}
        </button>
      )}
    </section>
  )
}
