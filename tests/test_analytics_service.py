"""
Tests for AnalyticsService.

Following TDD principles - these tests define the expected behavior
of the AnalyticsService before implementation.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import date, timedelta

from src.services.analytics_service import AnalyticsService
from src.models.analytics_models import (
    TrendData,
    ComparisonData,
    CorrelationResult,
    OptimalParameters,
    ConsistencyMetrics,
    AnalyticsSummary,
)


class TestAnalyticsServiceInit:
    """Tests for AnalyticsService initialization."""

    def test_initialization(self):
        """Service should initialize with logger."""
        service = AnalyticsService()
        assert service is not None
        assert hasattr(service, "logger")


class TestCalculateImprovementTrend:
    """Tests for calculate_improvement_trend method."""

    @pytest.fixture
    def service(self):
        return AnalyticsService()

    @pytest.fixture
    def sample_brew_data(self):
        """Create sample brew data with improving extraction over time."""
        today = date.today()
        return pd.DataFrame({
            "brew_id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "brew_date": [today - timedelta(days=i) for i in range(9, -1, -1)],
            "bean_name": ["Bean A"] * 10,
            "final_extraction_yield_percent": [18.0, 18.5, 19.0, 19.5, 20.0, 20.2, 20.5, 20.8, 21.0, 21.2],
            "final_tds_percent": [1.20, 1.22, 1.25, 1.27, 1.28, 1.30, 1.32, 1.33, 1.35, 1.36],
            "score_overall_rating": [6.5, 7.0, 7.2, 7.5, 7.8, 8.0, 8.2, 8.3, 8.5, 8.7],
        })

    def test_trend_with_improving_extraction(self, service, sample_brew_data):
        """Should detect improving trend in extraction."""
        result = service.calculate_improvement_trend(
            sample_brew_data, "final_extraction_yield_percent", window_days=30
        )

        assert isinstance(result, TrendData)
        assert result.metric == "final_extraction_yield_percent"
        assert result.trend_direction == "improving"
        assert result.percent_change > 0
        assert result.sample_size == 10

    def test_trend_with_declining_metric(self, service):
        """Should detect declining trend."""
        today = date.today()
        df = pd.DataFrame({
            "brew_date": [today - timedelta(days=i) for i in range(4, -1, -1)],
            "score_overall_rating": [8.5, 8.0, 7.5, 7.0, 6.5],
        })

        result = service.calculate_improvement_trend(df, "score_overall_rating", window_days=30)

        assert result.trend_direction == "declining"
        assert result.percent_change < 0

    def test_trend_with_stable_metric(self, service):
        """Should detect stable trend when values don't change significantly."""
        today = date.today()
        df = pd.DataFrame({
            "brew_date": [today - timedelta(days=i) for i in range(4, -1, -1)],
            "final_tds_percent": [1.28, 1.29, 1.27, 1.28, 1.29],
        })

        result = service.calculate_improvement_trend(df, "final_tds_percent", window_days=30)

        assert result.trend_direction == "stable"
        assert abs(result.percent_change) < 5  # Less than 5% change

    def test_trend_with_window_filter(self, service, sample_brew_data):
        """Should only include data within the window."""
        result = service.calculate_improvement_trend(
            sample_brew_data, "final_extraction_yield_percent", window_days=5
        )

        # Should only include last 5 days of data
        assert result.sample_size <= 6  # At most 6 brews in 5 days

    def test_trend_with_empty_dataframe(self, service):
        """Should handle empty DataFrame gracefully."""
        df = pd.DataFrame(columns=["brew_date", "final_extraction_yield_percent"])

        result = service.calculate_improvement_trend(df, "final_extraction_yield_percent", window_days=30)

        assert result.sample_size == 0
        assert not result.is_meaningful

    def test_trend_with_single_row(self, service):
        """Should handle single row DataFrame."""
        df = pd.DataFrame({
            "brew_date": [date.today()],
            "final_extraction_yield_percent": [20.0],
        })

        result = service.calculate_improvement_trend(df, "final_extraction_yield_percent", window_days=30)

        assert result.sample_size == 1
        assert not result.is_meaningful

    def test_trend_with_missing_column(self, service):
        """Should handle missing metric column gracefully."""
        df = pd.DataFrame({
            "brew_date": [date.today()],
            "other_column": [1.0],
        })

        result = service.calculate_improvement_trend(df, "nonexistent_column", window_days=30)

        assert result.sample_size == 0

    def test_trend_moving_average_calculation(self, service, sample_brew_data):
        """Should calculate moving average correctly."""
        result = service.calculate_improvement_trend(
            sample_brew_data, "final_extraction_yield_percent", window_days=30
        )

        assert len(result.moving_average) == len(result.values)
        # Moving average should smooth out the data
        assert all(isinstance(v, (int, float)) for v in result.moving_average)


class TestCalculateBeanComparison:
    """Tests for calculate_bean_comparison method."""

    @pytest.fixture
    def service(self):
        return AnalyticsService()

    @pytest.fixture
    def multi_bean_data(self):
        """Create data with multiple beans."""
        today = date.today()
        return pd.DataFrame({
            "brew_id": range(1, 16),
            "brew_date": [today - timedelta(days=i) for i in range(15)],
            "bean_name": ["Bean A"] * 5 + ["Bean B"] * 5 + ["Bean C"] * 5,
            "final_extraction_yield_percent": [20.0, 20.5, 19.8, 20.2, 20.3] +
                                               [21.0, 21.5, 21.2, 21.3, 21.1] +
                                               [19.0, 18.5, 19.2, 18.8, 19.0],
            "final_tds_percent": [1.28, 1.30, 1.27, 1.29, 1.28] +
                                  [1.35, 1.38, 1.36, 1.37, 1.36] +
                                  [1.22, 1.20, 1.23, 1.21, 1.22],
            "score_overall_rating": [7.5, 8.0, 7.8, 7.6, 7.9] +
                                     [8.5, 8.8, 8.6, 8.7, 8.5] +
                                     [7.0, 6.8, 7.2, 6.9, 7.1],
            "score_brew": [80, 82, 79, 81, 80] +
                          [88, 90, 89, 88, 87] +
                          [72, 70, 74, 71, 73],
        })

    def test_comparison_two_beans(self, service, multi_bean_data):
        """Should compare two beans correctly."""
        result = service.calculate_bean_comparison(multi_bean_data, ["Bean A", "Bean B"])

        assert isinstance(result, ComparisonData)
        assert len(result.bean_names) == 2
        assert "Bean A" in result.bean_metrics
        assert "Bean B" in result.bean_metrics

    def test_comparison_metrics_calculated(self, service, multi_bean_data):
        """Should calculate all metrics for each bean."""
        result = service.calculate_bean_comparison(multi_bean_data, ["Bean A", "Bean B"])

        bean_a = result.bean_metrics["Bean A"]
        assert bean_a.sample_size == 5
        assert bean_a.avg_extraction is not None
        assert bean_a.avg_tds is not None
        assert bean_a.avg_rating is not None
        assert bean_a.extraction_std is not None

    def test_comparison_relative_performance(self, service, multi_bean_data):
        """Should show Bean B outperforms Bean A in this dataset."""
        result = service.calculate_bean_comparison(multi_bean_data, ["Bean A", "Bean B"])

        bean_a = result.bean_metrics["Bean A"]
        bean_b = result.bean_metrics["Bean B"]

        # Bean B has higher extraction and ratings in our test data
        assert bean_b.avg_extraction > bean_a.avg_extraction
        assert bean_b.avg_rating > bean_a.avg_rating

    def test_comparison_with_nonexistent_bean(self, service, multi_bean_data):
        """Should handle nonexistent bean gracefully."""
        result = service.calculate_bean_comparison(multi_bean_data, ["Bean A", "Nonexistent Bean"])

        assert "Bean A" in result.bean_metrics
        # Nonexistent bean should either be absent or have 0 sample size
        if "Nonexistent Bean" in result.bean_metrics:
            assert result.bean_metrics["Nonexistent Bean"].sample_size == 0

    def test_comparison_with_empty_dataframe(self, service):
        """Should handle empty DataFrame."""
        df = pd.DataFrame(columns=["bean_name", "final_extraction_yield_percent"])

        result = service.calculate_bean_comparison(df, ["Bean A", "Bean B"])

        assert result.min_sample_size == 0

    def test_comparison_confidence_level(self, service, multi_bean_data):
        """Should set appropriate confidence level."""
        result = service.calculate_bean_comparison(multi_bean_data, ["Bean A", "Bean B"])

        # With 5 samples each, should be medium confidence
        assert result.confidence_level == "medium"

    def test_comparison_with_single_sample_bean(self, service):
        """Should flag low confidence with single sample."""
        df = pd.DataFrame({
            "bean_name": ["Bean A", "Bean B"],
            "final_extraction_yield_percent": [20.0, 21.0],
            "final_tds_percent": [1.28, 1.35],
            "score_overall_rating": [7.5, 8.5],
        })

        result = service.calculate_bean_comparison(df, ["Bean A", "Bean B"])

        assert result.min_sample_size == 1
        assert not result.is_statistically_meaningful


class TestCalculateParameterCorrelations:
    """Tests for calculate_parameter_correlations method."""

    @pytest.fixture
    def service(self):
        return AnalyticsService()

    @pytest.fixture
    def correlated_data(self):
        """Create data with known correlations."""
        # Finer grind (lower number) -> higher extraction (negative correlation)
        # Higher temp -> higher extraction (positive correlation)
        np.random.seed(42)
        n = 20
        grind_sizes = np.linspace(3.0, 5.0, n)
        temps = np.linspace(90, 96, n)

        # Extraction correlates negatively with grind, positively with temp
        extraction = 22 - (grind_sizes - 3) * 1.5 + (temps - 90) * 0.3 + np.random.normal(0, 0.2, n)

        return pd.DataFrame({
            "brew_id": range(1, n + 1),
            "grind_size": grind_sizes,
            "water_temp_degC": temps,
            "brew_ratio_to_1": np.random.uniform(15, 17, n),
            "brew_bloom_time_s": np.random.uniform(30, 60, n),
            "brew_total_time_s": np.random.uniform(150, 240, n),
            "final_extraction_yield_percent": extraction,
            "final_tds_percent": np.random.uniform(1.2, 1.4, n),
            "score_overall_rating": np.random.uniform(7, 9, n),
        })

    def test_correlations_returns_list(self, service, correlated_data):
        """Should return list of CorrelationResult."""
        results = service.calculate_parameter_correlations(correlated_data)

        assert isinstance(results, list)
        assert all(isinstance(r, CorrelationResult) for r in results)

    def test_grind_extraction_negative_correlation(self, service, correlated_data):
        """Should detect negative correlation between grind and extraction."""
        results = service.calculate_parameter_correlations(correlated_data)

        grind_extraction = next(
            (r for r in results
             if r.parameter == "grind_size" and r.metric == "final_extraction_yield_percent"),
            None
        )

        assert grind_extraction is not None
        assert grind_extraction.correlation < 0
        assert grind_extraction.direction == "negative"

    def test_correlations_include_key_parameters(self, service, correlated_data):
        """Should include correlations for key brewing parameters."""
        results = service.calculate_parameter_correlations(correlated_data)

        parameters_checked = {r.parameter for r in results}

        # Should check these parameters
        assert "grind_size" in parameters_checked
        assert "water_temp_degC" in parameters_checked
        assert "brew_ratio_to_1" in parameters_checked

    def test_correlations_with_empty_dataframe(self, service):
        """Should handle empty DataFrame."""
        df = pd.DataFrame(columns=["grind_size", "final_extraction_yield_percent"])

        results = service.calculate_parameter_correlations(df)

        assert results == [] or all(not r.is_meaningful for r in results)

    def test_correlations_with_missing_columns(self, service):
        """Should skip parameters that don't exist in data."""
        df = pd.DataFrame({
            "brew_id": [1, 2, 3],
            "grind_size": [3.5, 4.0, 4.5],
            "final_extraction_yield_percent": [21.0, 20.0, 19.0],
        })

        results = service.calculate_parameter_correlations(df)

        # Should only include grind_size correlations
        parameters_checked = {r.parameter for r in results}
        assert "grind_size" in parameters_checked
        assert "water_temp_degC" not in parameters_checked

    def test_correlations_sample_size_tracked(self, service, correlated_data):
        """Should track sample size for each correlation."""
        results = service.calculate_parameter_correlations(correlated_data)

        for result in results:
            assert result.sample_size == len(correlated_data)


class TestIdentifyOptimalParameters:
    """Tests for identify_optimal_parameters method."""

    @pytest.fixture
    def service(self):
        return AnalyticsService()

    @pytest.fixture
    def rated_brew_data(self):
        """Create brew data with varying ratings."""
        return pd.DataFrame({
            "brew_id": range(1, 11),
            "bean_name": ["Bean A"] * 5 + ["Bean B"] * 5,
            "grind_size": [3.5, 4.0, 3.8, 3.6, 4.2, 4.5, 4.0, 4.2, 4.8, 4.3],
            "water_temp_degC": [94, 93, 95, 94, 92, 96, 94, 95, 93, 94],
            "brew_ratio_to_1": [16, 15.5, 16.2, 16, 15, 17, 16, 16.5, 15.5, 16],
            "brew_bloom_time_s": [45, 40, 50, 45, 35, 60, 45, 55, 40, 45],
            "brew_total_time_s": [180, 170, 190, 185, 160, 210, 180, 200, 165, 185],
            "score_overall_rating": [8.5, 7.0, 9.0, 8.8, 6.5, 8.0, 8.5, 8.8, 7.0, 8.2],
        })

    def test_optimal_for_all_beans(self, service, rated_brew_data):
        """Should identify optimal parameters across all beans."""
        result = service.identify_optimal_parameters(rated_brew_data, bean_name=None)

        assert isinstance(result, OptimalParameters)
        assert result.bean_name is None
        assert result.based_on_brews == 10

    def test_optimal_for_specific_bean(self, service, rated_brew_data):
        """Should identify optimal parameters for specific bean."""
        result = service.identify_optimal_parameters(rated_brew_data, bean_name="Bean A")

        assert result.bean_name == "Bean A"
        assert result.based_on_brews == 5

    def test_optimal_based_on_top_ratings(self, service, rated_brew_data):
        """Should base optimal on top-rated brews."""
        result = service.identify_optimal_parameters(rated_brew_data, bean_name="Bean A")

        # The top-rated Bean A brew has grind 3.8, temp 95
        # Optimal should be close to these values
        assert result.optimal_grind is not None
        assert result.optimal_temp is not None

    def test_optimal_confidence_level(self, service, rated_brew_data):
        """Should set appropriate confidence level."""
        result = service.identify_optimal_parameters(rated_brew_data, bean_name=None)

        # 10 brews should give high confidence
        assert result.confidence in ["high", "medium"]

    def test_optimal_with_empty_dataframe(self, service):
        """Should handle empty DataFrame."""
        df = pd.DataFrame(columns=["bean_name", "grind_size", "score_overall_rating"])

        result = service.identify_optimal_parameters(df)

        assert result.based_on_brews == 0
        assert not result.is_meaningful

    def test_optimal_with_no_ratings(self, service):
        """Should handle data with no ratings."""
        df = pd.DataFrame({
            "bean_name": ["Bean A"] * 3,
            "grind_size": [3.5, 4.0, 4.5],
            "score_overall_rating": [None, None, None],
        })

        result = service.identify_optimal_parameters(df)

        # Should handle gracefully - either empty or based on all brews
        assert result is not None

    def test_optimal_with_nonexistent_bean(self, service, rated_brew_data):
        """Should handle nonexistent bean."""
        result = service.identify_optimal_parameters(rated_brew_data, bean_name="Nonexistent")

        assert result.based_on_brews == 0
        assert not result.is_meaningful


class TestCalculateConsistencyMetrics:
    """Tests for calculate_consistency_metrics method."""

    @pytest.fixture
    def service(self):
        return AnalyticsService()

    @pytest.fixture
    def consistent_data(self):
        """Create data with high consistency (low variance)."""
        return pd.DataFrame({
            "brew_id": range(1, 11),
            "bean_name": ["Consistent Bean"] * 10,
            "final_extraction_yield_percent": [20.0, 20.1, 19.9, 20.0, 20.2, 19.8, 20.1, 20.0, 19.9, 20.0],
            "final_tds_percent": [1.28, 1.29, 1.27, 1.28, 1.29, 1.27, 1.28, 1.28, 1.27, 1.28],
            "score_overall_rating": [8.0, 8.1, 7.9, 8.0, 8.2, 7.8, 8.0, 8.1, 7.9, 8.0],
        })

    @pytest.fixture
    def inconsistent_data(self):
        """Create data with low consistency (high variance)."""
        return pd.DataFrame({
            "brew_id": range(1, 11),
            "bean_name": ["Inconsistent Bean"] * 10,
            "final_extraction_yield_percent": [18.0, 22.0, 19.0, 21.5, 17.5, 23.0, 20.0, 18.5, 22.5, 19.5],
            "final_tds_percent": [1.15, 1.45, 1.22, 1.40, 1.18, 1.48, 1.30, 1.20, 1.42, 1.25],
            "score_overall_rating": [6.0, 9.0, 7.0, 8.5, 5.5, 9.5, 7.5, 6.5, 9.0, 7.0],
        })

    def test_consistency_for_all_brews(self, service, consistent_data):
        """Should calculate consistency across all brews."""
        result = service.calculate_consistency_metrics(consistent_data, bean_name=None)

        assert isinstance(result, ConsistencyMetrics)
        assert result.bean_name is None
        assert result.sample_size == 10

    def test_consistency_for_specific_bean(self, service, consistent_data):
        """Should calculate consistency for specific bean."""
        result = service.calculate_consistency_metrics(consistent_data, bean_name="Consistent Bean")

        assert result.bean_name == "Consistent Bean"
        assert result.sample_size == 10

    def test_high_consistency_score(self, service, consistent_data):
        """Consistent brews should have high consistency score."""
        result = service.calculate_consistency_metrics(consistent_data)

        assert result.consistency_score >= 70  # Should be high
        assert result.consistency_rating in ["excellent", "good"]

    def test_low_consistency_score(self, service, inconsistent_data):
        """Inconsistent brews should have low consistency score."""
        result = service.calculate_consistency_metrics(inconsistent_data)

        assert result.consistency_score < 50  # Should be low
        assert result.consistency_rating in ["fair", "needs improvement"]

    def test_consistency_std_calculations(self, service, consistent_data):
        """Should calculate standard deviations correctly."""
        result = service.calculate_consistency_metrics(consistent_data)

        assert result.extraction_std is not None
        assert result.tds_std is not None
        assert result.rating_std is not None

        # Consistent data should have low std
        assert result.extraction_std < 0.5
        assert result.tds_std < 0.05

    def test_consistency_cv_calculations(self, service, consistent_data):
        """Should calculate coefficient of variation correctly."""
        result = service.calculate_consistency_metrics(consistent_data)

        assert result.extraction_cv is not None
        assert result.tds_cv is not None

        # CV should be low for consistent data (< 5%)
        assert result.extraction_cv < 5

    def test_consistency_with_empty_dataframe(self, service):
        """Should handle empty DataFrame."""
        df = pd.DataFrame(columns=["bean_name", "final_extraction_yield_percent"])

        result = service.calculate_consistency_metrics(df)

        assert result.sample_size == 0
        assert not result.is_meaningful

    def test_consistency_with_nonexistent_bean(self, service, consistent_data):
        """Should handle nonexistent bean."""
        result = service.calculate_consistency_metrics(consistent_data, bean_name="Nonexistent")

        assert result.sample_size == 0
        assert not result.is_meaningful


class TestCalculateAnalyticsSummary:
    """Tests for calculate_analytics_summary method."""

    @pytest.fixture
    def service(self):
        return AnalyticsService()

    @pytest.fixture
    def comprehensive_data(self):
        """Create comprehensive brew data."""
        today = date.today()
        return pd.DataFrame({
            "brew_id": range(1, 21),
            "brew_date": [today - timedelta(days=i) for i in range(20)],
            "bean_name": ["Bean A"] * 8 + ["Bean B"] * 7 + ["Bean C"] * 5,
            "final_extraction_yield_percent": [20.0 + np.random.uniform(-1, 1) for _ in range(20)],
            "final_tds_percent": [1.28 + np.random.uniform(-0.05, 0.05) for _ in range(20)],
            "score_overall_rating": [7.5, 8.0, 7.8, 8.2, 7.6, 8.5, 8.0, 7.9,  # Bean A
                                      8.5, 8.8, 8.6, 8.3, 8.7, 9.0, 8.4,  # Bean B
                                      7.0, 7.2, 6.8, 7.1, 7.3],  # Bean C
        })

    def test_summary_basic_stats(self, service, comprehensive_data):
        """Should calculate basic statistics."""
        result = service.calculate_analytics_summary(comprehensive_data)

        assert isinstance(result, AnalyticsSummary)
        assert result.total_brews == 20
        assert result.unique_beans == 3

    def test_summary_averages(self, service, comprehensive_data):
        """Should calculate average metrics."""
        result = service.calculate_analytics_summary(comprehensive_data)

        assert result.avg_extraction is not None
        assert result.avg_tds is not None
        assert result.avg_rating is not None

        # Check reasonable ranges
        assert 18 < result.avg_extraction < 23
        assert 1.0 < result.avg_tds < 1.5
        assert 6 < result.avg_rating < 10

    def test_summary_best_bean(self, service, comprehensive_data):
        """Should identify best-rated bean."""
        result = service.calculate_analytics_summary(comprehensive_data)

        # Bean B has highest average rating in our test data
        assert result.best_bean == "Bean B"

    def test_summary_most_brewed_bean(self, service, comprehensive_data):
        """Should identify most frequently brewed bean."""
        result = service.calculate_analytics_summary(comprehensive_data)

        # Bean A has 8 brews, most in our test data
        assert result.most_brewed_bean == "Bean A"

    def test_summary_with_empty_dataframe(self, service):
        """Should handle empty DataFrame."""
        df = pd.DataFrame(columns=["brew_date", "bean_name", "score_overall_rating"])

        result = service.calculate_analytics_summary(df)

        assert result.total_brews == 0
        assert not result.has_enough_data

    def test_summary_date_range(self, service, comprehensive_data):
        """Should calculate date range correctly."""
        result = service.calculate_analytics_summary(comprehensive_data)

        # Data spans 20 days (indices 0-19)
        assert result.date_range_days >= 19


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.fixture
    def service(self):
        return AnalyticsService()

    def test_all_nan_values(self, service):
        """Should handle DataFrame with all NaN values in metric columns."""
        df = pd.DataFrame({
            "brew_date": [date.today()] * 5,
            "bean_name": ["Bean A"] * 5,
            "final_extraction_yield_percent": [None, None, None, None, None],
            "score_overall_rating": [None, None, None, None, None],
        })

        # Should not raise an error
        trend = service.calculate_improvement_trend(df, "final_extraction_yield_percent", 30)
        assert trend.sample_size == 0 or not trend.is_meaningful

    def test_mixed_nan_values(self, service):
        """Should handle DataFrame with some NaN values."""
        today = date.today()
        df = pd.DataFrame({
            "brew_date": [today - timedelta(days=i) for i in range(5)],
            "bean_name": ["Bean A"] * 5,
            "final_extraction_yield_percent": [20.0, None, 19.5, None, 20.5],
            "score_overall_rating": [8.0, 7.5, None, 8.2, 7.8],
        })

        # Should handle gracefully, using only non-NaN values
        trend = service.calculate_improvement_trend(df, "final_extraction_yield_percent", 30)
        assert trend is not None

    def test_duplicate_dates(self, service):
        """Should handle multiple brews on the same date."""
        today = date.today()
        df = pd.DataFrame({
            "brew_date": [today, today, today - timedelta(days=1), today - timedelta(days=1)],
            "bean_name": ["Bean A"] * 4,
            "final_extraction_yield_percent": [20.0, 20.5, 19.5, 19.8],
        })

        trend = service.calculate_improvement_trend(df, "final_extraction_yield_percent", 30)
        assert trend.sample_size == 4

    def test_very_large_dataset(self, service):
        """Should handle large datasets efficiently."""
        today = date.today()
        n = 1000
        df = pd.DataFrame({
            "brew_date": [today - timedelta(days=i % 365) for i in range(n)],
            "bean_name": [f"Bean {i % 10}" for i in range(n)],
            "final_extraction_yield_percent": [20.0 + np.random.uniform(-2, 2) for _ in range(n)],
            "final_tds_percent": [1.28 + np.random.uniform(-0.1, 0.1) for _ in range(n)],
            "score_overall_rating": [7.5 + np.random.uniform(-1.5, 1.5) for _ in range(n)],
            "grind_size": [4.0 + np.random.uniform(-0.5, 0.5) for _ in range(n)],
            "water_temp_degC": [94 + np.random.uniform(-3, 3) for _ in range(n)],
        })

        # All methods should complete without error
        summary = service.calculate_analytics_summary(df)
        assert summary.total_brews == n

        trend = service.calculate_improvement_trend(df, "score_overall_rating", 30)
        assert trend is not None

    def test_negative_window_days(self, service):
        """Should handle negative or zero window days."""
        df = pd.DataFrame({
            "brew_date": [date.today()],
            "final_extraction_yield_percent": [20.0],
        })

        # Should handle gracefully (treat as 0 or use absolute value)
        result = service.calculate_improvement_trend(df, "final_extraction_yield_percent", -10)
        assert result is not None
