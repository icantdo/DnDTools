"""Data models for the CR-Based Monster/Dungeon Generator."""

from typing import Optional
from pydantic import BaseModel, Field


class GeneratorParams(BaseModel):
    """Input parameters for monster/dungeon generation."""
    cr: float = Field(ge=0, description="Challenge Rating (e.g. 0.125, 0.5, 1, 5, 20)")
    theme: str = Field(description="Theme description, e.g. 'swamp boss', 'undead lich lair'")


class MonsterStatBlock(BaseModel):
    """A D&D 5e monster stat block."""
    name: str
    cr: str  # e.g. "5" or "1/2"
    hp: int
    ac: int
    speed: str  # e.g. "30 ft., swim 30 ft."
    ability_scores: dict[str, int] = Field(default_factory=dict)  # STR, DEX, CON, INT, WIS, CHA
    saving_throws: Optional[list[str]] = None
    skills: Optional[list[str]] = None
    damage_resistances: Optional[list[str]] = None
    damage_immunities: Optional[list[str]] = None
    condition_immunities: Optional[list[str]] = None
    senses: Optional[str] = None
    languages: Optional[str] = None
    special_abilities: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    legendary_actions: list[str] = Field(default_factory=list)
    description: Optional[str] = None


class DungeonRoom(BaseModel):
    """A thematic dungeon room/encounter area."""
    name: str
    atmosphere: str
    description: str
    traps: list[str] = Field(default_factory=list)
    environmental_features: list[str] = Field(default_factory=list)
    treasure_hint: str = ""


class GeneratorOutput(BaseModel):
    """Full output from the monster/dungeon generator."""
    monster: MonsterStatBlock
    room: DungeonRoom
