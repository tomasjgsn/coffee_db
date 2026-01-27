"""
Tests for Unified Brewing Score

Following TDD principles - tests written first before implementation.
Tests the brew-ratio-aware normalized Euclidean distance scoring system.
"""

import pytest
import math


class TestUnifiedBrewingScoreOptimalPoint:
    """Tests for the get_optimal_point() method - verifies lookup table values"""

    def test_optimal_point_at_65_gL(self):
        """Brew ratio 65 g/L should give optimal near (19.33, 1.26) - center of ideal zone"""
        from src.models.unified_score import UnifiedBrewingScore

        scorer = UnifiedBrewingScore()
        e_opt, t_opt = scorer.get_optimal_point(brew_ratio=65.0)

        assert abs(e_opt - 19.33) < 0.1, f"E_opt at 65 g/L expected ~19.33, got {e_opt}"
        assert abs(t_opt - 1.26) < 0.02, f"T_opt at 65 g/L expected ~1.26, got {t_opt}"

    def test_optimal_point_at_55_gL(self):
        """Brew ratio 55 g/L (SCA Golden Cup) should give optimal near (21.27, 1.17)"""
        from src.models.unified_score import UnifiedBrewingScore

        scorer = UnifiedBrewingScore()
        e_opt, t_opt = scorer.get_optimal_point(brew_ratio=55.0)

        assert abs(e_opt - 21.27) < 0.1, f"E_opt at 55 g/L expected ~21.27, got {e_opt}"
        assert abs(t_opt - 1.17) < 0.02, f"T_opt at 55 g/L expected ~1.17, got {t_opt}"

    def test_optimal_point_at_60_gL(self):
        """Brew ratio 60 g/L (common V60) should give optimal near (20.29, 1.22)"""
        from src.models.unified_score import UnifiedBrewingScore

        scorer = UnifiedBrewingScore()
        e_opt, t_opt = scorer.get_optimal_point(brew_ratio=60.0)

        assert abs(e_opt - 20.29) < 0.1, f"E_opt at 60 g/L expected ~20.29, got {e_opt}"
        assert abs(t_opt - 1.22) < 0.02, f"T_opt at 60 g/L expected ~1.22, got {t_opt}"

    def test_optimal_point_at_70_gL(self):
        """Brew ratio 70 g/L should give optimal near (18.41, 1.29)"""
        from src.models.unified_score import UnifiedBrewingScore

        scorer = UnifiedBrewingScore()
        e_opt, t_opt = scorer.get_optimal_point(brew_ratio=70.0)

        assert abs(e_opt - 18.41) < 0.1, f"E_opt at 70 g/L expected ~18.41, got {e_opt}"
        assert abs(t_opt - 1.29) < 0.02, f"T_opt at 70 g/L expected ~1.29, got {t_opt}"

    def test_optimal_point_at_80_gL(self):
        """Brew ratio 80 g/L should give optimal near (16.71, 1.34)"""
        from src.models.unified_score import UnifiedBrewingScore

        scorer = UnifiedBrewingScore()
        e_opt, t_opt = scorer.get_optimal_point(brew_ratio=80.0)

        assert abs(e_opt - 16.71) < 0.15, f"E_opt at 80 g/L expected ~16.71, got {e_opt}"
        assert abs(t_opt - 1.34) < 0.03, f"T_opt at 80 g/L expected ~1.34, got {t_opt}"

    def test_optimal_point_satisfies_isometric_constraint(self):
        """The optimal point should lie on the isometric line: T = (R/1000) * E"""
        from src.models.unified_score import UnifiedBrewingScore

        scorer = UnifiedBrewingScore()

        for brew_ratio in [50, 55, 60, 65, 70, 75, 80, 85]:
            e_opt, t_opt = scorer.get_optimal_point(brew_ratio=brew_ratio)
            expected_t = (brew_ratio / 1000) * e_opt

            assert abs(t_opt - expected_t) < 0.001, \
                f"Optimal point at {brew_ratio} g/L should satisfy T = (R/1000)*E: got T={t_opt}, expected {expected_t}"


class TestUnifiedBrewingScoreCalculation:
    """Tests for the calculate() method"""

    def test_score_at_optimal_point_is_100(self):
        """Score at the exact optimal point for a given brew ratio should be 100"""
        from src.models.unified_score import UnifiedBrewingScore

        scorer = UnifiedBrewingScore()

        for brew_ratio in [55, 60, 65, 70, 75]:
            e_opt, t_opt = scorer.get_optimal_point(brew_ratio=brew_ratio)
            score = scorer.calculate(extraction=e_opt, tds=t_opt, brew_ratio=brew_ratio)

            assert abs(score - 100.0) < 0.01, \
                f"Score at optimal for {brew_ratio} g/L should be 100, got {score}"

    def test_score_decreases_with_distance(self):
        """Score should decrease as extraction moves away from optimal"""
        from src.models.unified_score import UnifiedBrewingScore

        scorer = UnifiedBrewingScore()
        brew_ratio = 65.0
        e_opt, t_opt = scorer.get_optimal_point(brew_ratio=brew_ratio)

        score_optimal = scorer.calculate(extraction=e_opt, tds=t_opt, brew_ratio=brew_ratio)
        score_near = scorer.calculate(extraction=e_opt - 1, tds=t_opt, brew_ratio=brew_ratio)
        score_far = scorer.calculate(extraction=e_opt - 3, tds=t_opt, brew_ratio=brew_ratio)
        score_very_far = scorer.calculate(extraction=e_opt - 5, tds=t_opt, brew_ratio=brew_ratio)

        assert score_optimal > score_near > score_far > score_very_far, \
            "Scores should decrease with distance from optimal"

    def test_score_symmetric_in_extraction(self):
        """Equal distance above/below optimal extraction should give similar scores"""
        from src.models.unified_score import UnifiedBrewingScore

        scorer = UnifiedBrewingScore()
        brew_ratio = 65.0
        e_opt, t_opt = scorer.get_optimal_point(brew_ratio=brew_ratio)

        delta = 1.0
        score_above = scorer.calculate(extraction=e_opt + delta, tds=t_opt, brew_ratio=brew_ratio)
        score_below = scorer.calculate(extraction=e_opt - delta, tds=t_opt, brew_ratio=brew_ratio)

        assert abs(score_above - score_below) < 1.0, \
            f"Symmetric extraction deviation should give similar scores: {score_above} vs {score_below}"

    def test_score_symmetric_in_tds(self):
        """Equal distance above/below optimal TDS should give similar scores"""
        from src.models.unified_score import UnifiedBrewingScore

        scorer = UnifiedBrewingScore()
        brew_ratio = 65.0
        e_opt, t_opt = scorer.get_optimal_point(brew_ratio=brew_ratio)

        delta = 0.05
        score_above = scorer.calculate(extraction=e_opt, tds=t_opt + delta, brew_ratio=brew_ratio)
        score_below = scorer.calculate(extraction=e_opt, tds=t_opt - delta, brew_ratio=brew_ratio)

        assert abs(score_above - score_below) < 1.0, \
            f"Symmetric TDS deviation should give similar scores: {score_above} vs {score_below}"

    def test_score_always_between_0_and_100(self):
        """Score should always be in range (0, 100]"""
        from src.models.unified_score import UnifiedBrewingScore

        scorer = UnifiedBrewingScore()

        extreme_cases = [
            (10.0, 0.5, 50.0),   # Very under-extracted, very weak
            (25.0, 2.0, 80.0),   # Very over-extracted, very strong
            (14.0, 1.0, 70.0),   # Under-weak zone
            (22.0, 1.5, 60.0),   # Over-strong zone
        ]

        for extraction, tds, brew_ratio in extreme_cases:
            score = scorer.calculate(extraction=extraction, tds=tds, brew_ratio=brew_ratio)
            assert 0 < score <= 100, \
                f"Score should be in (0, 100], got {score} for ({extraction}, {tds}, {brew_ratio})"


class TestUnifiedBrewingScoreDistance:
    """Tests for the get_distance() method"""

    def test_distance_at_optimal_is_zero(self):
        """Distance at the optimal point should be 0"""
        from src.models.unified_score import UnifiedBrewingScore

        scorer = UnifiedBrewingScore()

        for brew_ratio in [55, 60, 65, 70, 75]:
            e_opt, t_opt = scorer.get_optimal_point(brew_ratio=brew_ratio)
            distance = scorer.get_distance(extraction=e_opt, tds=t_opt, brew_ratio=brew_ratio)

            assert abs(distance) < 0.001, \
                f"Distance at optimal for {brew_ratio} g/L should be 0, got {distance}"

    def test_distance_one_sigma_extraction(self):
        """Moving σE (2.0) in extraction should give distance ~1.0"""
        from src.models.unified_score import UnifiedBrewingScore

        scorer = UnifiedBrewingScore()
        brew_ratio = 65.0
        e_opt, t_opt = scorer.get_optimal_point(brew_ratio=brew_ratio)

        # Move 1 sigma in extraction
        distance = scorer.get_distance(extraction=e_opt + 2.0, tds=t_opt, brew_ratio=brew_ratio)

        assert 0.9 < distance < 1.1, \
            f"1σ extraction deviation should give d≈1.0, got {distance}"

    def test_distance_one_sigma_tds(self):
        """Moving σT (0.1) in TDS should give distance ~1.0"""
        from src.models.unified_score import UnifiedBrewingScore

        scorer = UnifiedBrewingScore()
        brew_ratio = 65.0
        e_opt, t_opt = scorer.get_optimal_point(brew_ratio=brew_ratio)

        # Move 1 sigma in TDS
        distance = scorer.get_distance(extraction=e_opt, tds=t_opt + 0.1, brew_ratio=brew_ratio)

        assert 0.9 < distance < 1.1, \
            f"1σ TDS deviation should give d≈1.0, got {distance}"


class TestUnifiedBrewingScoreGradient:
    """Tests for the get_gradient() method - used for sensitivity analysis"""

    def test_gradient_at_optimal_is_zero(self):
        """Gradient at optimal point should be (0, 0) - local maximum"""
        from src.models.unified_score import UnifiedBrewingScore

        scorer = UnifiedBrewingScore()
        brew_ratio = 65.0
        e_opt, t_opt = scorer.get_optimal_point(brew_ratio=brew_ratio)

        grad_e, grad_t = scorer.get_gradient(extraction=e_opt, tds=t_opt, brew_ratio=brew_ratio)

        assert abs(grad_e) < 0.01, f"∂score/∂E at optimal should be ~0, got {grad_e}"
        assert abs(grad_t) < 0.01, f"∂score/∂T at optimal should be ~0, got {grad_t}"

    def test_gradient_points_toward_optimal(self):
        """Gradient should point toward optimal (positive when below, negative when above)"""
        from src.models.unified_score import UnifiedBrewingScore

        scorer = UnifiedBrewingScore()
        brew_ratio = 65.0
        e_opt, t_opt = scorer.get_optimal_point(brew_ratio=brew_ratio)

        # Below optimal extraction - gradient should be positive
        grad_e_below, _ = scorer.get_gradient(extraction=e_opt - 2, tds=t_opt, brew_ratio=brew_ratio)
        assert grad_e_below > 0, f"∂score/∂E below optimal should be positive, got {grad_e_below}"

        # Above optimal extraction - gradient should be negative
        grad_e_above, _ = scorer.get_gradient(extraction=e_opt + 2, tds=t_opt, brew_ratio=brew_ratio)
        assert grad_e_above < 0, f"∂score/∂E above optimal should be negative, got {grad_e_above}"


class TestUnifiedBrewingScoreRealData:
    """Tests against expected scores from real brewing data in the plan"""

    def test_real_data_brew_32(self):
        """Brew #32: 18.22% extraction, 1.28% TDS, 60.8 g/L -> expect score ~58.5"""
        from src.models.unified_score import UnifiedBrewingScore

        scorer = UnifiedBrewingScore()
        score = scorer.calculate(extraction=18.22, tds=1.28, brew_ratio=60.8)

        # Allow reasonable tolerance since we're comparing to hand-calculated values
        assert 50 < score < 70, f"Brew #32 expected score ~58.5, got {score}"

    def test_real_data_brew_58(self):
        """Brew #58: 17.87% extraction, 1.32% TDS, 63.6 g/L -> expect score ~57.0"""
        from src.models.unified_score import UnifiedBrewingScore

        scorer = UnifiedBrewingScore()
        score = scorer.calculate(extraction=17.87, tds=1.32, brew_ratio=63.6)

        assert 45 < score < 70, f"Brew #58 expected score ~57.0, got {score}"

    def test_real_data_brew_56_extreme_tds(self):
        """Brew #56: 19.91% extraction, 1.66% TDS, 57.0 g/L -> expect low score ~7.0"""
        from src.models.unified_score import UnifiedBrewingScore

        scorer = UnifiedBrewingScore()
        score = scorer.calculate(extraction=19.91, tds=1.66, brew_ratio=57.0)

        # This brew had TDS way above optimal, should score very low
        assert score < 20, f"Brew #56 with extreme TDS expected low score, got {score}"

    def test_real_data_brew_41_under_weak(self):
        """Brew #41: 13.71% extraction, 1.00% TDS, 65.2 g/L -> expect low score ~13.5"""
        from src.models.unified_score import UnifiedBrewingScore

        scorer = UnifiedBrewingScore()
        score = scorer.calculate(extraction=13.71, tds=1.00, brew_ratio=65.2)

        # This brew was in Under-Weak zone, should score low
        assert score < 25, f"Brew #41 in Under-Weak expected low score, got {score}"


class TestUnifiedBrewingScoreEdgeCases:
    """Edge case tests for robustness"""

    def test_none_extraction_raises_error(self):
        """Should raise appropriate error for None extraction"""
        from src.models.unified_score import UnifiedBrewingScore

        scorer = UnifiedBrewingScore()

        with pytest.raises((TypeError, ValueError)):
            scorer.calculate(extraction=None, tds=1.25, brew_ratio=65.0)

    def test_none_tds_raises_error(self):
        """Should raise appropriate error for None TDS"""
        from src.models.unified_score import UnifiedBrewingScore

        scorer = UnifiedBrewingScore()

        with pytest.raises((TypeError, ValueError)):
            scorer.calculate(extraction=19.5, tds=None, brew_ratio=65.0)

    def test_none_brew_ratio_raises_error(self):
        """Should raise appropriate error for None brew ratio"""
        from src.models.unified_score import UnifiedBrewingScore

        scorer = UnifiedBrewingScore()

        with pytest.raises((TypeError, ValueError)):
            scorer.calculate(extraction=19.5, tds=1.25, brew_ratio=None)

    def test_zero_brew_ratio_handled(self):
        """Zero brew ratio should raise ValueError (division by zero prevention)"""
        from src.models.unified_score import UnifiedBrewingScore

        scorer = UnifiedBrewingScore()

        with pytest.raises((ValueError, ZeroDivisionError)):
            scorer.get_optimal_point(brew_ratio=0.0)

    def test_negative_brew_ratio_handled(self):
        """Negative brew ratio should raise ValueError"""
        from src.models.unified_score import UnifiedBrewingScore

        scorer = UnifiedBrewingScore()

        with pytest.raises(ValueError):
            scorer.get_optimal_point(brew_ratio=-50.0)

    def test_custom_parameters(self):
        """Should accept custom sigma and decay parameters"""
        from src.models.unified_score import UnifiedBrewingScore

        scorer = UnifiedBrewingScore(sigma_e=3.0, sigma_t=0.15, decay_k=0.3)

        # Should still work with custom parameters
        brew_ratio = 65.0
        e_opt, t_opt = scorer.get_optimal_point(brew_ratio=brew_ratio)
        score = scorer.calculate(extraction=e_opt, tds=t_opt, brew_ratio=brew_ratio)

        # Optimal point score should still be 100 regardless of parameters
        assert abs(score - 100.0) < 0.01, f"Score at optimal with custom params should be 100, got {score}"


class TestUnifiedBrewingScoreIntegration:
    """Integration tests for typical usage patterns"""

    def test_batch_calculation(self):
        """Should be able to calculate scores for a batch of data"""
        from src.models.unified_score import UnifiedBrewingScore

        scorer = UnifiedBrewingScore()

        # Simulate batch data: (extraction, tds, brew_ratio)
        batch_data = [
            (19.5, 1.27, 65.0),  # Near optimal for 65 g/L
            (18.0, 1.20, 60.0),  # Reasonable extraction
            (20.5, 1.30, 70.0),  # Higher TDS with higher ratio
            (16.0, 1.10, 68.0),  # Under-extracted
        ]

        scores = [scorer.calculate(e, t, r) for e, t, r in batch_data]

        assert len(scores) == len(batch_data)
        assert all(0 < s <= 100 for s in scores)

    def test_score_ranking_consistency(self):
        """Brews closer to their optimal should score higher"""
        from src.models.unified_score import UnifiedBrewingScore

        scorer = UnifiedBrewingScore()
        brew_ratio = 65.0
        e_opt, t_opt = scorer.get_optimal_point(brew_ratio=brew_ratio)

        # Create brews at increasing distance from optimal
        score_at_opt = scorer.calculate(e_opt, t_opt, brew_ratio)
        score_near = scorer.calculate(e_opt - 1, t_opt, brew_ratio)
        score_far = scorer.calculate(e_opt - 3, t_opt, brew_ratio)

        assert score_at_opt > score_near > score_far, \
            "Scores should rank by proximity to optimal"
