"""Page 7 — Info: Business View and Engineering View."""

import streamlit as st

_BRAND_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,400;1,9..144,300;1,9..144,400&display=swap" rel="stylesheet">
<style>
/* ── Shared layout ── */
.info-section { margin-bottom: 40px; }
.info-eyebrow {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 9px; font-weight: 600; letter-spacing: 4px;
    text-transform: uppercase; color: #C8982A;
    display: flex; align-items: center; gap: 10px;
    margin-bottom: 8px;
}
.info-eyebrow::before {
    content: ''; display: block; width: 20px;
    height: 1px; background: #C8982A;
}
.info-h2 {
    font-family: 'Fraunces', Georgia, serif;
    font-size: 26px; font-weight: 300; color: #003366;
    margin: 0 0 12px;
}
.info-body {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 14px; color: #374151; line-height: 1.75;
    max-width: 820px;
}
.info-divider {
    height: 1px; background: #E0EAF4; margin: 36px 0;
}

/* ── Business View ── */
.biz-problem-box {
    background: #003366;
    border-radius: 12px; padding: 28px 32px;
    margin-bottom: 32px;
    background-image:
        linear-gradient(rgba(255,255,255,.025) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,.025) 1px, transparent 1px);
    background-size: 40px 40px;
}
.biz-problem-box p {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 14px; color: rgba(255,255,255,0.75);
    line-height: 1.8; margin: 0;
}
.biz-problem-box strong { color: #C8982A; }

.module-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px; margin-bottom: 8px;
}
.module-card {
    background: #ffffff;
    border-radius: 10px; padding: 20px 20px 16px;
    border-top: 3px solid #C8982A;
    box-shadow: 0 1px 4px rgba(0,51,102,.08);
}
.module-card-num {
    font-family: 'Fraunces', Georgia, serif;
    font-size: 11px; color: #C8982A;
    letter-spacing: 2px; margin-bottom: 6px;
}
.module-card-title {
    font-family: 'Fraunces', Georgia, serif;
    font-size: 16px; font-weight: 300; color: #003366;
    margin-bottom: 10px;
}
.module-card-body {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 12px; color: #6B7280; line-height: 1.65;
}
.module-card-impact {
    margin-top: 12px; padding-top: 10px;
    border-top: 1px solid #E0EAF4;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 11px; color: #003366; font-weight: 600;
    letter-spacing: 0.3px;
}

.advantage-row {
    display: grid; grid-template-columns: repeat(2, 1fr);
    gap: 14px; margin-bottom: 8px;
}
.advantage-item {
    display: flex; gap: 14px; align-items: flex-start;
    background: #ffffff; border-radius: 10px;
    padding: 18px 20px;
    box-shadow: 0 1px 4px rgba(0,51,102,.07);
}
.advantage-icon {
    width: 36px; height: 36px; flex-shrink: 0;
    background: rgba(0,51,102,0.07);
    border-radius: 8px; display: flex;
    align-items: center; justify-content: center;
}
.advantage-icon svg { width: 18px; height: 18px; }
.advantage-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 13px; font-weight: 600; color: #003366;
    margin-bottom: 4px;
}
.advantage-desc {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 12px; color: #6B7280; line-height: 1.6;
}

.integration-row {
    display: flex; gap: 14px; flex-wrap: wrap;
    margin-bottom: 8px;
}
.integration-chip {
    background: #ffffff; border-radius: 10px;
    padding: 16px 20px; min-width: 160px; flex: 1;
    border-left: 3px solid #003366;
    box-shadow: 0 1px 4px rgba(0,51,102,.07);
}
.integration-chip-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 13px; font-weight: 600; color: #003366;
    margin-bottom: 4px;
}
.integration-chip-desc {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 12px; color: #6B7280; line-height: 1.5;
}

/* ── Engineering View ── */
.arch-diagram {
    display: flex; flex-direction: column;
    align-items: center; gap: 0; margin: 24px 0;
    font-family: 'Plus Jakarta Sans', sans-serif;
}
.arch-layer {
    width: 100%; background: #003366;
    border-radius: 10px; padding: 20px 24px;
    border: 1px solid rgba(200,152,42,0.35);
    position: relative;
}
.arch-layer-label {
    font-size: 9px; font-weight: 600;
    letter-spacing: 3px; text-transform: uppercase;
    color: rgba(255,255,255,0.35); margin-bottom: 4px;
}
.arch-layer-title {
    font-family: 'Fraunces', Georgia, serif;
    font-size: 18px; font-weight: 300;
    color: #ffffff; margin-bottom: 14px;
}
.arch-chips {
    display: flex; gap: 8px; flex-wrap: wrap;
    margin-bottom: 10px;
}
.arch-chip {
    background: rgba(200,152,42,0.15);
    color: #C8982A; font-size: 12px;
    padding: 4px 12px; border-radius: 20px;
    border: 1px solid rgba(200,152,42,0.25);
    font-weight: 500;
}
.arch-chip-light {
    background: rgba(255,255,255,0.07);
    color: rgba(255,255,255,0.65); font-size: 11px;
    padding: 3px 10px; border-radius: 20px;
}
.arch-layer-desc {
    font-size: 11px; color: rgba(255,255,255,0.40);
    line-height: 1.5; margin-top: 6px;
}
.arch-arrow {
    width: 2px; background: #C8982A;
    height: 28px; position: relative;
    display: flex; justify-content: center;
}
.arch-arrow::after {
    content: '';
    position: absolute; bottom: -7px;
    left: 50%; transform: translateX(-50%);
    border-left: 7px solid transparent;
    border-right: 7px solid transparent;
    border-top: 8px solid #C8982A;
}

.tech-table {
    width: 100%; border-collapse: collapse;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 13px; background: #ffffff;
    border-radius: 10px; overflow: hidden;
    box-shadow: 0 1px 4px rgba(0,51,102,.08);
    margin-bottom: 8px;
}
.tech-table th {
    background: #003366; color: rgba(255,255,255,0.85);
    font-size: 10px; letter-spacing: 2px;
    text-transform: uppercase; font-weight: 500;
    padding: 12px 16px; text-align: left;
}
.tech-table td {
    padding: 12px 16px; color: #374151;
    border-bottom: 1px solid #F0F4F8;
    vertical-align: top; line-height: 1.55;
}
.tech-table tr:last-child td { border-bottom: none; }
.tech-table tr:nth-child(even) td { background: #F8FAFC; }
.tech-name {
    font-weight: 600; color: #003366;
    font-size: 12px;
}
.tech-badge {
    display: inline-block;
    background: rgba(0,51,102,0.08);
    color: #003366; font-size: 10px;
    padding: 2px 8px; border-radius: 20px;
    font-weight: 600; letter-spacing: 0.5px;
}

.eng-callout {
    background: #F4F6F9; border-left: 3px solid #C8982A;
    border-radius: 0 8px 8px 0;
    padding: 16px 20px; margin: 16px 0;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 13px; color: #374151; line-height: 1.65;
}
.eng-callout strong { color: #003366; }

.data-flow {
    display: flex; align-items: stretch;
    gap: 0; margin: 24px 0; overflow-x: auto;
}
.flow-node {
    background: #003366; border-radius: 8px;
    padding: 16px 18px; min-width: 130px;
    border: 1px solid rgba(200,152,42,0.30);
    flex: 1;
}
.flow-node-title {
    font-family: 'Fraunces', Georgia, serif;
    font-size: 13px; color: #ffffff; margin-bottom: 8px;
}
.flow-node-items {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 10px; color: rgba(255,255,255,0.50);
    line-height: 1.8;
}
.flow-arrow {
    display: flex; align-items: center;
    padding: 0 4px; color: #C8982A;
    font-size: 18px; font-weight: 300;
    flex-shrink: 0;
}

.db-schema {
    display: grid; grid-template-columns: repeat(2, 1fr);
    gap: 14px; margin: 16px 0;
}
.db-table-card {
    background: #ffffff; border-radius: 10px;
    overflow: hidden; box-shadow: 0 1px 4px rgba(0,51,102,.08);
}
.db-table-header {
    background: #003366; padding: 10px 16px;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 12px; font-weight: 600; color: #C8982A;
    letter-spacing: 1px;
}
.db-table-row {
    padding: 8px 16px; font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 11px; color: #374151; border-bottom: 1px solid #F0F4F8;
    display: flex; justify-content: space-between; align-items: center;
    line-height: 1.4;
}
.db-table-row:last-child { border-bottom: none; }
.db-col-type {
    color: #C8982A; font-size: 10px;
    font-weight: 600; letter-spacing: 0.5px;
}
.db-pk { color: #27B97C; font-size: 10px; font-weight: 600; }
</style>
"""

st.html(_BRAND_CSS)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.html("""
<div style="background:#003366;padding:36px 40px 28px;border-radius:12px;margin-bottom:28px;
background-image:linear-gradient(rgba(255,255,255,.025) 1px,transparent 1px),
linear-gradient(90deg,rgba(255,255,255,.025) 1px,transparent 1px);
background-size:48px 48px;">
    <div style="font-family:'Fraunces',Georgia,serif;font-weight:300;
                color:#ffffff;font-size:28px;margin:0 0 8px;">
        Platform <em style="color:#C8982A;font-style:italic;">Overview</em>
    </div>
    <div style="color:rgba(255,255,255,0.55);font-size:14px;
                font-family:'Plus Jakarta Sans',sans-serif;line-height:1.6;max-width:640px;">
        Two perspectives on RivalSense — a plain-language business brief
        and a full engineering breakdown for technical audiences.
    </div>
</div>
""")

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab_biz, tab_eng = st.tabs(["Business View", "Engineering View"])


# ═══════════════════════════════════════════════════════════════════════════════
# BUSINESS VIEW
# ═══════════════════════════════════════════════════════════════════════════════

with tab_biz:

    # What is it
    st.html("""
    <div class="info-section">
      <div class="info-eyebrow">Overview</div>
      <div class="info-h2">What is RivalSense?</div>
      <div class="info-body">
        RivalSense is a competitive intelligence platform that automatically collects,
        processes, and interprets public signals about your competitors — review platform
        feedback, social media conversations, and news coverage — and turns them into
        structured, actionable intelligence for sales and business development teams.
        <br><br>
        Rather than relying on quarterly analyst reports or manual research sprints,
        RivalSense runs continuously in the background, monitoring what real customers
        say about competing products and surfacing the most relevant intelligence at
        the moment it matters most.
      </div>
    </div>
    """)

    # The problem
    st.html("""
    <div class="biz-problem-box">
      <p>
        <strong>The gap RivalSense closes:</strong> Most sales and BD teams know their
        competitors exist but lack a systematic view of where those competitors are
        failing their customers right now. A competitor's pricing page tells you what
        they charge. A competitor's review trail tells you what is <strong>actually
        breaking</strong> for their customers, which features they are begging for,
        and when their customer satisfaction is deteriorating. That second category
        of intelligence — live, evidence-based, and customer-voiced — is what closes
        deals and wins accounts. RivalSense makes it available on demand.
      </p>
    </div>
    """)

    # Modules
    st.html("""
    <div class="info-section">
      <div class="info-eyebrow">Capabilities</div>
      <div class="info-h2">Six Intelligence Modules</div>
      <div class="info-body" style="margin-bottom:20px;">
        Each module targets a specific decision a sales or marketing team needs to make.
        They all draw from the same underlying data so insights are consistent and comparable.
      </div>
      <div class="module-grid">

        <div class="module-card">
          <div class="module-card-num">M01</div>
          <div class="module-card-title">Pain Point Radar</div>
          <div class="module-card-body">
            Clusters competitor customer complaints by topic and ranks them by how
            severe and how frequently they appear. Each cluster shows how the pain
            is trending — growing, stable, or fading.
          </div>
          <div class="module-card-impact">
            Sales use case: attack the top-ranked pain points in discovery calls
            with evidence from real customer quotes.
          </div>
        </div>

        <div class="module-card">
          <div class="module-card-num">M02</div>
          <div class="module-card-title">Sentiment Timeline</div>
          <div class="module-card-body">
            Plots a competitor's average customer sentiment across an 18-month window,
            overlaid with news events that correlate with sentiment drops or spikes.
            Shows whether a competitor's reputation is improving or deteriorating over time.
          </div>
          <div class="module-card-impact">
            Sales use case: time outreach campaigns to coincide with competitor
            sentiment dips, when accounts are most receptive.
          </div>
        </div>

        <div class="module-card">
          <div class="module-card-num">M03</div>
          <div class="module-card-title">Feature Wish Miner</div>
          <div class="module-card-body">
            Extracts and groups feature requests that competitor customers are publicly
            expressing. Flags which requested features your product already covers,
            and which represent genuine product gaps.
          </div>
          <div class="module-card-impact">
            Sales use case: build product differentiation narratives grounded in
            what the market is actually requesting.
          </div>
        </div>

        <div class="module-card">
          <div class="module-card-num">M04</div>
          <div class="module-card-title">Battlecard Generator</div>
          <div class="module-card-body">
            Uses the Claude AI model to synthesize pain point and feature gap data
            into a structured sales battlecard: objection handlers with evidence,
            counters, and real customer proof quotes. Regenerated on demand so cards
            never go stale. Downloadable as PDF or Markdown.
          </div>
          <div class="module-card-impact">
            Sales use case: arm every rep with a current, evidence-backed battlecard
            for each competitor, ready for any deal stage.
          </div>
        </div>

        <div class="module-card">
          <div class="module-card-num">M05</div>
          <div class="module-card-title">Trigger Alerts</div>
          <div class="module-card-body">
            Monitors three vulnerability signals: a sustained drop in competitor
            sentiment, negative press coverage containing keywords such as
            "outage", "breach", or "layoffs", and an unusual spike in complaint
            volume. Fires a Slack notification and drafts a personalised outreach
            email when a signal is detected.
          </div>
          <div class="module-card-impact">
            Sales use case: be first to reach accounts when a competitor is having
            a bad week — typically the highest-conversion moment in competitive sales.
          </div>
        </div>

        <div class="module-card">
          <div class="module-card-num">M06</div>
          <div class="module-card-title">Hot Prospect Finder</div>
          <div class="module-card-body">
            Scans Reddit communities for users who are actively expressing intent to
            switch away from a competitor. Scores each post by urgency, enriches it
            with company-size signals found in the post text, and suggests an outreach
            angle tailored to the specific complaint.
          </div>
          <div class="module-card-impact">
            Sales use case: engage buyers at the exact moment they are evaluating
            alternatives, before your competitors respond.
          </div>
        </div>

      </div>
    </div>
    """)

    st.html('<div class="info-divider"></div>')

    # Advantages
    st.html("""
    <div class="info-section">
      <div class="info-eyebrow">Key Advantages</div>
      <div class="info-h2">Why It Differs from Manual Research</div>
      <div class="advantage-row">

        <div class="advantage-item">
          <div class="advantage-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="#003366" stroke-width="2">
              <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
            </svg>
          </div>
          <div>
            <div class="advantage-title">Always Current</div>
            <div class="advantage-desc">
              Data is collected and processed automatically on a scheduled cadence.
              Intelligence reflects this week's customer conversations, not last
              quarter's analyst summary.
            </div>
          </div>
        </div>

        <div class="advantage-item">
          <div class="advantage-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="#003366" stroke-width="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
          </div>
          <div>
            <div class="advantage-title">Evidence-Backed</div>
            <div class="advantage-desc">
              Every insight is traceable to real customer reviews and posts. Sales
              reps can quote verbatim in calls — not synthesised claims, but the
              customer's own words.
            </div>
          </div>
        </div>

        <div class="advantage-item">
          <div class="advantage-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="#003366" stroke-width="2">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
            </svg>
          </div>
          <div>
            <div class="advantage-title">Signal-Triggered</div>
            <div class="advantage-desc">
              The platform distinguishes between background noise and meaningful
              signals — a statistically unusual spike in complaints or a sentiment
              drop beyond a defined threshold — so teams only act on events that matter.
            </div>
          </div>
        </div>

        <div class="advantage-item">
          <div class="advantage-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="#003366" stroke-width="2">
              <path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
            </svg>
          </div>
          <div>
            <div class="advantage-title">Output-Ready</div>
            <div class="advantage-desc">
              The platform does not stop at data. It produces finished artefacts —
              battlecards, outreach email drafts, exportable lead lists — that sales
              reps can use directly without additional synthesis work.
            </div>
          </div>
        </div>

        <div class="advantage-item">
          <div class="advantage-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="#003366" stroke-width="2">
              <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
              <line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>
            </svg>
          </div>
          <div>
            <div class="advantage-title">Zero Internal Data Required</div>
            <div class="advantage-desc">
              The system operates entirely on publicly available data. No CRM
              integration is required to produce intelligence — it ingests from
              external sources and outputs to your existing tools.
            </div>
          </div>
        </div>

        <div class="advantage-item">
          <div class="advantage-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="#003366" stroke-width="2">
              <circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/>
              <path d="M6 21V9a9 9 0 0 0 9 9"/>
            </svg>
          </div>
          <div>
            <div class="advantage-title">Modular and Extensible</div>
            <div class="advantage-desc">
              Each intelligence module is independent. New competitors are added
              through a single configuration entry and the entire pipeline runs
              against them automatically — no per-competitor development work.
            </div>
          </div>
        </div>

      </div>
    </div>
    """)

    st.html('<div class="info-divider"></div>')

    # Integrations
    st.html("""
    <div class="info-section">
      <div class="info-eyebrow">Integrations</div>
      <div class="info-h2">Where Intelligence Flows</div>
      <div class="info-body" style="margin-bottom:20px;">
        RivalSense connects to the tools sales and operations teams already use.
        No proprietary workflow is required.
      </div>
      <div class="integration-row">

        <div class="integration-chip">
          <div class="integration-chip-title">Slack</div>
          <div class="integration-chip-desc">
            Trigger alerts are posted to a configured webhook channel the moment a
            competitor vulnerability signal is detected. The message includes the
            evidence summary and the AI-drafted outreach copy.
          </div>
        </div>

        <div class="integration-chip">
          <div class="integration-chip-title">Salesforce / HubSpot</div>
          <div class="integration-chip-desc">
            Hot Prospect leads and trigger alert summaries export as structured CSV
            or JSON files mapped to standard CRM contact fields. Importable into
            any CRM without transformation.
          </div>
        </div>

        <div class="integration-chip">
          <div class="integration-chip-title">Email (SendGrid)</div>
          <div class="integration-chip-desc">
            Scheduled digest emails summarise the week's competitive signals and
            top prospects. Configurable per recipient — field reps can receive
            competitor-specific digests.
          </div>
        </div>

        <div class="integration-chip">
          <div class="integration-chip-title">PDF / Markdown Export</div>
          <div class="integration-chip-desc">
            Battlecards download as branded PDF documents or plain Markdown files
            suitable for pasting into sales enablement platforms like Seismic,
            Highspot, or Notion.
          </div>
        </div>

      </div>
    </div>
    """)

    st.html('<div class="info-divider"></div>')

    # Who benefits
    st.html("""
    <div class="info-section">
      <div class="info-eyebrow">Audience</div>
      <div class="info-h2">Who Uses Each Module</div>
      <div class="info-body">
        <table style="width:100%;border-collapse:collapse;font-family:'Plus Jakarta Sans',sans-serif;
                      font-size:13px;background:#ffffff;border-radius:10px;overflow:hidden;
                      box-shadow:0 1px 4px rgba(0,51,102,.08);">
          <thead>
            <tr style="background:#003366;">
              <th style="padding:12px 16px;text-align:left;color:rgba(255,255,255,0.8);
                         font-size:10px;letter-spacing:2px;text-transform:uppercase;font-weight:500;">Module</th>
              <th style="padding:12px 16px;text-align:center;color:rgba(255,255,255,0.8);
                         font-size:10px;letter-spacing:2px;text-transform:uppercase;font-weight:500;">Sales</th>
              <th style="padding:12px 16px;text-align:center;color:rgba(255,255,255,0.8);
                         font-size:10px;letter-spacing:2px;text-transform:uppercase;font-weight:500;">Marketing</th>
              <th style="padding:12px 16px;text-align:center;color:rgba(255,255,255,0.8);
                         font-size:10px;letter-spacing:2px;text-transform:uppercase;font-weight:500;">Product</th>
              <th style="padding:12px 16px;text-align:left;color:rgba(255,255,255,0.8);
                         font-size:10px;letter-spacing:2px;text-transform:uppercase;font-weight:500;">Primary Action</th>
            </tr>
          </thead>
          <tbody>
            <tr style="border-bottom:1px solid #F0F4F8;">
              <td style="padding:12px 16px;font-weight:600;color:#003366;">Pain Point Radar</td>
              <td style="padding:12px 16px;text-align:center;color:#27B97C;font-weight:700;">&#10003;</td>
              <td style="padding:12px 16px;text-align:center;color:#27B97C;font-weight:700;">&#10003;</td>
              <td style="padding:12px 16px;text-align:center;color:#27B97C;font-weight:700;">&#10003;</td>
              <td style="padding:12px 16px;color:#6B7280;">Craft messaging that targets competitor weaknesses</td>
            </tr>
            <tr style="border-bottom:1px solid #F0F4F8;background:#F8FAFC;">
              <td style="padding:12px 16px;font-weight:600;color:#003366;">Sentiment Timeline</td>
              <td style="padding:12px 16px;text-align:center;color:#27B97C;font-weight:700;">&#10003;</td>
              <td style="padding:12px 16px;text-align:center;color:#27B97C;font-weight:700;">&#10003;</td>
              <td style="padding:12px 16px;text-align:center;color:#6B7280;">&#8212;</td>
              <td style="padding:12px 16px;color:#6B7280;">Time campaigns to competitor reputation dips</td>
            </tr>
            <tr style="border-bottom:1px solid #F0F4F8;">
              <td style="padding:12px 16px;font-weight:600;color:#003366;">Feature Wish Miner</td>
              <td style="padding:12px 16px;text-align:center;color:#27B97C;font-weight:700;">&#10003;</td>
              <td style="padding:12px 16px;text-align:center;color:#6B7280;">&#8212;</td>
              <td style="padding:12px 16px;text-align:center;color:#27B97C;font-weight:700;">&#10003;</td>
              <td style="padding:12px 16px;color:#6B7280;">Build product differentiation and roadmap input</td>
            </tr>
            <tr style="border-bottom:1px solid #F0F4F8;background:#F8FAFC;">
              <td style="padding:12px 16px;font-weight:600;color:#003366;">Battlecard Generator</td>
              <td style="padding:12px 16px;text-align:center;color:#27B97C;font-weight:700;">&#10003;</td>
              <td style="padding:12px 16px;text-align:center;color:#27B97C;font-weight:700;">&#10003;</td>
              <td style="padding:12px 16px;text-align:center;color:#6B7280;">&#8212;</td>
              <td style="padding:12px 16px;color:#6B7280;">Equip reps with current objection handlers per competitor</td>
            </tr>
            <tr style="border-bottom:1px solid #F0F4F8;">
              <td style="padding:12px 16px;font-weight:600;color:#003366;">Trigger Alerts</td>
              <td style="padding:12px 16px;text-align:center;color:#27B97C;font-weight:700;">&#10003;</td>
              <td style="padding:12px 16px;text-align:center;color:#6B7280;">&#8212;</td>
              <td style="padding:12px 16px;text-align:center;color:#6B7280;">&#8212;</td>
              <td style="padding:12px 16px;color:#6B7280;">Act on competitor crises before competitors recover</td>
            </tr>
            <tr style="background:#F8FAFC;">
              <td style="padding:12px 16px;font-weight:600;color:#003366;">Hot Prospect Finder</td>
              <td style="padding:12px 16px;text-align:center;color:#27B97C;font-weight:700;">&#10003;</td>
              <td style="padding:12px 16px;text-align:center;color:#6B7280;">&#8212;</td>
              <td style="padding:12px 16px;text-align:center;color:#6B7280;">&#8212;</td>
              <td style="padding:12px 16px;color:#6B7280;">Identify and reach switching-intent buyers directly</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    """)


# ═══════════════════════════════════════════════════════════════════════════════
# ENGINEERING VIEW
# ═══════════════════════════════════════════════════════════════════════════════

with tab_eng:

    # Overview
    st.html("""
    <div class="info-section">
      <div class="info-eyebrow">Architecture</div>
      <div class="info-h2">System Overview</div>
      <div class="info-body">
        RivalSense is structured as a four-layer pipeline. Each layer has a single
        well-defined responsibility: raw data collection, NLP enrichment, intelligence
        computation, and output delivery. Layers communicate exclusively through a shared
        SQLite relational database, which means any layer can be rerun independently
        without affecting the others. This design prioritises operational simplicity for
        a prototype — one engineer can understand, debug, and extend the entire system
        without distributed infrastructure.
      </div>
    </div>
    """)

    # Architecture diagram
    st.html("""
    <div class="info-section">
      <div class="info-eyebrow">Diagram 1</div>
      <div class="info-h2">Four-Layer Architecture</div>
      <div class="arch-diagram">

        <div class="arch-layer">
          <div class="arch-layer-label">Layer 1</div>
          <div class="arch-layer-title">Data Ingestion</div>
          <div class="arch-chips">
            <span class="arch-chip">G2 Reviews</span>
            <span class="arch-chip">Trustpilot</span>
            <span class="arch-chip">Reddit (PRAW)</span>
            <span class="arch-chip">NewsAPI</span>
            <span class="arch-chip">App Store</span>
          </div>
          <div class="arch-chips">
            <span class="arch-chip-light">requests + BeautifulSoup</span>
            <span class="arch-chip-light">PRAW SDK</span>
            <span class="arch-chip-light">newsapi-python</span>
            <span class="arch-chip-light">1–2 s rate limiting</span>
          </div>
          <div class="arch-layer-desc">
            Writes raw rows to → <strong style="color:rgba(255,255,255,0.6)">reviews</strong> table (SQLite)
          </div>
        </div>

        <div class="arch-arrow"></div>

        <div class="arch-layer">
          <div class="arch-layer-label">Layer 2</div>
          <div class="arch-layer-title">NLP Pipeline</div>
          <div class="arch-chips">
            <span class="arch-chip">BERTopic — Topic Clustering</span>
            <span class="arch-chip">VADER + Sentence-BERT — Sentiment</span>
            <span class="arch-chip">spaCy NER — Entity Extraction</span>
          </div>
          <div class="arch-chips">
            <span class="arch-chip-light">sentence-transformers (all-MiniLM-L6-v2)</span>
            <span class="arch-chip-light">vaderSentiment</span>
            <span class="arch-chip-light">en_core_web_sm</span>
          </div>
          <div class="arch-layer-desc">
            Reads from reviews → writes enriched rows to → <strong style="color:rgba(255,255,255,0.6)">processed_reviews</strong> table
          </div>
        </div>

        <div class="arch-arrow"></div>

        <div class="arch-layer">
          <div class="arch-layer-label">Layer 3</div>
          <div class="arch-layer-title">Intelligence Modules</div>
          <div class="arch-chips">
            <span class="arch-chip">M01 Pain Point Radar</span>
            <span class="arch-chip">M02 Sentiment Timeline</span>
            <span class="arch-chip">M03 Feature Wish Miner</span>
          </div>
          <div class="arch-chips">
            <span class="arch-chip">M04 Battlecard Generator</span>
            <span class="arch-chip">M05 Trigger Alerts</span>
            <span class="arch-chip">M06 Hot Prospect Finder</span>
          </div>
          <div class="arch-chips">
            <span class="arch-chip-light">pandas aggregations</span>
            <span class="arch-chip-light">Claude API (M04, M05)</span>
            <span class="arch-chip-light">PRAW live scan (M06)</span>
          </div>
          <div class="arch-layer-desc">
            All modules read from processed_reviews. M04 + M05 additionally call the Claude API.
            Results are returned as DataFrames or Alert objects — not persisted (computed on demand).
          </div>
        </div>

        <div class="arch-arrow"></div>

        <div class="arch-layer">
          <div class="arch-layer-label">Layer 4</div>
          <div class="arch-layer-title">Output &amp; Delivery</div>
          <div class="arch-chips">
            <span class="arch-chip">Streamlit Dashboard</span>
            <span class="arch-chip">Slack Webhooks</span>
            <span class="arch-chip">CRM Export (CSV / JSON)</span>
            <span class="arch-chip">PDF Battlecards (WeasyPrint)</span>
          </div>
          <div class="arch-chips">
            <span class="arch-chip-light">APScheduler (cron)</span>
            <span class="arch-chip-light">SendGrid (email digests)</span>
          </div>
          <div class="arch-layer-desc">
            UI files import exclusively from modules/ — no business logic in UI layer.
            Scheduler triggers ingestion + alert checks on a configurable cadence.
          </div>
        </div>

      </div>
    </div>
    """)

    st.html('<div class="info-divider"></div>')

    # Data flow
    st.html("""
    <div class="info-section">
      <div class="info-eyebrow">Diagram 2</div>
      <div class="info-h2">Data Flow Through the System</div>
      <div class="data-flow">

        <div class="flow-node">
          <div class="flow-node-title">Public Sources</div>
          <div class="flow-node-items">
            G2 · Trustpilot<br>Reddit · NewsAPI<br>App Store
          </div>
        </div>
        <div class="flow-arrow">&#8594;</div>

        <div class="flow-node">
          <div class="flow-node-title">Ingestion Layer</div>
          <div class="flow-node-items">
            HTTP scraping<br>PRAW SDK<br>Rate-limited<br>&#8595; reviews table
          </div>
        </div>
        <div class="flow-arrow">&#8594;</div>

        <div class="flow-node">
          <div class="flow-node-title">NLP Pipeline</div>
          <div class="flow-node-items">
            Topic cluster<br>Sentiment score<br>Sentiment delta<br>&#8595; processed_reviews
          </div>
        </div>
        <div class="flow-arrow">&#8594;</div>

        <div class="flow-node">
          <div class="flow-node-title">Intelligence Layer</div>
          <div class="flow-node-items">
            SQL aggregations<br>Claude API calls<br>PRAW live scan<br>&#8595; DataFrames
          </div>
        </div>
        <div class="flow-arrow">&#8594;</div>

        <div class="flow-node">
          <div class="flow-node-title">Outputs</div>
          <div class="flow-node-items">
            Streamlit UI<br>Slack alert<br>CRM export<br>PDF battlecard
          </div>
        </div>

      </div>
    </div>
    """)

    st.html('<div class="info-divider"></div>')

    # Database schema
    st.html("""
    <div class="info-section">
      <div class="info-eyebrow">Data Model</div>
      <div class="info-h2">Database Schema</div>
      <div class="info-body" style="margin-bottom:20px;">
        Two primary tables underpin the entire system. <code style="background:#E0EAF4;color:#003366;
        padding:1px 6px;border-radius:4px;font-size:13px;">reviews</code> holds raw
        scraped content; <code style="background:#E0EAF4;color:#003366;padding:1px 6px;
        border-radius:4px;font-size:13px;">processed_reviews</code> holds NLP-enriched
        rows. All six intelligence modules read exclusively from processed_reviews.
        This separation means ingestion can be rerun without invalidating the NLP
        results, and the NLP pipeline can be rerun without re-scraping the sources.
      </div>
      <div class="db-schema">

        <div class="db-table-card">
          <div class="db-table-header">reviews</div>
          <div class="db-table-row">
            <span>id</span><span class="db-pk">PK · INTEGER</span>
          </div>
          <div class="db-table-row">
            <span>competitor_name</span><span class="db-col-type">TEXT</span>
          </div>
          <div class="db-table-row">
            <span>source</span><span class="db-col-type">TEXT</span>
          </div>
          <div class="db-table-row">
            <span>review_text</span><span class="db-col-type">TEXT</span>
          </div>
          <div class="db-table-row">
            <span>rating</span><span class="db-col-type">REAL</span>
          </div>
          <div class="db-table-row">
            <span>date</span><span class="db-col-type">DATE</span>
          </div>
          <div class="db-table-row">
            <span>author</span><span class="db-col-type">TEXT</span>
          </div>
        </div>

        <div class="db-table-card">
          <div class="db-table-header">processed_reviews</div>
          <div class="db-table-row">
            <span>id</span><span class="db-pk">PK · INTEGER</span>
          </div>
          <div class="db-table-row">
            <span>review_id</span><span class="db-col-type">FK → reviews</span>
          </div>
          <div class="db-table-row">
            <span>competitor_name</span><span class="db-col-type">TEXT · indexed</span>
          </div>
          <div class="db-table-row">
            <span>topic_cluster</span><span class="db-col-type">INTEGER</span>
          </div>
          <div class="db-table-row">
            <span>topic_label</span><span class="db-col-type">TEXT</span>
          </div>
          <div class="db-table-row">
            <span>sentiment_score</span><span class="db-col-type">REAL [−1, 1]</span>
          </div>
          <div class="db-table-row">
            <span>sentiment_delta</span><span class="db-col-type">REAL</span>
          </div>
          <div class="db-table-row">
            <span>wish_phrases</span><span class="db-col-type">TEXT · JSON array</span>
          </div>
          <div class="db-table-row">
            <span>entities</span><span class="db-col-type">TEXT · JSON array</span>
          </div>
          <div class="db-table-row">
            <span>source</span><span class="db-col-type">TEXT</span>
          </div>
          <div class="db-table-row">
            <span>date</span><span class="db-col-type">DATE · indexed</span>
          </div>
        </div>

      </div>
    </div>
    """)

    st.html('<div class="info-divider"></div>')

    # Technology justification
    st.html("""
    <div class="info-section">
      <div class="info-eyebrow">Engineering Decisions</div>
      <div class="info-h2">Technology Stack — Selection Rationale</div>
      <div class="info-body" style="margin-bottom:20px;">
        Each component was selected for a specific reason, not convenience.
        The table below documents the decision for future engineers who need
        to evaluate whether to replace any component.
      </div>
      <table class="tech-table">
        <thead>
          <tr>
            <th style="width:18%;">Component</th>
            <th style="width:14%;">Technology</th>
            <th style="width:14%;">Category</th>
            <th>Rationale</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><span class="tech-name">Topic Modeling</span></td>
            <td><span class="tech-badge">BERTopic</span></td>
            <td>NLP</td>
            <td>Unsupervised — no labelled training data required, which is the realistic
            constraint when adding a new competitor. Produces semantically coherent clusters
            via sentence embeddings rather than bag-of-words. Topic labels are human-readable
            noun phrases, not index numbers. Minimum corpus size (~100 docs) is achievable
            from public review data within days of scraping.</td>
          </tr>
          <tr>
            <td><span class="tech-name">Sentiment Scoring</span></td>
            <td><span class="tech-badge">VADER</span></td>
            <td>NLP</td>
            <td>Rule-based lexicon designed specifically for short social media text and
            review language — exactly the input domain here. Runs in microseconds per
            document, which matters when processing tens of thousands of reviews in a
            single pipeline run. No GPU required. Sentence-BERT embeddings are used
            alongside VADER for delta computation (change in sentiment over time).</td>
          </tr>
          <tr>
            <td><span class="tech-name">Entity Extraction</span></td>
            <td><span class="tech-badge">spaCy NER</span></td>
            <td>NLP</td>
            <td>The en_core_web_sm model identifies organisations, products, and
            persons mentioned in reviews — enabling the Hot Prospect Finder to surface
            company-size signals from unstructured post text. spaCy's C-extension
            backend processes the full corpus in seconds.</td>
          </tr>
          <tr>
            <td><span class="tech-name">Battlecard &amp; Outreach Generation</span></td>
            <td><span class="tech-badge">Claude API</span></td>
            <td>LLM</td>
            <td>Anthropic's claude-sonnet-4-6 model is used for two specific tasks that
            require genuine language understanding: synthesising ranked pain point data
            into structured objection handlers, and drafting personalised outreach emails
            from alert context. The model is called on demand, not in any automated loop,
            to keep API costs predictable. JSON-structured output is always requested and
            parsed — never free-form markdown — so the rendering layer has a stable contract.</td>
          </tr>
          <tr>
            <td><span class="tech-name">Database</span></td>
            <td><span class="tech-badge">SQLite</span></td>
            <td>Storage</td>
            <td>A single-file relational database is the correct choice for a prototype
            where the entire dataset fits in memory and there is no concurrent write
            requirement. The DATABASE_URL environment variable already supports a
            PostgreSQL URI, so the migration path to production is a one-line config
            change. Choosing PostgreSQL at prototype stage would add operational
            complexity with no benefit at this data volume.</td>
          </tr>
          <tr>
            <td><span class="tech-name">Dashboard</span></td>
            <td><span class="tech-badge">Streamlit</span></td>
            <td>UI</td>
            <td>Streamlit's reactive execution model — rerun the entire script on
            any interaction — eliminates the need for explicit state management code,
            which would dominate a React or Vue implementation of equivalent functionality.
            It renders Plotly charts natively, supports custom HTML injection via
            st.html(), and produces shareable demos via a single terminal command.
            For a prototype targeting business stakeholders, iteration speed outweighs
            the constraints of Streamlit's rendering model.</td>
          </tr>
          <tr>
            <td><span class="tech-name">Scheduling</span></td>
            <td><span class="tech-badge">APScheduler</span></td>
            <td>Orchestration</td>
            <td>In-process scheduling is sufficient for a single-server prototype. The
            daily scrape and alert check jobs run as background threads within the
            Streamlit process — no external scheduler (Airflow, Celery, cron) required.
            APScheduler supports cron-style intervals, job persistence, and graceful
            shutdown with minimal configuration overhead.</td>
          </tr>
          <tr>
            <td><span class="tech-name">Charts</span></td>
            <td><span class="tech-badge">Plotly</span></td>
            <td>Visualisation</td>
            <td>Interactive hover states are essential for the Sentiment Timeline
            (users need to read news event text on hover) and for the Pain Point bar
            chart (users inspect mention counts per cluster). Matplotlib produces static
            images. Plotly integrates directly with Streamlit via st.plotly_chart()
            and supports the brand colour system through layout configuration
            without requiring CSS overrides.</td>
          </tr>
        </tbody>
      </table>
    </div>
    """)

    st.html('<div class="info-divider"></div>')

    # LLM integration detail
    st.html("""
    <div class="info-section">
      <div class="info-eyebrow">LLM Integration</div>
      <div class="info-h2">How Claude is Used — and Where It Is Not</div>
      <div class="info-body" style="margin-bottom:16px;">
        A key architectural decision was to constrain Claude API usage to two
        specific, bounded tasks rather than using it as a general reasoning layer
        across the platform.
      </div>
      <div class="eng-callout">
        <strong>Module 04 — Battlecard Generator:</strong> The LLM receives a
        structured prompt containing ranked pain points (from M01), feature gaps
        (from M03), and a competitor name. It returns a JSON object matching a
        defined schema — objections, evidence, counters, and proof quotes — which
        the UI renders into a formatted battlecard. Requesting JSON output rather
        than free-form text eliminates parsing ambiguity and makes the output
        contract explicit. The <code>@retry_with_backoff</code> decorator handles
        transient API failures transparently.
      </div>
      <div class="eng-callout">
        <strong>Module 05 — Trigger Alerts:</strong> When a vulnerability signal
        fires, the LLM receives the alert type, competitor name, and evidence
        summary. It returns 3–4 sentences of outreach email copy personalised to
        the specific situation. This replaces a library of static templates with a
        single prompt that contextualises itself to each alert. A template fallback
        is always available if the API call fails.
      </div>
      <div class="info-body">
        Every other module — Pain Point Radar, Sentiment Timeline, Feature Wish Miner,
        and Hot Prospect Finder — operates entirely on SQL aggregations and local NLP
        models with no API dependency. This means the platform remains fully functional
        if the Claude API is unavailable or if the operator prefers to run without an
        API key, with only the AI-generated text outputs degraded.
      </div>
    </div>
    """)

    st.html('<div class="info-divider"></div>')

    # Limitations
    st.html("""
    <div class="info-section">
      <div class="info-eyebrow">Known Constraints</div>
      <div class="info-h2">Prototype Limitations and Production Path</div>
      <table class="tech-table">
        <thead>
          <tr>
            <th style="width:25%;">Limitation</th>
            <th>Current Behaviour</th>
            <th>Production Mitigation</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><span class="tech-name">SQLite concurrency</span></td>
            <td>Single-writer; concurrent dashboard and scheduler writes will queue</td>
            <td>Set DATABASE_URL to a PostgreSQL URI — no application code changes required</td>
          </tr>
          <tr>
            <td><span class="tech-name">BERTopic minimum corpus</span></td>
            <td>Below ~100 reviews, topic clusters are noisy or collapse to outlier class (−1)</td>
            <td>Enforce minimum review count gate in pipeline before topic modeling runs</td>
          </tr>
          <tr>
            <td><span class="tech-name">Scraping rate limits</span></td>
            <td>G2 and Trustpilot throttle aggressive scrapers; 1–2 s delay per request</td>
            <td>Use cached HTML fixtures for CI; consider licensed API access at scale</td>
          </tr>
          <tr>
            <td><span class="tech-name">No authentication</span></td>
            <td>Dashboard is publicly accessible on any network it is served from</td>
            <td>Add streamlit-authenticator or reverse-proxy with OAuth before exposing externally</td>
          </tr>
          <tr>
            <td><span class="tech-name">Reddit API tier</span></td>
            <td>Free tier limits to 100 req/min and 1,000 posts per query</td>
            <td>Upgrade to Reddit Data API commercial tier for production-scale monitoring</td>
          </tr>
          <tr>
            <td><span class="tech-name">In-process scheduling</span></td>
            <td>APScheduler runs inside the Streamlit process; a server restart kills jobs</td>
            <td>Move to a standalone worker process or managed scheduler (Cloud Scheduler, Airflow)</td>
          </tr>
        </tbody>
      </table>
    </div>
    """)
