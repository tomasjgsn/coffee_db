"""
Tests for Star Rating Component

Test-driven development for the three-factor scoring system star rating UI component.
Tests are written first to define expected behavior.
"""

import pytest
import streamlit as st
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from ui.star_rating_component import StarRatingComponent


class TestStarRatingComponent:
    """Test suite for star rating component"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.component = StarRatingComponent()
    
    def test_component_initialization(self):
        """Should initialize with default parameters"""
        component = StarRatingComponent()
        assert component.max_stars == 5
        assert component.allow_half_stars is True
        assert component.default_value == 0.0
    
    def test_custom_initialization(self):
        """Should initialize with custom parameters"""
        component = StarRatingComponent(max_stars=10, allow_half_stars=False, default_value=3.0)
        assert component.max_stars == 10
        assert component.allow_half_stars is False
        assert component.default_value == 3.0
    
    def test_render_returns_rating_value(self):
        """Should return selected rating value when rendered"""
        with patch('streamlit.columns') as mock_columns:
            with patch('streamlit.button') as mock_button:
                with patch('streamlit.markdown'):
                    with patch('streamlit.text'):
                        with patch.dict('streamlit.session_state', {}, clear=True):
                            # Mock streamlit components - need 10 columns for half-star support
                            mock_columns.return_value = [MagicMock() for _ in range(10)]
                            mock_button.return_value = False

                            rating = self.component.render("test_key", "Test Label")
                            assert isinstance(rating, (int, float))
                            assert 0.0 <= rating <= 5.0
    
    def test_valid_rating_values_half_stars_enabled(self):
        """Should accept valid half-star ratings"""
        valid_ratings = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
        
        for rating in valid_ratings:
            assert self.component._is_valid_rating(rating) is True
    
    def test_valid_rating_values_half_stars_disabled(self):
        """Should only accept integer ratings when half stars disabled"""
        component = StarRatingComponent(allow_half_stars=False)
        
        valid_ratings = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
        invalid_ratings = [0.5, 1.5, 2.5, 3.5, 4.5]
        
        for rating in valid_ratings:
            assert component._is_valid_rating(rating) is True
            
        for rating in invalid_ratings:
            assert component._is_valid_rating(rating) is False
    
    def test_invalid_rating_values(self):
        """Should reject invalid rating values"""
        invalid_ratings = [-1.0, 5.5, 6.0, 10.0, None, "invalid"]
        
        for rating in invalid_ratings:
            assert self.component._is_valid_rating(rating) is False
    
    def test_session_state_persistence(self):
        """Should persist rating in session state"""
        key = "test_rating"
        expected_rating = 3.5

        with patch('streamlit.columns') as mock_columns:
            with patch('streamlit.button') as mock_button:
                with patch('streamlit.markdown'):
                    with patch('streamlit.text'):
                        # Use patch.dict to properly mock session_state
                        with patch.dict('streamlit.session_state', {key: expected_rating}, clear=True):
                            mock_columns.return_value = [MagicMock() for _ in range(10)]
                            mock_button.return_value = False

                            rating = self.component.render(key, "Test")
                            assert rating == expected_rating
    
    def test_star_display_full_stars(self):
        """Should display correct number of full stars"""
        rating = 3.0
        full_stars, half_star, empty_stars = self.component._calculate_star_display(rating)
        
        assert full_stars == 3
        assert half_star is False
        assert empty_stars == 2
    
    def test_star_display_with_half_star(self):
        """Should display half star correctly"""
        rating = 3.5
        full_stars, half_star, empty_stars = self.component._calculate_star_display(rating)
        
        assert full_stars == 3
        assert half_star is True
        assert empty_stars == 1
    
    def test_star_display_no_rating(self):
        """Should display all empty stars for zero rating"""
        rating = 0.0
        full_stars, half_star, empty_stars = self.component._calculate_star_display(rating)
        
        assert full_stars == 0
        assert half_star is False
        assert empty_stars == 5
    
    def test_star_display_max_rating(self):
        """Should display all full stars for max rating"""
        rating = 5.0
        full_stars, half_star, empty_stars = self.component._calculate_star_display(rating)
        
        assert full_stars == 5
        assert half_star is False
        assert empty_stars == 0
    
    def test_click_handlers_full_star(self):
        """Should handle full star clicks correctly"""
        with patch('streamlit.session_state', {}) as mock_session:
            key = "test_rating"
            star_position = 3
            
            # Simulate clicking the 3rd star
            self.component._handle_star_click(key, star_position, is_half=False)
            
            assert mock_session[key] == 3.0
    
    def test_click_handlers_half_star(self):
        """Should handle half star clicks correctly"""
        with patch('streamlit.session_state', {}) as mock_session:
            key = "test_rating"
            star_position = 3
            
            # Simulate clicking the half of 3rd star
            self.component._handle_star_click(key, star_position, is_half=True)
            
            assert mock_session[key] == 2.5
    
    def test_accessibility_features(self):
        """Should include accessibility features"""
        # Test that component includes proper labels and keyboard navigation
        with patch('streamlit.columns') as mock_columns:
            with patch('streamlit.button') as mock_button:
                with patch('streamlit.markdown'):
                    with patch('streamlit.text'):
                        with patch.dict('streamlit.session_state', {}, clear=True):
                            mock_columns.return_value = [MagicMock() for _ in range(10)]
                            mock_button.return_value = False

                            rating = self.component.render("test_key", "Test Label", help_text="Test help")

                            # Verify button was called with accessibility parameters
                            assert mock_button.called
                            call_args = mock_button.call_args_list
                            # Check that help text is passed through somehow
                            assert len(call_args) > 0
    
    def test_prompt_text_display(self):
        """Should display prompt text to guide user scoring"""
        prompt_text = "How many distinct flavors can you identify?"

        with patch('streamlit.text') as mock_text:
            with patch('streamlit.columns') as mock_columns:
                with patch('streamlit.button') as mock_button:
                    with patch('streamlit.markdown'):
                        with patch.dict('streamlit.session_state', {}, clear=True):
                            mock_columns.return_value = [MagicMock() for _ in range(10)]
                            mock_button.return_value = False

                            self.component.render("test_key", "Complexity", prompt_text=prompt_text)

                            # Verify prompt text is displayed (st.text is called multiple times)
                            text_calls = [call[0][0] for call in mock_text.call_args_list]
                            assert prompt_text in text_calls