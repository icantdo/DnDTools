"""Streamlit UI for the CR-Based Monster/Dungeon Generator."""

import streamlit as st

from .generator import generate_monster_and_room
from .models import GeneratorParams, GeneratorOutput

CR_VALUES = [0.125, 0.25, 0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
             11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30]

CR_LABELS = {0.125: "1/8", 0.25: "1/4", 0.5: "1/2"}

# CSS is injected separately so it never mixes with HTML in the same markdown call
_MONSTER_CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700&family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400&display=swap');
.dnd-card{background:#efe6d6;background-image:radial-gradient(rgba(0,0,0,0.03) 1px,transparent 1px);background-size:6px 6px;padding:44px 52px;border-radius:6px;margin:20px 0 8px 0;font-family:'EB Garamond',serif;}
.dnd-two-col{display:flex;gap:48px;align-items:flex-start;}
.dnd-col-left{flex:1.1;min-width:0;}
.dnd-col-right{flex:0.9;min-width:0;border-left:2px solid #b89b5e;padding-left:36px;}
.dnd-title{font-family:'Cinzel',serif;font-size:38px;margin:0 0 2px 0;color:#5b1c1c;text-transform:uppercase;letter-spacing:1px;line-height:1.15;}
.dnd-subtitle{font-family:'Cinzel',serif;font-size:17px;margin:8px 0 4px 0;color:#4a2c2c;text-transform:uppercase;}
.dnd-divider{height:3px;width:200px;background:#b89b5e;margin:8px 0 16px 0;border:none;display:block;}
.dnd-section-divider{height:1px;background:#b89b5e;margin:14px 0;border:none;display:block;}
.dnd-core-stats{display:flex;gap:24px;flex-wrap:wrap;font-size:18px;color:#2a1a0e;margin-bottom:10px;}
.dnd-core-stats span{font-family:'Cinzel',serif;font-size:12px;text-transform:uppercase;color:#7a5c3c;display:block;}
.dnd-ability-table{display:flex;margin:10px 0 14px 0;border:1px solid #c9b48a;border-radius:4px;overflow:hidden;font-size:17px;text-align:center;}
.dnd-ability-col{flex:1;padding:6px 4px;border-right:1px solid #c9b48a;color:#2a1a0e;}
.dnd-ability-col:last-child{border-right:none;}
.dnd-ability-col .ability-name{font-family:'Cinzel',serif;font-size:12px;text-transform:uppercase;color:#7a5c3c;font-weight:700;display:block;}
.dnd-ability-col .ability-mod{font-size:14px;color:#5b1c1c;}
.dnd-stat-row{font-size:17px;color:#2a1a0e;margin:4px 0;line-height:1.5;}
.dnd-stat-row strong{color:#4a2c2c;}
.dnd-section-header{font-family:'Cinzel',serif;font-size:15px;text-transform:uppercase;color:#5b1c1c;letter-spacing:1px;margin:14px 0 6px 0;border-bottom:1px solid #b89b5e;padding-bottom:3px;}
.dnd-list{padding-left:22px;margin:0 0 8px 0;}
.dnd-list li{margin-bottom:8px;font-size:17px;line-height:1.55;color:#2a1a0e;}
.dnd-description{font-size:17px;line-height:1.65;color:#2a1a0e;font-style:italic;margin:0 0 12px 0;}
.dnd-room-body{font-size:17px;line-height:1.65;color:#2a1a0e;margin:0 0 12px 0;}
.dnd-treasure{font-size:17px;color:#5b3a2c;font-style:italic;margin-top:6px;}
</style>"""


def cr_label(cr: float) -> str:
    return CR_LABELS.get(cr, str(int(cr)))


def _esc(text) -> str:
    escaped = (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
    # Replace newlines AFTER escaping — blank lines inside a <div> block
    # terminate CommonMark's type-6 HTML block, causing st.markdown to
    # render subsequent content as raw markdown/code instead of HTML.
    return escaped.replace("\n\n", "<br><br>").replace("\n", "<br>")


def _li(items: list) -> str:
    if not items:
        return ""
    return "<ul class=\"dnd-list\">" + "".join(f"<li>{_esc(i)}</li>" for i in items) + "</ul>"


def _section(title: str, content: str) -> str:
    if not content:
        return ""
    return f"<div class=\"dnd-section-header\">{title}</div>{content}"


def render_stat_block(output: GeneratorOutput) -> None:
    """Render monster stat block + dungeon room as a parchment card."""
    m = output.monster
    r = output.room

    # Ability score table — all on one line, no leading spaces
    ability_order = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
    ability_cols = ""
    for ab in ability_order:
        score = m.ability_scores.get(ab, 10)
        mod = (score - 10) // 2
        mod_str = f"+{mod}" if mod >= 0 else str(mod)
        ability_cols += (
            f"<div class=\"dnd-ability-col\">"
            f"<span class=\"ability-name\">{ab}</span>"
            f"{score}<br><span class=\"ability-mod\">({mod_str})</span>"
            f"</div>"
        )

    def stat_row(label: str, value) -> str:
        if not value:
            return ""
        v = ", ".join(value) if isinstance(value, list) else str(value)
        return f"<div class=\"dnd-stat-row\"><strong>{_esc(label)}:</strong> {_esc(v)}</div>"

    stat_rows = (
        stat_row("Saving Throws", m.saving_throws)
        + stat_row("Skills", m.skills)
        + stat_row("Damage Resistances", m.damage_resistances)
        + stat_row("Damage Immunities", m.damage_immunities)
        + stat_row("Condition Immunities", m.condition_immunities)
        + stat_row("Senses", m.senses)
        + stat_row("Languages", m.languages)
    )

    desc_html = f"<p class=\"dnd-description\">{_esc(m.description)}</p>" if m.description else ""

    left_col = (
        f"<div class=\"dnd-col-left\">"
        f"<div class=\"dnd-title\">{_esc(m.name)}</div>"
        f"<div class=\"dnd-subtitle\">CR {_esc(m.cr)}</div>"
        f"<hr class=\"dnd-divider\">"
        f"{desc_html}"
        f"<div class=\"dnd-core-stats\">"
        f"<div><span>Hit Points</span>{m.hp}</div>"
        f"<div><span>Armor Class</span>{m.ac}</div>"
        f"<div><span>Speed</span>{_esc(m.speed)}</div>"
        f"</div>"
        f"<div class=\"dnd-ability-table\">{ability_cols}</div>"
        f"{stat_rows}"
        f"<hr class=\"dnd-section-divider\">"
        + _section("Special Abilities", _li(m.special_abilities))
        + _section("Actions", _li(m.actions))
        + _section("Legendary Actions", _li(m.legendary_actions))
        + "</div>"
    )

    right_col = (
        f"<div class=\"dnd-col-right\">"
        f"<div class=\"dnd-title\" style=\"font-size:28px\">{_esc(r.name)}</div>"
        f"<div class=\"dnd-subtitle\" style=\"font-size:14px\">Encounter Area</div>"
        f"<hr class=\"dnd-divider\">"
        f"<p class=\"dnd-description\">{_esc(r.atmosphere)}</p>"
        f"<p class=\"dnd-room-body\">{_esc(r.description)}</p>"
        + _section("Traps", _li(r.traps))
        + _section("Environmental Features", _li(r.environmental_features))
        + (f"<p class=\"dnd-treasure\">&#x1F4B0; {_esc(r.treasure_hint)}</p>" if r.treasure_hint else "")
        + "</div>"
    )

    card_html = (
        "<div class=\"dnd-card\">"
        "<div class=\"dnd-two-col\">"
        + left_col
        + right_col
        + "</div></div>"
    )

    # Inject CSS first, then the card — separate calls avoid markdown code-block misparse
    st.markdown(_MONSTER_CSS, unsafe_allow_html=True)
    st.markdown(card_html, unsafe_allow_html=True)


def render_monster_generator() -> None:
    """Render the Monster/Dungeon Generator UI."""
    st.header("CR-Based Monster & Dungeon Generator")
    st.markdown("Describe a monster concept and CR — AI generates a full stat block and encounter room.")

    if "generated_monster" not in st.session_state:
        st.session_state.generated_monster = None

    api_key = st.session_state.get("openrouter_api_key", "")

    col1, col2 = st.columns([1, 2])
    with col1:
        selected_cr = st.select_slider(
            "Challenge Rating",
            options=CR_VALUES,
            value=5,
            format_func=cr_label,
        )
    with col2:
        theme = st.text_input(
            "Monster Theme / Description",
            placeholder="e.g. swamp boss, ancient undead lich, fire salamander ambusher",
            key="monster_theme_input",
        )

    st.caption(
        "Examples: 'CR 3 forest troll guarding a bridge', "
        "'CR 8 corrupted water elemental in a sunken temple', "
        "'CR 15 dragon cultist warlord'"
    )

    if st.button("⚡ Generate Monster & Room", type="primary", use_container_width=True):
        if not theme.strip():
            st.warning("Please describe a monster theme.")
        else:
            params = GeneratorParams(cr=selected_cr, theme=theme)
            with st.spinner(f"Generating CR {cr_label(selected_cr)} {theme}..."):
                try:
                    output = generate_monster_and_room(params, api_key)
                    st.session_state.generated_monster = output
                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Error generating monster: {e}")

    if st.session_state.generated_monster:
        render_stat_block(st.session_state.generated_monster)
        if st.button("Generate Another", use_container_width=True):
            st.session_state.generated_monster = None
            st.rerun()
