"""
Analytics Service

Provides statistical analysis and insights for coffee brewing data.
Calculates trends, correlations, optimal parameters, and consistency metrics.
"""

import logging
from datetime import date, timedelta
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from src.models.analytics_models import (
    AnalyticsSummary,
    BeanComparisonMetrics,
    ComparisonData,
    ConsistencyMetrics,
    CorrelationResult,
    OptimalParameters,
    TrendData,
)
from src.services.cache import cache_dataframe_result
from src.services.metrics import monitor_performance


class AnalyticsService:
    """
    Service for analyzing coffee brewing data.

    Provides methods for:
    - Trend analysis (improvement over time)
    - Bean comparisons
    - Parameter correlations
    - Optimal parameter identification
    - Consistency metrics
    """

    # Brewing parameters to analyze for correlations
    BREWING_PARAMETERS = [
        "grind_size",
        "water_temp_degC",
        "brew_ratio_to_1",
        "brew_bloom_time_s",
        "brew_total_time_s",
        "brew_bloom_water_ml",
        "brew_pulse_target_water_ml",
        "coffee_dose_grams",
        "water_volume_ml",
    ]

    # Outcome metrics to correlate against
    OUTCOME_METRICS = [
        "final_extraction_yield_percent",
        "final_tds_percent",
        "score_overall_rating",
    ]

    # Minimum sample size for meaningful analysis
    MIN_SAMPLE_SIZE = 3

    # Threshold for considering a trend "stable" (percentage)
    STABLE_THRESHOLD = 5.0

    def __init__(self):
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger(f"{__name__}.AnalyticsService")
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
    def calculate_improvement_trend(
        self, df: pd.DataFrame, metric: str, window_days: int = 30
    ) -> TrendData:
        """
        Calculate improvement trend for a specific metric over time.

        Args:
            df: DataFrame containing brew data with brew_date column
            metric: Column name of the metric to analyze
            window_days: Number of days to look back (default 30)

        Returns:
            TrendData with trend analysis results
        """
        # Handle edge cases
        window_days = max(1, abs(window_days))

        if df.empty or metric not in df.columns:
            return self._empty_trend(metric, window_days)

        # Filter to window
        today = date.today()
        start_date = today - timedelta(days=window_days)

        # Ensure brew_date is date type
        df = df.copy()
        df["brew_date"] = pd.to_datetime(df["brew_date"], errors="coerce").dt.date

        window_df = df[df["brew_date"] >= start_date].copy()

        if window_df.empty:
            return self._empty_trend(metric, window_days)

        # Get metric values, dropping NaN
        metric_data = window_df[["brew_date", metric]].dropna()

        if len(metric_data) == 0:
            return self._empty_trend(metric, window_days)

        # Sort by date
        metric_data = metric_data.sort_values("brew_date")

        values = metric_data[metric].tolist()
        dates = metric_data["brew_date"].tolist()

        # Calculate trend
        if len(values) < 2:
            percent_change = 0.0
            trend_direction = "stable"
        else:
            first_val = values[0]
            last_val = values[-1]
            if first_val != 0:
                percent_change = ((last_val - first_val) / abs(first_val)) * 100
            else:
                percent_change = 0.0 if last_val == 0 else 100.0

            # Determine direction
            if abs(percent_change) < self.STABLE_THRESHOLD:
                trend_direction = "stable"
            elif percent_change > 0:
                trend_direction = "improving"
            else:
                trend_direction = "declining"

        # Calculate moving average
        moving_average = self._calculate_moving_average(values)

        return TrendData(
            metric=metric,
            window_days=window_days,
            values=values,
            dates=dates,
            trend_direction=trend_direction,
            percent_change=round(percent_change, 1),
            moving_average=moving_average,
            sample_size=len(values),
        )

    def _empty_trend(self, metric: str, window_days: int) -> TrendData:
        """Create an empty TrendData for edge cases."""
        return TrendData(
            metric=metric,
            window_days=window_days,
            values=[],
            dates=[],
            trend_direction="stable",
            percent_change=0.0,
            moving_average=[],
            sample_size=0,
        )

    def _calculate_moving_average(
        self, values: List[float], window: int = 3
    ) -> List[float]:
        """Calculate simple moving average."""
        if len(values) == 0:
            return []

        if len(values) < window:
            window = max(1, len(values))

        result = []
        for i in range(len(values)):
            start_idx = max(0, i - window + 1)
            window_vals = values[start_idx : i + 1]
            result.append(sum(window_vals) / len(window_vals))

        return [round(v, 2) for v in result]

    @monitor_performance
    def calculate_bean_comparison(
        self, df: pd.DataFrame, bean_names: List[str]
    ) -> ComparisonData:
        """
        Compare metrics across multiple coffee beans.

        Args:
            df: DataFrame containing brew data
            bean_names: List of bean names to compare

        Returns:
            ComparisonData with comparison results
        """
        if df.empty:
            return ComparisonData(
                bean_names=bean_names,
                bean_metrics={},
                comparison_metrics=[],
                min_sample_size=0,
            )

        bean_metrics = {}
        min_sample = float("inf")

        for bean_name in bean_names:
            bean_df = df[df["bean_name"] == bean_name]

            if bean_df.empty:
                # Create empty metrics for missing bean
                metrics = BeanComparisonMetrics(
                    bean_name=bean_name,
                    sample_size=0,
                    avg_extraction=None,
                    avg_tds=None,
                    avg_rating=None,
                    avg_brew_score=None,
                    extraction_std=None,
                    tds_std=None,
                    rating_std=None,
                    best_rating=None,
                    worst_rating=None,
                )
            else:
                sample_size = len(bean_df)
                min_sample = min(min_sample, sample_size)

                metrics = BeanComparisonMetrics(
                    bean_name=bean_name,
                    sample_size=sample_size,
                    avg_extraction=self._safe_mean(
                        bean_df, "final_extraction_yield_percent"
                    ),
                    avg_tds=self._safe_mean(bean_df, "final_tds_percent"),
                    avg_rating=self._safe_mean(bean_df, "score_overall_rating"),
                    avg_brew_score=self._safe_mean(bean_df, "score_brew"),
                    extraction_std=self._safe_std(
                        bean_df, "final_extraction_yield_percent"
                    ),
                    tds_std=self._safe_std(bean_df, "final_tds_percent"),
                    rating_std=self._safe_std(bean_df, "score_overall_rating"),
                    best_rating=self._safe_max(bean_df, "score_overall_rating"),
                    worst_rating=self._safe_min(bean_df, "score_overall_rating"),
                )

            bean_metrics[bean_name] = metrics

        # If no beans found, min_sample stays inf
        if min_sample == float("inf"):
            min_sample = 0

        return ComparisonData(
            bean_names=bean_names,
            bean_metrics=bean_metrics,
            comparison_metrics=[
                "avg_extraction",
                "avg_tds",
                "avg_rating",
                "avg_brew_score",
            ],
            min_sample_size=int(min_sample),
        )

    def _safe_mean(self, df: pd.DataFrame, column: str) -> Optional[float]:
        """Safely calculate mean, returning None if not possible."""
        if column not in df.columns:
            return None
        values = df[column].dropna()
        if len(values) == 0:
            return None
        return round(float(values.mean()), 2)

    def _safe_std(self, df: pd.DataFrame, column: str) -> Optional[float]:
        """Safely calculate std, returning None if not possible."""
        if column not in df.columns:
            return None
        values = df[column].dropna()
        if len(values) < 2:
            return None
        return round(float(values.std()), 2)

    def _safe_max(self, df: pd.DataFrame, column: str) -> Optional[float]:
        """Safely get max value."""
        if column not in df.columns:
            return None
        values = df[column].dropna()
        if len(values) == 0:
            return None
        return float(values.max())

    def _safe_min(self, df: pd.DataFrame, column: str) -> Optional[float]:
        """Safely get min value."""
        if column not in df.columns:
            return None
        values = df[column].dropna()
        if len(values) == 0:
            return None
        return float(values.min())

    @cache_dataframe_result(expire_minutes=10)
    @monitor_performance
    def calculate_parameter_correlations(
        self, df: pd.DataFrame
    ) -> List[CorrelationResult]:
        """
        Calculate correlations between brewing parameters and outcome metrics.

        Args:
            df: DataFrame containing brew data

        Returns:
            List of CorrelationResult for each parameter-metric pair
        """
        if df.empty:
            return []

        results = []

        for parameter in self.BREWING_PARAMETERS:
            if parameter not in df.columns:
                continue

            for metric in self.OUTCOME_METRICS:
                if metric not in df.columns:
                    continue

                # Get paired non-null values
                paired_data = df[[parameter, metric]].dropna()

                if len(paired_data) < self.MIN_SAMPLE_SIZE:
                    continue

                # Calculate Pearson correlation
                correlation, _ = self._calculate_correlation(
                    paired_data[parameter], paired_data[metric]
                )

                results.append(
                    CorrelationResult(
                        parameter=parameter,
                        metric=metric,
                        correlation=round(correlation, 2),
                        strength=CorrelationResult.determine_strength(correlation),
                        direction=CorrelationResult.determine_direction(correlation),
                        sample_size=len(paired_data),
                    )
                )

        return results

    def _calculate_correlation(
        self, x: pd.Series, y: pd.Series
    ) -> Tuple[float, float]:
        """
        Calculate Pearson correlation coefficient.

        Returns:
            Tuple of (correlation, p_value)
            p_value is approximated for simplicity
        """
        if len(x) < 2:
            return 0.0, 1.0

        # Use numpy for correlation calculation
        try:
            # Pearson correlation
            correlation = np.corrcoef(x.values, y.values)[0, 1]

            if np.isnan(correlation):
                return 0.0, 1.0

            # Simple p-value approximation (not as accurate as scipy)
            # For a rough estimate: p decreases as |r| and n increase
            n = len(x)
            if abs(correlation) < 1:
                t_stat = correlation * np.sqrt(n - 2) / np.sqrt(1 - correlation**2)
                # Rough p-value approximation
                p_value = 2 * (1 - min(0.999, abs(t_stat) / (abs(t_stat) + n)))
            else:
                p_value = 0.0

            return float(correlation), float(p_value)
        except Exception as e:
            self.logger.warning(f"Error calculating correlation: {e}")
            return 0.0, 1.0

    @monitor_performance
    def identify_optimal_parameters(
        self, df: pd.DataFrame, bean_name: Optional[str] = None
    ) -> OptimalParameters:
        """
        Identify optimal brewing parameters based on top-rated brews.

        Args:
            df: DataFrame containing brew data
            bean_name: Optional bean name to filter by

        Returns:
            OptimalParameters with recommended values
        """
        if df.empty:
            return self._empty_optimal(bean_name)

        # Filter by bean if specified
        if bean_name:
            df = df[df["bean_name"] == bean_name]

        if df.empty:
            return self._empty_optimal(bean_name)

        # Get brews with ratings
        rated_df = df.dropna(subset=["score_overall_rating"])

        if rated_df.empty:
            return self._empty_optimal(bean_name)

        total_brews = len(rated_df)

        # Get top 20% of brews (minimum 3, maximum 10)
        top_n = max(self.MIN_SAMPLE_SIZE, min(10, int(total_brews * 0.2)))
        top_n = min(top_n, total_brews)

        top_brews = rated_df.nlargest(top_n, "score_overall_rating")

        # Calculate optimal values from top brews
        optimal_grind = self._safe_mean(top_brews, "grind_size")
        optimal_temp = self._safe_mean(top_brews, "water_temp_degC")
        optimal_ratio = self._safe_mean(top_brews, "brew_ratio_to_1")
        optimal_bloom = self._safe_mean(top_brews, "brew_bloom_time_s")
        optimal_total = self._safe_mean(top_brews, "brew_total_time_s")
        avg_rating = self._safe_mean(top_brews, "score_overall_rating")

        # Determine confidence based on sample size
        if total_brews >= 10:
            confidence = "high"
        elif total_brews >= 5:
            confidence = "medium"
        else:
            confidence = "low"

        return OptimalParameters(
            bean_name=bean_name,
            optimal_grind=optimal_grind,
            optimal_temp=optimal_temp,
            optimal_ratio=optimal_ratio,
            optimal_bloom_time=optimal_bloom,
            optimal_total_time=optimal_total,
            confidence=confidence,
            based_on_brews=total_brews,
            top_brews_analyzed=len(top_brews),
            avg_rating_of_top=avg_rating,
        )

    def _empty_optimal(self, bean_name: Optional[str]) -> OptimalParameters:
        """Create empty OptimalParameters for edge cases."""
        return OptimalParameters(
            bean_name=bean_name,
            optimal_grind=None,
            optimal_temp=None,
            optimal_ratio=None,
            optimal_bloom_time=None,
            optimal_total_time=None,
            confidence="low",
            based_on_brews=0,
            top_brews_analyzed=0,
            avg_rating_of_top=None,
        )

    @monitor_performance
    def calculate_consistency_metrics(
        self, df: pd.DataFrame, bean_name: Optional[str] = None
    ) -> ConsistencyMetrics:
        """
        Calculate brewing consistency metrics.

        Args:
            df: DataFrame containing brew data
            bean_name: Optional bean name to filter by

        Returns:
            ConsistencyMetrics with consistency analysis
        """
        if df.empty:
            return self._empty_consistency(bean_name)

        # Filter by bean if specified
        if bean_name:
            df = df[df["bean_name"] == bean_name]

        if df.empty:
            return self._empty_consistency(bean_name)

        sample_size = len(df)

        # Calculate standard deviations
        extraction_std = self._safe_std(df, "final_extraction_yield_percent")
        tds_std = self._safe_std(df, "final_tds_percent")
        rating_std = self._safe_std(df, "score_overall_rating")

        # Calculate coefficient of variation (CV = std/mean * 100)
        extraction_cv = self._calculate_cv(df, "final_extraction_yield_percent")
        tds_cv = self._calculate_cv(df, "final_tds_percent")
        rating_cv = self._calculate_cv(df, "score_overall_rating")

        # Calculate consistency score (0-100)
        # Lower CV = higher consistency
        consistency_score = self._calculate_consistency_score(
            extraction_cv, tds_cv, rating_cv
        )

        return ConsistencyMetrics(
            bean_name=bean_name,
            extraction_std=extraction_std,
            extraction_cv=extraction_cv,
            tds_std=tds_std,
            tds_cv=tds_cv,
            rating_std=rating_std,
            rating_cv=rating_cv,
            consistency_score=consistency_score,
            sample_size=sample_size,
        )

    def _empty_consistency(self, bean_name: Optional[str]) -> ConsistencyMetrics:
        """Create empty ConsistencyMetrics for edge cases."""
        return ConsistencyMetrics(
            bean_name=bean_name,
            extraction_std=None,
            extraction_cv=None,
            tds_std=None,
            tds_cv=None,
            rating_std=None,
            rating_cv=None,
            consistency_score=0.0,
            sample_size=0,
        )

    def _calculate_cv(self, df: pd.DataFrame, column: str) -> Optional[float]:
        """Calculate coefficient of variation (std/mean * 100)."""
        if column not in df.columns:
            return None
        values = df[column].dropna()
        if len(values) < 2:
            return None
        mean_val = values.mean()
        if mean_val == 0:
            return None
        std_val = values.std()
        return round((std_val / abs(mean_val)) * 100, 1)

    def _calculate_consistency_score(
        self,
        extraction_cv: Optional[float],
        tds_cv: Optional[float],
        rating_cv: Optional[float],
    ) -> float:
        """
        Calculate overall consistency score (0-100).

        Lower CV values = higher consistency = higher score.
        """
        # Target CVs for "perfect" consistency
        # These are aspirational targets for a skilled home brewer
        target_extraction_cv = 2.0  # 2% CV in extraction
        target_tds_cv = 2.0  # 2% CV in TDS
        target_rating_cv = 5.0  # 5% CV in ratings (more subjective)

        scores = []

        if extraction_cv is not None:
            # Score = 100 * (1 - cv/target) capped at 0-100
            score = max(0, 100 * (1 - extraction_cv / (target_extraction_cv * 5)))
            scores.append(score)

        if tds_cv is not None:
            score = max(0, 100 * (1 - tds_cv / (target_tds_cv * 5)))
            scores.append(score)

        if rating_cv is not None:
            score = max(0, 100 * (1 - rating_cv / (target_rating_cv * 5)))
            scores.append(score)

        if not scores:
            return 0.0

        return round(sum(scores) / len(scores), 1)

    @monitor_performance
    def calculate_analytics_summary(self, df: pd.DataFrame) -> AnalyticsSummary:
        """
        Calculate high-level analytics summary.

        Args:
            df: DataFrame containing brew data

        Returns:
            AnalyticsSummary with overview statistics
        """
        if df.empty:
            return AnalyticsSummary(
                total_brews=0,
                unique_beans=0,
                date_range_days=0,
                avg_extraction=None,
                avg_tds=None,
                avg_rating=None,
                best_bean=None,
                most_brewed_bean=None,
                consistency_score=None,
                improvement_trend=None,
            )

        total_brews = len(df)
        unique_beans = df["bean_name"].nunique()

        # Calculate date range
        df = df.copy()
        df["brew_date"] = pd.to_datetime(df["brew_date"], errors="coerce").dt.date
        valid_dates = df["brew_date"].dropna()

        if len(valid_dates) >= 2:
            date_range_days = (valid_dates.max() - valid_dates.min()).days
        else:
            date_range_days = 0

        # Calculate averages
        avg_extraction = self._safe_mean(df, "final_extraction_yield_percent")
        avg_tds = self._safe_mean(df, "final_tds_percent")
        avg_rating = self._safe_mean(df, "score_overall_rating")

        # Find best bean (highest average rating)
        best_bean = None
        if "score_overall_rating" in df.columns:
            bean_ratings = (
                df.groupby("bean_name")["score_overall_rating"]
                .mean()
                .dropna()
            )
            if len(bean_ratings) > 0:
                best_bean = bean_ratings.idxmax()

        # Find most brewed bean
        most_brewed_bean = None
        bean_counts = df["bean_name"].value_counts()
        if len(bean_counts) > 0:
            most_brewed_bean = bean_counts.idxmax()

        # Calculate consistency
        consistency = self.calculate_consistency_metrics(df)
        consistency_score = (
            consistency.consistency_score if consistency.is_meaningful else None
        )

        # Calculate improvement trend (last 30 days)
        trend = self.calculate_improvement_trend(df, "score_overall_rating", 30)
        improvement_trend = trend.trend_direction if trend.is_meaningful else None

        return AnalyticsSummary(
            total_brews=total_brews,
            unique_beans=unique_beans,
            date_range_days=date_range_days,
            avg_extraction=avg_extraction,
            avg_tds=avg_tds,
            avg_rating=avg_rating,
            best_bean=best_bean,
            most_brewed_bean=most_brewed_bean,
            consistency_score=consistency_score,
            improvement_trend=improvement_trend,
        )
