"""Streamlit UI for the Encounter Tracker."""

import streamlit as st

from config import D5E_CONDITIONS, SRD_MONSTERS_FILE, SAVED_ENCOUNTERS_FILE
from utils import load_json, save_json
from .models import Creature, Encounter
from .combat import roll_initiative, sort_by_initiative


def get_hp_color(percentage: float) -> str:
    """Get color based on HP percentage."""
    if percentage > 50:
        return "green"
    elif percentage > 25:
        return "orange"
    else:
        return "red"


def render_health_bar(creature: Creature, key_prefix: str) -> None:
    """Render a health bar with controls for a creature."""
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

    with col1:
        hp_pct = creature.hp_percentage
        color = get_hp_color(hp_pct)
        st.progress(hp_pct / 100, text=f"HP: {creature.current_hp}/{creature.max_hp}")

    with col2:
        damage = st.number_input(
            "Dmg",
            min_value=0,
            value=0,
            key=f"{key_prefix}_damage",
            label_visibility="collapsed"
        )
        if st.button("-HP", key=f"{key_prefix}_apply_damage"):
            creature.current_hp = max(0, creature.current_hp - damage)
            st.rerun()

    with col3:
        healing = st.number_input(
            "Heal",
            min_value=0,
            value=0,
            key=f"{key_prefix}_healing",
            label_visibility="collapsed"
        )
        if st.button("+HP", key=f"{key_prefix}_apply_heal"):
            creature.current_hp = min(creature.max_hp, creature.current_hp + healing)
            st.rerun()

    with col4:
        if st.button("Full", key=f"{key_prefix}_full_heal"):
            creature.current_hp = creature.max_hp
            st.rerun()


def render_creature_card(creature: Creature, index: int, is_current: bool, encounter: Encounter) -> None:
    """Render a creature card in the initiative order."""
    key_prefix = f"creature_{index}"

    # Card styling
    border_color = "#4CAF50" if is_current else "#333"
    bg_color = "#1a1a2e" if is_current else "#16213e"

    container = st.container(border=True)
    with container:
        # Header row
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

        with col1:
            icon = "🎮" if creature.is_player else "👹"
            status = ""
            if creature.is_unconscious:
                status = " (Unconscious)"
            elif creature.is_bloodied:
                status = " (Bloodied)"
            st.markdown(f"### {icon} {creature.name}{status}")

        with col2:
            st.metric("Initiative", creature.initiative)

        with col3:
            st.metric("AC", creature.armor_class)

        with col4:
            if st.button("🗑️", key=f"{key_prefix}_remove"):
                encounter.remove_creature(index)
                st.rerun()

        # Health bar
        render_health_bar(creature, key_prefix)

        # Conditions
        current_conditions = st.multiselect(
            "Conditions",
            options=D5E_CONDITIONS,
            default=creature.conditions,
            key=f"{key_prefix}_conditions",
            label_visibility="collapsed"
        )
        creature.conditions = current_conditions

        # Notes
        if creature.conditions:
            st.caption(f"Conditions: {', '.join(creature.conditions)}")


def render_add_creature_form(encounter: Encounter) -> None:
    """Render the form to add a new creature."""
    st.subheader("Add Creature")

    # Load SRD monsters
    srd_monsters = load_json(SRD_MONSTERS_FILE, [])
    monster_names = ["-- Custom --"] + [m["name"] for m in srd_monsters]

    col1, col2 = st.columns(2)

    with col1:
        selected_monster = st.selectbox(
            "Select from SRD Monsters",
            options=monster_names,
            key="srd_monster_select"
        )

    # Pre-fill form if SRD monster selected
    default_name = ""
    default_hp = 10
    default_ac = 10
    default_init_mod = 0

    if selected_monster != "-- Custom --":
        monster = next((m for m in srd_monsters if m["name"] == selected_monster), None)
        if monster:
            default_name = monster["name"]
            default_hp = monster["hp"]
            default_ac = monster["ac"]
            default_init_mod = monster.get("initiative_modifier", 0)

    with col2:
        is_player = st.checkbox("Is Player Character", key="new_is_player")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        name = st.text_input("Name", value=default_name, key="new_creature_name")

    with col2:
        max_hp = st.number_input("Max HP", min_value=1, value=default_hp, key="new_max_hp")

    with col3:
        ac = st.number_input("AC", min_value=0, value=default_ac, key="new_ac")

    with col4:
        init_mod = st.number_input("Init Mod", value=default_init_mod, key="new_init_mod")

    if st.button("Add Creature", type="primary", use_container_width=True):
        if not name:
            st.error("Please enter a creature name.")
            return

        new_creature = Creature(
            name=name,
            initiative=0,
            initiative_modifier=init_mod,
            current_hp=max_hp,
            max_hp=max_hp,
            armor_class=ac,
            is_player=is_player,
        )
        encounter.creatures.append(new_creature)
        st.success(f"Added {name} to encounter!")
        st.rerun()


def render_encounter_tracker():
    """Render the Encounter Tracker UI."""
    st.header("Encounter Tracker")
    st.markdown("Track initiative order, HP, and conditions for your D&D combat.")

    # Initialize session state for encounter
    if "encounter" not in st.session_state:
        st.session_state.encounter = Encounter()

    encounter = st.session_state.encounter

    # Encounter controls row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        encounter_name = st.text_input(
            "Encounter Name",
            value=encounter.name,
            key="encounter_name_input"
        )
        encounter.name = encounter_name

    with col2:
        st.metric("Round", encounter.round_number)

    with col3:
        if st.button("Roll All Initiative", use_container_width=True):
            for creature in encounter.creatures:
                creature.initiative = roll_initiative(creature)
            encounter.creatures = sort_by_initiative(encounter.creatures)
            encounter.current_turn_index = 0
            encounter.is_active = True
            st.rerun()

    with col4:
        if st.button("Reset Combat", use_container_width=True):
            encounter.reset_combat()
            st.rerun()

    st.divider()

    # Turn controls
    if encounter.creatures and encounter.is_active:
        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            if st.button("⬅️ Previous Turn", use_container_width=True):
                encounter.prev_turn()
                st.rerun()

        with col2:
            current = encounter.current_creature
            if current:
                st.markdown(f"### Current Turn: {current.name}")

        with col3:
            if st.button("Next Turn ➡️", use_container_width=True):
                encounter.next_turn()
                st.rerun()

        st.divider()

    # Initiative order display
    if encounter.creatures:
        st.subheader("Initiative Order")

        for i, creature in enumerate(encounter.creatures):
            is_current = encounter.is_active and i == encounter.current_turn_index
            render_creature_card(creature, i, is_current, encounter)
    else:
        st.info("No creatures in encounter. Add some below!")

    st.divider()

    # Add creature form
    render_add_creature_form(encounter)

    # Save/Load controls
    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Save Encounter", use_container_width=True):
            saved_encounters = load_json(SAVED_ENCOUNTERS_FILE, [])
            # Check if encounter with same name exists and update it
            existing_index = next(
                (i for i, e in enumerate(saved_encounters) if e["name"] == encounter.name),
                None
            )
            if existing_index is not None:
                saved_encounters[existing_index] = encounter.model_dump()
            else:
                saved_encounters.append(encounter.model_dump())
            save_json(SAVED_ENCOUNTERS_FILE, saved_encounters)
            st.success(f"Saved encounter: {encounter.name}")

    with col2:
        saved_encounters = load_json(SAVED_ENCOUNTERS_FILE, [])
        if saved_encounters:
            encounter_names = [e["name"] for e in saved_encounters]
            selected = st.selectbox(
                "Load Encounter",
                options=["-- Select --"] + encounter_names,
                key="load_encounter_select",
                label_visibility="collapsed"
            )
            if selected != "-- Select --":
                if st.button("Load", use_container_width=True):
                    encounter_data = next(
                        (e for e in saved_encounters if e["name"] == selected),
                        None
                    )
                    if encounter_data:
                        st.session_state.encounter = Encounter(**encounter_data)
                        st.success(f"Loaded encounter: {selected}")
                        st.rerun()

    # Quick add multiple creatures
    st.divider()
    with st.expander("Quick Add Multiple Creatures"):
        quick_add_text = st.text_area(
            "Enter creatures (one per line: name, hp, ac, init_mod)",
            placeholder="Goblin, 7, 15, 2\nOrc, 15, 13, 1\nWolf, 11, 13, 2",
            key="quick_add_text"
        )
        if st.button("Add All", key="quick_add_button"):
            lines = [l.strip() for l in quick_add_text.split("\n") if l.strip()]
            added = 0
            for line in lines:
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 3:
                    try:
                        name = parts[0]
                        hp = int(parts[1])
                        ac = int(parts[2])
                        init_mod = int(parts[3]) if len(parts) > 3 else 0
                        creature = Creature(
                            name=name,
                            initiative=0,
                            initiative_modifier=init_mod,
                            current_hp=hp,
                            max_hp=hp,
                            armor_class=ac,
                            is_player=False,
                        )
                        encounter.creatures.append(creature)
                        added += 1
                    except (ValueError, IndexError):
                        st.warning(f"Could not parse: {line}")
            if added > 0:
                st.success(f"Added {added} creatures!")
                st.rerun()
