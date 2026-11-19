// All HTTP calls go through this file — no component imports fetch directly.

const BASE = '/api'

async function fetchOk(path: string, opts?: RequestInit): Promise<Response> {
  const res = await fetch(`${BASE}${path}`, {
    ...opts,
    headers: {
      'Content-Type': 'application/json',
      ...opts?.headers,
    },
  })
  if (!res.ok) {
    // FastAPI reports errors as { detail: string } — surface that to the user.
    let detail = ''
    try {
      const body: unknown = await res.json()
      const d = (body as { detail?: unknown } | null)?.detail
      if (typeof d === 'string') detail = d
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail || `Request failed (${res.status})`)
  }
  return res
}

async function request<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetchOk(path, opts)
  return res.json() as Promise<T>
}

export interface FileDownload {
  blob:     Blob
  mimeType: string
  filename: string
}

/** Binary download; the file name comes from the server's Content-Disposition. */
async function download(path: string, fallbackName: string): Promise<FileDownload> {
  const res = await fetchOk(path)
  const disposition = res.headers.get('Content-Disposition') ?? ''
  const filename = /filename="?([^";]+)"?/.exec(disposition)?.[1] ?? fallbackName
  const mimeType = (res.headers.get('Content-Type') ?? '').split(';')[0].trim()
  return { blob: await res.blob(), mimeType, filename }
}

// ── TypeScript interfaces ─────────────────────────────────────────────────────

export interface PainPoint {
  topic_label: string
  mention_count: number
  avg_severity: number
  trend_direction: 'rising' | 'stable' | 'declining'
}

export interface TimelineEntry {
  month: string
  avg_sentiment: number
  stddev: number
  review_count: number
  top_event: string | null
}

export interface WishCluster {
  wish_phrase_cluster: string
  count: number
  sample_quotes: string[]
  your_product_has_it: boolean
  matched_feature: string | null
}

export interface Objection {
  objection: string
  evidence: string
  counter: string
  proof_quote: string
}

export interface FeatureGap {
  gap: string
  frequency: number
  your_advantage: string
}

export interface Battlecard {
  competitor: string
  generated_at: string
  recommended_pitch: string
  objections: Objection[]
  feature_gaps: FeatureGap[]
}

export type AlertType =
  | 'sentiment_drop'
  | 'negative_news'
  | 'review_spike'
  | 'pricing_change'
  | 'hiring_signal'

export type AlertStatus = 'new' | 'seen' | 'dismissed'

export interface Alert {
  trigger_type: AlertType
  competitor: string
  evidence_summary: string
  timestamp: string
  outreach_draft: string | null
  // History fields — absent for the "Simulate Bad Week" demo, which is not stored.
  id?:           number | null
  status?:       AlertStatus | null
  is_new?:       boolean
  first_seen?:   string
  last_seen?:    string
  times_seen?:   number
  is_synthetic?: boolean
}

export interface AlertHistory {
  alerts: Alert[]
  counts: Record<AlertStatus, number>
}

// ── What changed / Compare ──────────────────────────────────────────────────

export interface TopicMove { topic: string; current: number; previous: number }

export interface WindowStats { reviews: number; sentiment: number | null; rating: number | null }

export interface BattlecardChanges {
  versions:          number
  current_date:      string
  previous_date:     string | null
  pitch_changed:     boolean
  pitch_before:      string | null
  pitch_after:       string | null
  objections_added:  string[]
  objections_removed: string[]
  gaps_added:        string[]
  gaps_removed:      string[]
}

export interface DigestEntry {
  sentiment_delta:  number | null
  sentiment_signal: string | null
  top_pain:         string | null
  summary:          string | null
}

export interface Changes {
  competitor:  string
  window_days: number
  reviews: {
    anchor_date: string | null
    current:     WindowStats
    previous:    WindowStats
    topics:      { new: TopicMove[]; rising: TopicMove[]; fading: TopicMove[] }
  }
  battlecard: BattlecardChanges | null
  digest: {
    current_at:   string
    previous_at:  string | null
    theme_before: string | null
    theme_after:  string | null
    before:       DigestEntry | null
    after:        DigestEntry | null
  } | null
  alerts:     Alert[]
  pricing:    { url: string; date: string; changes: string[] }[]
  hiring:     { new_roles: number; support: number; integration: number } | null
  highlights: string[]
}

export interface CompetitorComparison {
  name:               string
  reviews_total:      number
  synthetic_share:    number
  latest_date:        string | null
  reviews_30d:        number
  sentiment_30d:      number | null
  sentiment_prev_30d: number | null
  sentiment_change:   number | null
  rating_30d:         number | null
  pain_points:        { topic: string; severity: number; mentions: number; trend: string }[]
  churn:              { label: string; mention_pct: number; trend: string }[] | null
  timeline:           { month: string; avg_sentiment: number }[]
  active_alerts:      number
  last_price_change:  string | null
  support_share:      number | null
  new_roles:          number
}

export interface Comparison {
  window_days: number
  competitors: CompetitorComparison[]
}

// ── Market signals ──────────────────────────────────────────────────────────

export interface PricingChange {
  date:    string
  changes: string[]
  added:   string[]
  removed: string[]
}

export interface PricingPage {
  url:             string
  last_checked:    string
  monitored_since: string
  versions:        number
  price_points:    string[]
  last_change:     PricingChange | null
  is_synthetic:    boolean
}

export interface PricingOverview {
  competitor:     string
  pages:          PricingPage[]
  monitored_urls: string[]
}

export type RoleCategory = 'support' | 'engineering' | 'sales' | 'product' | 'marketing' | 'other'

export interface JobRole {
  title:       string
  department:  string | null
  location:    string | null
  url:         string | null
  category:    RoleCategory
  posted_date: string
}

export interface HiringOverview {
  competitor:        string
  crawled_on:        string | null
  source:            string | null
  window_days:       number
  open_roles:        number
  new_roles:         number
  by_category:       { category: RoleCategory; label: string; open: number; new: number }[]
  integration_new:   number
  integration_roles: JobRole[]
  recent_roles:      JobRole[]
  is_synthetic:      boolean
  board:             { provider: string; board: string; recent_only: boolean } | null
  category_labels:   Record<RoleCategory, string>
}

export interface SignalsRefreshReport {
  competitor: string
  pricing:    { url: string; status: 'first' | 'unchanged' | 'changed'; price_points: number; rendered: boolean; changes: string[] }[]
  jobs:       { source: string; seen: number; new: number } | null
  errors:     string[]
  headless_browser: boolean
}

export interface ChurnBucket {
  category:        'pricing' | 'ux' | 'features' | 'support' | 'reliability'
  label:           string
  mention_pct:     number
  trend_direction: 'worsening' | 'stable' | 'improving'
  proof_quotes:    string[]
}

export interface ChurnAnalysis {
  competitor:               string
  generated_at:             string
  total_reviews_analysed:   number
  buckets:                  ChurnBucket[]
}

export interface CompetitorBrief {
  name:              string
  sentiment_delta:   number
  sentiment_signal:  'improving' | 'declining' | 'stable'
  top_pain:          string
  summary:           string
  action_bullets:    string[]
}

export interface DigestReport {
  generated_at:     string
  overall_theme:    string
  per_competitor:   CompetitorBrief[]
  top_alert:        string | null
  top_lead:         string | null
}

export interface DigestMeta {
  id:           number
  generated_at: string
}

export interface OutreachEmail {
  subject: string
  body:    string
}

export interface OutreachBundle {
  competitor:    string
  username:      string
  generated_at:  string
  email:         OutreachEmail
  linkedin_dm:   string
  call_bullets:  string[]
}

export interface Lead {
  username: string
  post_url: string
  created_at: string
  competitor_name: string
  urgency_score: number
  complaint_summary: string
  company_signals: string[]
  suggested_angle: string
  is_synthetic: boolean
  // Pipeline fields — null when the lead could not be stored.
  status?: LeadStage | null
  note?: string | null
  first_seen?: string
  last_seen?: string
}

export type LeadStage = 'new' | 'contacted' | 'replied' | 'opportunity' | 'dismissed'

export interface Pipeline {
  stages: { id: LeadStage; label: string; count: number }[]
  leads:  Lead[]
}

export type CrmTarget = 'hubspot' | 'salesforce'

export interface CrmStatus {
  demo_mode:  boolean
  hubspot:    boolean
  salesforce: boolean
}

export interface CrmLeadResult {
  username:   string
  status:     'created' | 'exists' | 'skipped' | 'failed'
  record_id:  string | null
  record_url: string | null
  error:      string | null
}

export interface CrmPushResult {
  target:  CrmTarget
  created: number
  exists:  number
  skipped: number
  failed:  number
  results: CrmLeadResult[]
}

export interface ReviewEvidence {
  id:              number
  source:          string
  date:            string | null
  rating:          number | null
  sentiment_score: number
  review_text:     string
  topic_label:     string | null
  is_synthetic:    boolean
}

export interface ReviewList {
  competitor: string
  topic:      string | null
  month:      string | null
  total:      number
  reviews:    ReviewEvidence[]
}

export interface ReviewQuery {
  topic?: string
  month?: string
  sort?:  'negative' | 'positive' | 'recent'
  limit?: number
}

export interface CompetitorDataStatus {
  name:        string
  reviews:     number
  synthetic:   number
  latest_date: string | null
}

export interface DataStatus {
  demo_mode:   boolean
  competitors: CompetitorDataStatus[]
}

// ── API object ────────────────────────────────────────────────────────────────

export const api = {
  meta: {
    competitors: () =>
      request<{ competitors: string[] }>('/meta/competitors'),
    ownFeatures: () =>
      request<{ features: string[] }>('/meta/own-features'),
    dataStatus: () => request<DataStatus>('/meta/data-status'),
  },

  reviews: {
    list: (competitor: string, query: ReviewQuery = {}) => {
      const params = new URLSearchParams({ competitor })
      if (query.topic) params.set('topic', query.topic)
      if (query.month) params.set('month', query.month)
      if (query.sort) params.set('sort', query.sort)
      if (query.limit) params.set('limit', String(query.limit))
      return request<ReviewList>(`/reviews?${params}`)
    },
  },

  painPoints: {
    get: (competitor: string, topN: number = 10) =>
      request<{ competitor: string; points: PainPoint[] }>(
        `/pain-points?competitor=${encodeURIComponent(competitor)}&top_n=${topN}`,
      ),
  },

  sentiment: {
    get: (competitor: string, months: number = 18) =>
      request<{ competitor: string; months: number; timeline: TimelineEntry[] }>(
        `/sentiment?competitor=${encodeURIComponent(competitor)}&months=${months}`,
      ),
  },

  wishes: {
    get: (competitor: string, gapsOnly: boolean = false) =>
      request<{ competitor: string; clusters: WishCluster[] }>(
        `/wishes?competitor=${encodeURIComponent(competitor)}&gaps_only=${gapsOnly}`,
      ),
  },

  battlecard: {
    getCached: (competitor: string) =>
      request<Battlecard | null>(
        `/battlecard?competitor=${encodeURIComponent(competitor)}`,
      ),
    export: (competitor: string) =>
      download(
        `/battlecard/export?competitor=${encodeURIComponent(competitor)}`,
        `battlecard_${competitor.toLowerCase()}.pdf`,
      ),
    generate: (competitor: string) =>
      request<Battlecard>('/battlecard', {
        method: 'POST',
        body: JSON.stringify({ competitor }),
      }),
  },

  signals: {
    pricing: (competitor: string) =>
      request<PricingOverview>(`/signals/pricing?competitor=${encodeURIComponent(competitor)}`),
    hiring: (competitor: string) =>
      request<HiringOverview>(`/signals/hiring?competitor=${encodeURIComponent(competitor)}`),
    refresh: (competitor: string) =>
      request<SignalsRefreshReport>('/signals/refresh', {
        method: 'POST',
        body:   JSON.stringify({ competitor }),
      }),
  },

  alerts: {
    demo: () => request<Alert[]>('/alerts/demo'),
    scan: () => request<Alert[]>('/alerts/scan', { method: 'POST' }),
    outreach: (
      alertData: Omit<Alert, 'outreach_draft'> & { outreach_draft?: string | null },
      useLlm: boolean,
    ) =>
      request<{ draft: string }>('/alerts/outreach', {
        method: 'POST',
        // alert_id saves the draft on the stored alert.
        body: JSON.stringify({ ...alertData, use_llm: useLlm, alert_id: alertData.id ?? null }),
      }),
    history: (query: { status?: AlertStatus; competitor?: string; active?: boolean } = {}) => {
      const params = new URLSearchParams()
      if (query.status) params.set('status', query.status)
      if (query.competitor) params.set('competitor', query.competitor)
      if (query.active) params.set('active', 'true')
      const qs = params.toString()
      return request<AlertHistory>(`/alerts/history${qs ? `?${qs}` : ''}`)
    },
    setStatus: (id: number, status: AlertStatus) =>
      request<Alert>(`/alerts/${id}/status`, {
        method: 'POST',
        body:   JSON.stringify({ status }),
      }),
    markAllSeen: () =>
      request<{ updated: number }>('/alerts/mark-seen', { method: 'POST', body: JSON.stringify({}) }),
  },

  prospects: {
    demo: () => request<Lead[]>('/prospects/demo'),
    scan: () => request<Lead[]>('/prospects/scan', { method: 'POST' }),
    pipeline: (includeDismissed = false) =>
      request<Pipeline>(`/prospects/pipeline${includeDismissed ? '?include_dismissed=true' : ''}`),
    setStage: (postUrl: string, status: LeadStage, note?: string) =>
      request<Lead>('/prospects/stage', {
        method: 'POST',
        body:   JSON.stringify({ post_url: postUrl, status, note: note ?? null }),
      }),
  },

  insights: {
    changes: (competitor: string, days = 7) =>
      request<Changes>(`/changes?competitor=${encodeURIComponent(competitor)}&days=${days}`),
    compare: () => request<Comparison>('/compare'),
  },

  crm: {
    status: () => request<CrmStatus>('/crm/status'),
    push: (target: CrmTarget, leads: Lead[]) =>
      request<CrmPushResult>('/crm/push', {
        method: 'POST',
        body:   JSON.stringify({ target, leads }),
      }),
  },

  churn: {
    getCached: (competitor: string) =>
      request<ChurnAnalysis | null>(
        `/churn?competitor=${encodeURIComponent(competitor)}`,
      ),
    analyse: (competitor: string) =>
      request<ChurnAnalysis>(
        `/churn?competitor=${encodeURIComponent(competitor)}`,
        { method: 'POST' },
      ),
  },

  digest: {
    latest:   () => request<DigestReport | null>('/digest/latest'),
    history:  () => request<DigestMeta[]>('/digest/history'),
    generate: () => request<DigestReport>('/digest/generate', { method: 'POST' }),
  },

  outreach: {
    compose: (competitor: string, complaint: string, username: string) =>
      request<OutreachBundle>('/outreach/compose', {
        method: 'POST',
        body:   JSON.stringify({ competitor, complaint, username }),
      }),
  },
}
