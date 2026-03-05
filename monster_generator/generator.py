"""OpenRouter AI integration for monster and dungeon room generation."""

import json
import re
from typing import Optional

from openai import OpenAI

from config import OPENROUTER_BASE_URL, OPENROUTER_DEFAULT_MODEL
from .models import GeneratorParams, GeneratorOutput, MonsterStatBlock, DungeonRoom


def _cr_display(cr: float) -> str:
    """Convert a float CR to a display string (e.g. 0.125 -> '1/8')."""
    cr_map = {0.125: "1/8", 0.25: "1/4", 0.5: "1/2"}
    if cr in cr_map:
        return cr_map[cr]
    return str(int(cr))


def build_monster_prompt(params: GeneratorParams) -> str:
    """Build the Gemini prompt for monster + dungeon room generation."""
    cr_str = _cr_display(params.cr)
    return f"""You are an expert D&D 5th Edition encounter designer. Create a balanced, thematic monster and its dungeon room.

## Requirements
- **Challenge Rating:** {cr_str}
- **Theme:** {params.theme}

## Your Task
1. Design a unique monster appropriate for CR {cr_str} with the given theme
2. Create the encounter area / dungeon room where this monster lives

## Respond in this exact JSON format:
```json
{{
  "monster": {{
    "name": "Monster name",
    "cr": "{cr_str}",
    "hp": integer HP total,
    "ac": integer AC,
    "speed": "30 ft.",
    "ability_scores": {{"STR": 10, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10}},
    "saving_throws": ["list of saving throw proficiencies, e.g. 'CON +5'"],
    "skills": ["Perception +3", "Stealth +5"],
    "damage_resistances": ["list or null"],
    "damage_immunities": ["list or null"],
    "condition_immunities": ["list or null"],
    "senses": "Darkvision 60 ft., passive Perception 13",
    "languages": "Common, Goblin",
    "special_abilities": [
      "Ability Name. Description of the special ability."
    ],
    "actions": [
      "Multiattack. The monster makes two attacks.",
      "Attack Name. Melee Weapon Attack: +X to hit, reach 5 ft., one target. Hit: Xd6 + X damage type damage."
    ],
    "legendary_actions": [],
    "description": "Brief physical description of the monster"
  }},
  "room": {{
    "name": "Room name",
    "atmosphere": "One sentence capturing the feel of the space",
    "description": "2-3 sentence vivid description of the room layout, lighting, smells, sounds",
    "traps": [
      "Trap name: DC X Perception to notice, DC X Dexterity save or take Xd6 damage"
    ],
    "environmental_features": [
      "Feature that can be used tactically during combat"
    ],
    "treasure_hint": "A hint at what treasure might be found here"
  }}
}}
```

Make the monster feel unique and dangerous for its CR. Ensure all numbers are balanced for D&D 5e."""


def _extract_json(text: str) -> Optional[dict]:
    """Extract JSON from the AI response."""
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if json_match:
        try:
            return json.loads(json_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    json_match = re.search(r"\{[\s\S]*\}", text)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def generate_monster_and_room(params: GeneratorParams, api_key: str) -> GeneratorOutput:
    """Generate a monster stat block and dungeon room using OpenRouter.

    Args:
        params: CR and theme for the generator.
        api_key: OpenRouter API key.

    Returns:
        A GeneratorOutput with monster and room data.

    Raises:
        ValueError: If the response cannot be parsed.
    """
    client = OpenAI(api_key=api_key, base_url=OPENROUTER_BASE_URL)
    prompt = build_monster_prompt(params)

    response = client.chat.completions.create(
        model=OPENROUTER_DEFAULT_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    response_text = response.choices[0].message.content

    data = _extract_json(response_text)
    if not data:
        raise ValueError(f"Failed to parse AI response as JSON.\nRaw response:\n{response_text}")

    monster_data = data.get("monster", {})
    room_data = data.get("room", {})

    monster = MonsterStatBlock(
        name=monster_data.get("name", "Unknown Creature"),
        cr=monster_data.get("cr", _cr_display(params.cr)),
        hp=monster_data.get("hp", 10),
        ac=monster_data.get("ac", 10),
        speed=monster_data.get("speed", "30 ft."),
        ability_scores=monster_data.get("ability_scores", {}),
        saving_throws=monster_data.get("saving_throws") or [],
        skills=monster_data.get("skills") or [],
        damage_resistances=monster_data.get("damage_resistances") or [],
        damage_immunities=monster_data.get("damage_immunities") or [],
        condition_immunities=monster_data.get("condition_immunities") or [],
        senses=monster_data.get("senses"),
        languages=monster_data.get("languages"),
        special_abilities=monster_data.get("special_abilities", []),
        actions=monster_data.get("actions", []),
        legendary_actions=monster_data.get("legendary_actions", []),
        description=monster_data.get("description"),
    )

    room = DungeonRoom(
        name=room_data.get("name", "Unknown Room"),
        atmosphere=room_data.get("atmosphere", ""),
        description=room_data.get("description", ""),
        traps=room_data.get("traps", []),
        environmental_features=room_data.get("environmental_features", []),
        treasure_hint=room_data.get("treasure_hint", ""),
    )

    return GeneratorOutput(monster=monster, room=room)
