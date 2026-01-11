"""Combat logic utilities for the Encounter Tracker."""

import random
from .models import Creature


def roll_d20() -> int:
    """Roll a d20."""
    return random.randint(1, 20)


def roll_initiative(creature: Creature) -> int:
    """Roll initiative for a creature.

    Args:
        creature: The creature to roll initiative for.

    Returns:
        The initiative roll result (d20 + modifier).
    """
    roll = roll_d20()
    return roll + creature.initiative_modifier


def sort_by_initiative(creatures: list[Creature]) -> list[Creature]:
    """Sort creatures by initiative (highest first).

    Ties are broken by:
    1. Higher initiative modifier
    2. Players go before non-players
    3. Random if still tied

    Args:
        creatures: List of creatures to sort.

    Returns:
        Sorted list of creatures.
    """
    def sort_key(c: Creature) -> tuple:
        # Higher initiative first (negative for descending)
        # Higher modifier as tiebreaker
        # Players before non-players
        # Random final tiebreaker
        return (
            -c.initiative,
            -c.initiative_modifier,
            0 if c.is_player else 1,
            random.random(),
        )

    return sorted(creatures, key=sort_key)


def apply_damage(creature: Creature, damage: int) -> Creature:
    """Apply damage to a creature.

    Args:
        creature: The creature to damage.
        damage: Amount of damage to apply.

    Returns:
        Updated creature with new HP.
    """
    new_hp = max(0, creature.current_hp - damage)
    creature.current_hp = new_hp
    return creature


def apply_healing(creature: Creature, healing: int) -> Creature:
    """Apply healing to a creature.

    Args:
        creature: The creature to heal.
        healing: Amount of healing to apply.

    Returns:
        Updated creature with new HP.
    """
    new_hp = min(creature.max_hp, creature.current_hp + healing)
    creature.current_hp = new_hp
    return creature
