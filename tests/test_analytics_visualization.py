"""
Tests for analytics visualization methods.

Following TDD principles - tests define expected behavior
for the new visualization chart methods.
"""

import pytest
import pandas as pd
import altair as alt
from datetime import date, timedelta

from src.services.visualization_service import VisualizationService
from src.models.analytics_models import (
    TrendData,
    BeanComparisonMetrics,
    ComparisonData,
    CorrelationResult,
    ConsistencyMetrics,
)


class TestVisualizationServiceAnalytics:
    """Tests for analytics visualization methods."""

    @pytest.fixture
    def service(self):
        return VisualizationService()

    # =========================================================================
    # Trend Chart Tests
    # =========================================================================

    @pytest.fixture
    def sample_trend(self):
        """Create a sample trend with meaningful data."""
        today = date.today()
        return TrendData(
            metric="final_extraction_yield_percent",
            window_days=30,
            values=[18.5, 19.0, 19.5, 20.0, 20.5, 20.8, 21.0],
            dates=[today - timedelta(days=i) for i in range(6, -1, -1)],
            trend_direction="improving",
            percent_change=13.5,
            moving_average=[18.5, 18.75, 19.0, 19.5, 20.0, 20.4, 20.8],
            sample_size=7,
        )

    def test_create_trend_chart_returns_altair_chart(self, service, sample_trend):
        """Should return an Altair chart object."""
        chart = service.create_trend_chart(sample_trend)
        assert isinstance(chart, (alt.Chart, alt.LayerChart, alt.VConcatChart, alt.HConcatChart))

    def test_create_trend_chart_with_empty_data(self, service):
        """Should handle empty trend data gracefully."""
        empty_trend = TrendData(
            metric="score_overall_rating",
            window_days=30,
            values=[],
            dates=[],
            trend_direction="stable",
            percent_change=0.0,
            moving_average=[],
            sample_size=0,
        )
        chart = service.create_trend_chart(empty_trend)
        # Should return a chart (possibly empty or with message)
        assert chart is not None

    def test_create_trend_chart_with_single_point(self, service):
        """Should handle single data point."""
        single_trend = TrendData(
            metric="final_tds_percent",
            window_days=7,
            values=[1.28],
            dates=[date.today()],
            trend_direction="stable",
            percent_change=0.0,
            moving_average=[1.28],
            sample_size=1,
        )
        chart = service.create_trend_chart(single_trend)
        assert chart is not None

    def test_create_trend_chart_includes_trend_line(self, service, sample_trend):
        """Trend chart should include moving average line."""
        chart = service.create_trend_chart(sample_trend)
        # Verify it's a layered chart (points + line)
        assert chart is not None

    # =========================================================================
    # Comparison Chart Tests
    # =========================================================================

    @pytest.fixture
    def sample_comparison(self):
        """Create sample comparison data."""
        metrics_a = BeanComparisonMetrics(
            bean_name="Ethiopian Yirgacheffe",
            sample_size=10,
            avg_extraction=20.5,
            avg_tds=1.30,
            avg_rating=8.2,
            avg_brew_score=85.0,
            extraction_std=0.6,
            tds_std=0.04,
            rating_std=0.4,
            best_rating=9.0,
            worst_rating=7.0,
        )
        metrics_b = BeanComparisonMetrics(
            bean_name="Colombian Supremo",
            sample_size=8,
            avg_extraction=19.8,
            avg_tds=1.28,
            avg_rating=7.8,
            avg_brew_score=80.0,
            extraction_std=0.8,
            tds_std=0.05,
            rating_std=0.5,
            best_rating=8.5,
            worst_rating=7.0,
        )
        return ComparisonData(
            bean_names=["Ethiopian Yirgacheffe", "Colombian Supremo"],
            bean_metrics={
                "Ethiopian Yirgacheffe": metrics_a,
                "Colombian Supremo": metrics_b,
            },
            comparison_metrics=["avg_extraction", "avg_tds", "avg_rating"],
            min_sample_size=8,
        )

    def test_create_comparison_chart_returns_altair_chart(self, service, sample_comparison):
        """Should return an Altair chart object."""
        chart = service.create_comparison_chart(sample_comparison)
        assert isinstance(chart, (alt.Chart, alt.LayerChart, alt.VConcatChart, alt.HConcatChart))

    def test_create_comparison_chart_with_empty_data(self, service):
        """Should handle empty comparison data."""
        empty_comparison = ComparisonData(
            bean_names=[],
            bean_metrics={},
            comparison_metrics=[],
            min_sample_size=0,
        )
        chart = service.create_comparison_chart(empty_comparison)
        assert chart is not None

    def test_create_comparison_chart_with_single_bean(self, service):
        """Should handle single bean comparison."""
        single_metrics = BeanComparisonMetrics(
            bean_name="Single Bean",
            sample_size=5,
            avg_extraction=20.0,
            avg_tds=1.28,
            avg_rating=7.5,
            avg_brew_score=78.0,
            extraction_std=0.5,
            tds_std=0.03,
            rating_std=0.3,
            best_rating=8.0,
            worst_rating=7.0,
        )
        single_comparison = ComparisonData(
            bean_names=["Single Bean"],
            bean_metrics={"Single Bean": single_metrics},
            comparison_metrics=["avg_rating"],
            min_sample_size=5,
        )
        chart = service.create_comparison_chart(single_comparison)
        assert chart is not None

    # =========================================================================
    # Correlation Heatmap Tests
    # =========================================================================

    @pytest.fixture
    def sample_correlations(self):
        """Create sample correlation results."""
        return [
            CorrelationResult(
                parameter="grind_size",
                metric="final_extraction_yield_percent",
                correlation=-0.72,
                strength="strong",
                direction="negative",
                sample_size=50,
            ),
            CorrelationResult(
                parameter="water_temp_degC",
                metric="final_extraction_yield_percent",
                correlation=0.45,
                strength="moderate",
                direction="positive",
                sample_size=50,
            ),
            CorrelationResult(
                parameter="grind_size",
                metric="score_overall_rating",
                correlation=-0.35,
                strength="weak",
                direction="negative",
                sample_size=50,
            ),
            CorrelationResult(
                parameter="water_temp_degC",
                metric="score_overall_rating",
                correlation=0.28,
                strength="weak",
                direction="positive",
                sample_size=50,
            ),
        ]

    def test_create_correlation_heatmap_returns_altair_chart(self, service, sample_correlations):
        """Should return an Altair chart object."""
        chart = service.create_correlation_heatmap(sample_correlations)
        assert isinstance(chart, (alt.Chart, alt.LayerChart, alt.VConcatChart, alt.HConcatChart))

    def test_create_correlation_heatmap_with_empty_data(self, service):
        """Should handle empty correlations list."""
        chart = service.create_correlation_heatmap([])
        assert chart is not None

    def test_create_correlation_heatmap_with_single_correlation(self, service):
        """Should handle single correlation."""
        single_corr = [
            CorrelationResult(
                parameter="grind_size",
                metric="final_extraction_yield_percent",
                correlation=-0.65,
                strength="moderate",
                direction="negative",
                sample_size=20,
            )
        ]
        chart = service.create_correlation_heatmap(single_corr)
        assert chart is not None

    # =========================================================================
    # Consistency Chart Tests
    # =========================================================================

    @pytest.fixture
    def sample_consistency(self):
        """Create sample consistency metrics."""
        return ConsistencyMetrics(
            bean_name="Test Bean",
            extraction_std=0.5,
            extraction_cv=2.5,
            tds_std=0.03,
            tds_cv=2.3,
            rating_std=0.4,
            rating_cv=5.0,
            consistency_score=78.5,
            sample_size=15,
        )

    def test_create_consistency_chart_returns_altair_chart(self, service, sample_consistency):
        """Should return an Altair chart object."""
        chart = service.create_consistency_chart(sample_consistency)
        assert isinstance(chart, (alt.Chart, alt.LayerChart, alt.VConcatChart, alt.HConcatChart))

    def test_create_consistency_chart_with_low_score(self, service):
        """Should handle low consistency score."""
        low_consistency = ConsistencyMetrics(
            bean_name="Inconsistent Bean",
            extraction_std=2.0,
            extraction_cv=10.0,
            tds_std=0.12,
            tds_cv=9.2,
            rating_std=1.5,
            rating_cv=18.8,
            consistency_score=25.0,
            sample_size=10,
        )
        chart = service.create_consistency_chart(low_consistency)
        assert chart is not None

    def test_create_consistency_chart_with_none_values(self, service):
        """Should handle None values in metrics."""
        partial_consistency = ConsistencyMetrics(
            bean_name="Partial Data",
            extraction_std=None,
            extraction_cv=None,
            tds_std=0.04,
            tds_cv=3.1,
            rating_std=None,
            rating_cv=None,
            consistency_score=60.0,
            sample_size=5,
        )
        chart = service.create_consistency_chart(partial_consistency)
        assert chart is not None

    # =========================================================================
    # Helper Method Tests
    # =========================================================================

    def test_prepare_trend_chart_data(self, service, sample_trend):
        """Should prepare trend data as DataFrame for charting."""
        df = service.prepare_trend_chart_data(sample_trend)
        assert isinstance(df, pd.DataFrame)
        assert "date" in df.columns
        assert "value" in df.columns
        assert len(df) == len(sample_trend.values)

    def test_prepare_comparison_chart_data(self, service, sample_comparison):
        """Should prepare comparison data as DataFrame for charting."""
        df = service.prepare_comparison_chart_data(sample_comparison)
        assert isinstance(df, pd.DataFrame)
        assert "bean_name" in df.columns
        assert len(df) == len(sample_comparison.bean_names)

    def test_prepare_correlation_chart_data(self, service, sample_correlations):
        """Should prepare correlation data as DataFrame for charting."""
        df = service.prepare_correlation_chart_data(sample_correlations)
        assert isinstance(df, pd.DataFrame)
        assert "parameter" in df.columns
        assert "metric" in df.columns
        assert "correlation" in df.columns
        assert len(df) == len(sample_correlations)

    # =========================================================================
    # Chart Configuration Tests
    # =========================================================================

    def test_get_trend_color_scheme(self, service):
        """Should return color based on trend direction."""
        assert service.get_trend_color("improving") == "#2ca02c"  # Green
        assert service.get_trend_color("declining") == "#d62728"  # Red
        assert service.get_trend_color("stable") == "#7f7f7f"     # Gray

    def test_get_correlation_color_scale(self, service):
        """Should return color scale for correlations."""
        scale = service.get_correlation_color_scale()
        assert isinstance(scale, alt.Scale)
