"""Module tests — one class per module, added per sprint.

Sprint 2: TestPainPointRadar
Sprint 3: TestSentimentTimeline, TestFeatureWishMiner
Sprint 4: TestBattlecardGenerator
Sprint 5: TestTriggerAlerts, TestHotProspectFinder
"""

import json
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# ── Sprint 2 — Pain Point Radar ───────────────────────────────────────────────

# Fixture: simulated processed_reviews rows for a single competitor
_PAIN_FIXTURE = pd.DataFrame(
    {
        "topic_label": [
            "pricing_costs", "support_response", "learning_curve",
            "mobile_app", "integration", "reporting",
        ],
        "topic_cluster": [0, 1, 2, 3, 4, 5],
        "mention_count": [45, 30, 25, 18, 15, 12],
        "avg_sentiment": [-0.72, -0.65, -0.58, -0.40, -0.30, -0.20],
        "last_seen": ["2025-12-01"] * 6,
    }
)


def _make_get_pain_points_df() -> pd.DataFrame:
    """Return the expected output of get_pain_points built from _PAIN_FIXTURE."""
    df = _PAIN_FIXTURE.copy()
    df["avg_severity"] = ((1.0 - df["avg_sentiment"]) / 2.0).clip(0.0, 1.0).round(3)
    df["trend_direction"] = "stable"
    df["trend_icon"] = "→"
    return df[["topic_label", "mention_count", "avg_severity", "trend_direction", "trend_icon"]]


class TestPainPointRadar:
    """Unit tests for modules/pain_point_radar.py."""

    @patch("modules.pain_point_radar.query_df")
    @patch("modules.pain_point_radar.compute_trend", return_value="stable")
    def test_returns_required_columns(self, mock_trend, mock_query) -> None:
        """get_pain_points() output must have exactly the expected columns."""
        from modules.pain_point_radar import get_pain_points

        mock_query.return_value = _PAIN_FIXTURE.copy()

        result = get_pain_points("Salesforce", top_n=10)

        required = {"topic_label", "mention_count", "avg_severity", "trend_direction", "trend_icon"}
        assert required.issubset(result.columns), (
            f"Missing columns: {required - set(result.columns)}"
        )

    @patch("modules.pain_point_radar.query_df")
    @patch("modules.pain_point_radar.compute_trend", return_value="stable")
    def test_sorted_by_severity_descending(self, mock_trend, mock_query) -> None:
        """Rows must be ordered with highest avg_severity first."""
        from modules.pain_point_radar import get_pain_points

        mock_query.return_value = _PAIN_FIXTURE.copy()

        result = get_pain_points("Salesforce")

        severities = result["avg_severity"].tolist()
        assert severities == sorted(severities, reverse=True), (
            "Pain points must be sorted by avg_severity descending"
        )

    @patch("modules.pain_point_radar.query_df")
    @patch("modules.pain_point_radar.compute_trend", return_value="stable")
    def test_avg_severity_in_valid_range(self, mock_trend, mock_query) -> None:
        """avg_severity must be in [0, 1] for all rows."""
        from modules.pain_point_radar import get_pain_points

        mock_query.return_value = _PAIN_FIXTURE.copy()

        result = get_pain_points("Salesforce")

        assert (result["avg_severity"] >= 0.0).all(), "avg_severity must be ≥ 0"
        assert (result["avg_severity"] <= 1.0).all(), "avg_severity must be ≤ 1"

    @patch("modules.pain_point_radar.query_df")
    @patch("modules.pain_point_radar.compute_trend", return_value="stable")
    def test_top_n_limit_respected(self, mock_trend, mock_query) -> None:
        """get_pain_points() must respect the top_n parameter."""
        from modules.pain_point_radar import get_pain_points

        mock_query.return_value = _PAIN_FIXTURE.copy()

        result = get_pain_points("Salesforce", top_n=3)

        # The SQL LIMIT is applied by query_df which is mocked — we return 6 rows.
        # The function should not further truncate, but with a real DB it would.
        # We test that top_n is passed through as a query param.
        assert mock_query.call_args[0][1] == ("Salesforce", 3)

    @patch("modules.pain_point_radar.query_df")
    @patch("modules.pain_point_radar.compute_trend", return_value="stable")
    def test_empty_db_returns_empty_df(self, mock_trend, mock_query) -> None:
        """When no data exists, get_pain_points() returns an empty DataFrame."""
        from modules.pain_point_radar import get_pain_points

        mock_query.return_value = pd.DataFrame()

        result = get_pain_points("UnknownCompetitor")

        assert result.empty
        assert "topic_label" in result.columns

    @patch("modules.pain_point_radar.query_df")
    def test_compute_trend_returns_valid_string(self, mock_query) -> None:
        """compute_trend() must return one of the three valid values."""
        from modules.pain_point_radar import compute_trend

        # Simulate an anchor date and counts that yield each trend type
        valid_results = set()
        for current, prior in [(10, 5), (5, 5), (5, 10)]:
            mock_query.side_effect = [
                pd.DataFrame({"0": ["2025-12-01"]}),  # anchor query
                pd.DataFrame({"current_count": [current], "prior_count": [prior]}),
            ]
            result = compute_trend(topic_id=0, window_days=30)
            assert result in {"rising", "stable", "declining"}, (
                f"compute_trend() returned invalid value: '{result}'"
            )
            valid_results.add(result)

    @patch("modules.pain_point_radar.query_df")
    @patch("modules.pain_point_radar.compute_trend", return_value="rising")
    def test_trend_icon_matches_direction(self, mock_trend, mock_query) -> None:
        """trend_icon must correspond to trend_direction for every row."""
        from modules.pain_point_radar import get_pain_points

        mock_query.return_value = _PAIN_FIXTURE.copy()

        result = get_pain_points("Salesforce")

        icon_map = {"rising": "↑", "stable": "→", "declining": "↓"}
        for _, row in result.iterrows():
            assert row["trend_icon"] == icon_map[row["trend_direction"]], (
                f"Mismatch: direction={row['trend_direction']}, icon={row['trend_icon']}"
            )


# ── Sprint 3 — Sentiment Timeline ─────────────────────────────────────────────

# Fixture: raw sentiment rows (one per review, before aggregation)
_TIMELINE_RAW = pd.DataFrame(
    {
        "month": [
            "2025-06", "2025-06", "2025-06",
            "2025-07", "2025-07",
            "2025-08", "2025-08", "2025-08",
            "2025-09", "2025-09",
        ],
        "sentiment_score": [
            -0.60, -0.50, -0.70,   # 2025-06: avg ≈ -0.600
            -0.40, -0.30,           # 2025-07: avg = -0.350
            -0.20, -0.10, -0.30,   # 2025-08: avg ≈ -0.200
            -0.45, -0.55,           # 2025-09: avg = -0.500
        ],
    }
)

# Fixture: news rows returned by the second query_df call inside fetch_news_events
_NEWS_RAW = pd.DataFrame(
    {
        "month": ["2025-07", "2025-09"],
        "headline": ["Salesforce announces price hike", "Major Salesforce outage reported"],
        "sentiment_score": [-0.80, -0.90],
    }
)


class TestSentimentTimeline:
    """Unit tests for modules/sentiment_timeline.py."""

    @patch("modules.sentiment_timeline.fetch_news_events", return_value=[])
    @patch("modules.sentiment_timeline.query_df")
    def test_returns_required_columns(self, mock_query, mock_events) -> None:
        """build_timeline() must return all seven required columns."""
        from modules.sentiment_timeline import build_timeline

        mock_query.return_value = _TIMELINE_RAW.copy()
        result = build_timeline("Salesforce", months=18)

        required = {"month", "competitor", "avg_sentiment", "stddev", "review_count", "top_event", "event_url"}
        assert required.issubset(result.columns), f"Missing: {required - set(result.columns)}"

    @patch("modules.sentiment_timeline.fetch_news_events", return_value=[])
    @patch("modules.sentiment_timeline.query_df")
    def test_avg_sentiment_within_range(self, mock_query, mock_events) -> None:
        """avg_sentiment must be within [-1.0, 1.0] for all rows."""
        from modules.sentiment_timeline import build_timeline

        mock_query.return_value = _TIMELINE_RAW.copy()
        result = build_timeline("Salesforce")

        assert (result["avg_sentiment"] >= -1.0).all(), "avg_sentiment below -1"
        assert (result["avg_sentiment"] <= 1.0).all(), "avg_sentiment above 1"

    @patch("modules.sentiment_timeline.fetch_news_events", return_value=[])
    @patch("modules.sentiment_timeline.query_df")
    def test_months_filter_limits_rows(self, mock_query, mock_events) -> None:
        """months=2 should return at most 2 distinct calendar months."""
        from modules.sentiment_timeline import build_timeline

        mock_query.return_value = _TIMELINE_RAW.copy()
        result = build_timeline("Salesforce", months=2)

        assert len(result) <= 2, (
            f"Expected ≤ 2 month rows with months=2, got {len(result)}"
        )

    @patch("modules.sentiment_timeline.fetch_news_events", return_value=[])
    @patch("modules.sentiment_timeline.query_df")
    def test_stddev_nonnegative(self, mock_query, mock_events) -> None:
        """stddev must be ≥ 0 for all rows."""
        from modules.sentiment_timeline import build_timeline

        mock_query.return_value = _TIMELINE_RAW.copy()
        result = build_timeline("Salesforce")

        assert (result["stddev"] >= 0.0).all(), "stddev must be non-negative"

    @patch("modules.sentiment_timeline.fetch_news_events", return_value=[])
    @patch("modules.sentiment_timeline.query_df")
    def test_empty_db_returns_empty_df(self, mock_query, mock_events) -> None:
        """When no data exists, build_timeline() returns an empty DataFrame."""
        from modules.sentiment_timeline import build_timeline

        mock_query.return_value = pd.DataFrame()
        result = build_timeline("UnknownCompetitor")

        assert result.empty
        assert "month" in result.columns

    @patch("modules.sentiment_timeline.fetch_news_events")
    @patch("modules.sentiment_timeline.query_df")
    def test_news_events_overlay_populates_top_event(self, mock_query, mock_events) -> None:
        """Months with a news event must have top_event populated."""
        from modules.sentiment_timeline import build_timeline

        mock_query.return_value = _TIMELINE_RAW.copy()
        mock_events.return_value = [
            {"month": "2025-07", "headline": "Price hike announced", "url": None, "sentiment_score": -0.8},
        ]

        result = build_timeline("Salesforce")

        july_row = result[result["month"] == "2025-07"]
        assert not july_row.empty, "Expected a row for 2025-07"
        assert july_row["top_event"].iloc[0] == "Price hike announced"

    @patch("modules.sentiment_timeline.query_df")
    def test_fetch_news_events_returns_worst_per_month(self, mock_query) -> None:
        """fetch_news_events() must return exactly one (worst) event per month."""
        from modules.sentiment_timeline import fetch_news_events

        mock_query.return_value = _NEWS_RAW.copy()
        result = fetch_news_events("Salesforce", ("2025-06-01", "2025-09-30"))

        assert len(result) == 2, "Expected one event per month"
        months = {e["month"] for e in result}
        assert months == {"2025-07", "2025-09"}
        required_keys = {"month", "headline", "url", "sentiment_score"}
        for event in result:
            assert required_keys.issubset(event.keys()), f"Missing keys in event: {event}"


# ── Sprint 3 — Feature Wish Miner ─────────────────────────────────────────────

# Fixture: two distinct wish clusters separated in embedding space.
# Phrases 0 and 1 should cluster together; phrase 2 is orthogonal.
_WISH_FIXTURE = pd.DataFrame(
    {
        "wish_phrases": [
            json.dumps(["I wish the mobile app had offline mode"]),
            json.dumps(["would be nice if they added offline support for the mobile app"]),
            json.dumps(["I wish pricing was more transparent and predictable"]),
        ]
    }
)


def _mock_model_factory() -> MagicMock:
    """Return a SentenceTransformer mock with deterministic normalized embeddings.

    Phrases 0 and 1 (mobile/offline) → vectors that yield cosine sim ≥ 0.80.
    Phrase 2 (pricing) → orthogonal vector (cosine sim = 0).
    """
    import numpy as np

    mock_model = MagicMock()

    # Encoding order matches the flattened phrase list: [phrase0, phrase1, phrase2]
    # Using unit vectors: dot(v0, v1) = 0.95 ≥ 0.80 → same cluster
    # dot(v0, v2) = 0.0 < 0.80 → different cluster
    mock_model.encode.return_value = np.array(
        [
            [1.0, 0.0, 0.0],          # phrase 0
            [0.951, 0.309, 0.0],       # phrase 1 — cos_sim with phrase 0 ≈ 0.951
            [0.0, 1.0, 0.0],           # phrase 2 — orthogonal
        ],
        dtype=float,
    )
    return mock_model


class TestFeatureWishMiner:
    """Unit tests for modules/feature_wish_miner.py."""

    @patch("modules.feature_wish_miner._get_model")
    @patch("modules.feature_wish_miner.query_df")
    def test_returns_required_columns(self, mock_query, mock_get_model) -> None:
        """extract_wishes() output must have the three required columns."""
        from modules.feature_wish_miner import extract_wishes

        mock_query.return_value = _WISH_FIXTURE.copy()
        mock_get_model.return_value = _mock_model_factory()

        result = extract_wishes("Salesforce")

        required = {"wish_phrase_cluster", "count", "sample_quotes"}
        assert required.issubset(result.columns), f"Missing: {required - set(result.columns)}"

    @patch("modules.feature_wish_miner._get_model")
    @patch("modules.feature_wish_miner.query_df")
    def test_two_distinct_phrases_form_two_clusters(self, mock_query, mock_get_model) -> None:
        """Orthogonal phrases must yield separate clusters."""
        from modules.feature_wish_miner import extract_wishes

        mock_query.return_value = _WISH_FIXTURE.copy()
        mock_get_model.return_value = _mock_model_factory()

        result = extract_wishes("Salesforce")

        # Phrases 0+1 merge (cos_sim ≈ 0.95 ≥ 0.80); phrase 2 is separate → 2 clusters
        assert len(result) == 2, (
            f"Expected 2 clusters (1 mobile/offline + 1 pricing), got {len(result)}"
        )

    @patch("modules.feature_wish_miner._get_model")
    @patch("modules.feature_wish_miner.query_df")
    def test_cluster_count_reflects_merged_phrases(self, mock_query, mock_get_model) -> None:
        """The merged cluster must report count=2 (both mobile/offline phrases)."""
        from modules.feature_wish_miner import extract_wishes

        mock_query.return_value = _WISH_FIXTURE.copy()
        mock_get_model.return_value = _mock_model_factory()

        result = extract_wishes("Salesforce")

        # Sorted by count desc — largest cluster is first
        assert result.iloc[0]["count"] == 2, (
            f"Mobile/offline cluster should have count=2, got {result.iloc[0]['count']}"
        )

    @patch("modules.feature_wish_miner._get_model")
    @patch("modules.feature_wish_miner.query_df")
    def test_empty_db_returns_empty_df(self, mock_query, mock_get_model) -> None:
        """When no wish phrases exist, extract_wishes() returns an empty DataFrame."""
        from modules.feature_wish_miner import extract_wishes

        mock_query.return_value = pd.DataFrame()
        result = extract_wishes("UnknownCompetitor")

        assert result.empty
        assert "wish_phrase_cluster" in result.columns

    @patch("modules.feature_wish_miner._get_model")
    def test_flag_own_features_adds_columns(self, mock_get_model) -> None:
        """flag_own_features() must add your_product_has_it and matched_feature."""
        import numpy as np

        from modules.feature_wish_miner import flag_own_features

        wish_df = pd.DataFrame(
            {
                "wish_phrase_cluster": ["offline mobile support", "transparent pricing"],
                "count": [2, 1],
                "sample_quotes": [[], []],
            }
        )

        mock_model = MagicMock()
        # wish embeddings: shape (2, 2); feature embeddings: shape (1, 2)
        # sim(wish0, feature0) = 0.95 ≥ 0.45 → covered
        # sim(wish1, feature0) = 0.10 < 0.45 → gap
        mock_model.encode.side_effect = [
            np.array([[1.0, 0.0], [0.0, 1.0]]),   # wish embeddings
            np.array([[0.95, 0.31]]),               # feature embeddings (normalized)
        ]
        mock_get_model.return_value = mock_model

        result = flag_own_features(wish_df, ["offline mobile"])

        assert "your_product_has_it" in result.columns, "Missing your_product_has_it"
        assert "matched_feature" in result.columns, "Missing matched_feature"
        assert result["your_product_has_it"].dtype == bool or result["your_product_has_it"].dtype == object

    @patch("modules.feature_wish_miner._get_model")
    def test_empty_own_features_flags_nothing(self, mock_get_model) -> None:
        """With an empty own_feature_list, every cluster must be flagged as a gap."""
        from modules.feature_wish_miner import flag_own_features

        wish_df = pd.DataFrame(
            {
                "wish_phrase_cluster": ["offline mobile support"],
                "count": [3],
                "sample_quotes": [[]],
            }
        )
        result = flag_own_features(wish_df, own_feature_list=[])

        assert not result["your_product_has_it"].any(), (
            "No features should be covered when own_feature_list is empty"
        )


# ── Sprint 4 — Battlecard Generator ───────────────────────────────────────────

_PAIN_FIXTURE_5 = pd.DataFrame(
    {
        "topic_label": [
            "pricing_costs", "support_response", "learning_curve",
            "mobile_app", "integration",
        ],
        "mention_count": [45, 30, 25, 18, 15],
        "avg_severity": [0.86, 0.82, 0.79, 0.70, 0.65],
        "trend_direction": ["rising", "stable", "stable", "declining", "stable"],
        "trend_icon": ["↑", "→", "→", "↓", "→"],
    }
)

_VALID_BATTLECARD_JSON = json.dumps(
    {
        "competitor": "Salesforce",
        "generated_at": "2025-12-01T10:00:00+00:00",
        "objections": [
            {
                "objection": "Salesforce has deeper enterprise features",
                "evidence": "pricing_costs — 45 mentions, severity 0.86",
                "counter": "We deliver 80% of Salesforce's feature depth at 40% of the cost with flat-rate pricing.",
                "proof_quote": "The per-seat licensing cost was killing our margins — we had to find an alternative.",
            }
        ],
        "feature_gaps": [
            {
                "gap": "offline mobile access",
                "frequency": 18,
                "your_advantage": "Full offline mode on iOS and Android — no signal required.",
            }
        ],
        "recommended_pitch": (
            "73% of Salesforce customers cite cost and complexity as their top complaints. "
            "Our flat-rate pricing eliminates surprise renewals, and onboarding takes 2 weeks, not 3 months."
        ),
    }
)


class TestBattlecardGenerator:
    """Unit tests for modules/battlecard_generator.py."""

    @patch("modules.battlecard_generator._save_battlecard")
    @patch("modules.battlecard_generator._call_claude")
    @patch("modules.battlecard_generator.extract_wishes")
    @patch("modules.battlecard_generator.get_pain_points")
    def test_returns_valid_schema(
        self, mock_pain, mock_wishes, mock_claude, mock_save
    ) -> None:
        """generate_battlecard() must return a dict with all four required top-level keys."""
        from modules.battlecard_generator import generate_battlecard

        mock_pain.return_value = _PAIN_FIXTURE_5.copy()
        mock_wishes.return_value = pd.DataFrame()
        mock_claude.return_value = _VALID_BATTLECARD_JSON

        result = generate_battlecard("Salesforce")

        for key in ("competitor", "generated_at", "objections", "feature_gaps", "recommended_pitch"):
            assert key in result, f"Missing key: {key}"
        assert result["competitor"] == "Salesforce"
        assert isinstance(result["objections"], list)
        assert isinstance(result["feature_gaps"], list)

    @patch("modules.battlecard_generator._save_battlecard")
    @patch("modules.battlecard_generator._call_claude")
    @patch("modules.battlecard_generator.extract_wishes")
    @patch("modules.battlecard_generator.get_pain_points")
    def test_repairs_malformed_json(
        self, mock_pain, mock_wishes, mock_claude, mock_save
    ) -> None:
        """When the first response is invalid JSON, a second repair call must succeed."""
        from modules.battlecard_generator import generate_battlecard

        mock_pain.return_value = _PAIN_FIXTURE_5.copy()
        mock_wishes.return_value = pd.DataFrame()
        # First call: malformed JSON.  Second call (repair): valid JSON.
        mock_claude.side_effect = ["{ invalid json {{", _VALID_BATTLECARD_JSON]

        result = generate_battlecard("Salesforce")

        assert "competitor" in result
        assert mock_claude.call_count == 2, (
            "Expected exactly 2 API calls: initial + repair"
        )

    @patch("modules.battlecard_generator._save_battlecard")
    @patch("modules.battlecard_generator._call_claude")
    @patch("modules.battlecard_generator.extract_wishes")
    @patch("modules.battlecard_generator.get_pain_points")
    def test_raises_when_repair_also_fails(
        self, mock_pain, mock_wishes, mock_claude, mock_save
    ) -> None:
        """generate_battlecard() must raise ValueError if both JSON parse attempts fail."""
        from modules.battlecard_generator import generate_battlecard

        mock_pain.return_value = _PAIN_FIXTURE_5.copy()
        mock_wishes.return_value = pd.DataFrame()
        mock_claude.side_effect = ["{ broken {{", "still broken {{"]

        with pytest.raises(ValueError, match="Failed to parse battlecard JSON"):
            generate_battlecard("Salesforce")

    def test_battlecard_to_markdown_has_required_sections(self) -> None:
        """battlecard_to_markdown() must include all structural sections."""
        from modules.battlecard_generator import battlecard_to_markdown

        card = json.loads(_VALID_BATTLECARD_JSON)
        md = battlecard_to_markdown(card)

        assert "Salesforce" in md, "Competitor name missing"
        assert "Recommended Pitch" in md, "'Recommended Pitch' section missing"
        assert "Objection Handlers" in md, "'Objection Handlers' section missing"
        assert "Feature Gaps" in md, "'Feature Gaps' section missing"
        assert "pricing_costs" in md or "enterprise" in md.lower(), (
            "Objection content missing"
        )

    @patch("modules.battlecard_generator.generate_battlecard")
    def test_refresh_all_battlecards_calls_each_competitor(
        self, mock_generate
    ) -> None:
        """refresh_all_battlecards() must call generate_battlecard once per competitor."""
        from config import COMPETITORS
        from modules.battlecard_generator import refresh_all_battlecards

        mock_generate.return_value = json.loads(_VALID_BATTLECARD_JSON)

        refresh_all_battlecards()

        assert mock_generate.call_count == len(COMPETITORS), (
            f"Expected {len(COMPETITORS)} calls, got {mock_generate.call_count}"
        )
        called_names = {call.args[0] for call in mock_generate.call_args_list}
        expected_names = {c["name"] for c in COMPETITORS}
        assert called_names == expected_names

    @patch("modules.battlecard_generator._save_battlecard")
    @patch("modules.battlecard_generator._call_claude")
    @patch("modules.battlecard_generator.extract_wishes")
    @patch("modules.battlecard_generator.get_pain_points")
    def test_empty_pain_data_still_generates(
        self, mock_pain, mock_wishes, mock_claude, mock_save
    ) -> None:
        """generate_battlecard() must not crash when pain_df is empty."""
        from modules.battlecard_generator import generate_battlecard

        mock_pain.return_value = pd.DataFrame()
        mock_wishes.return_value = pd.DataFrame()
        mock_claude.return_value = _VALID_BATTLECARD_JSON

        result = generate_battlecard("Salesforce")

        assert "competitor" in result
        # The user prompt was still constructed and the API was called
        assert mock_claude.call_count == 1
