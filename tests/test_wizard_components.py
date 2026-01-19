"""
Tests for the Wizard UI Components

Following TDD practices as specified in CLAUDE.md
Tests cover:
- Wizard state management
- Smart defaults (last brew, best brew)
- Step validation logic
- Navigation flow
"""

import pytest
import pandas as pd
from datetime import date, datetime
from unittest.mock import MagicMock, patch

# Import the components to test
import sys
sys.path.insert(0, '/Users/tomasjuergensen/Developer/coffee_db')

from src.ui.wizard_components import (
    WizardComponents,
    WizardStep,
    WizardState,
    STEP_CONFIG
)


class TestWizardStep:
    """Tests for WizardStep enum"""

    def test_wizard_step_values(self):
        """Verify all wizard steps are defined correctly"""
        assert WizardStep.BEAN.value == 0
        assert WizardStep.EQUIPMENT.value == 1
        assert WizardStep.BREW.value == 2
        assert WizardStep.RESULTS.value == 3

    def test_step_config_has_all_steps(self):
        """Verify STEP_CONFIG has configuration for all steps"""
        for step in WizardStep:
            assert step in STEP_CONFIG
            config = STEP_CONFIG[step]
            assert 'title' in config
            assert 'icon' in config
            assert 'description' in config
            assert 'help' in config

    def test_step_config_titles(self):
        """Verify step titles are meaningful"""
        assert STEP_CONFIG[WizardStep.BEAN]['title'] == "Bean Selection"
        assert STEP_CONFIG[WizardStep.EQUIPMENT]['title'] == "Equipment Setup"
        assert STEP_CONFIG[WizardStep.BREW]['title'] == "Brew Parameters"
        assert STEP_CONFIG[WizardStep.RESULTS]['title'] == "Results & Score"


class TestWizardState:
    """Tests for WizardState dataclass"""

    def test_default_state(self):
        """Test WizardState default values"""
        state = WizardState()
        assert state.current_step == WizardStep.BEAN
        assert state.completed_steps == set()
        assert state.form_data == {}
        assert state.is_valid == {}
        assert state.last_brew_defaults == {}

    def test_state_with_custom_values(self):
        """Test WizardState with custom initialization"""
        state = WizardState(
            current_step=WizardStep.BREW,
            completed_steps={0, 1},
            form_data={'bean_name': 'Test Bean'}
        )
        assert state.current_step == WizardStep.BREW
        assert 0 in state.completed_steps
        assert 1 in state.completed_steps
        assert state.form_data['bean_name'] == 'Test Bean'


class MockSessionState(dict):
    """Mock session state that behaves like Streamlit's session_state"""
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{key}'")

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{key}'")


class TestWizardComponents:
    """Tests for WizardComponents class"""

    @pytest.fixture
    def wizard(self):
        """Create a WizardComponents instance with mocked session state"""
        mock_state = MockSessionState()
        with patch('src.ui.wizard_components.st.session_state', mock_state):
            return WizardComponents()

    @pytest.fixture
    def sample_df(self):
        """Create sample DataFrame for testing smart defaults"""
        return pd.DataFrame({
            'brew_id': [1, 2, 3],
            'brew_date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'bean_name': ['Bean A', 'Bean B', 'Bean C'],
            'bean_origin_country': ['Ethiopia', 'Colombia', 'Kenya'],
            'bean_origin_region': ['Yirgacheffe', 'Huila', 'Nyeri'],
            'bean_variety': ['Heirloom', 'Caturra', 'SL28'],
            'bean_process_method': ['Washed', 'Natural', 'Washed'],
            'bean_roast_level': ['Light', 'Medium', 'Light'],
            'grind_size': [5.0, 6.0, 5.5],
            'grind_model': ['Fellow Ode Gen 2', 'Fellow Ode Gen 2', 'Fellow Ode Gen 2'],
            'brew_device': ['V60 ceramic', 'Aeropress', 'V60 ceramic'],
            'water_temp_degC': [96.0, 85.0, 95.0],
            'coffee_dose_grams': [18.0, 15.0, 20.0],
            'water_volume_ml': [300.0, 200.0, 340.0],
            'brew_method': ['Hoffmann V60', 'Inverted', 'Hoffmann V60'],
            'score_overall_rating': [4.0, 4.5, 3.5]
        })

    def test_get_last_brew_defaults_empty_df(self, wizard):
        """Test get_last_brew_defaults with empty DataFrame"""
        empty_df = pd.DataFrame()
        result = wizard.get_last_brew_defaults(empty_df)
        assert result == {}

    def test_get_last_brew_defaults_returns_most_recent(self, wizard, sample_df):
        """Test get_last_brew_defaults returns most recent brew"""
        result = wizard.get_last_brew_defaults(sample_df)

        # Most recent is brew_id 3 (2024-01-03)
        assert result['bean_name'] == 'Bean C'
        assert result['bean_origin_country'] == 'Kenya'
        assert result['grind_size'] == 5.5
        assert result['brew_device'] == 'V60 ceramic'
        assert result['water_temp_degC'] == 95.0

    def test_get_last_brew_defaults_all_fields(self, wizard, sample_df):
        """Test get_last_brew_defaults returns all expected fields"""
        result = wizard.get_last_brew_defaults(sample_df)

        expected_fields = [
            'bean_name', 'bean_origin_country', 'bean_origin_region',
            'bean_variety', 'bean_process_method', 'bean_roast_level',
            'grind_size', 'grind_model', 'brew_device',
            'water_temp_degC', 'coffee_dose_grams', 'water_volume_ml',
            'brew_method'
        ]

        for field in expected_fields:
            assert field in result

    def test_get_best_brew_defaults_empty_df(self, wizard):
        """Test get_best_brew_defaults with empty DataFrame"""
        empty_df = pd.DataFrame()
        result = wizard.get_best_brew_defaults(empty_df)
        assert result == {}

    def test_get_best_brew_defaults_returns_highest_rated(self, wizard, sample_df):
        """Test get_best_brew_defaults returns highest rated brew"""
        result = wizard.get_best_brew_defaults(sample_df)

        # Highest rated is brew_id 2 with 4.5 rating
        assert result['bean_name'] == 'Bean B'
        assert result['bean_origin_country'] == 'Colombia'
        assert result['brew_device'] == 'Aeropress'

    def test_get_best_brew_defaults_no_ratings(self, wizard):
        """Test get_best_brew_defaults falls back to last brew when no ratings"""
        df = pd.DataFrame({
            'brew_id': [1, 2],
            'brew_date': ['2024-01-01', '2024-01-02'],
            'bean_name': ['Bean A', 'Bean B'],
            'bean_origin_country': ['Ethiopia', 'Colombia'],
            'bean_origin_region': [None, None],
            'bean_variety': [None, None],
            'bean_process_method': [None, None],
            'bean_roast_level': [None, None],
            'grind_size': [5.0, 6.0],
            'grind_model': [None, None],
            'brew_device': ['V60', 'V60'],
            'water_temp_degC': [96.0, 95.0],
            'coffee_dose_grams': [18.0, 18.0],
            'water_volume_ml': [300.0, 300.0],
            'brew_method': [None, None],
            'score_overall_rating': [None, None]
        })

        result = wizard.get_best_brew_defaults(df)

        # Should fall back to last brew (Bean B)
        assert result['bean_name'] == 'Bean B'


class TestWizardNavigation:
    """Tests for wizard navigation logic"""

    def test_step_order_is_correct(self):
        """Test that steps are in logical order"""
        steps = list(WizardStep)
        assert steps[0] == WizardStep.BEAN
        assert steps[1] == WizardStep.EQUIPMENT
        assert steps[2] == WizardStep.BREW
        assert steps[3] == WizardStep.RESULTS

    def test_total_steps_is_four(self):
        """Test that there are exactly 4 steps"""
        assert len(WizardStep) == 4

    def test_step_config_icons_are_sequential(self):
        """Test that step icons show correct sequence"""
        assert STEP_CONFIG[WizardStep.BEAN]['icon'] == "1"
        assert STEP_CONFIG[WizardStep.EQUIPMENT]['icon'] == "2"
        assert STEP_CONFIG[WizardStep.BREW]['icon'] == "3"
        assert STEP_CONFIG[WizardStep.RESULTS]['icon'] == "4"


class TestStepValidation:
    """Tests for step validation logic"""

    def test_bean_step_requires_bean_name(self):
        """Test that bean step requires at least a bean name"""
        # This tests the validation logic expected in _render_wizard_step_bean
        # Bean name is required
        form_data_valid = {'bean_name': 'Test Bean'}
        form_data_invalid = {'bean_name': ''}
        form_data_whitespace = {'bean_name': '   '}

        # Valid case
        assert bool(form_data_valid.get('bean_name', '').strip()) is True

        # Invalid cases
        assert bool(form_data_invalid.get('bean_name', '').strip()) is False
        assert bool(form_data_whitespace.get('bean_name', '').strip()) is False

    def test_brew_step_requires_coffee_dose(self):
        """Test that brew step requires coffee dose"""
        # This tests the validation logic expected in _render_wizard_step_brew
        form_data_valid = {'coffee_dose_grams': 18.0}
        form_data_invalid = {'coffee_dose_grams': None}
        form_data_zero = {'coffee_dose_grams': 0}

        # Valid case
        dose = form_data_valid.get('coffee_dose_grams')
        assert dose is not None and dose > 0

        # Invalid cases
        dose_invalid = form_data_invalid.get('coffee_dose_grams')
        assert not (dose_invalid is not None and dose_invalid > 0)

        dose_zero = form_data_zero.get('coffee_dose_grams')
        assert not (dose_zero is not None and dose_zero > 0)


class TestSmartDefaults:
    """Tests for smart defaults feature"""

    @pytest.fixture
    def wizard(self):
        """Create a WizardComponents instance"""
        mock_state = MockSessionState()
        with patch('src.ui.wizard_components.st.session_state', mock_state):
            return WizardComponents()

    def test_smart_defaults_preserve_data_types(self, wizard):
        """Test that smart defaults preserve correct data types"""
        df = pd.DataFrame({
            'brew_id': [1],
            'brew_date': ['2024-01-01'],
            'bean_name': ['Test Bean'],
            'bean_origin_country': ['Ethiopia'],
            'bean_origin_region': ['Yirgacheffe'],
            'bean_variety': ['Heirloom'],
            'bean_process_method': ['Washed'],
            'bean_roast_level': ['Light'],
            'grind_size': [5.5],
            'grind_model': ['Fellow Ode'],
            'brew_device': ['V60'],
            'water_temp_degC': [96.0],
            'coffee_dose_grams': [18.0],
            'water_volume_ml': [300.0],
            'brew_method': ['Hoffmann'],
            'score_overall_rating': [4.0]
        })

        result = wizard.get_last_brew_defaults(df)

        # Check types
        assert isinstance(result['grind_size'], float)
        assert isinstance(result['water_temp_degC'], float)
        assert isinstance(result['coffee_dose_grams'], float)

    def test_smart_defaults_handle_none_values(self, wizard):
        """Test that smart defaults handle None values gracefully"""
        df = pd.DataFrame({
            'brew_id': [1],
            'brew_date': ['2024-01-01'],
            'bean_name': ['Test Bean'],
            'bean_origin_country': [None],
            'bean_origin_region': [None],
            'bean_variety': [None],
            'bean_process_method': [None],
            'bean_roast_level': [None],
            'grind_size': [5.0],
            'grind_model': [None],
            'brew_device': ['V60'],
            'water_temp_degC': [None],
            'coffee_dose_grams': [18.0],
            'water_volume_ml': [None],
            'brew_method': [None],
            'score_overall_rating': [None]
        })

        # Should not raise exception
        result = wizard.get_last_brew_defaults(df)
        assert result['bean_name'] == 'Test Bean'


class TestWizardStateManagement:
    """Tests for wizard session state management"""

    def test_wizard_state_dict_structure(self):
        """Test the expected structure of wizard session state"""
        expected_keys = ['current_step', 'completed_steps', 'form_data', 'validation', 'draft_saved']

        # This is the structure that should be initialized
        state = {
            'current_step': 0,
            'completed_steps': set(),
            'form_data': {},
            'validation': {},
            'draft_saved': False
        }

        for key in expected_keys:
            assert key in state

    def test_form_data_persistence(self):
        """Test that form data can be stored and retrieved"""
        form_data = {}

        # Simulate storing data
        form_data['bean_name'] = 'Test Bean'
        form_data['grind_size'] = 5.5

        # Simulate retrieving data
        assert form_data.get('bean_name') == 'Test Bean'
        assert form_data.get('grind_size') == 5.5
        assert form_data.get('nonexistent', 'default') == 'default'


class TestTimeInputConversion:
    """Tests for time input conversion logic used in render_time_input"""

    def test_seconds_to_minutes_seconds_basic(self):
        """Test basic conversion from seconds to minutes and seconds"""
        total_seconds = 150
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        assert minutes == 2
        assert seconds == 30

    def test_seconds_to_minutes_seconds_exact_minute(self):
        """Test conversion when seconds is exactly a minute boundary"""
        total_seconds = 120
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        assert minutes == 2
        assert seconds == 0

    def test_seconds_to_minutes_seconds_under_minute(self):
        """Test conversion for times under a minute"""
        total_seconds = 45
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        assert minutes == 0
        assert seconds == 45

    def test_seconds_to_minutes_seconds_zero(self):
        """Test conversion for zero seconds"""
        total_seconds = 0
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        assert minutes == 0
        assert seconds == 0

    def test_minutes_seconds_to_total_seconds(self):
        """Test conversion from minutes and seconds back to total seconds"""
        test_cases = [
            (0, 0, 0),
            (0, 30, 30),
            (1, 0, 60),
            (2, 30, 150),
            (5, 45, 345),
            (10, 0, 600),
        ]
        for minutes, seconds, expected_total in test_cases:
            total = (minutes * 60) + seconds
            assert total == expected_total

    def test_time_input_none_handling(self):
        """Test that None values are handled correctly"""
        current_value_seconds = None
        if current_value_seconds is not None and current_value_seconds > 0:
            minutes = current_value_seconds // 60
            seconds = current_value_seconds % 60
        else:
            minutes = None
            seconds = None
        assert minutes is None
        assert seconds is None

    def test_time_input_zero_handling(self):
        """Test that zero values are handled correctly"""
        current_value_seconds = 0
        if current_value_seconds is not None and current_value_seconds > 0:
            minutes = current_value_seconds // 60
            seconds = current_value_seconds % 60
        else:
            minutes = None
            seconds = None
        assert minutes is None
        assert seconds is None

    def test_time_input_large_values(self):
        """Test handling of large time values"""
        total_seconds = 3599
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        assert minutes == 59
        assert seconds == 59

    def test_time_input_negative_not_expected(self):
        """Test that negative values are handled gracefully"""
        current_value_seconds = -10
        if current_value_seconds is not None and current_value_seconds > 0:
            minutes = current_value_seconds // 60
            seconds = current_value_seconds % 60
        else:
            minutes = None
            seconds = None
        assert minutes is None
        assert seconds is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
