"""Prompt templates for Gemini AI item generation."""

from .models import LootParameters, QuickLootParameters


def build_item_prompt(params: LootParameters) -> str:
    """Build a detailed prompt for generating a magic item.

    Args:
        params: The item parameters to use for generation.

    Returns:
        A formatted prompt string for the AI.
    """
    prompt_parts = [
        "You are an expert D&D 5th Edition magic item designer. Create a unique and balanced magic item based on the following specifications.",
        "",
        "## Base Identity",
        f"- Item Type: {params.item_type.value}",
        f"- Subtype: {params.item_subtype.value}",
        f"- Rarity: {params.rarity.value}",
        f"- Requires Attunement: {'Yes' if params.requires_attunement else 'No'}",
    ]

    # Passive Bonuses
    bonuses = params.passive_bonuses
    if bonuses.attack_bonus or bonuses.damage_bonus or bonuses.ac_bonus or bonuses.ability_bonuses or bonuses.saving_throw_bonuses:
        prompt_parts.append("")
        prompt_parts.append("## Passive Numerical Bonuses")
        if bonuses.attack_bonus:
            prompt_parts.append(f"- +{bonuses.attack_bonus} to attack rolls")
        if bonuses.damage_bonus:
            prompt_parts.append(f"- +{bonuses.damage_bonus} to damage")
        if bonuses.ac_bonus:
            prompt_parts.append(f"- +{bonuses.ac_bonus} to Armor Class")
        for ab in bonuses.ability_bonuses:
            prompt_parts.append(f"- {ab}")
        for stb in bonuses.saving_throw_bonuses:
            prompt_parts.append(f"- {stb}")

    # Active Effects
    if params.active_effect.enabled and params.active_effect.spell_name:
        prompt_parts.append("")
        prompt_parts.append("## Active Effects")
        prompt_parts.append(f"- Spell-like Effect: {params.active_effect.spell_name}")
        if params.active_effect.spell_level:
            prompt_parts.append(f"- Spell Level/Power Tier: {params.active_effect.spell_level}")
        prompt_parts.append(f"- Action Economy: {params.active_effect.action_economy.value}")
        prompt_parts.append(f"- Target Type: {params.active_effect.target_type.value}")

    # Usage Limits
    limits = params.usage_limits
    if limits.limit_type.value != "At-Will":
        prompt_parts.append("")
        prompt_parts.append("## Usage Limits")
        prompt_parts.append(f"- Limit Type: {limits.limit_type.value}")
        if limits.uses_per_rest:
            prompt_parts.append(f"- Uses: {limits.uses_per_rest} per rest")
        if limits.max_charges:
            prompt_parts.append(f"- Maximum Charges: {limits.max_charges}")
        if limits.regain_charges:
            prompt_parts.append(f"- Charge Regain: {limits.regain_charges}")

    # Triggers
    if params.triggers:
        prompt_parts.append("")
        prompt_parts.append("## Triggers")
        for trigger in params.triggers:
            prompt_parts.append(f"- {trigger.value}")

    # Additional Properties
    props = params.additional_properties
    if props.damage_type_change or props.resistances or props.immunities or props.conditions_inflicted or props.visual_effects:
        prompt_parts.append("")
        prompt_parts.append("## Additional Properties")
        if props.damage_type_change:
            prompt_parts.append(f"- Damage Type: {props.damage_type_change}")
        for res in props.resistances:
            prompt_parts.append(f"- Resistance to {res}")
        for imm in props.immunities:
            prompt_parts.append(f"- Immunity to {imm}")
        for cond in props.conditions_inflicted:
            prompt_parts.append(f"- Can inflict: {cond}")
        if props.visual_effects:
            prompt_parts.append(f"- Visual Theme: {props.visual_effects}")

    # Restrictions
    rest = params.restrictions
    if rest.class_restrictions or rest.alignment_restrictions or rest.has_curse or rest.side_effects:
        prompt_parts.append("")
        prompt_parts.append("## Restrictions & Costs")
        for cr in rest.class_restrictions:
            prompt_parts.append(f"- Class Restriction: {cr} only")
        for ar in rest.alignment_restrictions:
            prompt_parts.append(f"- Alignment Restriction: {ar}")
        if rest.has_curse:
            prompt_parts.append("- This item IS CURSED")
            if rest.curse_description:
                prompt_parts.append(f"- Curse Theme: {rest.curse_description}")
        for se in rest.side_effects:
            prompt_parts.append(f"- Side Effect: {se}")

    # Theme keywords
    if params.theme_keywords:
        prompt_parts.append("")
        prompt_parts.append(f"## Theme/Flavor Keywords: {params.theme_keywords}")

    if params.power_level_notes:
        prompt_parts.append("")
        prompt_parts.append(f"## Power Level Notes: {params.power_level_notes}")

    # Output format instructions
    prompt_parts.extend([
        "",
        "---",
        "",
        "Generate a complete magic item with the following structure. Be creative with the name and lore, but ensure the mechanics match the specifications above.",
        "",
        "Respond in this exact JSON format:",
        "```json",
        "{",
        '  "name": "Creative item name",',
        '  "item_type": "The item type",',
        '  "subtype": "The subtype",',
        '  "rarity": "The rarity",',
        '  "requires_attunement": true/false,',
        '  "attunement_requirement": "Optional requirement like class or alignment, or null",',
        '  "description": "Full mechanical description of the item including all properties and effects",',
        '  "properties": ["List", "of", "individual", "properties"],',
        '  "curse": "Description of the curse if applicable, or null",',
        '  "lore": "A short paragraph of flavor text about the item\'s history or origin"',
        "}",
        "```",
        "",
        "Ensure the item is balanced for D&D 5th Edition based on its rarity. Make the name evocative and memorable.",
    ])

    return "\n".join(prompt_parts)


def build_quick_item_prompt(params: QuickLootParameters) -> str:
    """Build a prompt for quick/lazy item generation.

    The AI decides item type, subtype, and all properties based on
    just the rarity and theme description.

    Args:
        params: The quick item parameters (rarity + theme).

    Returns:
        A formatted prompt string for the AI.
    """
    theme = params.theme_description.strip() if params.theme_description else "a mysterious and interesting magic item"

    prompt = f"""You are an expert D&D 5th Edition magic item designer. Create a unique and balanced magic item based on minimal input.

## Requirements
- **Rarity:** {params.rarity.value}
- **Theme/Description:** {theme}

## Your Task
Based on the theme description, decide:
1. What type of item this should be (weapon, armor, ring, wondrous item, potion, scroll, etc.)
2. The specific subtype (longsword, cloak, amulet, etc.)
3. Whether it requires attunement
4. All mechanical properties appropriate for the rarity level
5. Any special effects, bonuses, or abilities
6. Creative name and backstory

## Rarity Guidelines
- Common: Minor cosmetic or utility effects
- Uncommon: +1 bonuses or simple magical effects
- Rare: +2 bonuses or moderate magical effects, may require attunement
- Very Rare: +3 bonuses or powerful effects, usually requires attunement
- Legendary: Multiple powerful effects, always requires attunement
- Artifact: World-changing power with significant drawbacks

---

Respond in this exact JSON format:
```json
{{
  "name": "Creative item name",
  "item_type": "The item type (Weapon, Armor, Ring, Wondrous Item, Potion, Scroll)",
  "subtype": "The specific subtype",
  "rarity": "{params.rarity.value}",
  "requires_attunement": true/false,
  "attunement_requirement": "Optional requirement like class or alignment, or null",
  "description": "Full mechanical description of the item including all properties and effects",
  "properties": ["List", "of", "individual", "properties"],
  "curse": "Description of the curse if applicable, or null",
  "lore": "A short paragraph of flavor text about the item's history or origin"
}}
```

Be creative and make the item feel magical and unique while staying balanced for its rarity level."""

    return prompt
