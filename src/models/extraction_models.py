"""
Extraction analysis data models.

These dataclasses represent the results of extraction-focused analytics.
The primary goal is understanding which brewing parameters drive extraction.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List, Dict


@dataclass
class ParameterImpact:
    """
    Represents the impact of a single parameter on extraction.

    This is the core insight: how much does changing this parameter
    affect extraction yield?
    """
    parameter: str  # e.g., "grind_size", "water_temp_degC"
    parameter_display_name: str  # e.g., "Grind Size", "Water Temperature"
    correlation: float  # Pearson correlation (-1 to 1)
    impact_strength: str  # "high", "moderate", "low", "none"
    impact_direction: str  # "positive", "negative", "none"
    sample_size: int

    # Parameter range in your data
    min_value: Optional[float]
    max_value: Optional[float]

    # What extraction you get at extremes
    extraction_at_min: Optional[float]  # Avg extraction at low param values
    extraction_at_max: Optional[float]  # Avg extraction at high param values

    @property
    def actionable_insight(self) -> str:
        """Generate actionable insight for the user."""
        if self.impact_strength == "none":
            return f"{self.parameter_display_name} shows no clear relationship with extraction in your data."

        direction_word = "increases" if self.impact_direction == "positive" else "decreases"
        opposite_word = "decrease" if self.impact_direction == "positive" else "increase"

        return (
            f"{self.parameter_display_name} {self.impact_direction}ly correlates with extraction "
            f"(r={self.correlation:.2f}). Higher {self.parameter_display_name.lower()} {direction_word} extraction. "
            f"To {opposite_word} extraction, try lowering {self.parameter_display_name.lower()}."
        )


@dataclass
class ExtractionDrivers:
    """
    Complete analysis of what drives extraction in your brews.

    Ranks all parameters by their impact on extraction yield.
    """
    parameter_impacts: List[ParameterImpact]  # Sorted by |correlation|
    total_brews_analyzed: int
    avg_extraction: Optional[float]
    extraction_range: tuple  # (min, max)

    @property
    def top_drivers(self) -> List[ParameterImpact]:
        """Get parameters with meaningful impact (moderate or higher)."""
        return [p for p in self.parameter_impacts
                if p.impact_strength in ("high", "moderate")]

    @property
    def summary(self) -> str:
        """Generate summary of extraction drivers."""
        if not self.parameter_impacts:
            return "Not enough data to analyze extraction drivers."

        top = self.top_drivers
        if not top:
            return (
                f"Analyzed {self.total_brews_analyzed} brews. "
                "No parameters show strong correlation with extraction. "
                "This could mean: (1) parameters are already well-dialed, "
                "(2) need more variation in experiments, or "
                "(3) other unmeasured factors dominate."
            )

        driver_names = [p.parameter_display_name for p in top[:3]]
        return (
            f"Analyzed {self.total_brews_analyzed} brews. "
            f"Top extraction drivers: {', '.join(driver_names)}. "
            f"Your extraction ranges from {self.extraction_range[0]:.1f}% to {self.extraction_range[1]:.1f}%."
        )


@dataclass
class MethodComparison:
    """
    Extraction comparison across different brew methods/devices.
    """
    method_name: str
    device_name: Optional[str]
    brew_count: int
    avg_extraction: Optional[float]
    extraction_std: Optional[float]
    avg_tds: Optional[float]
    avg_rating: Optional[float]

    # Best performing settings for this method
    best_grind: Optional[float]
    best_temp: Optional[float]
    best_ratio: Optional[float]
    best_extraction: Optional[float]


@dataclass
class MethodAnalysis:
    """
    Complete analysis comparing extraction across methods.
    """
    method_comparisons: List[MethodComparison]
    total_brews: int

    @property
    def best_method(self) -> Optional[MethodComparison]:
        """Get method with highest average extraction."""
        valid = [m for m in self.method_comparisons if m.avg_extraction is not None]
        if not valid:
            return None
        return max(valid, key=lambda m: m.avg_extraction)

    @property
    def most_consistent_method(self) -> Optional[MethodComparison]:
        """Get method with lowest extraction std dev."""
        valid = [m for m in self.method_comparisons
                 if m.extraction_std is not None and m.brew_count >= 3]
        if not valid:
            return None
        return min(valid, key=lambda m: m.extraction_std)


@dataclass
class ParameterExtractionData:
    """
    Data for plotting parameter vs extraction scatter plot.
    """
    parameter: str
    parameter_display_name: str
    param_values: List[float]
    extraction_values: List[float]
    correlation: float

    # Trend line coefficients (y = slope * x + intercept)
    slope: float
    intercept: float

    @property
    def trend_description(self) -> str:
        """Describe the trend in plain language."""
        if abs(self.correlation) < 0.2:
            return "No clear trend"

        direction = "increases" if self.slope > 0 else "decreases"
        strength = "strongly" if abs(self.correlation) >= 0.7 else "moderately" if abs(self.correlation) >= 0.4 else "weakly"

        return f"Extraction {strength} {direction} as {self.parameter_display_name.lower()} increases"


@dataclass
class ExtractionInsights:
    """
    High-level extraction insights combining multiple analyses.
    """
    drivers: ExtractionDrivers
    method_analysis: MethodAnalysis
    parameter_plots: Dict[str, ParameterExtractionData]

    # Quick recommendations
    recommended_grind: Optional[float]
    recommended_temp: Optional[float]
    recommended_ratio: Optional[float]

    @property
    def key_findings(self) -> List[str]:
        """Generate list of key findings."""
        findings = []

        # Top driver insight
        if self.drivers.top_drivers:
            top = self.drivers.top_drivers[0]
            findings.append(f"🎯 {top.parameter_display_name} has the strongest impact on extraction (r={top.correlation:.2f})")

        # Method insight
        if self.method_analysis.best_method:
            best = self.method_analysis.best_method
            findings.append(f"📊 {best.method_name} achieves highest avg extraction ({best.avg_extraction:.1f}%)")

        # Consistency insight
        if self.method_analysis.most_consistent_method:
            consistent = self.method_analysis.most_consistent_method
            findings.append(f"🎯 {consistent.method_name} is most consistent (±{consistent.extraction_std:.1f}%)")

        # Recommendation
        if self.recommended_grind is not None:
            findings.append(f"💡 For optimal extraction, try grind size ~{self.recommended_grind:.1f}")

        return findings
