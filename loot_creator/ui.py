"""Streamlit UI for the Loot Creator."""

import streamlit as st

from config import (
    DAMAGE_TYPES,
    D5E_CONDITIONS,
    ABILITY_SCORES,
    CLASSES,
    ALIGNMENTS,
    SAVED_ITEMS_FILE,
)
from utils import load_json, save_json
from .models import (
    ItemType,
    ItemSubtype,
    Rarity,
    ActionEconomy,
    TargetType,
    UsageLimit,
    TriggerType,
    LootParameters,
    PassiveBonuses,
    ActiveEffect,
    UsageLimits,
    AdditionalProperties,
    Restrictions,
    QuickLootParameters,
)
from .generator import generate_item, generate_quick_item
from .balance import calculate_power_score, get_power_score_details, get_suggested_rarity, RARITY_POWER_RANGES


# Mapping of item types to valid subtypes
SUBTYPE_MAP = {
    ItemType.WEAPON: [
        ItemSubtype.LONGSWORD, ItemSubtype.SHORTSWORD, ItemSubtype.GREATSWORD,
        ItemSubtype.DAGGER, ItemSubtype.BATTLEAXE, ItemSubtype.GREATAXE,
        ItemSubtype.WARHAMMER, ItemSubtype.MAUL, ItemSubtype.SPEAR,
        ItemSubtype.HALBERD, ItemSubtype.LONGBOW, ItemSubtype.SHORTBOW,
        ItemSubtype.CROSSBOW, ItemSubtype.STAFF, ItemSubtype.MACE,
        ItemSubtype.FLAIL, ItemSubtype.RAPIER, ItemSubtype.SCIMITAR, ItemSubtype.TRIDENT,
    ],
    ItemType.ARMOR: [
        ItemSubtype.PLATE_ARMOR, ItemSubtype.CHAIN_MAIL, ItemSubtype.SCALE_MAIL,
        ItemSubtype.LEATHER_ARMOR, ItemSubtype.STUDDED_LEATHER, ItemSubtype.SHIELD,
        ItemSubtype.HELMET, ItemSubtype.GAUNTLETS, ItemSubtype.BOOTS,
    ],
    ItemType.RING: [ItemSubtype.RING],
    ItemType.WONDROUS_ITEM: [
        ItemSubtype.CLOAK, ItemSubtype.AMULET, ItemSubtype.BELT,
        ItemSubtype.BRACERS, ItemSubtype.CIRCLET, ItemSubtype.GLOVES,
        ItemSubtype.GOGGLES, ItemSubtype.HAT, ItemSubtype.ROBE,
        ItemSubtype.BAG, ItemSubtype.CAPE, ItemSubtype.MANTLE,
    ],
    ItemType.POTION: [ItemSubtype.POTION],
    ItemType.SCROLL: [ItemSubtype.SCROLL],
}


def render_power_score(params: LootParameters) -> None:
    """Render the power score breakdown for advanced mode."""
    details = get_power_score_details(params)

    st.subheader("Power Score Analysis")

    # Power score with color coding
    score = details["power_score"]
    suggested = details["suggested_rarity"]
    selected = params.rarity

    # Determine color based on balance
    min_power, max_power = RARITY_POWER_RANGES.get(selected, (0, 100))
    if score < min_power:
        color = "blue"  # Underpowered
        status = "Underpowered"
    elif score > max_power:
        color = "red"  # Overpowered
        status = "Overpowered"
    else:
        color = "green"  # Balanced
        status = "Balanced"

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Power Score",
            f"{score:.1f}",
            delta=f"{status} for {selected.value}",
            delta_color="normal" if color == "green" else ("off" if color == "blue" else "inverse")
        )

    with col2:
        st.metric(
            "Suggested Rarity",
            suggested.value,
            delta="Match!" if suggested == selected else f"vs {selected.value}",
            delta_color="normal" if suggested == selected else "off"
        )

    # Formula breakdown
    with st.expander("Formula Breakdown"):
        st.markdown("**Formula:** `[(ΔDPR × A × U) + D + C] × R − (Kₐ + Kₙ)`")
        st.markdown(f"""
| Component | Value | Description |
|-----------|-------|-------------|
| ΔDPR | {details['dpr']} | Damage per round increase |
| A | {details['action_economy']} | Action economy multiplier |
| U | {details['usage']} | Usage multiplier |
| D | {details['defensive']} | Defensive power |
| C | {details['control_utility']} | Control/utility power |
| R | {details['reliability']} | Reliability multiplier |
| Kₐ | {details['constraints']} | Structural constraints (penalty) |
| Kₙ | {details['negative_effects']} | Negative effects (penalty) |
        """)


def render_quick_mode() -> None:
    """Render the Quick/Lazy Mode UI."""
    st.markdown("Just pick a rarity and describe what you want - AI handles the rest!")

    col1, col2 = st.columns([1, 2])

    with col1:
        rarity = st.selectbox(
            "Rarity",
            options=list(Rarity),
            format_func=lambda x: x.value,
            index=1,  # Default to Uncommon
            key="quick_rarity"
        )

    with col2:
        theme = st.text_input(
            "Describe your item",
            placeholder="e.g., fire sword for a paladin, mysterious ring that whispers, healing potion for emergencies",
            key="quick_theme"
        )

    # Example suggestions
    st.caption("Examples: 'ice dagger for a rogue', 'protective amulet against undead', 'boots that let you walk on water'")

    if st.button("Generate Item", type="primary", use_container_width=True, key="quick_generate"):
        if not theme.strip():
            st.warning("Please describe what kind of item you want.")
            return

        params = QuickLootParameters(
            rarity=rarity,
            theme_description=theme
        )

        # Get user API key from session state
        user_api_key = st.session_state.get("user_api_key", "")

        with st.spinner("AI is creating your item..."):
            try:
                item = generate_quick_item(params, api_key=user_api_key if user_api_key else None)
                st.session_state.generated_item = item
                st.session_state.generated_params = None  # No params for power calculation in quick mode
            except ValueError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"Error generating item: {e}")


def render_advanced_mode() -> None:
    """Render the Advanced Mode UI with all parameters."""
    # Create two columns for parameter input
    col1, col2 = st.columns(2)

    with col1:
        # A) Base Identity
        st.subheader("A) Base Identity")

        item_type = st.selectbox(
            "Item Type",
            options=list(ItemType),
            format_func=lambda x: x.value,
        )

        valid_subtypes = SUBTYPE_MAP.get(item_type, list(ItemSubtype))
        item_subtype = st.selectbox(
            "Subtype",
            options=valid_subtypes,
            format_func=lambda x: x.value,
        )

        rarity = st.selectbox(
            "Rarity",
            options=list(Rarity),
            format_func=lambda x: x.value,
            index=1,  # Default to Uncommon
        )

        requires_attunement = st.checkbox("Requires Attunement")

        # B) Passive Numerical Bonuses
        st.subheader("B) Passive Numerical Bonuses")

        attack_bonus = st.slider("+ Attack Rolls", 0, 3, 0)
        damage_bonus = st.slider("+ Damage", 0, 3, 0)
        ac_bonus = st.slider("+ Armor Class", 0, 3, 0)

        ability_bonuses = []
        st.markdown("**Ability Score Bonuses:**")
        for ability in ABILITY_SCORES:
            bonus = st.selectbox(
                f"{ability}",
                options=[0, 1, 2],
                key=f"ability_{ability}",
            )
            if bonus > 0:
                ability_bonuses.append(f"+{bonus} {ability[:3].upper()}")

        # C) Active Effects
        st.subheader("C) Active Effects")

        has_active_effect = st.checkbox("Has Active Effect")

        active_effect = ActiveEffect()
        if has_active_effect:
            active_effect.enabled = True
            active_effect.spell_name = st.text_input(
                "Spell/Effect Name",
                placeholder="e.g., Fireball, Fly, Invisibility"
            )
            active_effect.spell_level = st.slider("Spell Level / Power Tier", 1, 9, 3)
            active_effect.action_economy = st.selectbox(
                "Action Economy",
                options=list(ActionEconomy),
                format_func=lambda x: x.value,
            )
            active_effect.target_type = st.selectbox(
                "Target Type",
                options=list(TargetType),
                format_func=lambda x: x.value,
            )

    with col2:
        # D) Usage Limits
        st.subheader("D) Usage Limits")

        limit_type = st.selectbox(
            "Usage Limit Type",
            options=list(UsageLimit),
            format_func=lambda x: x.value,
        )

        uses_per_rest = None
        max_charges = None
        regain_charges = None

        if limit_type in [UsageLimit.PER_LONG_REST, UsageLimit.PER_SHORT_REST]:
            uses_per_rest = st.slider("Uses Per Rest", 1, 10, 3)
        elif limit_type == UsageLimit.CHARGES:
            max_charges = st.slider("Maximum Charges", 1, 20, 7)
            regain_charges = st.text_input(
                "Charge Regain",
                value="1d6+1 at dawn",
                placeholder="e.g., 1d6+1 at dawn"
            )

        usage_limits = UsageLimits(
            limit_type=limit_type,
            uses_per_rest=uses_per_rest,
            max_charges=max_charges,
            regain_charges=regain_charges,
        )

        # E) Triggers
        st.subheader("E) Triggers")

        triggers = st.multiselect(
            "Trigger Conditions",
            options=list(TriggerType),
            format_func=lambda x: x.value,
        )

        # F) Additional Properties
        st.subheader("F) Additional Properties")

        damage_type_change = st.selectbox(
            "Damage Type Change",
            options=["None"] + DAMAGE_TYPES,
        )
        if damage_type_change == "None":
            damage_type_change = None

        resistances = st.multiselect("Resistances", options=DAMAGE_TYPES)
        conditions_inflicted = st.multiselect("Conditions Inflicted", options=D5E_CONDITIONS)

        visual_effects = st.text_input(
            "Visual/Thematic Effects",
            placeholder="e.g., glows with blue fire, whispers ancient secrets"
        )

        additional_properties = AdditionalProperties(
            damage_type_change=damage_type_change,
            resistances=resistances,
            conditions_inflicted=conditions_inflicted,
            visual_effects=visual_effects if visual_effects else None,
        )

        # G) Restrictions & Costs
        st.subheader("G) Restrictions & Costs")

        class_restrictions = st.multiselect("Class Restrictions", options=CLASSES)
        alignment_restrictions = st.multiselect("Alignment Restrictions", options=ALIGNMENTS)

        has_curse = st.checkbox("Is Cursed")
        curse_description = None
        if has_curse:
            curse_description = st.text_input(
                "Curse Theme",
                placeholder="e.g., causes paranoia, binds to wielder"
            )

        side_effects = st.text_area(
            "Side Effects (one per line)",
            placeholder="e.g., HP loss\nexhaustion\nbacklash damage"
        )
        side_effects_list = [s.strip() for s in side_effects.split("\n") if s.strip()]

        restrictions = Restrictions(
            class_restrictions=class_restrictions,
            alignment_restrictions=alignment_restrictions,
            has_curse=has_curse,
            curse_description=curse_description if curse_description else None,
            side_effects=side_effects_list,
        )

    # Theme keywords (full width)
    st.divider()
    theme_keywords = st.text_input(
        "Theme/Flavor Keywords (optional)",
        placeholder="e.g., fire, phoenix, rebirth, ancient elven"
    )

    # Build parameters
    params = LootParameters(
        item_type=item_type,
        item_subtype=item_subtype,
        rarity=rarity,
        requires_attunement=requires_attunement,
        passive_bonuses=PassiveBonuses(
            attack_bonus=attack_bonus,
            damage_bonus=damage_bonus,
            ac_bonus=ac_bonus,
            ability_bonuses=ability_bonuses,
        ),
        active_effect=active_effect,
        usage_limits=usage_limits,
        triggers=triggers,
        additional_properties=additional_properties,
        restrictions=restrictions,
        theme_keywords=theme_keywords if theme_keywords else None,
    )

    # Show power score analysis
    st.divider()
    render_power_score(params)

    # Generate button
    st.divider()
    if st.button("Generate Magic Item", type="primary", use_container_width=True):
        # Get user API key from session state
        user_api_key = st.session_state.get("user_api_key", "")

        with st.spinner("Generating item with AI..."):
            try:
                item = generate_item(params, api_key=user_api_key if user_api_key else None)
                st.session_state.generated_item = item
                st.session_state.generated_params = params  # Store for power calculation
            except ValueError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"Error generating item: {e}")


def render_generated_item() -> None:
    """Render the generated item display."""
    if not st.session_state.generated_item:
        return

    item = st.session_state.generated_item

    st.divider()
    st.subheader(f"{item.name}")

    st.markdown(f"**{item.subtype}** ({item.item_type}) - *{item.rarity}*")

    if item.requires_attunement:
        attunement_text = "Requires Attunement"
        if item.attunement_requirement:
            attunement_text += f" ({item.attunement_requirement})"
        st.markdown(f"*{attunement_text}*")

    st.markdown("---")
    st.markdown(item.description)

    if item.properties:
        st.markdown("**Properties:**")
        for prop in item.properties:
            st.markdown(f"- {prop}")

    if item.curse:
        st.markdown("---")
        st.markdown(f"**Curse:** {item.curse}")

    if item.lore:
        st.markdown("---")
        st.markdown(f"*{item.lore}*")

    # Save button
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Item", use_container_width=True):
            saved_items = load_json(SAVED_ITEMS_FILE, [])
            saved_items.append(item.model_dump())
            save_json(SAVED_ITEMS_FILE, saved_items)
            st.success(f"Saved '{item.name}' to collection!")

    with col2:
        if st.button("Clear", use_container_width=True):
            st.session_state.generated_item = None
            st.session_state.generated_params = None
            st.rerun()


def render_saved_items() -> None:
    """Render the saved items section."""
    st.divider()
    with st.expander("View Saved Items"):
        saved_items = load_json(SAVED_ITEMS_FILE, [])
        if not saved_items:
            st.info("No saved items yet. Generate and save some items!")
        else:
            for i, item_data in enumerate(saved_items):
                st.markdown(f"**{item_data['name']}** - {item_data['rarity']} {item_data['subtype']}")
                if st.button(f"Delete", key=f"delete_{i}"):
                    saved_items.pop(i)
                    save_json(SAVED_ITEMS_FILE, saved_items)
                    st.rerun()
                st.markdown("---")


def render_loot_creator():
    """Render the Loot Creator UI."""
    st.header("AI Loot Creator")

    # Initialize session state
    if "generated_item" not in st.session_state:
        st.session_state.generated_item = None
    if "generated_params" not in st.session_state:
        st.session_state.generated_params = None

    # Mode toggle
    mode = st.radio(
        "Mode",
        options=["Quick Mode", "Advanced Mode"],
        horizontal=True,
        help="Quick Mode: Just describe what you want. Advanced Mode: Full control over all parameters."
    )

    st.divider()

    if mode == "Quick Mode":
        render_quick_mode()
    else:
        render_advanced_mode()

    # Display generated item (common for both modes)
    render_generated_item()

    # Show saved items
    render_saved_items()
