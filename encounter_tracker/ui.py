"""Streamlit UI for the Encounter Tracker."""

import streamlit as st

from config import D5E_CONDITIONS, SRD_MONSTERS_FILE, SAVED_ENCOUNTERS_FILE
from utils import load_json, save_json
from .models import Creature, Encounter
from .combat import roll_initiative, sort_by_initiative
from .themes import get_encounter_css


def get_hp_color(percentage: float) -> str:
    """Get color based on HP percentage."""
    if percentage > 50:
        return "green"
    elif percentage > 25:
        return "orange"
    else:
        return "red"


def render_health_bar(creature: Creature, key_prefix: str, encounter: Encounter) -> None:
    """Render a health bar with controls for a creature."""
    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])

    with col1:
        hp_pct = creature.hp_percentage
        st.progress(hp_pct / 100, text=f"HP: {creature.current_hp}/{creature.max_hp}")

    with col2:
        attack_name = st.text_input(
            "Attack",
            placeholder="Attack/spell",
            key=f"{key_prefix}_attack_name",
            label_visibility="collapsed",
        )

    with col3:
        damage = st.number_input(
            "Dmg",
            min_value=0,
            value=0,
            key=f"{key_prefix}_damage",
            label_visibility="collapsed",
        )
        if st.button("-HP", key=f"{key_prefix}_apply_damage"):
            old_hp = creature.current_hp
            creature.current_hp = max(0, creature.current_hp - damage)
            new_hp = creature.current_hp
            source = f" from {attack_name}" if attack_name.strip() else ""
            encounter.log(f"{creature.name} took {damage} damage{source} ({old_hp} → {new_hp} HP)")
            if new_hp == 0 and old_hp > 0:
                encounter.log(f"{creature.name} dropped to 0 HP!")
            st.rerun()

    with col4:
        healing = st.number_input(
            "Heal",
            min_value=0,
            value=0,
            key=f"{key_prefix}_healing",
            label_visibility="collapsed",
        )
        if st.button("+HP", key=f"{key_prefix}_apply_heal"):
            old_hp = creature.current_hp
            creature.current_hp = min(creature.max_hp, creature.current_hp + healing)
            new_hp = creature.current_hp
            encounter.log(f"{creature.name} was healed for {healing} HP ({old_hp} → {new_hp} HP)")
            if old_hp == 0 and new_hp > 0:
                creature.reset_death_saves()
                encounter.log(f"{creature.name}'s death saves reset (healing received)")
            st.rerun()

    with col5:
        if st.button("Full", key=f"{key_prefix}_full_heal"):
            old_hp = creature.current_hp
            creature.current_hp = creature.max_hp
            encounter.log(f"{creature.name} was fully healed ({old_hp} → {creature.max_hp} HP)")
            if old_hp == 0:
                creature.reset_death_saves()
            st.rerun()


def render_action_counters(creature: Creature, key_prefix: str, encounter: Encounter) -> None:
    """Render action/bonus action/reaction/legendary action counters."""
    counter_defs = [
        ("⚔️ Actions", "actions", creature.actions_total),
        ("⚡ Bonus", "bonus_actions", creature.bonus_actions_total),
        ("🛡️ Reaction", "reactions", creature.reactions_total),
    ]
    if creature.legendary_actions_total > 0:
        counter_defs.append(("✨ Legendary", "legendary_actions", creature.legendary_actions_total))

    cols = st.columns(len(counter_defs))
    for col, (label, attr, total) in zip(cols, counter_defs):
        used = getattr(creature, f"{attr}_used")
        with col:
            st.caption(label)
            btn_col1, val_col, btn_col2 = st.columns([1, 2, 1])
            with btn_col1:
                if st.button("−", key=f"{key_prefix}_{attr}_dec", disabled=used <= 0):
                    setattr(creature, f"{attr}_used", used - 1)
                    st.rerun()
            with val_col:
                remaining = total - used
                color = "red" if remaining == 0 else "inherit"
                st.markdown(
                    f"<div style='text-align:center;color:{color};font-weight:bold'>{used}/{total}</div>",
                    unsafe_allow_html=True,
                )
            with btn_col2:
                if st.button("+", key=f"{key_prefix}_{attr}_inc", disabled=used >= total):
                    setattr(creature, f"{attr}_used", used + 1)
                    st.rerun()


def render_death_saves(creature: Creature, key_prefix: str, encounter: Encounter) -> None:
    """Render death saving throw panel (shown when creature is at 0 HP)."""
    st.markdown("**Death Saving Throws**")
    col1, col2, col3 = st.columns(3)

    with col1:
        successes_pips = "🟢" * creature.death_save_successes + "⬜" * (3 - creature.death_save_successes)
        st.markdown(f"Successes: {successes_pips}")

    with col2:
        failures_pips = "🔴" * creature.death_save_failures + "⬜" * (3 - creature.death_save_failures)
        st.markdown(f"Failures: {failures_pips}")

    with col3:
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("✨ Success", key=f"{key_prefix}_ds_success"):
                creature.death_save_successes = min(3, creature.death_save_successes + 1)
                s = creature.death_save_successes
                encounter.log(f"{creature.name} — Death Save SUCCESS ({s}/3)")
                if creature.is_stable:
                    encounter.log(f"{creature.name} is now stable!")
                st.rerun()
        with btn_col2:
            if st.button("💀 Failure", key=f"{key_prefix}_ds_failure"):
                creature.death_save_failures = min(3, creature.death_save_failures + 1)
                f = creature.death_save_failures
                encounter.log(f"{creature.name} — Death Save FAILURE ({f}/3)")
                if creature.is_dead:
                    encounter.log(f"{creature.name} has died.")
                st.rerun()


def render_creature_card(creature: Creature, index: int, is_current: bool, encounter: Encounter) -> None:
    """Render a creature card in the initiative order."""
    key_prefix = f"creature_{index}"

    container = st.container(border=True)
    with container:
        # Header row
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

        with col1:
            icon = "🎮" if creature.is_player else "👹"
            status_parts = []
            if is_current:
                status_parts.append("**[ACTIVE]**")
            if creature.is_dead:
                status_parts.append("💀 Dead")
            elif creature.is_stable:
                status_parts.append("✨ Stable")
            elif creature.is_unconscious:
                status_parts.append("😵 Unconscious")
            elif creature.is_bloodied:
                status_parts.append("🩸 Bloodied")
            status_str = "  " + "  ".join(status_parts) if status_parts else ""
            st.markdown(f"### {icon} {creature.name}{status_str}")

        with col2:
            st.metric("Initiative", creature.initiative)

        with col3:
            st.metric("AC", creature.armor_class)

        with col4:
            if st.button("🗑️", key=f"{key_prefix}_remove"):
                encounter.remove_creature(index)
                st.rerun()

        # Health bar
        render_health_bar(creature, key_prefix, encounter)

        # Death saves panel (shown only at 0 HP and not yet determined)
        if creature.is_unconscious and creature.is_dead:
            st.error("💀 Dead")
        elif creature.is_unconscious and creature.is_stable:
            st.success("✨ Stable")
        elif creature.is_unconscious:
            render_death_saves(creature, key_prefix, encounter)

        # Action counters
        render_action_counters(creature, key_prefix, encounter)

        # Conditions
        current_conditions = st.multiselect(
            "Conditions",
            options=D5E_CONDITIONS,
            default=creature.conditions,
            key=f"{key_prefix}_conditions",
            label_visibility="collapsed",
        )
        # Log condition changes
        added = set(current_conditions) - set(creature.conditions)
        removed = set(creature.conditions) - set(current_conditions)
        for cond in added:
            encounter.log(f"{creature.name} gained condition: {cond}")
        for cond in removed:
            encounter.log(f"{creature.name} lost condition: {cond}")
        creature.conditions = current_conditions

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
            key="srd_monster_select",
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

    # Action economy configuration
    with st.expander("⚔️ Action Economy (optional)"):
        eco_col1, eco_col2, eco_col3, eco_col4 = st.columns(4)
        with eco_col1:
            actions_total = st.number_input("Actions", min_value=1, value=1, key="new_actions_total")
        with eco_col2:
            bonus_total = st.number_input("Bonus Actions", min_value=1, value=1, key="new_bonus_total")
        with eco_col3:
            reactions_total = st.number_input("Reactions", min_value=1, value=1, key="new_reactions_total")
        with eco_col4:
            legendary_total = st.number_input("Legendary Actions", min_value=0, value=0, key="new_legendary_total")

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
            actions_total=actions_total,
            bonus_actions_total=bonus_total,
            reactions_total=reactions_total,
            legendary_actions_total=legendary_total,
        )
        encounter.creatures.append(new_creature)
        st.success(f"Added {name} to encounter!")
        st.rerun()


def render_combat_log(encounter: Encounter) -> None:
    """Render the combat log panel."""
    with st.expander(f"📜 Combat Log ({len(encounter.combat_log)} entries)"):
        if not encounter.combat_log:
            st.caption("No events logged yet.")
        else:
            if st.button("Clear Log", key="clear_combat_log"):
                encounter.combat_log = []
                st.rerun()
            for entry in reversed(encounter.combat_log):
                st.markdown(f"- {entry}")


def render_narrator_section(encounter: Encounter) -> None:
    """Render the AI combat narrator section."""
    if not encounter.combat_log:
        return

    st.divider()
    st.subheader("📖 Combat Narrator")

    if not st.session_state.get("ai_features_enabled", True):
        st.info("🔒 Combat Narrator is available for Patreon subscribers. Log in via the sidebar.")
        return

    api_key = st.session_state.get("openrouter_api_key", "")

    st.text_area(
        "Combat Context (optional)",
        key="combat_context",
        placeholder=(
            "Give the AI some background to enrich the story:\n"
            "• Where are the adventurers? (e.g. a crumbling watchtower at dusk)\n"
            "• How did combat start? (e.g. ambushed by bandits on the road)\n"
            "• Any other details the narrator should know"
        ),
        height=110,
        label_visibility="collapsed",
    )

    if st.button("Generate Combat Story", type="primary", use_container_width=True):
        from .narrator import generate_combat_narrative
        with st.spinner("Weaving the tale of battle..."):
            try:
                context = st.session_state.get("combat_context", "")
                narrative = generate_combat_narrative(encounter.combat_log, api_key, context)
                st.session_state.combat_narrative = narrative
            except Exception as e:
                st.error(f"Error generating narrative: {e}")

    if st.session_state.get("combat_narrative"):
        st.markdown("---")
        st.markdown(st.session_state.combat_narrative)


def render_post_combat_loot(encounter: Encounter) -> None:
    """Render post-combat loot generation button."""
    enemies = [c for c in encounter.creatures if not c.is_player]
    if not enemies:
        return

    st.divider()
    st.subheader("💎 Combat Loot")

    if not st.session_state.get("ai_features_enabled", True):
        st.info("🔒 Combat Loot is available for Patreon subscribers. Log in via the sidebar.")
        return

    api_key = st.session_state.get("openrouter_api_key", "")

    st.text_area(
        "Loot Context (optional)",
        key="loot_context",
        placeholder=(
            "Help the AI generate fitting loot:\n"
            "• Where did the fight take place? (e.g. a bandit camp deep in the forest)\n"
            "• Any story details? (e.g. the bandit leader wore a strange amulet)\n"
            "• Tone: gritty, magical, cursed, ancient…"
        ),
        height=110,
        label_visibility="collapsed",
    )

    if st.button("Generate Combat Loot", use_container_width=True):
        from loot_creator.generator import generate_quick_item
        from loot_creator.models import QuickLootParameters, Rarity

        monster_names = ", ".join(c.name for c in enemies)
        loot_context = st.session_state.get("loot_context", "").strip()
        theme = f"loot found after defeating {monster_names}"
        if loot_context:
            theme += f". Context: {loot_context}"
        params = QuickLootParameters(
            rarity=Rarity.UNCOMMON,
            theme_description=theme,
        )
        with st.spinner("Generating loot from the fallen..."):
            try:
                item = generate_quick_item(params, api_key=api_key)
                st.session_state.encounter_loot = item
            except Exception as e:
                st.error(f"Error generating loot: {e}")

    if st.session_state.get("encounter_loot"):
        item = st.session_state.encounter_loot
        with st.expander(f"🗡️ {item.name} ({item.rarity})", expanded=True):
            st.markdown(f"**{item.subtype}** — *{item.rarity}*")
            st.markdown(item.description)
            if item.properties:
                for prop in item.properties:
                    st.markdown(f"- {prop}")
            if item.gold_value:
                st.markdown(f"💰 **Value:** {item.gold_value:,} gp")
            if item.lore:
                st.markdown(f"*{item.lore}*")
        if st.button("Clear Loot", key="clear_encounter_loot"):
            st.session_state.encounter_loot = None
            st.rerun()


def render_encounter_tracker():
    """Render the Encounter Tracker UI."""
    st.markdown(get_encounter_css(), unsafe_allow_html=True)

    st.header("Encounter Tracker")
    st.markdown("Track initiative order, HP, and conditions for your D&D combat.")

    # Initialize session state
    if "encounter" not in st.session_state:
        st.session_state.encounter = Encounter()
    if "combat_narrative" not in st.session_state:
        st.session_state.combat_narrative = None
    if "encounter_loot" not in st.session_state:
        st.session_state.encounter_loot = None

    encounter = st.session_state.encounter

    # Encounter controls row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        encounter_name = st.text_input(
            "Encounter Name",
            value=encounter.name,
            key="encounter_name_input",
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
            active = encounter.current_creature
            if active:
                active.reset_turn_actions()
                encounter.log(f"Combat begins! {active.name}'s turn.")
            st.rerun()

    with col4:
        if st.button("Reset Combat", use_container_width=True):
            encounter.reset_combat()
            st.session_state.combat_narrative = None
            st.session_state.encounter_loot = None
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

    # Combat log
    if encounter.combat_log:
        render_combat_log(encounter)

    st.divider()

    # Add creature form
    render_add_creature_form(encounter)

    # Save/Load controls
    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Save Encounter", use_container_width=True):
            saved_encounters = load_json(SAVED_ENCOUNTERS_FILE, [])
            existing_index = next(
                (i for i, e in enumerate(saved_encounters) if e["name"] == encounter.name),
                None,
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
                label_visibility="collapsed",
            )
            if selected != "-- Select --":
                if st.button("Load", use_container_width=True):
                    encounter_data = next(
                        (e for e in saved_encounters if e["name"] == selected),
                        None,
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
            key="quick_add_text",
        )
        if st.button("Add All", key="quick_add_button"):
            lines = [ln.strip() for ln in quick_add_text.split("\n") if ln.strip()]
            added = 0
            for line in lines:
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 3:
                    try:
                        creature = Creature(
                            name=parts[0],
                            initiative=0,
                            initiative_modifier=int(parts[3]) if len(parts) > 3 else 0,
                            current_hp=int(parts[1]),
                            max_hp=int(parts[1]),
                            armor_class=int(parts[2]),
                            is_player=False,
                        )
                        encounter.creatures.append(creature)
                        added += 1
                    except (ValueError, IndexError):
                        st.warning(f"Could not parse: {line}")
            if added > 0:
                st.success(f"Added {added} creatures!")
                st.rerun()

    # AI sections
    render_narrator_section(encounter)
    render_post_combat_loot(encounter)
