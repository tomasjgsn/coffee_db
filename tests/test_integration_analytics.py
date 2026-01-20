"""
Integration tests for the analytics feature.

Tests the full flow from data loading through analytics calculations
to visualization generation.
"""

import pytest
import pandas as pd
from datetime import date, timedelta

from src.services.analytics_service import AnalyticsService
from src.services.visualization_service import VisualizationService
from src.services.data_management_service import DataManagementService


class TestAnalyticsIntegration:
    """Integration tests for the analytics pipeline."""

    @pytest.fixture
    def analytics_service(self):
        return AnalyticsService()

    @pytest.fixture
    def viz_service(self):
        return VisualizationService()

    @pytest.fixture
    def realistic_brew_data(self):
        """Create realistic brew data similar to actual CSV structure."""
        today = date.today()
        return pd.DataFrame({
            "brew_id": range(1, 21),
            "brew_date": [today - timedelta(days=i) for i in range(20)],
            "bean_name": ["Ethiopian Yirgacheffe"] * 8 + ["Colombian Supremo"] * 7 + ["Brazilian Santos"] * 5,
            "bean_origin_country": ["Ethiopia"] * 8 + ["Colombia"] * 7 + ["Brazil"] * 5,
            "grind_size": [3.5, 4.0, 3.8, 3.6, 4.2, 3.9, 3.7, 4.1,
                          4.0, 4.2, 4.1, 3.9, 4.3, 4.0, 4.2,
                          4.5, 4.3, 4.6, 4.4, 4.7],
            "water_temp_degC": [94, 93, 95, 94, 92, 94, 93, 95,
                               96, 95, 94, 96, 95, 94, 95,
                               92, 93, 91, 92, 93],
            "brew_ratio_to_1": [16.0, 15.5, 16.2, 16.0, 15.0, 16.5, 15.8, 16.0,
                               17.0, 16.5, 17.2, 16.8, 17.0, 16.5, 17.0,
                               15.0, 15.5, 14.8, 15.2, 15.0],
            "brew_bloom_time_s": [45, 40, 50, 45, 35, 48, 42, 45,
                                 60, 55, 58, 62, 55, 60, 58,
                                 30, 35, 32, 30, 33],
            "brew_total_time_s": [180, 175, 190, 185, 165, 188, 178, 182,
                                 210, 205, 215, 208, 200, 210, 205,
                                 160, 165, 155, 162, 158],
            "final_extraction_yield_percent": [20.5, 19.8, 21.0, 20.8, 19.2, 20.6, 20.0, 20.3,
                                              21.5, 21.2, 21.8, 21.3, 21.0, 21.5, 21.2,
                                              18.5, 18.8, 18.2, 18.6, 18.4],
            "final_tds_percent": [1.28, 1.25, 1.32, 1.30, 1.22, 1.29, 1.26, 1.28,
                                 1.35, 1.33, 1.38, 1.34, 1.32, 1.36, 1.34,
                                 1.18, 1.20, 1.15, 1.19, 1.17],
            "score_overall_rating": [7.5, 7.0, 8.0, 7.8, 6.5, 7.6, 7.2, 7.4,
                                    8.5, 8.2, 8.8, 8.3, 8.0, 8.5, 8.2,
                                    6.5, 6.8, 6.2, 6.6, 6.4],
            "score_brew": [75, 70, 80, 78, 65, 76, 72, 74,
                          85, 82, 88, 83, 80, 85, 82,
                          65, 68, 62, 66, 64],
        })

    def test_full_analytics_pipeline(self, analytics_service, viz_service, realistic_brew_data):
        """Test the complete analytics pipeline from data to visualization."""
        df = realistic_brew_data

        # Step 1: Calculate analytics summary
        summary = analytics_service.calculate_analytics_summary(df)
        assert summary.total_brews == 20
        assert summary.unique_beans == 3
        assert summary.has_enough_data

        # Step 2: Calculate trend
        trend = analytics_service.calculate_improvement_trend(
            df, "score_overall_rating", window_days=30
        )
        assert trend.is_meaningful
        assert len(trend.values) > 0

        # Step 3: Generate trend chart
        trend_chart = viz_service.create_trend_chart(trend)
        assert trend_chart is not None

        # Step 4: Calculate bean comparison
        comparison = analytics_service.calculate_bean_comparison(
            df, ["Ethiopian Yirgacheffe", "Colombian Supremo"]
        )
        assert comparison.is_statistically_meaningful
        assert len(comparison.bean_metrics) == 2

        # Step 5: Generate comparison chart
        comparison_chart = viz_service.create_comparison_chart(comparison)
        assert comparison_chart is not None

        # Step 6: Calculate correlations
        correlations = analytics_service.calculate_parameter_correlations(df)
        assert len(correlations) > 0

        # Step 7: Generate correlation heatmap
        heatmap = viz_service.create_correlation_heatmap(correlations)
        assert heatmap is not None

        # Step 8: Calculate consistency
        consistency = analytics_service.calculate_consistency_metrics(df)
        assert consistency.is_meaningful
        assert consistency.consistency_score > 0

        # Step 9: Generate consistency chart
        consistency_chart = viz_service.create_consistency_chart(consistency)
        assert consistency_chart is not None

    def test_analytics_with_real_csv_structure(self, analytics_service):
        """Test analytics with DataFrame matching real CSV column structure."""
        # This mimics the actual CSV structure from cups_of_coffee.csv
        today = date.today()
        df = pd.DataFrame({
            "brew_id": [1, 2, 3, 4, 5],
            "brew_date": [today - timedelta(days=i) for i in range(5)],
            "bean_name": ["Test Bean"] * 5,
            "bean_origin_country": ["Ethiopia"] * 5,
            "bean_origin_region": ["Yirgacheffe"] * 5,
            "grind_size": [3.5, 3.6, 3.4, 3.5, 3.7],
            "water_temp_degC": [94, 93, 95, 94, 93],
            "coffee_dose_grams": [18.0, 18.0, 18.0, 18.0, 18.0],
            "water_volume_ml": [300, 300, 300, 300, 300],
            "brew_bloom_time_s": [45, 45, 45, 45, 45],
            "brew_total_time_s": [180, 175, 185, 180, 182],
            "final_tds_percent": [1.28, 1.25, 1.30, 1.27, 1.29],
            "final_brew_mass_grams": [280, 278, 282, 280, 281],
            "score_overall_rating": [7.5, 7.0, 8.0, 7.8, 7.2],
            "brew_ratio_to_1": [16.67, 16.67, 16.67, 16.67, 16.67],
            "final_extraction_yield_percent": [20.5, 19.8, 21.0, 20.2, 20.8],
            "score_brewing_zone": ["Ideal-Ideal"] * 5,
            "score_brew": [75, 70, 80, 78, 72],
        })

        # Should work with this data structure
        summary = analytics_service.calculate_analytics_summary(df)
        assert summary.total_brews == 5
        assert summary.unique_beans == 1

        trend = analytics_service.calculate_improvement_trend(
            df, "final_extraction_yield_percent", 30
        )
        assert trend.sample_size == 5

        consistency = analytics_service.calculate_consistency_metrics(df)
        assert consistency.is_meaningful

    def test_analytics_handles_missing_columns_gracefully(self, analytics_service):
        """Test that analytics handles missing optional columns."""
        df = pd.DataFrame({
            "brew_date": [date.today() - timedelta(days=i) for i in range(5)],
            "bean_name": ["Test"] * 5,
            "score_overall_rating": [7.0, 7.5, 8.0, 7.8, 7.2],
            # Missing: grind_size, water_temp_degC, extraction, etc.
        })

        # Should not raise an error
        summary = analytics_service.calculate_analytics_summary(df)
        assert summary.total_brews == 5

        # Correlations should return empty (no parameters to correlate)
        correlations = analytics_service.calculate_parameter_correlations(df)
        assert correlations == []

    def test_analytics_with_sparse_data(self, analytics_service):
        """Test analytics with sparse data (many NaN values)."""
        df = pd.DataFrame({
            "brew_date": [date.today() - timedelta(days=i) for i in range(10)],
            "bean_name": ["Bean A"] * 5 + ["Bean B"] * 5,
            "grind_size": [3.5, None, 3.8, None, 4.0, None, 4.2, None, 4.5, None],
            "water_temp_degC": [94, 93, None, 95, None, 96, None, 94, None, 95],
            "final_extraction_yield_percent": [20.0, 20.5, None, 21.0, 19.5, None, 21.5, 20.8, None, 21.2],
            "final_tds_percent": [1.28, None, 1.30, None, 1.25, 1.32, None, 1.28, 1.35, None],
            "score_overall_rating": [7.5, 8.0, None, 7.8, 8.2, 8.5, None, 8.0, 8.8, None],
        })

        # Should handle gracefully
        summary = analytics_service.calculate_analytics_summary(df)
        assert summary.total_brews == 10

        # Correlations should still work with non-null pairs
        correlations = analytics_service.calculate_parameter_correlations(df)
        # Some correlations may be calculated from available data
        assert isinstance(correlations, list)

    def test_bean_comparison_identifies_best_performer(self, analytics_service, realistic_brew_data):
        """Test that bean comparison correctly identifies best performing bean."""
        comparison = analytics_service.calculate_bean_comparison(
            realistic_brew_data,
            ["Ethiopian Yirgacheffe", "Colombian Supremo", "Brazilian Santos"]
        )

        # Colombian should have highest average rating in our test data
        colombian = comparison.bean_metrics["Colombian Supremo"]
        ethiopian = comparison.bean_metrics["Ethiopian Yirgacheffe"]
        brazilian = comparison.bean_metrics["Brazilian Santos"]

        assert colombian.avg_rating > ethiopian.avg_rating
        assert ethiopian.avg_rating > brazilian.avg_rating

    def test_correlation_detects_grind_extraction_relationship(self, analytics_service, realistic_brew_data):
        """Test that correlation analysis detects the grind-extraction relationship."""
        correlations = analytics_service.calculate_parameter_correlations(realistic_brew_data)

        # Find grind-extraction correlation
        grind_extraction = next(
            (c for c in correlations
             if c.parameter == "grind_size" and c.metric == "final_extraction_yield_percent"),
            None
        )

        assert grind_extraction is not None
        # In our test data, coarser grind (higher number) = lower extraction
        assert grind_extraction.direction == "negative"


class TestAnalyticsWithDataManagementService:
    """Test analytics integration with actual data loading."""

    @pytest.fixture
    def data_service(self):
        return DataManagementService()

    @pytest.fixture
    def analytics_service(self):
        return AnalyticsService()

    def test_analytics_with_loaded_data(self, data_service, analytics_service):
        """Test that analytics works with data loaded from the actual CSV."""
        df = data_service.load_data()

        # Skip if no data
        if df.empty:
            pytest.skip("No data in CSV file")

        # Should be able to calculate summary
        summary = analytics_service.calculate_analytics_summary(df)
        assert summary.total_brews == len(df)

        # If we have enough data, test other analytics
        if len(df) >= 3:
            trend = analytics_service.calculate_improvement_trend(
                df, "score_overall_rating", 90
            )
            assert trend is not None

            consistency = analytics_service.calculate_consistency_metrics(df)
            assert consistency is not None
