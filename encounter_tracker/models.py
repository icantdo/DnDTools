"""Data models for the Encounter Tracker."""

from typing import Optional
from pydantic import BaseModel, Field


class Creature(BaseModel):
    """A creature in an encounter (player, enemy, or NPC)."""
    name: str
    initiative: int = 0
    initiative_modifier: int = 0
    current_hp: int = Field(ge=0)
    max_hp: int = Field(ge=1)
    armor_class: int = Field(default=10, ge=0)
    is_player: bool = False
    conditions: list[str] = Field(default_factory=list)
    notes: Optional[str] = None

    @property
    def hp_percentage(self) -> float:
        """Get HP as a percentage of max HP."""
        return (self.current_hp / self.max_hp) * 100

    @property
    def is_bloodied(self) -> bool:
        """Check if creature is at or below 50% HP."""
        return self.current_hp <= self.max_hp / 2

    @property
    def is_unconscious(self) -> bool:
        """Check if creature is at 0 HP."""
        return self.current_hp == 0


class Encounter(BaseModel):
    """An encounter with multiple creatures."""
    name: str = "New Encounter"
    creatures: list[Creature] = Field(default_factory=list)
    current_turn_index: int = 0
    round_number: int = 1
    is_active: bool = False

    @property
    def current_creature(self) -> Optional[Creature]:
        """Get the creature whose turn it currently is."""
        if not self.creatures or self.current_turn_index >= len(self.creatures):
            return None
        return self.creatures[self.current_turn_index]

    def next_turn(self) -> None:
        """Advance to the next turn."""
        if not self.creatures:
            return

        self.current_turn_index += 1
        if self.current_turn_index >= len(self.creatures):
            self.current_turn_index = 0
            self.round_number += 1

    def prev_turn(self) -> None:
        """Go back to the previous turn."""
        if not self.creatures:
            return

        self.current_turn_index -= 1
        if self.current_turn_index < 0:
            self.current_turn_index = len(self.creatures) - 1
            self.round_number = max(1, self.round_number - 1)

    def reset_combat(self) -> None:
        """Reset the combat to round 1, turn 1."""
        self.current_turn_index = 0
        self.round_number = 1
        self.is_active = False

    def remove_creature(self, index: int) -> None:
        """Remove a creature from the encounter."""
        if 0 <= index < len(self.creatures):
            self.creatures.pop(index)
            # Adjust current turn index if needed
            if self.current_turn_index >= len(self.creatures):
                self.current_turn_index = max(0, len(self.creatures) - 1)
