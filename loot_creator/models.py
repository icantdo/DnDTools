"""Data models for the Loot Creator."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ItemType(str, Enum):
    """Main item type categories."""
    WEAPON = "Weapon"
    ARMOR = "Armor"
    RING = "Ring"
    WONDROUS_ITEM = "Wondrous Item"
    POTION = "Potion"
    SCROLL = "Scroll"


class ItemSubtype(str, Enum):
    """Specific item subtypes."""
    # Weapons
    LONGSWORD = "Longsword"
    SHORTSWORD = "Shortsword"
    GREATSWORD = "Greatsword"
    DAGGER = "Dagger"
    BATTLEAXE = "Battleaxe"
    GREATAXE = "Greataxe"
    WARHAMMER = "Warhammer"
    MAUL = "Maul"
    SPEAR = "Spear"
    HALBERD = "Halberd"
    LONGBOW = "Longbow"
    SHORTBOW = "Shortbow"
    CROSSBOW = "Crossbow"
    STAFF = "Staff"
    MACE = "Mace"
    FLAIL = "Flail"
    RAPIER = "Rapier"
    SCIMITAR = "Scimitar"
    TRIDENT = "Trident"

    # Armor
    PLATE_ARMOR = "Plate Armor"
    CHAIN_MAIL = "Chain Mail"
    SCALE_MAIL = "Scale Mail"
    LEATHER_ARMOR = "Leather Armor"
    STUDDED_LEATHER = "Studded Leather"
    SHIELD = "Shield"
    HELMET = "Helmet"
    GAUNTLETS = "Gauntlets"
    BOOTS = "Boots"

    # Wondrous Items
    CLOAK = "Cloak"
    AMULET = "Amulet"
    BELT = "Belt"
    BRACERS = "Bracers"
    CIRCLET = "Circlet"
    GLOVES = "Gloves"
    GOGGLES = "Goggles"
    HAT = "Hat"
    ROBE = "Robe"
    BAG = "Bag"
    CAPE = "Cape"
    MANTLE = "Mantle"

    # Ring
    RING = "Ring"

    # Consumables
    POTION = "Potion"
    SCROLL = "Scroll"


class Rarity(str, Enum):
    """Item rarity levels."""
    COMMON = "Common"
    UNCOMMON = "Uncommon"
    RARE = "Rare"
    VERY_RARE = "Very Rare"
    LEGENDARY = "Legendary"
    ARTIFACT = "Artifact"


class ActionEconomy(str, Enum):
    """Action types for active effects."""
    ACTION = "Action"
    BONUS_ACTION = "Bonus Action"
    REACTION = "Reaction"
    FREE = "Free Action"


class TargetType(str, Enum):
    """Target types for effects."""
    SELF = "Self"
    SINGLE_TARGET = "Single Target"
    AREA = "Area"
    MULTIPLE_TARGETS = "Multiple Targets"


class UsageLimit(str, Enum):
    """Usage limitation types."""
    AT_WILL = "At-Will"
    PER_LONG_REST = "Per Long Rest"
    PER_SHORT_REST = "Per Short Rest"
    CHARGES = "Charges"
    SINGLE_USE = "Single Use"


class TriggerType(str, Enum):
    """Trigger conditions for effects."""
    ON_HIT = "On Hit"
    WHEN_HIT = "When You Are Hit"
    AT_ZERO_HP = "When You Drop to 0 HP"
    AS_REACTION = "As a Reaction When..."
    AT_DAWN = "At Dawn"
    AT_DUSK = "At Dusk"
    ON_CRITICAL = "On Critical Hit"
    ALWAYS_ACTIVE = "Always Active (Passive)"


class PassiveBonuses(BaseModel):
    """Passive numerical bonuses."""
    attack_bonus: int = Field(default=0, ge=0, le=3)
    damage_bonus: int = Field(default=0, ge=0, le=3)
    ac_bonus: int = Field(default=0, ge=0, le=3)
    ability_bonuses: list[str] = Field(default_factory=list)  # e.g., ["+2 STR", "+1 DEX"]
    saving_throw_bonuses: list[str] = Field(default_factory=list)


class ActiveEffect(BaseModel):
    """Active spell-like effects."""
    enabled: bool = False
    spell_name: Optional[str] = None
    spell_level: Optional[int] = Field(default=None, ge=1, le=9)
    action_economy: ActionEconomy = ActionEconomy.ACTION
    target_type: TargetType = TargetType.SELF


class UsageLimits(BaseModel):
    """Usage limitation configuration."""
    limit_type: UsageLimit = UsageLimit.AT_WILL
    uses_per_rest: Optional[int] = Field(default=None, ge=1, le=10)
    max_charges: Optional[int] = Field(default=None, ge=1, le=20)
    regain_charges: Optional[str] = None  # e.g., "1d6+1 at dawn"


class AdditionalProperties(BaseModel):
    """Additional item properties."""
    damage_type_change: Optional[str] = None
    resistances: list[str] = Field(default_factory=list)
    immunities: list[str] = Field(default_factory=list)
    conditions_inflicted: list[str] = Field(default_factory=list)
    visual_effects: Optional[str] = None


class Restrictions(BaseModel):
    """Item restrictions and costs."""
    class_restrictions: list[str] = Field(default_factory=list)
    alignment_restrictions: list[str] = Field(default_factory=list)
    has_curse: bool = False
    curse_description: Optional[str] = None
    side_effects: list[str] = Field(default_factory=list)


class LootParameters(BaseModel):
    """Complete parameters for generating a magic item."""
    # A) Base Identity
    item_type: ItemType = ItemType.WEAPON
    item_subtype: ItemSubtype = ItemSubtype.LONGSWORD
    rarity: Rarity = Rarity.UNCOMMON
    requires_attunement: bool = False

    # B) Passive Numerical Bonuses
    passive_bonuses: PassiveBonuses = Field(default_factory=PassiveBonuses)

    # C) Active Effects
    active_effect: ActiveEffect = Field(default_factory=ActiveEffect)

    # D) Usage Limits
    usage_limits: UsageLimits = Field(default_factory=UsageLimits)

    # E) Triggers
    triggers: list[TriggerType] = Field(default_factory=list)

    # F) Additional Properties
    additional_properties: AdditionalProperties = Field(default_factory=AdditionalProperties)

    # G) Restrictions & Costs
    restrictions: Restrictions = Field(default_factory=Restrictions)

    # Extra guidance for AI
    theme_keywords: Optional[str] = None  # e.g., "fire, phoenix, rebirth"
    power_level_notes: Optional[str] = None


class MagicItem(BaseModel):
    """Generated magic item."""
    name: str
    item_type: str
    subtype: str
    rarity: str
    requires_attunement: bool
    attunement_requirement: Optional[str] = None
    description: str
    properties: list[str] = Field(default_factory=list)
    curse: Optional[str] = None
    lore: Optional[str] = None


class QuickLootParameters(BaseModel):
    """Simplified parameters for quick item generation.

    Only requires rarity and theme - AI decides everything else.
    """
    rarity: Rarity = Rarity.UNCOMMON
    theme_description: str = Field(
        default="",
        description="Describe what kind of item you want, e.g., 'fire sword for a paladin' or 'mysterious ring that whispers'"
    )
