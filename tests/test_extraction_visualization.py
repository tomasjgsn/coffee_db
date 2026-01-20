"""
Tests for extraction-focused visualization methods.

Tests the visualization service methods that create charts for extraction analysis.
"""

import pytest
import pandas as pd
import altair as alt

from src.services.visualization_service import VisualizationService
from src.models.extraction_models import (
    ExtractionDrivers,
    MethodAnalysis,
    MethodComparison,
    ParameterExtractionData,
    ParameterImpact,
)


class TestExtractionVisualization:
    """Tests for extraction visualization methods."""

    @pytest.fixture
    def service(self):
        return VisualizationService()

    @pytest.fixture
    def sample_drivers(self):
        """Create sample ExtractionDrivers."""
        return ExtractionDrivers(
            parameter_impacts=[
                ParameterImpact(
                    parameter="grind_size",
                    parameter_display_name="Grind Size",
                    correlation=-0.72,
                    impact_strength="high",
                    impact_direction="negative",
                    sample_size=30,
                    min_value=4.0,
                    max_value=6.0,
                    extraction_at_min=21.5,
                    extraction_at_max=18.5,
                ),
                ParameterImpact(
                    parameter="water_temp_degC",
                    parameter_display_name="Water Temperature",
                    correlation=0.45,
                    impact_strength="moderate",
                    impact_direction="positive",
                    sample_size=30,
                    min_value=92.0,
                    max_value=100.0,
                    extraction_at_min=19.0,
                    extraction_at_max=21.0,
                ),
                ParameterImpact(
                    parameter="brew_ratio_to_1",
                    parameter_display_name="Brew Ratio",
                    correlation=0.12,
                    impact_strength="none",
                    impact_direction="none",
                    sample_size=30,
                    min_value=15.0,
                    max_value=17.0,
                    extraction_at_min=20.0,
                    extraction_at_max=20.1,
                ),
            ],
            total_brews_analyzed=30,
            avg_extraction=20.0,
            extraction_range=(18.0, 22.0),
        )

    @pytest.fixture
    def sample_method_analysis(self):
        """Create sample MethodAnalysis."""
        return MethodAnalysis(
            method_comparisons=[
                MethodComparison(
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
                ),
                MethodComparison(
                    method_name="Workshop Switch",
                    device_name="Hario Switch",
                    brew_count=10,
                    avg_extraction=21.2,
                    extraction_std=0.9,
                    avg_tds=1.30,
                    avg_rating=7.8,
                    best_grind=5.0,
                    best_temp=94.0,
                    best_ratio=16.0,
                    best_extraction=22.5,
                ),
            ],
            total_brews=30,
        )

    @pytest.fixture
    def sample_parameter_data(self):
        """Create sample ParameterExtractionData."""
        return ParameterExtractionData(
            parameter="grind_size",
            parameter_display_name="Grind Size",
            param_values=[4.0, 4.5, 5.0, 5.5, 6.0],
            extraction_values=[22.0, 21.0, 20.0, 19.0, 18.0],
            correlation=-0.99,
            slope=-2.0,
            intercept=30.0,
        )

    # =========================================================================
    # create_extraction_drivers_chart tests
    # =========================================================================

    def test_create_extraction_drivers_chart_returns_chart(self, service, sample_drivers):
        """Should return an Altair chart."""
        chart = service.create_extraction_drivers_chart(sample_drivers)
        assert isinstance(chart, (alt.Chart, alt.LayerChart))

    def test_create_extraction_drivers_chart_empty_data(self, service):
        """Should handle empty drivers gracefully."""
        empty_drivers = ExtractionDrivers(
            parameter_impacts=[],
            total_brews_analyzed=0,
            avg_extraction=None,
            extraction_range=(0, 0),
        )
        chart = service.create_extraction_drivers_chart(empty_drivers)
        assert chart is not None

    def test_create_extraction_drivers_chart_single_parameter(self, service):
        """Should handle single parameter."""
        single_drivers = ExtractionDrivers(
            parameter_impacts=[
                ParameterImpact(
                    "grind", "Grind", -0.65, "moderate", "negative", 10, 4, 6, 21, 19
                ),
            ],
            total_brews_analyzed=10,
            avg_extraction=20.0,
            extraction_range=(19.0, 21.0),
        )
        chart = service.create_extraction_drivers_chart(single_drivers)
        assert chart is not None

    # =========================================================================
    # create_parameter_scatter tests
    # =========================================================================

    def test_create_parameter_scatter_returns_chart(self, service, sample_parameter_data):
        """Should return an Altair chart."""
        chart = service.create_parameter_scatter(sample_parameter_data)
        assert isinstance(chart, (alt.Chart, alt.LayerChart))

    def test_create_parameter_scatter_empty_data(self, service):
        """Should handle empty data gracefully."""
        empty_data = ParameterExtractionData(
            parameter="grind_size",
            parameter_display_name="Grind Size",
            param_values=[],
            extraction_values=[],
            correlation=0.0,
            slope=0.0,
            intercept=0.0,
        )
        chart = service.create_parameter_scatter(empty_data)
        assert chart is not None

    def test_create_parameter_scatter_negative_correlation(self, service):
        """Should show red trend line for negative correlation."""
        data = ParameterExtractionData(
            parameter="grind_size",
            parameter_display_name="Grind Size",
            param_values=[4.0, 5.0, 6.0],
            extraction_values=[22.0, 20.0, 18.0],
            correlation=-0.99,
            slope=-2.0,
            intercept=30.0,
        )
        chart = service.create_parameter_scatter(data)
        assert chart is not None

    def test_create_parameter_scatter_positive_correlation(self, service):
        """Should show green trend line for positive correlation."""
        data = ParameterExtractionData(
            parameter="water_temp_degC",
            parameter_display_name="Water Temperature",
            param_values=[92.0, 96.0, 100.0],
            extraction_values=[18.0, 20.0, 22.0],
            correlation=0.99,
            slope=0.5,
            intercept=-28.0,
        )
        chart = service.create_parameter_scatter(data)
        assert chart is not None

    def test_create_parameter_scatter_no_correlation(self, service):
        """Should show gray trend line for no correlation."""
        data = ParameterExtractionData(
            parameter="brew_ratio",
            parameter_display_name="Brew Ratio",
            param_values=[15.0, 16.0, 17.0],
            extraction_values=[20.0, 20.1, 19.9],
            correlation=0.05,
            slope=0.0,
            intercept=20.0,
        )
        chart = service.create_parameter_scatter(data)
        assert chart is not None

    # =========================================================================
    # create_method_comparison_chart tests
    # =========================================================================

    def test_create_method_comparison_chart_returns_chart(self, service, sample_method_analysis):
        """Should return an Altair chart."""
        chart = service.create_method_comparison_chart(sample_method_analysis)
        assert isinstance(chart, (alt.Chart, alt.LayerChart))

    def test_create_method_comparison_chart_empty_data(self, service):
        """Should handle empty method analysis."""
        empty_analysis = MethodAnalysis(method_comparisons=[], total_brews=0)
        chart = service.create_method_comparison_chart(empty_analysis)
        assert chart is not None

    def test_create_method_comparison_chart_single_method(self, service):
        """Should handle single method."""
        single_analysis = MethodAnalysis(
            method_comparisons=[
                MethodComparison(
                    "V60", "V60 ceramic", 20, 20.5, 1.2, 1.28, 7.5, 5.0, 96, 16, 22.1
                ),
            ],
            total_brews=20,
        )
        chart = service.create_method_comparison_chart(single_analysis)
        assert chart is not None

    def test_create_method_comparison_chart_none_extraction(self, service):
        """Should handle methods with None extraction."""
        analysis = MethodAnalysis(
            method_comparisons=[
                MethodComparison(
                    "V60", "V60", 20, 20.5, 1.2, 1.28, 7.5, 5.0, 96, 16, 22.1
                ),
                MethodComparison(
                    "Switch", "Hario", 2, None, None, None, None, None, None, None, None
                ),
            ],
            total_brews=22,
        )
        chart = service.create_method_comparison_chart(analysis)
        assert chart is not None

    # =========================================================================
    # create_extraction_summary_cards tests
    # =========================================================================

    def test_create_extraction_summary_cards(self, service, sample_drivers):
        """Should return summary metrics dictionary."""
        summary = service.create_extraction_summary_cards(sample_drivers)
        assert isinstance(summary, dict)
        assert "total_brews" in summary
        assert "avg_extraction" in summary
        assert "top_driver" in summary

    def test_create_extraction_summary_cards_empty(self, service):
        """Should handle empty drivers."""
        empty_drivers = ExtractionDrivers(
            parameter_impacts=[],
            total_brews_analyzed=0,
            avg_extraction=None,
            extraction_range=(0, 0),
        )
        summary = service.create_extraction_summary_cards(empty_drivers)
        assert summary["total_brews"] == 0
        assert summary["top_driver"] == "N/A"

    def test_create_extraction_summary_cards_values(self, service, sample_drivers):
        """Should have correct values."""
        summary = service.create_extraction_summary_cards(sample_drivers)
        assert summary["total_brews"] == 30
        assert summary["avg_extraction"] == 20.0
        assert summary["top_driver"] == "Grind Size"
        assert summary["num_meaningful_drivers"] == 2  # Strong + Moderate
