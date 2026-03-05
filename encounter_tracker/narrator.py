"""AI combat narrative generator using OpenRouter."""

from openai import OpenAI

from config import OPENROUTER_BASE_URL, OPENROUTER_DEFAULT_MODEL


def generate_combat_narrative(log: list[str], api_key: str, context: str = "") -> str:
    """Generate an epic narrative summary of the combat from the log.

    Args:
        log: List of combat log entries.
        api_key: OpenRouter API key.
        context: Optional DM context (location, how combat started, time/date, etc.)

    Returns:
        A cinematic narrative paragraph describing the battle.
    """
    log_text = "\n".join(log)

    system_prompt = (
        "You are an expert Dungeons & Dragons narrator who transforms dry combat logs "
        "into epic, cinematic battle narratives. Write in a vivid, dramatic fantasy style "
        "with rich descriptions. Keep it to 2-4 paragraphs. Focus on the most dramatic "
        "moments: near-death experiences, killing blows, heroic saves, and the emotional "
        "arc of the fight."
    )

    context_block = f"\n\n## Combat Context (provided by the DM)\n{context.strip()}" if context.strip() else ""

    user_prompt = (
        f"Transform this combat log into an epic narrative:{context_block}\n\n"
        f"## Combat Log\n{log_text}\n\n"
        "Write the narrative as if recounting the battle to other adventurers at a tavern. "
        "Incorporate the DM context naturally into the story."
    )

    client = OpenAI(api_key=api_key, base_url=OPENROUTER_BASE_URL)
    response = client.chat.completions.create(
        model=OPENROUTER_DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content
