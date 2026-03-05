"""OpenRouter AI integration for magic item generation."""

import json
import re
from typing import Optional

from openai import OpenAI

from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_DEFAULT_MODEL
from .models import LootParameters, QuickLootParameters, MagicItem
from .templates import build_item_prompt, build_quick_item_prompt


def _get_api_key(user_api_key: Optional[str] = None) -> str:
    """Get the API key to use, preferring user-provided key.

    Args:
        user_api_key: Optional user-provided API key.

    Returns:
        The API key to use.

    Raises:
        ValueError: If no API key is available.
    """
    api_key = user_api_key or OPENROUTER_API_KEY

    if not api_key:
        raise ValueError(
            "No API key configured. Please enter your OpenRouter API key in the sidebar. "
            "Get one at https://openrouter.ai/keys"
        )

    return api_key


def _call_openrouter(prompt: str, api_key: str) -> str:
    """Call the OpenRouter API with a prompt.

    Args:
        prompt: The prompt to send.
        api_key: The OpenRouter API key.

    Returns:
        The response text.
    """
    client = OpenAI(api_key=api_key, base_url=OPENROUTER_BASE_URL)
    response = client.chat.completions.create(
        model=OPENROUTER_DEFAULT_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def _extract_json_from_response(text: str) -> Optional[dict]:
    """Extract JSON from the AI response.

    Args:
        text: The raw response text from the AI.

    Returns:
        Parsed JSON dict or None if parsing fails.
    """
    # Try to find JSON in code blocks first
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if json_match:
        try:
            return json.loads(json_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try to parse the entire response as JSON
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in the text
    json_match = re.search(r"\{[\s\S]*\}", text)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def generate_item(params: LootParameters, api_key: Optional[str] = None) -> MagicItem:
    """Generate a magic item using OpenRouter AI.

    Args:
        params: The parameters defining the item to generate.
        api_key: Optional user-provided API key. If not provided, uses env variable.

    Returns:
        A generated MagicItem.

    Raises:
        ValueError: If the API key is not configured or response parsing fails.
        Exception: For API errors.
    """
    key = _get_api_key(api_key)
    prompt = build_item_prompt(params)
    response_text = _call_openrouter(prompt, key)

    item_data = _extract_json_from_response(response_text)

    if not item_data:
        raise ValueError(f"Failed to parse AI response as JSON. Raw response:\n{response_text}")

    return MagicItem(
        name=item_data.get("name", "Unknown Item"),
        item_type=item_data.get("item_type", params.item_type.value),
        subtype=item_data.get("subtype", params.item_subtype.value),
        rarity=item_data.get("rarity", params.rarity.value),
        requires_attunement=item_data.get("requires_attunement", params.requires_attunement),
        attunement_requirement=item_data.get("attunement_requirement"),
        description=item_data.get("description", "No description provided."),
        properties=item_data.get("properties", []),
        curse=item_data.get("curse"),
        lore=item_data.get("lore"),
        gold_value=item_data.get("gold_value"),
        crafting_materials=item_data.get("crafting_materials"),
        suggested_cr=item_data.get("suggested_cr"),
    )


def generate_quick_item(params: QuickLootParameters, api_key: Optional[str] = None) -> MagicItem:
    """Generate a magic item using OpenRouter AI with minimal input.

    The AI decides item type, subtype, and all properties based on
    just the rarity and theme description.

    Args:
        params: The quick parameters (rarity + theme).
        api_key: Optional user-provided API key. If not provided, uses env variable.

    Returns:
        A generated MagicItem.

    Raises:
        ValueError: If the API key is not configured or response parsing fails.
        Exception: For API errors.
    """
    key = _get_api_key(api_key)
    prompt = build_quick_item_prompt(params)
    response_text = _call_openrouter(prompt, key)

    item_data = _extract_json_from_response(response_text)

    if not item_data:
        raise ValueError(f"Failed to parse AI response as JSON. Raw response:\n{response_text}")

    return MagicItem(
        name=item_data.get("name", "Unknown Item"),
        item_type=item_data.get("item_type", "Wondrous Item"),
        subtype=item_data.get("subtype", "Unknown"),
        rarity=item_data.get("rarity", params.rarity.value),
        requires_attunement=item_data.get("requires_attunement", False),
        attunement_requirement=item_data.get("attunement_requirement"),
        description=item_data.get("description", "No description provided."),
        properties=item_data.get("properties", []),
        curse=item_data.get("curse"),
        lore=item_data.get("lore"),
        gold_value=item_data.get("gold_value"),
        crafting_materials=item_data.get("crafting_materials"),
        suggested_cr=item_data.get("suggested_cr"),
    )
