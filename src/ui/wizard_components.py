"""
Modern Multi-Step Wizard Components for Coffee Brewing App

Implements 2025 UX best practices:
- Progressive disclosure with visual stepper
- Smart defaults from previous brews
- One-section-at-a-time focus
- Real-time validation feedback
- Mobile-friendly design patterns

References:
- NN/g Progressive Disclosure patterns
- Carbon Design System form patterns
- Streamlit wizard pattern (session state based)
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum


class WizardStep(Enum):
    """Wizard step identifiers"""
    BEAN = 0
    EQUIPMENT = 1
    BREW = 2
    RESULTS = 3


@dataclass
class WizardState:
    """State container for the wizard form"""
    current_step: WizardStep = WizardStep.BEAN
    completed_steps: set = field(default_factory=set)
    form_data: Dict[str, Any] = field(default_factory=dict)
    is_valid: Dict[str, bool] = field(default_factory=dict)
    last_brew_defaults: Dict[str, Any] = field(default_factory=dict)


STEP_CONFIG = {
    WizardStep.BEAN: {
        "title": "Bean Selection",
        "icon": "1",
        "description": "Choose your coffee",
        "help": "Select an existing bean or create a new one"
    },
    WizardStep.EQUIPMENT: {
        "title": "Equipment Setup",
        "icon": "2",
        "description": "Set up your gear",
        "help": "Configure your grinder and brewing device"
    },
    WizardStep.BREW: {
        "title": "Brew Parameters",
        "icon": "3",
        "description": "Dial in your brew",
        "help": "Water temp, dose, and method-specific settings"
    },
    WizardStep.RESULTS: {
        "title": "Results & Score",
        "icon": "4",
        "description": "Rate your cup",
        "help": "Record TDS, taste, and notes"
    }
}


class WizardComponents:
    """Modern wizard UI components for the Add Cup flow"""

    def __init__(self):
        self._init_session_state()

    def _init_session_state(self):
        """Initialize wizard session state"""
        if 'wizard_state' not in st.session_state:
            st.session_state.wizard_state = {
                'current_step': 0,
                'completed_steps': set(),
                'form_data': {},
                'validation': {},
                'draft_saved': False
            }

    def get_wizard_state(self) -> Dict:
        """Get current wizard state"""
        return st.session_state.wizard_state

    def set_step(self, step_index: int):
        """Set current wizard step"""
        st.session_state.wizard_state['current_step'] = step_index

    def mark_step_complete(self, step_index: int):
        """Mark a step as completed"""
        st.session_state.wizard_state['completed_steps'].add(step_index)

    def save_form_data(self, key: str, value: Any):
        """Save data to wizard form state"""
        st.session_state.wizard_state['form_data'][key] = value

    def get_form_data(self, key: str, default: Any = None) -> Any:
        """Get data from wizard form state"""
        return st.session_state.wizard_state['form_data'].get(key, default)

    def render_progress_stepper(self, current_step: int) -> None:
        """
        Render a modern horizontal progress stepper using Streamlit native components

        Based on Carbon Design System and Material Design patterns
        """
        steps = list(STEP_CONFIG.values())
        completed = st.session_state.get('wizard_completed_steps', set())

        # Use native Streamlit columns for the stepper
        cols = st.columns(len(steps))

        for i, (col, step) in enumerate(zip(cols, steps)):
            with col:
                # Determine step status
                if i < current_step or i in completed:
                    # Completed step
                    st.markdown(
                        f"<div style='text-align: center;'>"
                        f"<div style='width: 40px; height: 40px; border-radius: 50%; "
                        f"background: #4CAF50; color: white; display: inline-flex; "
                        f"align-items: center; justify-content: center; font-weight: bold; "
                        f"font-size: 16px; margin-bottom: 8px;'>✓</div>"
                        f"<div style='font-size: 12px; color: #666;'>{step['title']}</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                elif i == current_step:
                    # Active step
                    st.markdown(
                        f"<div style='text-align: center;'>"
                        f"<div style='width: 44px; height: 44px; border-radius: 50%; "
                        f"background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); "
                        f"color: white; display: inline-flex; align-items: center; "
                        f"justify-content: center; font-weight: bold; font-size: 18px; "
                        f"margin-bottom: 8px; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);'>"
                        f"{step['icon']}</div>"
                        f"<div style='font-size: 12px; color: #667eea; font-weight: 600;'>"
                        f"{step['title']}</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                else:
                    # Pending step
                    st.markdown(
                        f"<div style='text-align: center;'>"
                        f"<div style='width: 40px; height: 40px; border-radius: 50%; "
                        f"background: #e0e0e0; color: #666; display: inline-flex; "
                        f"align-items: center; justify-content: center; font-weight: bold; "
                        f"font-size: 16px; margin-bottom: 8px;'>{step['icon']}</div>"
                        f"<div style='font-size: 12px; color: #999;'>{step['title']}</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

        # Add a progress bar below
        progress_value = current_step / (len(steps) - 1) if len(steps) > 1 else 0
        st.progress(progress_value)

    def render_step_header(self, step: WizardStep) -> None:
        """Render the header for current step"""
        config = STEP_CONFIG[step]

        # Use native Streamlit components for better compatibility
        st.subheader(f"Step {step.value + 1}: {config['title']}")
        st.caption(config['help'])

    def render_navigation_buttons(self, current_step: int, total_steps: int = 4,
                                   can_proceed: bool = True,
                                   is_final: bool = False) -> Tuple[bool, bool, bool]:
        """
        Render wizard navigation buttons

        Returns: (go_back, go_next, submit) tuple
        """
        st.markdown("---")

        col1, col2, col3 = st.columns([1, 2, 1])

        go_back = False
        go_next = False
        submit = False

        with col1:
            if current_step > 0:
                if st.button("← Back", use_container_width=True, key="wizard_back"):
                    go_back = True

        with col2:
            # Progress text
            st.markdown(f"""
            <div style="text-align: center; color: #666; padding: 8px 0;">
                Step {current_step + 1} of {total_steps}
            </div>
            """, unsafe_allow_html=True)

        with col3:
            if is_final:
                if st.button("☕ Add Cup", type="primary", use_container_width=True,
                            disabled=not can_proceed, key="wizard_submit"):
                    submit = True
            else:
                if st.button("Next →", type="primary", use_container_width=True,
                            disabled=not can_proceed, key="wizard_next"):
                    go_next = True

        return go_back, go_next, submit

    def render_quick_actions_bar(self, df: pd.DataFrame) -> Optional[str]:
        """
        Render quick action buttons for smart defaults

        Returns: Action taken or None
        """
        if df.empty:
            return None

        st.markdown("### Quick Start")

        col1, col2, col3 = st.columns(3)

        action = None

        with col1:
            if st.button("📋 Repeat Last Brew", use_container_width=True,
                        help="Use the same settings as your last brew"):
                action = "repeat_last"

        with col2:
            if st.button("⭐ Use Best Rated", use_container_width=True,
                        help="Use settings from your highest-rated brew"):
                action = "use_best"

        with col3:
            if st.button("🆕 Start Fresh", use_container_width=True,
                        help="Begin with default values"):
                action = "fresh"

        return action

    def get_last_brew_defaults(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get default values from the most recent brew"""
        if df.empty:
            return {}

        # Get most recent brew
        df_sorted = df.sort_values('brew_date', ascending=False)
        last_brew = df_sorted.iloc[0]

        return {
            'bean_name': last_brew.get('bean_name'),
            'bean_origin_country': last_brew.get('bean_origin_country'),
            'bean_origin_region': last_brew.get('bean_origin_region'),
            'bean_variety': last_brew.get('bean_variety'),
            'bean_process_method': last_brew.get('bean_process_method'),
            'bean_roast_level': last_brew.get('bean_roast_level'),
            'grind_size': last_brew.get('grind_size'),
            'grind_model': last_brew.get('grind_model'),
            'brew_device': last_brew.get('brew_device'),
            'water_temp_degC': last_brew.get('water_temp_degC'),
            'coffee_dose_grams': last_brew.get('coffee_dose_grams'),
            'water_volume_ml': last_brew.get('water_volume_ml'),
            'brew_method': last_brew.get('brew_method'),
        }

    def get_best_brew_defaults(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get default values from the highest-rated brew"""
        if df.empty:
            return {}

        # Get highest rated brew
        df_rated = df[df['score_overall_rating'].notna()]
        if df_rated.empty:
            return self.get_last_brew_defaults(df)

        best_brew = df_rated.loc[df_rated['score_overall_rating'].idxmax()]

        return {
            'bean_name': best_brew.get('bean_name'),
            'bean_origin_country': best_brew.get('bean_origin_country'),
            'bean_origin_region': best_brew.get('bean_origin_region'),
            'bean_variety': best_brew.get('bean_variety'),
            'bean_process_method': best_brew.get('bean_process_method'),
            'bean_roast_level': best_brew.get('bean_roast_level'),
            'grind_size': best_brew.get('grind_size'),
            'grind_model': best_brew.get('grind_model'),
            'brew_device': best_brew.get('brew_device'),
            'water_temp_degC': best_brew.get('water_temp_degC'),
            'coffee_dose_grams': best_brew.get('coffee_dose_grams'),
            'water_volume_ml': best_brew.get('water_volume_ml'),
            'brew_method': best_brew.get('brew_method'),
        }

    def render_validation_feedback(self, field_name: str, is_valid: bool,
                                    message: str = "") -> None:
        """Render inline validation feedback"""
        if is_valid:
            st.markdown(f"""
            <div style="color: #4CAF50; font-size: 12px; margin-top: -10px; margin-bottom: 10px;">
                ✓ {message if message else 'Looks good!'}
            </div>
            """, unsafe_allow_html=True)
        elif message:
            st.markdown(f"""
            <div style="color: #f44336; font-size: 12px; margin-top: -10px; margin-bottom: 10px;">
                ⚠ {message}
            </div>
            """, unsafe_allow_html=True)

    def render_smart_suggestion(self, suggestion_type: str, value: Any,
                                 context: str = "") -> bool:
        """
        Render a smart suggestion chip that user can accept

        Returns: True if suggestion was accepted
        """
        accepted = False

        suggestion_html = f"""
        <div style="
            display: inline-block;
            background: #e3f2fd;
            border: 1px solid #2196F3;
            border-radius: 20px;
            padding: 4px 12px;
            font-size: 12px;
            color: #1976D2;
            margin: 4px 0;
        ">
            💡 {context}: <strong>{value}</strong>
        </div>
        """
        st.markdown(suggestion_html, unsafe_allow_html=True)

        if st.button(f"Use {value}", key=f"accept_{suggestion_type}_{value}"):
            accepted = True

        return accepted

    def render_step_summary_card(self, step_name: str, data: Dict[str, Any]) -> None:
        """Render a summary card showing completed step data"""

        # Filter out None/empty values
        display_data = {k: v for k, v in data.items() if v is not None and v != ''}

        if not display_data:
            return

        items_html = ""
        for key, value in display_data.items():
            # Format key for display
            display_key = key.replace('_', ' ').replace('bean ', '').title()
            items_html += f"<li><strong>{display_key}:</strong> {value}</li>"

        st.markdown(f"""
        <div style="
            background: #f8f9fa;
            border-left: 4px solid #4CAF50;
            padding: 12px 16px;
            margin: 8px 0;
            border-radius: 0 8px 8px 0;
        ">
            <div style="font-weight: 600; color: #333; margin-bottom: 8px;">
                ✓ {step_name}
            </div>
            <ul style="margin: 0; padding-left: 20px; color: #666; font-size: 13px;">
                {items_html}
            </ul>
        </div>
        """, unsafe_allow_html=True)

    def render_compact_review(self) -> None:
        """Render a compact review of all entered data before submission"""
        form_data = st.session_state.wizard_state.get('form_data', {})

        if not form_data:
            st.info("No data entered yet")
            return

        st.markdown("### Review Your Brew")

        # Group data by category
        categories = {
            'Bean': ['bean_name', 'bean_origin_country', 'bean_origin_region',
                    'bean_variety', 'bean_process_method', 'bean_roast_level', 'bean_roast_date'],
            'Equipment': ['grind_size', 'grind_model', 'brew_device'],
            'Brew': ['water_temp_degC', 'coffee_dose_grams', 'water_volume_ml',
                    'brew_method', 'brew_total_time_s'],
            'Scores': ['final_tds_percent', 'score_complexity', 'score_bitterness',
                      'score_mouthfeel', 'score_flavor_profile_category', 'score_notes']
        }

        cols = st.columns(2)
        col_idx = 0

        for category, fields in categories.items():
            category_data = {f: form_data.get(f) for f in fields if form_data.get(f)}
            if category_data:
                with cols[col_idx % 2]:
                    self.render_step_summary_card(category, category_data)
                col_idx += 1

    def reset_wizard(self):
        """Reset wizard to initial state"""
        st.session_state.wizard_state = {
            'current_step': 0,
            'completed_steps': set(),
            'form_data': {},
            'validation': {},
            'draft_saved': False
        }
