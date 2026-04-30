"""Module tests — one class per module, added per sprint.

Sprint 2: TestPainPointRadar
Sprint 3: TestSentimentTimeline, TestFeatureWishMiner
Sprint 4: TestBattlecardGenerator
Sprint 5: TestTriggerAlerts, TestHotProspectFinder
"""

from unittest.mock import patch

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
