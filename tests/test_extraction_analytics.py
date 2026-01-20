"""
Tests for extraction-focused analytics.

Tests the ExtractionAnalyticsService which analyzes which brewing parameters
drive extraction yield.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import date, timedelta

from src.services.extraction_analytics_service import ExtractionAnalyticsService
from src.models.extraction_models import (
    ExtractionDrivers,
    ExtractionInsights,
    MethodAnalysis,
    MethodComparison,
    ParameterExtractionData,
    ParameterImpact,
)


class TestExtractionAnalyticsService:
    """Tests for ExtractionAnalyticsService."""

    @pytest.fixture
    def service(self):
        return ExtractionAnalyticsService()

    @pytest.fixture
    def sample_df(self):
        """Create sample brewing data with realistic correlations."""
        np.random.seed(42)
        n = 30

        # Create data where grind_size negatively correlates with extraction
        # and water_temp positively correlates with extraction
        grind_sizes = np.random.uniform(4.0, 6.0, n)
        water_temps = np.random.uniform(92, 100, n)
        brew_ratios = np.random.uniform(15, 17, n)

        # Extraction influenced by grind (negative) and temp (positive)
        extraction = (
            20
            - 2 * (grind_sizes - 5)  # Negative correlation with grind
            + 0.15 * (water_temps - 96)  # Positive correlation with temp
            + np.random.normal(0, 0.5, n)  # Noise
        )

        return pd.DataFrame({
            "brew_date": [date.today() - timedelta(days=i) for i in range(n)],
            "bean_name": ["Test Bean"] * n,
            "brew_method": ["3 pulse V60"] * (n - 10) + ["Workshop Switch"] * 10,
            "brew_device": ["V60 ceramic"] * (n - 10) + ["Hario Switch"] * 10,
            "grind_size": grind_sizes,
            "water_temp_degC": water_temps,
            "brew_ratio_to_1": brew_ratios,
            "brew_bloom_time_s": np.random.uniform(30, 60, n),
            "brew_total_time_s": np.random.uniform(180, 240, n),
            "final_extraction_yield_percent": extraction,
            "final_tds_percent": np.random.uniform(1.1, 1.4, n),
            "score_overall_rating": np.random.uniform(6, 9, n),
        })

    # =========================================================================
    # analyze_extraction_drivers tests
    # =========================================================================

    def test_analyze_extraction_drivers_returns_drivers(self, service, sample_df):
        """Should return ExtractionDrivers object."""
        result = service.analyze_extraction_drivers(sample_df)
        assert isinstance(result, ExtractionDrivers)

    def test_analyze_extraction_drivers_has_parameter_impacts(self, service, sample_df):
        """Should identify parameter impacts."""
        result = service.analyze_extraction_drivers(sample_df)
        assert len(result.parameter_impacts) > 0

    def test_analyze_extraction_drivers_sorted_by_impact(self, service, sample_df):
        """Should sort parameters by absolute correlation."""
        result = service.analyze_extraction_drivers(sample_df)
        correlations = [abs(p.correlation) for p in result.parameter_impacts]
        assert correlations == sorted(correlations, reverse=True)

    def test_analyze_extraction_drivers_identifies_grind_correlation(self, service, sample_df):
        """Should identify grind_size as having negative correlation."""
        result = service.analyze_extraction_drivers(sample_df)
        grind_impact = next(
            (p for p in result.parameter_impacts if p.parameter == "grind_size"),
            None
        )
        assert grind_impact is not None
        assert grind_impact.impact_direction == "negative"

    def test_analyze_extraction_drivers_identifies_temp_correlation(self, service, sample_df):
        """Should identify water_temp as having positive correlation."""
        result = service.analyze_extraction_drivers(sample_df)
        temp_impact = next(
            (p for p in result.parameter_impacts if p.parameter == "water_temp_degC"),
            None
        )
        assert temp_impact is not None
        assert temp_impact.impact_direction == "positive"

    def test_analyze_extraction_drivers_empty_df(self, service):
        """Should handle empty DataFrame."""
        result = service.analyze_extraction_drivers(pd.DataFrame())
        assert isinstance(result, ExtractionDrivers)
        assert len(result.parameter_impacts) == 0
        assert result.total_brews_analyzed == 0

    def test_analyze_extraction_drivers_insufficient_data(self, service):
        """Should handle insufficient data gracefully."""
        df = pd.DataFrame({
            "grind_size": [5.0],
            "final_extraction_yield_percent": [20.0],
        })
        result = service.analyze_extraction_drivers(df)
        assert result.total_brews_analyzed == 0

    def test_analyze_extraction_drivers_filters_by_bean(self, service, sample_df):
        """Should filter by bean name when specified."""
        sample_df.loc[:9, "bean_name"] = "Different Bean"

        result = service.analyze_extraction_drivers(sample_df, bean_name="Test Bean")
        assert result.total_brews_analyzed == 20  # Only Test Bean rows

    def test_analyze_extraction_drivers_calculates_extraction_range(self, service, sample_df):
        """Should calculate extraction range."""
        result = service.analyze_extraction_drivers(sample_df)
        assert result.extraction_range[0] is not None
        assert result.extraction_range[1] is not None
        assert result.extraction_range[0] <= result.extraction_range[1]

    def test_analyze_extraction_drivers_has_avg_extraction(self, service, sample_df):
        """Should calculate average extraction."""
        result = service.analyze_extraction_drivers(sample_df)
        assert result.avg_extraction is not None
        assert 15 <= result.avg_extraction <= 25

    # =========================================================================
    # ParameterImpact tests
    # =========================================================================

    def test_parameter_impact_has_actionable_insight(self, service, sample_df):
        """ParameterImpact should generate actionable insight."""
        result = service.analyze_extraction_drivers(sample_df)
        assert len(result.parameter_impacts) > 0

        impact = result.parameter_impacts[0]
        insight = impact.actionable_insight
        assert isinstance(insight, str)
        assert len(insight) > 0

    def test_parameter_impact_extraction_at_extremes(self, service, sample_df):
        """Should calculate extraction at parameter extremes."""
        result = service.analyze_extraction_drivers(sample_df)
        grind_impact = next(
            (p for p in result.parameter_impacts if p.parameter == "grind_size"),
            None
        )
        assert grind_impact is not None
        assert grind_impact.extraction_at_min is not None
        assert grind_impact.extraction_at_max is not None
        # For negative correlation, extraction at min grind should be higher
        assert grind_impact.extraction_at_min > grind_impact.extraction_at_max

    # =========================================================================
    # analyze_methods tests
    # =========================================================================

    def test_analyze_methods_returns_method_analysis(self, service, sample_df):
        """Should return MethodAnalysis object."""
        result = service.analyze_methods(sample_df)
        assert isinstance(result, MethodAnalysis)

    def test_analyze_methods_identifies_methods(self, service, sample_df):
        """Should identify different brew methods."""
        result = service.analyze_methods(sample_df)
        method_names = [m.method_name for m in result.method_comparisons]
        assert "3 pulse V60" in method_names

    def test_analyze_methods_calculates_avg_extraction(self, service, sample_df):
        """Should calculate average extraction per method."""
        result = service.analyze_methods(sample_df)
        for method in result.method_comparisons:
            assert method.avg_extraction is not None

    def test_analyze_methods_finds_best_settings(self, service, sample_df):
        """Should find best settings per method."""
        result = service.analyze_methods(sample_df)
        for method in result.method_comparisons:
            assert method.best_extraction is not None

    def test_analyze_methods_empty_df(self, service):
        """Should handle empty DataFrame."""
        result = service.analyze_methods(pd.DataFrame())
        assert isinstance(result, MethodAnalysis)
        assert len(result.method_comparisons) == 0

    def test_analyze_methods_best_method_property(self, service, sample_df):
        """Should identify best method by extraction."""
        result = service.analyze_methods(sample_df)
        best = result.best_method
        assert best is not None

        # Verify it's actually the highest
        all_extractions = [m.avg_extraction for m in result.method_comparisons
                          if m.avg_extraction is not None]
        assert best.avg_extraction == max(all_extractions)

    # =========================================================================
    # get_parameter_extraction_data tests
    # =========================================================================

    def test_get_parameter_extraction_data_returns_data(self, service, sample_df):
        """Should return ParameterExtractionData object."""
        result = service.get_parameter_extraction_data(sample_df, "grind_size")
        assert isinstance(result, ParameterExtractionData)

    def test_get_parameter_extraction_data_has_values(self, service, sample_df):
        """Should have parameter and extraction values."""
        result = service.get_parameter_extraction_data(sample_df, "grind_size")
        assert len(result.param_values) > 0
        assert len(result.extraction_values) > 0
        assert len(result.param_values) == len(result.extraction_values)

    def test_get_parameter_extraction_data_calculates_trend(self, service, sample_df):
        """Should calculate trend line coefficients."""
        result = service.get_parameter_extraction_data(sample_df, "grind_size")
        assert result.slope is not None
        assert result.intercept is not None

    def test_get_parameter_extraction_data_trend_description(self, service, sample_df):
        """Should generate trend description."""
        result = service.get_parameter_extraction_data(sample_df, "grind_size")
        assert isinstance(result.trend_description, str)
        assert len(result.trend_description) > 0

    def test_get_parameter_extraction_data_missing_parameter(self, service, sample_df):
        """Should return None for missing parameter."""
        result = service.get_parameter_extraction_data(sample_df, "nonexistent_param")
        assert result is None

    def test_get_parameter_extraction_data_insufficient_data(self, service):
        """Should return None for insufficient data."""
        df = pd.DataFrame({
            "grind_size": [5.0, 5.5],
            "final_extraction_yield_percent": [20.0, 20.5],
        })
        result = service.get_parameter_extraction_data(df, "grind_size")
        assert result is None  # Need >= 3 samples

    # =========================================================================
    # get_extraction_insights tests
    # =========================================================================

    def test_get_extraction_insights_returns_insights(self, service, sample_df):
        """Should return ExtractionInsights object."""
        result = service.get_extraction_insights(sample_df)
        assert isinstance(result, ExtractionInsights)

    def test_get_extraction_insights_has_drivers(self, service, sample_df):
        """Should include extraction drivers."""
        result = service.get_extraction_insights(sample_df)
        assert result.drivers is not None
        assert isinstance(result.drivers, ExtractionDrivers)

    def test_get_extraction_insights_has_method_analysis(self, service, sample_df):
        """Should include method analysis."""
        result = service.get_extraction_insights(sample_df)
        assert result.method_analysis is not None
        assert isinstance(result.method_analysis, MethodAnalysis)

    def test_get_extraction_insights_has_parameter_plots(self, service, sample_df):
        """Should include parameter plot data."""
        result = service.get_extraction_insights(sample_df)
        assert result.parameter_plots is not None
        assert isinstance(result.parameter_plots, dict)
        assert len(result.parameter_plots) > 0

    def test_get_extraction_insights_has_recommendations(self, service, sample_df):
        """Should include parameter recommendations."""
        result = service.get_extraction_insights(sample_df)
        # At least one recommendation should be present
        has_recommendation = (
            result.recommended_grind is not None
            or result.recommended_temp is not None
            or result.recommended_ratio is not None
        )
        assert has_recommendation

    def test_get_extraction_insights_key_findings(self, service, sample_df):
        """Should generate key findings."""
        result = service.get_extraction_insights(sample_df)
        findings = result.key_findings
        assert isinstance(findings, list)


class TestExtractionModels:
    """Tests for extraction model dataclasses."""

    def test_parameter_impact_actionable_insight_positive(self):
        """Should generate positive direction insight."""
        impact = ParameterImpact(
            parameter="water_temp_degC",
            parameter_display_name="Water Temperature",
            correlation=0.65,
            impact_strength="moderate",
            impact_direction="positive",
            sample_size=30,
            min_value=92.0,
            max_value=100.0,
            extraction_at_min=18.5,
            extraction_at_max=21.0,
        )
        insight = impact.actionable_insight
        assert "positive" in insight.lower()
        assert "increases" in insight.lower()

    def test_parameter_impact_actionable_insight_negative(self):
        """Should generate negative direction insight."""
        impact = ParameterImpact(
            parameter="grind_size",
            parameter_display_name="Grind Size",
            correlation=-0.72,
            impact_strength="strong",
            impact_direction="negative",
            sample_size=30,
            min_value=4.0,
            max_value=6.0,
            extraction_at_min=21.5,
            extraction_at_max=18.5,
        )
        insight = impact.actionable_insight
        assert "negative" in insight.lower()
        assert "decreases" in insight.lower()

    def test_parameter_impact_actionable_insight_none(self):
        """Should handle no correlation case."""
        impact = ParameterImpact(
            parameter="brew_ratio",
            parameter_display_name="Brew Ratio",
            correlation=0.05,
            impact_strength="none",
            impact_direction="none",
            sample_size=30,
            min_value=15.0,
            max_value=17.0,
            extraction_at_min=20.0,
            extraction_at_max=20.1,
        )
        insight = impact.actionable_insight
        assert "no clear" in insight.lower()

    def test_extraction_drivers_top_drivers(self):
        """Should filter to meaningful drivers."""
        drivers = ExtractionDrivers(
            parameter_impacts=[
                ParameterImpact("grind", "Grind", -0.72, "high", "negative", 30, 4, 6, 21, 18),
                ParameterImpact("temp", "Temp", 0.45, "moderate", "positive", 30, 92, 100, 18, 21),
                ParameterImpact("ratio", "Ratio", 0.15, "none", "none", 30, 15, 17, 20, 20),
            ],
            total_brews_analyzed=30,
            avg_extraction=20.0,
            extraction_range=(18.0, 22.0),
        )

        top = drivers.top_drivers
        assert len(top) == 2  # Only high and moderate
        assert all(d.impact_strength in ("high", "moderate") for d in top)

    def test_extraction_drivers_summary(self):
        """Should generate summary string."""
        drivers = ExtractionDrivers(
            parameter_impacts=[
                ParameterImpact("grind", "Grind", -0.72, "high", "negative", 30, 4, 6, 21, 18),
            ],
            total_brews_analyzed=30,
            avg_extraction=20.0,
            extraction_range=(18.0, 22.0),
        )
        summary = drivers.summary
        assert "30" in summary
        assert "Grind" in summary

    def test_method_comparison_data(self):
        """Should store method comparison data correctly."""
        comparison = MethodComparison(
            method_name="3 pulse V60",
            device_name="V60 ceramic",
            brew_count=20,
            avg_extraction=20.5,
            extraction_std=1.2,
            avg_tds=1.28,
            avg_rating=7.5,
            best_grind=5.0,
            best_temp=96.0,
            best_ratio=16.0,
            best_extraction=22.1,
        )
        assert comparison.method_name == "3 pulse V60"
        assert comparison.avg_extraction == 20.5

    def test_method_analysis_best_method(self):
        """Should identify best method."""
        analysis = MethodAnalysis(
            method_comparisons=[
                MethodComparison("V60", "V60", 20, 20.5, 1.2, 1.28, 7.5, 5.0, 96, 16, 22.1),
                MethodComparison("Switch", "Hario", 10, 21.2, 0.9, 1.30, 7.8, 5.0, 94, 16, 22.5),
            ],
            total_brews=30,
        )
        best = analysis.best_method
        assert best.method_name == "Switch"  # Higher avg extraction

    def test_method_analysis_most_consistent(self):
        """Should identify most consistent method."""
        analysis = MethodAnalysis(
            method_comparisons=[
                MethodComparison("V60", "V60", 20, 20.5, 1.2, 1.28, 7.5, 5.0, 96, 16, 22.1),
                MethodComparison("Switch", "Hario", 10, 21.2, 0.9, 1.30, 7.8, 5.0, 94, 16, 22.5),
            ],
            total_brews=30,
        )
        consistent = analysis.most_consistent_method
        assert consistent.method_name == "Switch"  # Lower std dev

    def test_parameter_extraction_data_trend_description(self):
        """Should generate trend description."""
        data = ParameterExtractionData(
            parameter="grind_size",
            parameter_display_name="Grind Size",
            param_values=[4.0, 5.0, 6.0],
            extraction_values=[22.0, 20.0, 18.0],
            correlation=-0.99,
            slope=-2.0,
            intercept=30.0,
        )
        desc = data.trend_description
        assert "decreases" in desc.lower()
        assert "strongly" in desc.lower()
