"""
Analytics data models for coffee brewing analysis.

These dataclasses represent the results of various analytical calculations
performed on brewing data. They provide structured outputs that can be
used by the visualization layer and MCP tools.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional, List, Dict


@dataclass
class TrendData:
    """
    Represents trend analysis for a specific metric over time.

    Used for tracking improvement in extraction, TDS, ratings, etc.
    """
    metric: str
    window_days: int
    values: List[float]
    dates: List[date]
    trend_direction: str  # "improving", "declining", "stable"
    percent_change: float
    moving_average: List[float]
    sample_size: int

    @property
    def is_meaningful(self) -> bool:
        """Check if we have enough data for meaningful trend analysis."""
        return self.sample_size >= 3

    @property
    def summary(self) -> str:
        """Human-readable summary of the trend."""
        if not self.is_meaningful:
            return f"Insufficient data ({self.sample_size} brews) for {self.metric} trend analysis"

        direction_text = {
            "improving": "improved",
            "declining": "declined",
            "stable": "remained stable"
        }

        return (
            f"{self.metric} has {direction_text.get(self.trend_direction, 'changed')} "
            f"by {abs(self.percent_change):.1f}% over the last {self.window_days} days "
            f"({self.sample_size} brews)"
        )


@dataclass
class BeanComparisonMetrics:
    """Metrics for a single bean in a comparison."""
    bean_name: str
    sample_size: int
    avg_extraction: Optional[float]
    avg_tds: Optional[float]
    avg_rating: Optional[float]
    avg_brew_score: Optional[float]
    extraction_std: Optional[float]
    tds_std: Optional[float]
    rating_std: Optional[float]
    best_rating: Optional[float]
    worst_rating: Optional[float]


@dataclass
class ComparisonData:
    """
    Represents a comparison between multiple coffee beans.

    Contains aggregated metrics for each bean to enable side-by-side analysis.
    """
    bean_names: List[str]
    bean_metrics: Dict[str, BeanComparisonMetrics]
    comparison_metrics: List[str]  # Which metrics were compared
    min_sample_size: int  # Smallest sample among compared beans

    @property
    def is_statistically_meaningful(self) -> bool:
        """Check if comparison has enough data to be meaningful."""
        return self.min_sample_size >= 3

    @property
    def confidence_level(self) -> str:
        """Return confidence level based on sample sizes."""
        if self.min_sample_size >= 10:
            return "high"
        elif self.min_sample_size >= 5:
            return "medium"
        elif self.min_sample_size >= 3:
            return "low"
        else:
            return "insufficient"


@dataclass
class CorrelationResult:
    """
    Represents the correlation between a brewing parameter and an outcome metric.

    Used to identify which parameters most influence extraction, TDS, or ratings.
    """
    parameter: str  # e.g., "grind_size", "water_temp_degC"
    metric: str     # e.g., "final_extraction_yield_percent", "score_overall_rating"
    correlation: float  # Pearson correlation coefficient (-1 to 1)
    strength: str   # "strong", "moderate", "weak", "none"
    direction: str  # "positive", "negative", "none"
    sample_size: int

    @property
    def is_meaningful(self) -> bool:
        """Check if correlation is based on enough data."""
        return self.sample_size >= 3

    @property
    def summary(self) -> str:
        """Human-readable summary of the correlation."""
        if not self.is_meaningful:
            return f"Insufficient data to analyze {self.parameter} vs {self.metric}"

        if self.strength == "none":
            return f"No correlation found between {self.parameter} and {self.metric}"

        return (
            f"{self.strength.capitalize()} {self.direction} correlation "
            f"between {self.parameter} and {self.metric} "
            f"(r={self.correlation:.2f}, n={self.sample_size})"
        )

    @classmethod
    def determine_strength(cls, correlation: float) -> str:
        """Determine correlation strength from coefficient."""
        abs_corr = abs(correlation)
        if abs_corr >= 0.7:
            return "strong"
        elif abs_corr >= 0.4:
            return "moderate"
        elif abs_corr >= 0.2:
            return "weak"
        else:
            return "none"

    @classmethod
    def determine_direction(cls, correlation: float) -> str:
        """Determine correlation direction from coefficient."""
        if abs(correlation) < 0.2:
            return "none"
        return "positive" if correlation > 0 else "negative"


@dataclass
class OptimalParameters:
    """
    Represents the identified optimal brewing parameters.

    Can be calculated for a specific bean or across all beans.
    Based on brews with the highest ratings/scores.
    """
    bean_name: Optional[str]  # None means all beans
    optimal_grind: Optional[float]
    optimal_temp: Optional[float]
    optimal_ratio: Optional[float]
    optimal_bloom_time: Optional[float]
    optimal_total_time: Optional[float]
    confidence: str  # "high", "medium", "low"
    based_on_brews: int
    top_brews_analyzed: int  # How many top brews were used
    avg_rating_of_top: Optional[float]

    @property
    def is_meaningful(self) -> bool:
        """Check if we have enough data for meaningful recommendations."""
        return self.based_on_brews >= 3

    def get_parameter_dict(self) -> Dict[str, Optional[float]]:
        """Return optimal parameters as a dictionary."""
        return {
            "grind_size": self.optimal_grind,
            "water_temp_degC": self.optimal_temp,
            "brew_ratio_to_1": self.optimal_ratio,
            "brew_bloom_time_s": self.optimal_bloom_time,
            "brew_total_time_s": self.optimal_total_time,
        }


@dataclass
class ConsistencyMetrics:
    """
    Represents brewing consistency analysis.

    Measures how consistent the brewer is across multiple brews,
    optionally filtered to a specific bean.
    """
    bean_name: Optional[str]  # None means all beans
    extraction_std: Optional[float]
    extraction_cv: Optional[float]  # Coefficient of variation (std/mean * 100)
    tds_std: Optional[float]
    tds_cv: Optional[float]
    rating_std: Optional[float]
    rating_cv: Optional[float]
    consistency_score: float  # 0-100, higher = more consistent
    sample_size: int

    # Thresholds for consistency rating
    EXCELLENT_THRESHOLD: float = field(default=80, repr=False)
    GOOD_THRESHOLD: float = field(default=60, repr=False)
    FAIR_THRESHOLD: float = field(default=40, repr=False)

    @property
    def is_meaningful(self) -> bool:
        """Check if we have enough data for meaningful consistency analysis."""
        return self.sample_size >= 3

    @property
    def consistency_rating(self) -> str:
        """Return a human-readable consistency rating."""
        if not self.is_meaningful:
            return "insufficient data"
        if self.consistency_score >= self.EXCELLENT_THRESHOLD:
            return "excellent"
        elif self.consistency_score >= self.GOOD_THRESHOLD:
            return "good"
        elif self.consistency_score >= self.FAIR_THRESHOLD:
            return "fair"
        else:
            return "needs improvement"

    @property
    def summary(self) -> str:
        """Human-readable summary of consistency."""
        if not self.is_meaningful:
            return f"Insufficient data ({self.sample_size} brews) for consistency analysis"

        scope = f"for {self.bean_name}" if self.bean_name else "overall"
        return (
            f"Brewing consistency {scope}: {self.consistency_rating} "
            f"(score: {self.consistency_score:.0f}/100, based on {self.sample_size} brews)"
        )


@dataclass
class AnalyticsSummary:
    """
    High-level analytics summary combining multiple analyses.

    Provides a quick overview of brewing performance.
    """
    total_brews: int
    unique_beans: int
    date_range_days: int
    avg_extraction: Optional[float]
    avg_tds: Optional[float]
    avg_rating: Optional[float]
    best_bean: Optional[str]
    most_brewed_bean: Optional[str]
    consistency_score: Optional[float]
    improvement_trend: Optional[str]  # "improving", "declining", "stable"

    @property
    def has_enough_data(self) -> bool:
        """Check if there's enough data for meaningful summary."""
        return self.total_brews >= 3
