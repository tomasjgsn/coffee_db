"""
Star Rating Component for Three-Factor Coffee Scoring

Interactive star rating component with half-star support for Streamlit.
Implements the UI for complexity, bitterness, and mouthfeel scoring.
"""

import streamlit as st
from typing import Optional


class StarRatingComponent:
    """Interactive star rating component with half-star support"""
    
    def __init__(self, max_stars: int = 5, allow_half_stars: bool = True, default_value: float = 0.0):
        """
        Initialize star rating component
        
        Args:
            max_stars: Maximum number of stars (default: 5)
            allow_half_stars: Whether to allow half-star ratings (default: True)
            default_value: Default rating value (default: 0.0)
        """
        self.max_stars = max_stars
        self.allow_half_stars = allow_half_stars
        self.default_value = default_value
    
    def render(self, key: str, label: str, prompt_text: Optional[str] = None, help_text: Optional[str] = None) -> float:
        """
        Render the star rating component
        
        Args:
            key: Unique key for this component instance
            label: Label to display above the stars
            prompt_text: Guidance text for user scoring
            help_text: Additional help text (for accessibility)
            
        Returns:
            Current rating value (0.0 to max_stars)
        """
        # Display label and prompt
        st.markdown(f"**{label}**")
        if prompt_text:
            st.text(prompt_text)
        
        # Initialize session state if not exists
        if key not in st.session_state:
            st.session_state[key] = self.default_value
        
        current_rating = st.session_state[key]
        
        # Create columns for star display
        cols = st.columns(self.max_stars * 2 if self.allow_half_stars else self.max_stars)
        
        # Render stars
        for star_pos in range(1, self.max_stars + 1):
            if self.allow_half_stars:
                # Half star button
                col_idx = (star_pos - 1) * 2
                with cols[col_idx]:
                    half_star_key = f"{key}_half_{star_pos}"
                    if st.button("⭐", key=half_star_key, help=f"Rate {star_pos - 0.5} stars"):
                        self._handle_star_click(key, star_pos, is_half=True)
                
                # Full star button  
                col_idx = (star_pos - 1) * 2 + 1
                with cols[col_idx]:
                    full_star_key = f"{key}_full_{star_pos}"
                    if st.button("⭐", key=full_star_key, help=f"Rate {star_pos} stars"):
                        self._handle_star_click(key, star_pos, is_half=False)
            else:
                # Full star only
                with cols[star_pos - 1]:
                    star_key = f"{key}_star_{star_pos}"
                    if st.button("⭐", key=star_key, help=f"Rate {star_pos} stars"):
                        self._handle_star_click(key, star_pos, is_half=False)
        
        # Display current rating
        full_stars, half_star, empty_stars = self._calculate_star_display(current_rating)
        display_stars = "★" * full_stars + ("☆" if half_star else "") + "☆" * empty_stars
        st.text(f"Rating: {display_stars} ({current_rating}/5)")
        
        return current_rating
    
    def _handle_star_click(self, key: str, star_position: int, is_half: bool) -> None:
        """Handle star click events"""
        if is_half:
            new_rating = star_position - 0.5
        else:
            new_rating = float(star_position)
        
        if self._is_valid_rating(new_rating):
            st.session_state[key] = new_rating
    
    def _is_valid_rating(self, rating) -> bool:
        """Validate if rating is within acceptable range and increment"""
        if rating is None or not isinstance(rating, (int, float)):
            return False
        
        if rating < 0.0 or rating > self.max_stars:
            return False
        
        if not self.allow_half_stars:
            # Only allow integer values
            return rating == int(rating)
        else:
            # Allow half increments (0.5, 1.0, 1.5, etc.)
            return (rating * 2) == int(rating * 2)
    
    def _calculate_star_display(self, rating: float) -> tuple[int, bool, int]:
        """
        Calculate star display components
        
        Returns:
            (full_stars, has_half_star, empty_stars)
        """
        if rating < 0:
            rating = 0
        elif rating > self.max_stars:
            rating = self.max_stars
        
        full_stars = int(rating)
        has_half_star = (rating - full_stars) >= 0.5
        
        if has_half_star:
            empty_stars = self.max_stars - full_stars - 1
        else:
            empty_stars = self.max_stars - full_stars
        
        return full_stars, has_half_star, empty_stars