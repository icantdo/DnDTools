"""Power balance calculation for magic items.

Implements the formula: Power Score = [(ΔDPR × A × U) + D + C] × R − (Kₐ + Kₙ)

Variables:
- ΔDPR: Damage increase per round
- A: Action economy multiplier
- U: Usage multiplier
- D: Defensive power
- C: Control/utility power
- R: Reliability multiplier
- Kₐ: Structural constraints (attunement, restrictions)
- Kₙ: Negative effects (curses, drawbacks)
"""

from .models import (
    LootParameters,
    ActionEconomy,
    UsageLimit,
    TriggerType,
    Rarity,
)


# Action Economy Multipliers
ACTION_ECONOMY_MULTIPLIERS = {
    ActionEconomy.FREE: 1.5,       # Passive effects are most valuable
    ActionEconomy.BONUS_ACTION: 1.2,
    ActionEconomy.REACTION: 1.0,
    ActionEconomy.ACTION: 0.8,
}

# Usage Multipliers
USAGE_MULTIPLIERS = {
    UsageLimit.AT_WILL: 1.0,
    UsageLimit.PER_SHORT_REST: 0.7,
    UsageLimit.PER_LONG_REST: 0.4,
    UsageLimit.CHARGES: 0.5,       # Average, depends on charges
    UsageLimit.SINGLE_USE: 0.1,
}

# Reliability Multipliers
RELIABILITY_AUTOMATIC = 1.0
RELIABILITY_ATTACK_ROLL = 0.65
RELIABILITY_SAVE_DC = 0.6

# Defensive Power Values
AC_BONUS_VALUE = 2.0
RESISTANCE_VALUE = 3.0
IMMUNITY_VALUE = 5.0

# Control/Utility Values
CONDITION_WITH_SAVE = 2.0
CONDITION_NO_SAVE = 4.0
UTILITY_BASE = 1.5

# Constraint Penalties
ATTUNEMENT_PENALTY = 1.0
CLASS_RESTRICTION_PENALTY = 0.5
ALIGNMENT_RESTRICTION_PENALTY = 0.3

# Curse/Negative Effect Penalties
MINOR_CURSE_PENALTY = 1.0
MAJOR_CURSE_PENALTY = 3.0
SIDE_EFFECT_PENALTY = 0.5

# Rarity Power Ranges
RARITY_POWER_RANGES = {
    Rarity.COMMON: (0, 2),
    Rarity.UNCOMMON: (2, 5),
    Rarity.RARE: (5, 10),
    Rarity.VERY_RARE: (10, 18),
    Rarity.LEGENDARY: (18, 30),
    Rarity.ARTIFACT: (30, 100),
}


def calculate_dpr(params: LootParameters) -> float:
    """Calculate damage per round increase (ΔDPR).

    +1 attack bonus ≈ 1 DPR increase (5% hit chance on ~20 damage)
    +1 damage bonus ≈ 0.5 DPR (assuming ~50% hit rate)
    """
    bonuses = params.passive_bonuses
    dpr = 0.0

    # Attack bonus contribution
    dpr += bonuses.attack_bonus * 1.0

    # Damage bonus contribution
    dpr += bonuses.damage_bonus * 0.5

    # Active effect spell damage (rough estimate based on spell level)
    if params.active_effect.enabled and params.active_effect.spell_level:
        # Assume average spell damage scales with level
        spell_level = params.active_effect.spell_level
        dpr += spell_level * 1.5  # Rough average damage per spell level

    return dpr


def get_action_economy_multiplier(params: LootParameters) -> float:
    """Get action economy multiplier (A).

    Passive effects are most valuable, actions least.
    """
    # Check if there are passive triggers
    passive_triggers = [TriggerType.ALWAYS_ACTIVE, TriggerType.ON_HIT, TriggerType.WHEN_HIT]
    if any(t in params.triggers for t in passive_triggers):
        return ACTION_ECONOMY_MULTIPLIERS[ActionEconomy.FREE]

    # Use active effect action economy if enabled
    if params.active_effect.enabled:
        return ACTION_ECONOMY_MULTIPLIERS.get(
            params.active_effect.action_economy,
            ACTION_ECONOMY_MULTIPLIERS[ActionEconomy.ACTION]
        )

    # Default to passive for items with only passive bonuses
    if params.passive_bonuses.attack_bonus or params.passive_bonuses.damage_bonus or params.passive_bonuses.ac_bonus:
        return ACTION_ECONOMY_MULTIPLIERS[ActionEconomy.FREE]

    return 1.0


def get_usage_multiplier(params: LootParameters) -> float:
    """Get usage multiplier (U).

    At-will is most valuable, single-use least.
    """
    base_multiplier = USAGE_MULTIPLIERS.get(
        params.usage_limits.limit_type,
        USAGE_MULTIPLIERS[UsageLimit.AT_WILL]
    )

    # Adjust for charges
    if params.usage_limits.limit_type == UsageLimit.CHARGES:
        max_charges = params.usage_limits.max_charges or 7
        # More charges = higher multiplier (capped at at-will)
        base_multiplier = min(1.0, 0.3 + (max_charges * 0.05))

    # Adjust for uses per rest
    if params.usage_limits.limit_type in [UsageLimit.PER_LONG_REST, UsageLimit.PER_SHORT_REST]:
        uses = params.usage_limits.uses_per_rest or 1
        # More uses = higher multiplier
        base_multiplier = min(1.0, base_multiplier + (uses * 0.05))

    return base_multiplier


def calculate_defensive_power(params: LootParameters) -> float:
    """Calculate defensive power value (D).

    AC bonuses, resistances, immunities.
    """
    d = 0.0

    # AC bonus
    d += params.passive_bonuses.ac_bonus * AC_BONUS_VALUE

    # Resistances
    d += len(params.additional_properties.resistances) * RESISTANCE_VALUE

    # Immunities
    d += len(params.additional_properties.immunities) * IMMUNITY_VALUE

    return d


def calculate_control_utility(params: LootParameters) -> float:
    """Calculate control and utility power (C).

    Conditions, crowd control, utility effects.
    """
    c = 0.0

    # Conditions inflicted (assume they require saves)
    c += len(params.additional_properties.conditions_inflicted) * CONDITION_WITH_SAVE

    # Saving throw bonuses are utility
    c += len(params.passive_bonuses.saving_throw_bonuses) * UTILITY_BASE

    # Ability score bonuses
    c += len(params.passive_bonuses.ability_bonuses) * UTILITY_BASE

    # Active spell effects add utility
    if params.active_effect.enabled and params.active_effect.spell_name:
        c += UTILITY_BASE * 2

    return c


def get_reliability_multiplier(params: LootParameters) -> float:
    """Get reliability multiplier (R).

    Automatic effects are most reliable, saves least.
    """
    # Passive bonuses are automatic
    if (params.passive_bonuses.attack_bonus or
        params.passive_bonuses.damage_bonus or
        params.passive_bonuses.ac_bonus):
        return RELIABILITY_AUTOMATIC

    # Check for conditions that imply saves
    if params.additional_properties.conditions_inflicted:
        return RELIABILITY_SAVE_DC

    # Active effects often require attack rolls or saves
    if params.active_effect.enabled:
        return RELIABILITY_ATTACK_ROLL

    return RELIABILITY_AUTOMATIC


def calculate_structural_constraints(params: LootParameters) -> float:
    """Calculate structural constraint penalty (Kₐ).

    Attunement, class/alignment restrictions.
    """
    ka = 0.0

    if params.requires_attunement:
        ka += ATTUNEMENT_PENALTY

    ka += len(params.restrictions.class_restrictions) * CLASS_RESTRICTION_PENALTY
    ka += len(params.restrictions.alignment_restrictions) * ALIGNMENT_RESTRICTION_PENALTY

    return ka


def calculate_negative_effects(params: LootParameters) -> float:
    """Calculate negative effect penalty (Kₙ).

    Curses, side effects, drawbacks.
    """
    kn = 0.0

    if params.restrictions.has_curse:
        # Determine curse severity based on description
        curse_desc = (params.restrictions.curse_description or "").lower()
        if any(word in curse_desc for word in ["death", "kill", "destroy", "permanent"]):
            kn += MAJOR_CURSE_PENALTY
        else:
            kn += MINOR_CURSE_PENALTY

    # Side effects
    kn += len(params.restrictions.side_effects) * SIDE_EFFECT_PENALTY

    return kn


def calculate_power_score(params: LootParameters) -> float:
    """Calculate total power score using the balance formula.

    Formula: [(ΔDPR × A × U) + D + C] × R − (Kₐ + Kₙ)

    Args:
        params: The item parameters.

    Returns:
        The calculated power score.
    """
    dpr = calculate_dpr(params)
    a = get_action_economy_multiplier(params)
    u = get_usage_multiplier(params)
    d = calculate_defensive_power(params)
    c = calculate_control_utility(params)
    r = get_reliability_multiplier(params)
    ka = calculate_structural_constraints(params)
    kn = calculate_negative_effects(params)

    power_score = ((dpr * a * u) + d + c) * r - (ka + kn)

    return max(0, power_score)  # Power score can't be negative


def get_suggested_rarity(power_score: float) -> Rarity:
    """Suggest appropriate rarity based on power score.

    Args:
        power_score: The calculated power score.

    Returns:
        Suggested Rarity enum value.
    """
    for rarity, (min_power, max_power) in RARITY_POWER_RANGES.items():
        if min_power <= power_score < max_power:
            return rarity

    # If above all ranges, it's an artifact
    return Rarity.ARTIFACT


def get_power_score_details(params: LootParameters) -> dict:
    """Get detailed breakdown of power score calculation.

    Args:
        params: The item parameters.

    Returns:
        Dictionary with all component values and final score.
    """
    dpr = calculate_dpr(params)
    a = get_action_economy_multiplier(params)
    u = get_usage_multiplier(params)
    d = calculate_defensive_power(params)
    c = calculate_control_utility(params)
    r = get_reliability_multiplier(params)
    ka = calculate_structural_constraints(params)
    kn = calculate_negative_effects(params)

    power_score = ((dpr * a * u) + d + c) * r - (ka + kn)
    power_score = max(0, power_score)

    return {
        "dpr": round(dpr, 2),
        "action_economy": round(a, 2),
        "usage": round(u, 2),
        "defensive": round(d, 2),
        "control_utility": round(c, 2),
        "reliability": round(r, 2),
        "constraints": round(ka, 2),
        "negative_effects": round(kn, 2),
        "power_score": round(power_score, 2),
        "suggested_rarity": get_suggested_rarity(power_score),
    }
