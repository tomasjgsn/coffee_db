"""
Unified Brewing Score

A brew-ratio-aware scoring system that measures how close a brew's
(extraction, TDS) pair is to the optimal point for its specific brew ratio.

The optimal point varies along each isometric line (constant brew ratio)
based on where that line passes closest to the global ideal zone center.

Formula:
    Score = 100 × exp(-k × d)

    where d = √[(ΔE/σE)² + (ΔT/σT)²]

    and the target (E_opt, T_opt) is calculated for each brew ratio:
    E_opt(R) = (4.875 + 1.25×R) / (0.25 + 0.01×R²)
    T_opt(R) = (R/100) × E_opt(R)

References:
    - SCA Coffee Brewing Control Chart
    - UC Davis Coffee Center research on brewing parameters
"""

import math
from typing import Optional, Tuple


class UnifiedBrewingScore:
    """
    Calculate a unified brewing quality score based on normalized
    Euclidean distance from the brew-ratio-specific optimal point.

    Attributes:
        sigma_e: Standard deviation for extraction normalization (default: 2.0)
        sigma_t: Standard deviation for TDS normalization (default: 0.1)
        decay_k: Exponential decay constant (default: 0.5)
        global_target_e: Global ideal extraction percentage (default: 19.5)
        global_target_t: Global ideal TDS percentage (default: 1.25)
    """

    def __init__(
        self,
        sigma_e: float = 2.0,
        sigma_t: float = 0.1,
        decay_k: float = 0.5,
        global_target_e: float = 19.5,
        global_target_t: float = 1.25
    ):
        """
        Initialize the scorer with normalization and decay parameters.

        Args:
            sigma_e: Extraction standard deviation for normalization.
                     Default 2.0 is half the ideal zone width (18-22%).
            sigma_t: TDS standard deviation for normalization.
                     Default 0.1 is half the ideal zone width (1.15-1.35%).
            decay_k: Exponential decay constant. Higher = steeper score drop.
                     Default 0.5 gives reasonable score spread.
            global_target_e: The global ideal extraction yield percentage.
            global_target_t: The global ideal TDS percentage.
        """
        self.sigma_e = sigma_e
        self.sigma_t = sigma_t
        self.decay_k = decay_k
        self.global_target_e = global_target_e
        self.global_target_t = global_target_t

        # Pre-compute constants for optimal point formula
        # E_opt(R) = (E₀/σE² + T₀×R/(100×σT²)) / (1/σE² + R²/(100²×σT²))
        self._a = global_target_e / (sigma_e ** 2)  # 19.5/4 = 4.875
        self._b = global_target_t / (sigma_t ** 2)  # 1.25/0.01 = 125
        self._c = 1 / (sigma_e ** 2)                # 1/4 = 0.25
        self._d = 1 / (sigma_t ** 2)                # 1/0.01 = 100

    def get_optimal_point(self, brew_ratio: float) -> Tuple[float, float]:
        """
        Calculate the optimal (extraction, TDS) point for a given brew ratio.

        The optimal point is where the isometric line (constant brew ratio)
        passes closest to the global ideal zone center (19.5%, 1.25%).

        The isometric line equation is: TDS = (R/1000) × Extraction
        where R is brew ratio in g/L.

        Args:
            brew_ratio: Brew ratio in grams of coffee per liter of water (g/L).
                       Typical values: 55-80 g/L.

        Returns:
            Tuple of (E_opt, T_opt) - the optimal extraction and TDS
            for the given brew ratio.

        Raises:
            ValueError: If brew_ratio is <= 0 or None.
        """
        if brew_ratio is None:
            raise ValueError("brew_ratio cannot be None")
        if brew_ratio <= 0:
            raise ValueError(f"brew_ratio must be positive, got {brew_ratio}")

        # The isometric line: T = (R/1000) × E
        # Minimize: d² = ((E - E₀)/σE)² + ((T - T₀)/σT)²
        # Subject to: T = (R/1000) × E
        #
        # Solution:
        # E_opt = (E₀/σE² + (R/1000)×T₀/σT²) / (1/σE² + (R/1000)²/σT²)
        # T_opt = (R/1000) × E_opt

        r_factor = brew_ratio / 1000  # R/1000 for correct TDS relationship

        numerator = self._a + self._b * r_factor
        denominator = self._c + self._d * (r_factor ** 2)

        e_opt = numerator / denominator
        t_opt = r_factor * e_opt  # T = (R/1000) × E

        return e_opt, t_opt

    def get_distance(
        self,
        extraction: float,
        tds: float,
        brew_ratio: float
    ) -> float:
        """
        Calculate the normalized distance from the brew-ratio-specific optimal.

        Args:
            extraction: Extraction yield percentage (typical: 14-24%)
            tds: Total dissolved solids percentage (typical: 0.8-1.7%)
            brew_ratio: Brew ratio in g/L (typical: 55-80)

        Returns:
            Normalized Euclidean distance from optimal point.
            d = 0 at optimal, d ≈ 1 at one sigma deviation, increases with distance.

        Raises:
            ValueError: If any parameter is None.
            TypeError: If parameters are not numeric.
        """
        if extraction is None or tds is None or brew_ratio is None:
            raise ValueError("extraction, tds, and brew_ratio cannot be None")

        e_opt, t_opt = self.get_optimal_point(brew_ratio)

        delta_e = (extraction - e_opt) / self.sigma_e
        delta_t = (tds - t_opt) / self.sigma_t

        distance = math.sqrt(delta_e ** 2 + delta_t ** 2)

        return distance

    def calculate(
        self,
        extraction: float,
        tds: float,
        brew_ratio: float
    ) -> float:
        """
        Calculate the unified brewing score (0-100).

        Score = 100 × exp(-k × d)

        where d is the normalized distance from the brew-ratio-specific optimal.

        Args:
            extraction: Extraction yield percentage (typical: 14-24%)
            tds: Total dissolved solids percentage (typical: 0.8-1.7%)
            brew_ratio: Brew ratio in g/L (typical: 55-80)

        Returns:
            Score between 0 and 100.
            - 100 = at optimal point for this brew ratio
            - ~60-70 = at edge of ideal zone
            - <30 = far from optimal (corner zones)

        Raises:
            ValueError: If any parameter is None.
            TypeError: If parameters are not numeric.
        """
        distance = self.get_distance(extraction, tds, brew_ratio)
        score = 100 * math.exp(-self.decay_k * distance)

        return score

    def get_gradient(
        self,
        extraction: float,
        tds: float,
        brew_ratio: float
    ) -> Tuple[float, float]:
        """
        Calculate the gradient of the score with respect to extraction and TDS.

        Useful for sensitivity analysis - shows which direction improves score.

        Args:
            extraction: Extraction yield percentage
            tds: Total dissolved solids percentage
            brew_ratio: Brew ratio in g/L

        Returns:
            Tuple of (∂score/∂extraction, ∂score/∂tds)
            - Positive gradient means score increases if parameter increases
            - Negative gradient means score increases if parameter decreases
            - Gradient near zero means parameter is near optimal
        """
        if extraction is None or tds is None or brew_ratio is None:
            raise ValueError("extraction, tds, and brew_ratio cannot be None")

        e_opt, t_opt = self.get_optimal_point(brew_ratio)
        distance = self.get_distance(extraction, tds, brew_ratio)

        # Score = 100 × exp(-k × d)
        # d = √[(ΔE/σE)² + (ΔT/σT)²]
        #
        # ∂score/∂E = 100 × exp(-k×d) × (-k) × (∂d/∂E)
        # ∂d/∂E = (1/d) × (ΔE/σE²) = (E - E_opt) / (σE² × d)

        if distance < 1e-10:
            # At optimal point, gradient is zero
            return 0.0, 0.0

        score = 100 * math.exp(-self.decay_k * distance)

        delta_e = extraction - e_opt
        delta_t = tds - t_opt

        # ∂d/∂E = (E - E_opt) / (σE² × d)
        dd_de = delta_e / (self.sigma_e ** 2 * distance)
        dd_dt = delta_t / (self.sigma_t ** 2 * distance)

        # ∂score/∂E = -k × score × (∂d/∂E)
        grad_e = -self.decay_k * score * dd_de
        grad_t = -self.decay_k * score * dd_dt

        return grad_e, grad_t


def calculate_unified_score(
    extraction: Optional[float],
    tds: Optional[float],
    brew_ratio: Optional[float],
    sigma_e: float = 2.0,
    sigma_t: float = 0.1,
    decay_k: float = 0.5
) -> Optional[float]:
    """
    Convenience function to calculate unified brewing score.

    Returns None if any required parameter is None (handles missing data gracefully).

    Args:
        extraction: Extraction yield percentage
        tds: Total dissolved solids percentage
        brew_ratio: Brew ratio in g/L
        sigma_e: Extraction normalization factor
        sigma_t: TDS normalization factor
        decay_k: Score decay constant

    Returns:
        Unified brewing score (0-100) or None if data is missing.
    """
    if extraction is None or tds is None or brew_ratio is None:
        return None

    if brew_ratio <= 0:
        return None

    scorer = UnifiedBrewingScore(sigma_e=sigma_e, sigma_t=sigma_t, decay_k=decay_k)
    return scorer.calculate(extraction, tds, brew_ratio)
