"""Main Streamlit application for D&D Loot Creator and Encounter Tracker."""

import streamlit as st

import config
from loot_creator.ui import render_loot_creator
from encounter_tracker.ui import render_encounter_tracker
from monster_generator.ui import render_monster_generator


# ---------------------------------------------------------------------------
# OpenRouter API key
# ---------------------------------------------------------------------------

def _get_api_key() -> str:
    """Load OpenRouter API key from st.secrets, falling back to .env."""
    try:
        return st.secrets["OPENROUTER_API_KEY"]
    except (KeyError, FileNotFoundError):
        return config.OPENROUTER_API_KEY or ""


# ---------------------------------------------------------------------------
# Patreon OAuth
# ---------------------------------------------------------------------------

def _get_patreon_config() -> tuple[str, str, str, str] | None:
    """Return (client_id, client_secret, campaign_id, redirect_uri) or None.

    Returns None when any key is missing or empty — this puts the app into
    dev mode where all features are accessible without authentication.
    """
    try:
        cfg = (
            st.secrets["PATREON_CLIENT_ID"],
            st.secrets["PATREON_CLIENT_SECRET"],
            st.secrets["PATREON_CAMPAIGN_ID"],
            st.secrets["PATREON_REDIRECT_URI"],
        )
        # All four values must be non-empty strings
        if all(cfg):
            return cfg
        return None
    except (KeyError, FileNotFoundError):
        return None


def _handle_patreon_callback() -> None:
    """Process a Patreon OAuth callback code from the URL query params.

    Runs at the very top of main() so the code is consumed before anything
    else renders. Uses a session-state flag to prevent re-processing on
    Streamlit reruns triggered by st.query_params.clear().
    """
    if st.session_state.get("patreon_processed"):
        return

    code = st.query_params.get("code")
    if not code:
        return

    cfg = _get_patreon_config()
    if not cfg:
        return

    client_id, client_secret, campaign_id, redirect_uri = cfg
    st.session_state.patreon_processed = True  # set before any rerun

    try:
        from auth.patreon import exchange_code, is_active_patron
        token = exchange_code(code, client_id, client_secret, redirect_uri)
        patron = is_active_patron(token, campaign_id)
        st.session_state.is_patron = patron
        st.query_params.clear()  # removes ?code=... from the URL → triggers rerun
    except Exception as e:
        st.session_state.is_patron = False
        st.query_params.clear()
        st.error(f"Patreon login failed: {e}")


def _render_auth_sidebar(cfg: tuple | None) -> None:
    """Render the Patreon login widget in the sidebar.

    Does nothing when Patreon is not configured (dev mode).
    """
    if cfg is None:
        return

    client_id, _, _, redirect_uri = cfg

    with st.sidebar:
        st.divider()
        if st.session_state.get("is_patron"):
            st.success("Patron access active")
            if st.button("Log out", key="patreon_logout"):
                st.session_state.is_patron = False
                st.session_state.patreon_processed = False
                st.rerun()
        else:
            st.info("AI features require a Patreon subscription.")
            from auth.patreon import build_auth_url
            auth_url = build_auth_url(client_id, redirect_uri)
            # target="_self" keeps navigation in the same tab so the OAuth
            # redirect lands back on this Streamlit app correctly.
            st.markdown(
                f"""<a href="{auth_url}" target="_self" style="
                    display:inline-block;padding:8px 16px;
                    background:#f96854;color:#fff;border-radius:6px;
                    font-weight:600;text-decoration:none;font-size:14px;">
                    Login with Patreon
                </a>""",
                unsafe_allow_html=True,
            )


def _render_patron_wall(feature_name: str, cfg: tuple) -> None:
    """Show a lock screen in place of a gated feature tab."""
    client_id, _, _, redirect_uri = cfg
    from auth.patreon import build_auth_url
    auth_url = build_auth_url(client_id, redirect_uri)

    st.markdown(
        f"""<div style="text-align:center;padding:60px 20px;">
            <div style="font-size:56px;">🔒</div>
            <h2 style="margin:16px 0 8px 0;">{feature_name}</h2>
            <p style="color:#666;margin-bottom:24px;">
                This feature is available exclusively for Patreon subscribers.
            </p>
            <a href="{auth_url}" target="_self" style="
                display:inline-block;padding:12px 28px;
                background:#f96854;color:#fff;border-radius:8px;
                font-weight:700;text-decoration:none;font-size:16px;">
                Unlock with Patreon
            </a>
        </div>""",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Main application entry point."""
    st.set_page_config(
        page_title="D&D Loot & Encounter Manager",
        page_icon="🎲",
        layout="wide",
    )

    # 1. Consume OAuth callback code before anything else renders
    _handle_patreon_callback()

    # 2. Load OpenRouter key once per session
    if "openrouter_api_key" not in st.session_state:
        st.session_state.openrouter_api_key = _get_api_key()

    # 3. Determine AI access
    cfg = _get_patreon_config()
    ai_enabled = (cfg is None) or st.session_state.get("is_patron", False)
    st.session_state.ai_features_enabled = ai_enabled

    # 4. Sidebar auth widget
    _render_auth_sidebar(cfg)

    st.title("🎲 D&D Loot Creator & Encounter Tracker")

    tab1, tab2, tab3 = st.tabs(["⚔️ Loot Creator", "🛡️ Encounter Tracker", "🐉 Monster Generator"])

    with tab1:
        if ai_enabled:
            render_loot_creator()
        else:
            _render_patron_wall("Loot Creator", cfg)

    with tab2:
        render_encounter_tracker()  # always accessible

    with tab3:
        if ai_enabled:
            render_monster_generator()
        else:
            _render_patron_wall("Monster Generator", cfg)


if __name__ == "__main__":
    main()
