// All HTTP calls go through this file — no component imports fetch directly.

const BASE = '/api'

async function request<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...opts,
    headers: {
      'Content-Type': 'application/json',
      ...opts?.headers,
    },
  })
  if (!res.ok) throw new Error(`${res.status} ${path}`)
  return res.json() as Promise<T>
}

// ── TypeScript interfaces ─────────────────────────────────────────────────────

export interface PainPoint {
  topic_label: string
  mention_count: number
  avg_severity: number
  trend_direction: 'rising' | 'stable' | 'declining'
  trend_icon: string
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

export interface Alert {
  trigger_type: 'sentiment_drop' | 'negative_news' | 'review_spike'
  competitor: string
  evidence_summary: string
  timestamp: string
  outreach_draft: string | null
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
}

// ── API object ────────────────────────────────────────────────────────────────

export const api = {
  meta: {
    competitors: () =>
      request<{ competitors: string[] }>('/meta/competitors'),
    ownFeatures: () =>
      request<{ features: string[] }>('/meta/own-features'),
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
    generate: (competitor: string) =>
      request<Battlecard>('/battlecard', {
        method: 'POST',
        body: JSON.stringify({ competitor }),
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
        body: JSON.stringify({ ...alertData, use_llm: useLlm }),
      }),
  },

  prospects: {
    demo: () => request<Lead[]>('/prospects/demo'),
    scan: () => request<Lead[]>('/prospects/scan', { method: 'POST' }),
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
