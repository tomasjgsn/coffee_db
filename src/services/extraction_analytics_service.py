"""
Extraction Analytics Service

Focused analytics for understanding what drives extraction yield.
This is the core insight engine for coffee brewing optimization.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.models.extraction_models import (
    ExtractionDrivers,
    ExtractionInsights,
    MethodAnalysis,
    MethodComparison,
    ParameterExtractionData,
    ParameterImpact,
)
from src.services.metrics import monitor_performance


# Parameter display names for user-friendly output
PARAMETER_DISPLAY_NAMES = {
    "grind_size": "Grind Size",
    "water_temp_degC": "Water Temperature (°C)",
    "brew_ratio_to_1": "Brew Ratio",
    "brew_bloom_time_s": "Bloom Time (s)",
    "brew_total_time_s": "Total Brew Time (s)",
    "coffee_dose_grams": "Coffee Dose (g)",
    "water_volume_ml": "Water Volume (ml)",
    "drawdown_time_s": "Drawdown Time (s)",
    "hario_infusion_duration_s": "Infusion Duration (s)",
    "hario_valve_release_time_s": "Valve Release Time (s)",
    "num_pours": "Number of Pours",
}


class ExtractionAnalyticsService:
    """
    Service for extraction-focused brewing analytics.

    Answers the key question: "What parameters most influence my extraction?"

    Example:
        >>> service = ExtractionAnalyticsService()
        >>> drivers = service.analyze_extraction_drivers(df)
        >>> print(drivers.summary)
        'Top extraction drivers: Grind Size, Water Temperature.'
    """

    # Core brewing parameters to analyze
    BREWING_PARAMETERS = [
        "grind_size",
        "water_temp_degC",
        "brew_ratio_to_1",
        "brew_bloom_time_s",
        "brew_total_time_s",
        "drawdown_time_s",
    ]

    # Device-specific parameters (analyzed when present)
    DEVICE_PARAMETERS = {
        "Hario Switch": [
            "hario_infusion_duration_s",
            "hario_valve_release_time_s",
        ],
        "V60": [
            "num_pours",
            "drawdown_time_s",
        ],
    }

    MIN_SAMPLE_SIZE = 3

    def __init__(self):
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger(f"{__name__}.ExtractionAnalyticsService")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    @monitor_performance
    def analyze_extraction_drivers(
        self, df: pd.DataFrame, bean_name: Optional[str] = None
    ) -> ExtractionDrivers:
        """
        Analyze which parameters most influence extraction yield.

        Args:
            df: DataFrame with brewing data
            bean_name: Optional filter for specific bean

        Returns:
            ExtractionDrivers with ranked parameter impacts
        """
        if df.empty or "final_extraction_yield_percent" not in df.columns:
            return self._empty_drivers()

        # Filter by bean if specified
        analysis_df = df.copy()
        if bean_name:
            analysis_df = analysis_df[analysis_df["bean_name"] == bean_name]

        if analysis_df.empty:
            return self._empty_drivers()

        # Get extraction data
        extraction = analysis_df["final_extraction_yield_percent"].dropna()
        if len(extraction) < self.MIN_SAMPLE_SIZE:
            return self._empty_drivers()

        # Analyze each parameter
        impacts = []
        for param in self.BREWING_PARAMETERS:
            impact = self._analyze_parameter_impact(analysis_df, param)
            if impact:
                impacts.append(impact)

        # Add device-specific parameters
        for device, params in self.DEVICE_PARAMETERS.items():
            device_df = analysis_df[analysis_df["brew_device"].str.contains(device, case=False, na=False)]
            if len(device_df) >= self.MIN_SAMPLE_SIZE:
                for param in params:
                    impact = self._analyze_parameter_impact(device_df, param)
                    if impact:
                        impacts.append(impact)

        # Sort by absolute correlation (strongest impact first)
        impacts.sort(key=lambda x: abs(x.correlation), reverse=True)

        # Calculate extraction stats
        avg_extraction = float(extraction.mean())
        extraction_range = (float(extraction.min()), float(extraction.max()))

        return ExtractionDrivers(
            parameter_impacts=impacts,
            total_brews_analyzed=len(analysis_df),
            avg_extraction=round(avg_extraction, 2),
            extraction_range=extraction_range,
        )

    def _analyze_parameter_impact(
        self, df: pd.DataFrame, parameter: str
    ) -> Optional[ParameterImpact]:
        """Analyze the impact of a single parameter on extraction."""
        if parameter not in df.columns:
            return None

        # Get paired non-null values
        extraction_col = "final_extraction_yield_percent"
        paired = df[[parameter, extraction_col]].dropna()

        if len(paired) < self.MIN_SAMPLE_SIZE:
            return None

        param_vals = paired[parameter].values
        extraction_vals = paired[extraction_col].values

        # Calculate correlation
        try:
            correlation = float(np.corrcoef(param_vals, extraction_vals)[0, 1])
            if np.isnan(correlation):
                correlation = 0.0
        except Exception:
            correlation = 0.0

        # Determine impact strength and direction
        abs_corr = abs(correlation)
        if abs_corr >= 0.7:
            strength = "high"
        elif abs_corr >= 0.4:
            strength = "moderate"
        elif abs_corr >= 0.2:
            strength = "low"
        else:
            strength = "none"

        if abs_corr < 0.2:
            direction = "none"
        else:
            direction = "positive" if correlation > 0 else "negative"

        # Calculate extraction at parameter extremes
        sorted_by_param = paired.sort_values(parameter)
        n = len(sorted_by_param)
        tercile_size = max(1, n // 3)

        low_tercile = sorted_by_param.head(tercile_size)
        high_tercile = sorted_by_param.tail(tercile_size)

        extraction_at_min = float(low_tercile[extraction_col].mean())
        extraction_at_max = float(high_tercile[extraction_col].mean())

        display_name = PARAMETER_DISPLAY_NAMES.get(parameter, parameter.replace("_", " ").title())

        return ParameterImpact(
            parameter=parameter,
            parameter_display_name=display_name,
            correlation=round(correlation, 3),
            impact_strength=strength,
            impact_direction=direction,
            sample_size=len(paired),
            min_value=float(param_vals.min()),
            max_value=float(param_vals.max()),
            extraction_at_min=round(extraction_at_min, 2),
            extraction_at_max=round(extraction_at_max, 2),
        )

    def _empty_drivers(self) -> ExtractionDrivers:
        """Return empty ExtractionDrivers for edge cases."""
        return ExtractionDrivers(
            parameter_impacts=[],
            total_brews_analyzed=0,
            avg_extraction=None,
            extraction_range=(0, 0),
        )

    @monitor_performance
    def analyze_methods(self, df: pd.DataFrame) -> MethodAnalysis:
        """
        Analyze extraction across different brew methods and devices.

        Args:
            df: DataFrame with brewing data

        Returns:
            MethodAnalysis comparing methods
        """
        if df.empty:
            return MethodAnalysis(method_comparisons=[], total_brews=0)

        comparisons = []

        # Group by brew_method
        for method, method_df in df.groupby("brew_method", dropna=True):
            if len(method_df) < self.MIN_SAMPLE_SIZE:
                continue

            # Get primary device for this method
            devices = method_df["brew_device"].value_counts()
            device = devices.index[0] if len(devices) > 0 else None

            comparison = self._build_method_comparison(method, device, method_df)
            comparisons.append(comparison)

        # Sort by average extraction
        comparisons.sort(
            key=lambda x: x.avg_extraction if x.avg_extraction else 0,
            reverse=True
        )

        return MethodAnalysis(
            method_comparisons=comparisons,
            total_brews=len(df),
        )

    def _build_method_comparison(
        self, method: str, device: Optional[str], df: pd.DataFrame
    ) -> MethodComparison:
        """Build MethodComparison for a single method."""
        extraction = df["final_extraction_yield_percent"].dropna()
        tds = df["final_tds_percent"].dropna() if "final_tds_percent" in df.columns else pd.Series()
        rating = df["score_overall_rating"].dropna() if "score_overall_rating" in df.columns else pd.Series()

        avg_extraction = float(extraction.mean()) if len(extraction) > 0 else None
        extraction_std = float(extraction.std()) if len(extraction) > 1 else None
        avg_tds = float(tds.mean()) if len(tds) > 0 else None
        avg_rating = float(rating.mean()) if len(rating) > 0 else None

        # Find best settings (from highest extraction brews)
        best_grind = best_temp = best_ratio = best_extraction = None
        if len(extraction) > 0:
            best_idx = extraction.idxmax()
            best_row = df.loc[best_idx]
            best_grind = best_row.get("grind_size")
            best_temp = best_row.get("water_temp_degC")
            best_ratio = best_row.get("brew_ratio_to_1")
            best_extraction = float(extraction.max())

        return MethodComparison(
            method_name=method,
            device_name=device,
            brew_count=len(df),
            avg_extraction=round(avg_extraction, 2) if avg_extraction else None,
            extraction_std=round(extraction_std, 2) if extraction_std else None,
            avg_tds=round(avg_tds, 3) if avg_tds else None,
            avg_rating=round(avg_rating, 2) if avg_rating else None,
            best_grind=float(best_grind) if best_grind and pd.notna(best_grind) else None,
            best_temp=float(best_temp) if best_temp and pd.notna(best_temp) else None,
            best_ratio=round(float(best_ratio), 1) if best_ratio and pd.notna(best_ratio) else None,
            best_extraction=round(best_extraction, 2) if best_extraction else None,
        )

    @monitor_performance
    def get_parameter_extraction_data(
        self, df: pd.DataFrame, parameter: str
    ) -> Optional[ParameterExtractionData]:
        """
        Get data for plotting parameter vs extraction scatter.

        Args:
            df: DataFrame with brewing data
            parameter: Parameter column name

        Returns:
            ParameterExtractionData for charting, or None if insufficient data
        """
        extraction_col = "final_extraction_yield_percent"

        if df.empty or parameter not in df.columns or extraction_col not in df.columns:
            return None

        # Get paired data
        paired = df[[parameter, extraction_col]].dropna()
        if len(paired) < self.MIN_SAMPLE_SIZE:
            return None

        param_vals = paired[parameter].values.tolist()
        extraction_vals = paired[extraction_col].values.tolist()

        # Calculate correlation and trend line
        try:
            correlation = float(np.corrcoef(param_vals, extraction_vals)[0, 1])
            if np.isnan(correlation):
                correlation = 0.0

            # Linear regression for trend line
            coeffs = np.polyfit(param_vals, extraction_vals, 1)
            slope = float(coeffs[0])
            intercept = float(coeffs[1])
        except Exception:
            correlation = 0.0
            slope = 0.0
            intercept = float(np.mean(extraction_vals))

        display_name = PARAMETER_DISPLAY_NAMES.get(parameter, parameter.replace("_", " ").title())

        return ParameterExtractionData(
            parameter=parameter,
            parameter_display_name=display_name,
            param_values=param_vals,
            extraction_values=extraction_vals,
            correlation=round(correlation, 3),
            slope=round(slope, 4),
            intercept=round(intercept, 2),
        )

    @monitor_performance
    def get_extraction_insights(
        self, df: pd.DataFrame, bean_name: Optional[str] = None
    ) -> ExtractionInsights:
        """
        Get comprehensive extraction insights.

        Args:
            df: DataFrame with brewing data
            bean_name: Optional filter for specific bean

        Returns:
            ExtractionInsights with all analyses combined
        """
        # Filter if needed
        analysis_df = df.copy()
        if bean_name:
            analysis_df = analysis_df[analysis_df["bean_name"] == bean_name]

        # Run analyses
        drivers = self.analyze_extraction_drivers(analysis_df)
        method_analysis = self.analyze_methods(analysis_df)

        # Get parameter plots for top parameters
        parameter_plots = {}
        for param in self.BREWING_PARAMETERS[:4]:  # Top 4 core parameters
            plot_data = self.get_parameter_extraction_data(analysis_df, param)
            if plot_data:
                parameter_plots[param] = plot_data

        # Calculate recommendations from top brews
        recommended_grind = None
        recommended_temp = None
        recommended_ratio = None

        if not analysis_df.empty and "final_extraction_yield_percent" in analysis_df.columns:
            rated = analysis_df.dropna(subset=["final_extraction_yield_percent"])
            if len(rated) >= self.MIN_SAMPLE_SIZE:
                # Get top 20% by extraction
                top_n = max(self.MIN_SAMPLE_SIZE, len(rated) // 5)
                top_brews = rated.nlargest(top_n, "final_extraction_yield_percent")

                if "grind_size" in top_brews.columns:
                    grind_vals = top_brews["grind_size"].dropna()
                    if len(grind_vals) > 0:
                        recommended_grind = round(float(grind_vals.mean()), 1)

                if "water_temp_degC" in top_brews.columns:
                    temp_vals = top_brews["water_temp_degC"].dropna()
                    if len(temp_vals) > 0:
                        recommended_temp = round(float(temp_vals.mean()), 1)

                if "brew_ratio_to_1" in top_brews.columns:
                    ratio_vals = top_brews["brew_ratio_to_1"].dropna()
                    if len(ratio_vals) > 0:
                        recommended_ratio = round(float(ratio_vals.mean()), 1)

        return ExtractionInsights(
            drivers=drivers,
            method_analysis=method_analysis,
            parameter_plots=parameter_plots,
            recommended_grind=recommended_grind,
            recommended_temp=recommended_temp,
            recommended_ratio=recommended_ratio,
        )
