"""Main Streamlit application for D&D Loot Creator and Encounter Tracker."""

import streamlit as st

from loot_creator.ui import render_loot_creator
from encounter_tracker.ui import render_encounter_tracker


def render_sidebar():
    """Render the sidebar with API key configuration."""
    with st.sidebar:
        st.header("Settings")

        # API Key input
        st.subheader("Gemini API Key")
        st.caption("Enter your own Gemini API key to use the Loot Creator.")

        # Initialize session state for API key
        if "user_api_key" not in st.session_state:
            st.session_state.user_api_key = ""

        api_key = st.text_input(
            "API Key",
            value=st.session_state.user_api_key,
            type="password",
            placeholder="Enter your Gemini API key",
            help="Get your API key from https://aistudio.google.com/apikey"
        )

        # Update session state
        if api_key != st.session_state.user_api_key:
            st.session_state.user_api_key = api_key

        # Show status
        if st.session_state.user_api_key:
            st.success("API key configured")
        else:
            st.warning("No API key - Loot Creator won't work")

        st.markdown("---")
        st.markdown("[Get API Key](https://aistudio.google.com/apikey)")
        st.caption("Your API key is stored only in your browser session and is never saved to any server.")


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="D&D Loot & Encounter Manager",
        page_icon="🎲",
        layout="wide",
    )

    # Render sidebar with settings
    render_sidebar()

    st.title("🎲 D&D Loot Creator & Encounter Tracker")

    # Create tabs for the two main features
    tab1, tab2 = st.tabs(["⚔️ Loot Creator", "🛡️ Encounter Tracker"])

    with tab1:
        render_loot_creator()

    with tab2:
        render_encounter_tracker()


if __name__ == "__main__":
    main()
