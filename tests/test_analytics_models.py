"""
Tests for analytics data models.

Following TDD principles - these tests define the expected behavior
of the analytics model dataclasses.
"""

import pytest
from datetime import date, timedelta

from src.models.analytics_models import (
    TrendData,
    BeanComparisonMetrics,
    ComparisonData,
    CorrelationResult,
    OptimalParameters,
    ConsistencyMetrics,
    AnalyticsSummary,
)


class TestTrendData:
    """Tests for TrendData model."""

    @pytest.fixture
    def sample_trend(self):
        """Create a sample trend with meaningful data."""
        today = date.today()
        return TrendData(
            metric="final_extraction_yield_percent",
            window_days=30,
            values=[18.5, 19.0, 19.5, 20.0, 20.5],
            dates=[today - timedelta(days=i) for i in range(4, -1, -1)],
            trend_direction="improving",
            percent_change=10.8,
            moving_average=[18.5, 18.75, 19.0, 19.5, 20.0],
            sample_size=5,
        )

    @pytest.fixture
    def insufficient_trend(self):
        """Create a trend with insufficient data."""
        today = date.today()
        return TrendData(
            metric="score_overall_rating",
            window_days=30,
            values=[7.5, 8.0],
            dates=[today - timedelta(days=1), today],
            trend_direction="improving",
            percent_change=6.7,
            moving_average=[7.5, 7.75],
            sample_size=2,
        )

    def test_is_meaningful_with_enough_data(self, sample_trend):
        """Trend with 3+ samples should be meaningful."""
        assert sample_trend.is_meaningful is True

    def test_is_meaningful_with_insufficient_data(self, insufficient_trend):
        """Trend with <3 samples should not be meaningful."""
        assert insufficient_trend.is_meaningful is False

    def test_summary_with_meaningful_data(self, sample_trend):
        """Summary should describe the trend when data is meaningful."""
        summary = sample_trend.summary
        assert "improved" in summary
        assert "10.8%" in summary
        assert "30 days" in summary
        assert "5 brews" in summary

    def test_summary_with_insufficient_data(self, insufficient_trend):
        """Summary should indicate insufficient data."""
        summary = insufficient_trend.summary
        assert "Insufficient data" in summary
        assert "2 brews" in summary

    def test_summary_declining_trend(self):
        """Summary should correctly describe declining trends."""
        trend = TrendData(
            metric="score_overall_rating",
            window_days=14,
            values=[8.0, 7.5, 7.0],
            dates=[date.today() - timedelta(days=i) for i in range(2, -1, -1)],
            trend_direction="declining",
            percent_change=-12.5,
            moving_average=[8.0, 7.75, 7.5],
            sample_size=3,
        )
        summary = trend.summary
        assert "declined" in summary

    def test_summary_stable_trend(self):
        """Summary should correctly describe stable trends."""
        trend = TrendData(
            metric="final_tds_percent",
            window_days=30,
            values=[1.25, 1.26, 1.24, 1.25],
            dates=[date.today() - timedelta(days=i) for i in range(3, -1, -1)],
            trend_direction="stable",
            percent_change=0.0,
            moving_average=[1.25, 1.255, 1.25, 1.25],
            sample_size=4,
        )
        summary = trend.summary
        assert "remained stable" in summary


class TestBeanComparisonMetrics:
    """Tests for BeanComparisonMetrics model."""

    def test_creation(self):
        """Should create bean metrics with all fields."""
        metrics = BeanComparisonMetrics(
            bean_name="Ethiopian Yirgacheffe",
            sample_size=10,
            avg_extraction=20.5,
            avg_tds=1.30,
            avg_rating=8.2,
            avg_brew_score=85.0,
            extraction_std=0.8,
            tds_std=0.05,
            rating_std=0.5,
            best_rating=9.0,
            worst_rating=7.0,
        )
        assert metrics.bean_name == "Ethiopian Yirgacheffe"
        assert metrics.sample_size == 10
        assert metrics.avg_extraction == 20.5

    def test_creation_with_none_values(self):
        """Should handle None values for optional metrics."""
        metrics = BeanComparisonMetrics(
            bean_name="Test Bean",
            sample_size=2,
            avg_extraction=None,
            avg_tds=None,
            avg_rating=7.5,
            avg_brew_score=None,
            extraction_std=None,
            tds_std=None,
            rating_std=None,
            best_rating=8.0,
            worst_rating=7.0,
        )
        assert metrics.avg_extraction is None
        assert metrics.avg_rating == 7.5


class TestComparisonData:
    """Tests for ComparisonData model."""

    @pytest.fixture
    def sample_comparison(self):
        """Create a sample comparison with multiple beans."""
        metrics_a = BeanComparisonMetrics(
            bean_name="Bean A",
            sample_size=8,
            avg_extraction=20.0,
            avg_tds=1.28,
            avg_rating=7.8,
            avg_brew_score=80.0,
            extraction_std=0.6,
            tds_std=0.04,
            rating_std=0.4,
            best_rating=8.5,
            worst_rating=7.0,
        )
        metrics_b = BeanComparisonMetrics(
            bean_name="Bean B",
            sample_size=5,
            avg_extraction=21.0,
            avg_tds=1.32,
            avg_rating=8.5,
            avg_brew_score=88.0,
            extraction_std=0.5,
            tds_std=0.03,
            rating_std=0.3,
            best_rating=9.0,
            worst_rating=8.0,
        )
        return ComparisonData(
            bean_names=["Bean A", "Bean B"],
            bean_metrics={"Bean A": metrics_a, "Bean B": metrics_b},
            comparison_metrics=["avg_extraction", "avg_tds", "avg_rating"],
            min_sample_size=5,
        )

    def test_is_statistically_meaningful_with_enough_data(self, sample_comparison):
        """Comparison with min sample >= 3 should be meaningful."""
        assert sample_comparison.is_statistically_meaningful is True

    def test_is_statistically_meaningful_with_insufficient_data(self):
        """Comparison with min sample < 3 should not be meaningful."""
        metrics = BeanComparisonMetrics(
            bean_name="Test", sample_size=2,
            avg_extraction=20.0, avg_tds=1.3, avg_rating=8.0,
            avg_brew_score=80.0, extraction_std=0.5, tds_std=0.03,
            rating_std=0.3, best_rating=8.5, worst_rating=7.5,
        )
        comparison = ComparisonData(
            bean_names=["Test"],
            bean_metrics={"Test": metrics},
            comparison_metrics=["avg_rating"],
            min_sample_size=2,
        )
        assert comparison.is_statistically_meaningful is False

    def test_confidence_level_high(self, sample_comparison):
        """Sample size >= 10 should give high confidence."""
        sample_comparison.min_sample_size = 12
        assert sample_comparison.confidence_level == "high"

    def test_confidence_level_medium(self, sample_comparison):
        """Sample size 5-9 should give medium confidence."""
        assert sample_comparison.confidence_level == "medium"

    def test_confidence_level_low(self):
        """Sample size 3-4 should give low confidence."""
        metrics = BeanComparisonMetrics(
            bean_name="Test", sample_size=3,
            avg_extraction=20.0, avg_tds=1.3, avg_rating=8.0,
            avg_brew_score=80.0, extraction_std=0.5, tds_std=0.03,
            rating_std=0.3, best_rating=8.5, worst_rating=7.5,
        )
        comparison = ComparisonData(
            bean_names=["Test"],
            bean_metrics={"Test": metrics},
            comparison_metrics=["avg_rating"],
            min_sample_size=3,
        )
        assert comparison.confidence_level == "low"

    def test_confidence_level_insufficient(self):
        """Sample size < 3 should give insufficient confidence."""
        metrics = BeanComparisonMetrics(
            bean_name="Test", sample_size=1,
            avg_extraction=20.0, avg_tds=1.3, avg_rating=8.0,
            avg_brew_score=80.0, extraction_std=None, tds_std=None,
            rating_std=None, best_rating=8.0, worst_rating=8.0,
        )
        comparison = ComparisonData(
            bean_names=["Test"],
            bean_metrics={"Test": metrics},
            comparison_metrics=["avg_rating"],
            min_sample_size=1,
        )
        assert comparison.confidence_level == "insufficient"


class TestCorrelationResult:
    """Tests for CorrelationResult model."""

    def test_determine_strength_strong_positive(self):
        """Correlation >= 0.7 should be strong."""
        assert CorrelationResult.determine_strength(0.85) == "strong"
        assert CorrelationResult.determine_strength(0.70) == "strong"

    def test_determine_strength_strong_negative(self):
        """Correlation <= -0.7 should be strong."""
        assert CorrelationResult.determine_strength(-0.85) == "strong"
        assert CorrelationResult.determine_strength(-0.70) == "strong"

    def test_determine_strength_moderate(self):
        """Correlation 0.4-0.7 should be moderate."""
        assert CorrelationResult.determine_strength(0.55) == "moderate"
        assert CorrelationResult.determine_strength(-0.45) == "moderate"

    def test_determine_strength_weak(self):
        """Correlation 0.2-0.4 should be weak."""
        assert CorrelationResult.determine_strength(0.30) == "weak"
        assert CorrelationResult.determine_strength(-0.25) == "weak"

    def test_determine_strength_none(self):
        """Correlation < 0.2 should be none."""
        assert CorrelationResult.determine_strength(0.15) == "none"
        assert CorrelationResult.determine_strength(-0.10) == "none"
        assert CorrelationResult.determine_strength(0.0) == "none"

    def test_determine_direction_positive(self):
        """Positive correlation should have positive direction."""
        assert CorrelationResult.determine_direction(0.5) == "positive"

    def test_determine_direction_negative(self):
        """Negative correlation should have negative direction."""
        assert CorrelationResult.determine_direction(-0.5) == "negative"

    def test_determine_direction_none(self):
        """Near-zero correlation should have no direction."""
        assert CorrelationResult.determine_direction(0.1) == "none"
        assert CorrelationResult.determine_direction(-0.1) == "none"

    def test_is_meaningful_with_enough_data(self):
        """Correlation with 3+ samples should be meaningful."""
        result = CorrelationResult(
            parameter="grind_size",
            metric="final_extraction_yield_percent",
            correlation=-0.65,
            strength="moderate",
            direction="negative",
            sample_size=10,
        )
        assert result.is_meaningful is True

    def test_is_meaningful_with_insufficient_data(self):
        """Correlation with <3 samples should not be meaningful."""
        result = CorrelationResult(
            parameter="grind_size",
            metric="final_extraction_yield_percent",
            correlation=-0.8,
            strength="strong",
            direction="negative",
            sample_size=2,
        )
        assert result.is_meaningful is False

    def test_summary_meaningful_correlation(self):
        """Summary should describe the correlation when meaningful."""
        result = CorrelationResult(
            parameter="grind_size",
            metric="final_extraction_yield_percent",
            correlation=-0.65,
            strength="moderate",
            direction="negative",
            sample_size=15,
        )
        summary = result.summary
        assert "Moderate negative correlation" in summary
        assert "grind_size" in summary
        assert "final_extraction_yield_percent" in summary
        assert "r=-0.65" in summary
        assert "n=15" in summary

    def test_summary_no_correlation(self):
        """Summary should indicate no correlation when strength is none."""
        result = CorrelationResult(
            parameter="water_temp_degC",
            metric="score_overall_rating",
            correlation=0.08,
            strength="none",
            direction="none",
            sample_size=20,
        )
        summary = result.summary
        assert "No correlation found" in summary

    def test_summary_insufficient_data(self):
        """Summary should indicate insufficient data."""
        result = CorrelationResult(
            parameter="brew_ratio_to_1",
            metric="final_tds_percent",
            correlation=0.5,
            strength="moderate",
            direction="positive",
            sample_size=2,
        )
        summary = result.summary
        assert "Insufficient data" in summary


class TestOptimalParameters:
    """Tests for OptimalParameters model."""

    @pytest.fixture
    def sample_optimal(self):
        """Create sample optimal parameters."""
        return OptimalParameters(
            bean_name="Ethiopian Sidamo",
            optimal_grind=3.5,
            optimal_temp=94.0,
            optimal_ratio=16.0,
            optimal_bloom_time=45.0,
            optimal_total_time=180.0,
            confidence="high",
            based_on_brews=15,
            top_brews_analyzed=5,
            avg_rating_of_top=8.8,
        )

    def test_is_meaningful_with_enough_data(self, sample_optimal):
        """Optimal params with 3+ brews should be meaningful."""
        assert sample_optimal.is_meaningful is True

    def test_is_meaningful_with_insufficient_data(self):
        """Optimal params with <3 brews should not be meaningful."""
        optimal = OptimalParameters(
            bean_name="Test Bean",
            optimal_grind=4.0,
            optimal_temp=93.0,
            optimal_ratio=15.5,
            optimal_bloom_time=40.0,
            optimal_total_time=150.0,
            confidence="low",
            based_on_brews=2,
            top_brews_analyzed=2,
            avg_rating_of_top=7.5,
        )
        assert optimal.is_meaningful is False

    def test_get_parameter_dict(self, sample_optimal):
        """Should return parameters as dictionary."""
        params = sample_optimal.get_parameter_dict()
        assert params["grind_size"] == 3.5
        assert params["water_temp_degC"] == 94.0
        assert params["brew_ratio_to_1"] == 16.0
        assert params["brew_bloom_time_s"] == 45.0
        assert params["brew_total_time_s"] == 180.0

    def test_get_parameter_dict_with_none_values(self):
        """Should handle None values in parameter dict."""
        optimal = OptimalParameters(
            bean_name=None,
            optimal_grind=4.0,
            optimal_temp=None,
            optimal_ratio=16.0,
            optimal_bloom_time=None,
            optimal_total_time=None,
            confidence="low",
            based_on_brews=3,
            top_brews_analyzed=3,
            avg_rating_of_top=7.0,
        )
        params = optimal.get_parameter_dict()
        assert params["grind_size"] == 4.0
        assert params["water_temp_degC"] is None
        assert params["brew_ratio_to_1"] == 16.0


class TestConsistencyMetrics:
    """Tests for ConsistencyMetrics model."""

    @pytest.fixture
    def excellent_consistency(self):
        """Create metrics with excellent consistency."""
        return ConsistencyMetrics(
            bean_name="Consistent Bean",
            extraction_std=0.3,
            extraction_cv=1.5,
            tds_std=0.02,
            tds_cv=1.6,
            rating_std=0.2,
            rating_cv=2.4,
            consistency_score=92.0,
            sample_size=20,
        )

    @pytest.fixture
    def poor_consistency(self):
        """Create metrics with poor consistency."""
        return ConsistencyMetrics(
            bean_name="Inconsistent Bean",
            extraction_std=2.5,
            extraction_cv=12.5,
            tds_std=0.15,
            tds_cv=11.5,
            rating_std=1.8,
            rating_cv=22.5,
            consistency_score=25.0,
            sample_size=15,
        )

    def test_is_meaningful_with_enough_data(self, excellent_consistency):
        """Consistency with 3+ brews should be meaningful."""
        assert excellent_consistency.is_meaningful is True

    def test_is_meaningful_with_insufficient_data(self):
        """Consistency with <3 brews should not be meaningful."""
        metrics = ConsistencyMetrics(
            bean_name="Test",
            extraction_std=0.5,
            extraction_cv=2.5,
            tds_std=0.03,
            tds_cv=2.3,
            rating_std=0.3,
            rating_cv=3.8,
            consistency_score=85.0,
            sample_size=2,
        )
        assert metrics.is_meaningful is False

    def test_consistency_rating_excellent(self, excellent_consistency):
        """Score >= 80 should be excellent."""
        assert excellent_consistency.consistency_rating == "excellent"

    def test_consistency_rating_good(self):
        """Score 60-79 should be good."""
        metrics = ConsistencyMetrics(
            bean_name="Test", extraction_std=0.8, extraction_cv=4.0,
            tds_std=0.05, tds_cv=3.8, rating_std=0.5, rating_cv=6.3,
            consistency_score=70.0, sample_size=10,
        )
        assert metrics.consistency_rating == "good"

    def test_consistency_rating_fair(self):
        """Score 40-59 should be fair."""
        metrics = ConsistencyMetrics(
            bean_name="Test", extraction_std=1.2, extraction_cv=6.0,
            tds_std=0.08, tds_cv=6.2, rating_std=0.8, rating_cv=10.0,
            consistency_score=50.0, sample_size=10,
        )
        assert metrics.consistency_rating == "fair"

    def test_consistency_rating_needs_improvement(self, poor_consistency):
        """Score < 40 should need improvement."""
        assert poor_consistency.consistency_rating == "needs improvement"

    def test_consistency_rating_insufficient_data(self):
        """Should indicate insufficient data when sample < 3."""
        metrics = ConsistencyMetrics(
            bean_name="Test", extraction_std=0.5, extraction_cv=2.5,
            tds_std=0.03, tds_cv=2.3, rating_std=0.3, rating_cv=3.8,
            consistency_score=85.0, sample_size=1,
        )
        assert metrics.consistency_rating == "insufficient data"

    def test_summary_with_bean_name(self, excellent_consistency):
        """Summary should include bean name when specified."""
        summary = excellent_consistency.summary
        assert "for Consistent Bean" in summary
        assert "excellent" in summary
        assert "92" in summary
        assert "20 brews" in summary

    def test_summary_without_bean_name(self):
        """Summary should say 'overall' when no bean specified."""
        metrics = ConsistencyMetrics(
            bean_name=None, extraction_std=0.6, extraction_cv=3.0,
            tds_std=0.04, tds_cv=3.1, rating_std=0.4, rating_cv=5.0,
            consistency_score=75.0, sample_size=25,
        )
        summary = metrics.summary
        assert "overall" in summary
        assert "good" in summary

    def test_summary_insufficient_data(self):
        """Summary should indicate insufficient data."""
        metrics = ConsistencyMetrics(
            bean_name="Test", extraction_std=0.5, extraction_cv=2.5,
            tds_std=0.03, tds_cv=2.3, rating_std=0.3, rating_cv=3.8,
            consistency_score=85.0, sample_size=2,
        )
        summary = metrics.summary
        assert "Insufficient data" in summary
        assert "2 brews" in summary


class TestAnalyticsSummary:
    """Tests for AnalyticsSummary model."""

    @pytest.fixture
    def sample_summary(self):
        """Create a sample analytics summary."""
        return AnalyticsSummary(
            total_brews=50,
            unique_beans=8,
            date_range_days=90,
            avg_extraction=20.2,
            avg_tds=1.28,
            avg_rating=7.8,
            best_bean="Ethiopian Yirgacheffe",
            most_brewed_bean="Colombian Supremo",
            consistency_score=72.0,
            improvement_trend="improving",
        )

    def test_has_enough_data_with_sufficient_brews(self, sample_summary):
        """Summary with 3+ brews should have enough data."""
        assert sample_summary.has_enough_data is True

    def test_has_enough_data_with_insufficient_brews(self):
        """Summary with <3 brews should not have enough data."""
        summary = AnalyticsSummary(
            total_brews=2,
            unique_beans=1,
            date_range_days=7,
            avg_extraction=19.5,
            avg_tds=1.25,
            avg_rating=7.0,
            best_bean="Test Bean",
            most_brewed_bean="Test Bean",
            consistency_score=None,
            improvement_trend=None,
        )
        assert summary.has_enough_data is False

    def test_creation_with_none_values(self):
        """Should handle None values for optional fields."""
        summary = AnalyticsSummary(
            total_brews=5,
            unique_beans=2,
            date_range_days=14,
            avg_extraction=None,
            avg_tds=None,
            avg_rating=7.5,
            best_bean=None,
            most_brewed_bean="Test Bean",
            consistency_score=None,
            improvement_trend=None,
        )
        assert summary.avg_extraction is None
        assert summary.avg_rating == 7.5
        assert summary.has_enough_data is True
