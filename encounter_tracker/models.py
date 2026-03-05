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

    # Action economy counters (totals configurable per creature type)
    actions_total: int = 1
    bonus_actions_total: int = 1
    reactions_total: int = 1
    legendary_actions_total: int = 0  # 0 = not a legendary creature

    actions_used: int = 0
    bonus_actions_used: int = 0
    reactions_used: int = 0
    legendary_actions_used: int = 0

    # Death saving throws (relevant only at 0 HP)
    death_save_successes: int = 0
    death_save_failures: int = 0

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

    @property
    def is_stable(self) -> bool:
        """Check if creature has 3 death save successes."""
        return self.death_save_successes >= 3

    @property
    def is_dead(self) -> bool:
        """Check if creature has 3 death save failures."""
        return self.death_save_failures >= 3

    def reset_turn_actions(self) -> None:
        """Reset per-turn action counters (call at the start of this creature's turn)."""
        self.actions_used = 0
        self.bonus_actions_used = 0
        self.reactions_used = 0

    def reset_death_saves(self) -> None:
        """Reset death saving throws (call when creature receives any healing)."""
        self.death_save_successes = 0
        self.death_save_failures = 0


class Encounter(BaseModel):
    """An encounter with multiple creatures."""
    name: str = "New Encounter"
    creatures: list[Creature] = Field(default_factory=list)
    current_turn_index: int = 0
    round_number: int = 1
    is_active: bool = False
    combat_log: list[str] = Field(default_factory=list)

    @property
    def current_creature(self) -> Optional[Creature]:
        """Get the creature whose turn it currently is."""
        if not self.creatures or self.current_turn_index >= len(self.creatures):
            return None
        return self.creatures[self.current_turn_index]

    def log(self, message: str) -> None:
        """Append a combat log entry prefixed with the current round number."""
        self.combat_log.append(f"Round {self.round_number}: {message}")

    def next_turn(self) -> None:
        """Advance to the next turn."""
        if not self.creatures:
            return

        self.current_turn_index += 1
        new_round = False
        if self.current_turn_index >= len(self.creatures):
            self.current_turn_index = 0
            self.round_number += 1
            new_round = True

        # Reset per-turn action counters for the now-active creature
        active = self.current_creature
        if active:
            active.reset_turn_actions()
            # Legendary actions reset at the start of each new round
            if new_round:
                for c in self.creatures:
                    c.legendary_actions_used = 0
            self.log(f"{active.name}'s turn begins")

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
        self.combat_log = []
        for c in self.creatures:
            c.reset_turn_actions()
            c.legendary_actions_used = 0

    def remove_creature(self, index: int) -> None:
        """Remove a creature from the encounter."""
        if 0 <= index < len(self.creatures):
            self.creatures.pop(index)
            # Adjust current turn index if needed
            if self.current_turn_index >= len(self.creatures):
                self.current_turn_index = max(0, len(self.creatures) - 1)
