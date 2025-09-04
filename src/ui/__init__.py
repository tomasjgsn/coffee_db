"""
UI package for coffee brewing application

Contains Streamlit UI components and abstractions.
"""

try:
    from .streamlit_components import StreamlitComponents
    _streamlit_available = True
except ImportError:
    _streamlit_available = False

from .star_rating_component import StarRatingComponent

__all__ = ['StarRatingComponent']
if _streamlit_available:
    __all__.append('StreamlitComponents')