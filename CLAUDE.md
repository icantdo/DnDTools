# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Streamlit application with two main features:
1. **AI Loot Creator** - Generate D&D 5e magic items using Gemini AI with detailed parameter configuration
2. **Encounter Tracker** - Combat order management with initiative, HP tracking, and conditions

## Commands

```bash
# Activate virtual environment (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

## Project Structure

```
├── app.py                    # Main Streamlit entry point with tabs
├── config.py                 # Configuration constants and environment loading
├── loot_creator/             # AI-powered magic item generation
│   ├── models.py             # Pydantic models for item parameters
│   ├── templates.py          # Gemini prompt templates
│   ├── generator.py          # Gemini API integration
│   ├── balance.py            # Power score calculation formula
│   └── ui.py                 # Streamlit UI components
├── encounter_tracker/        # Combat management
│   ├── models.py             # Creature and Encounter models
│   ├── combat.py             # Initiative and combat logic
│   └── ui.py                 # Streamlit UI components
├── utils/storage.py          # JSON file read/write utilities
└── data/                     # JSON storage for monsters, items, encounters
```

## Key Technical Details

- **Gemini API**: Uses `google-genai` library with `genai.Client()` and `gemini-2.0-flash` model
- **API Key**: Users enter their own key in the sidebar (stored in session only, never saved)
- **Fallback**: Can also use `.env` file with `GEMINI_API_KEY` for local development
- **State Management**: Uses `st.session_state` for encounter and generated item state
- **Data Persistence**: JSON files in `data/` directory

## Loot Creator Modes

### Quick Mode
Minimal input - just rarity and a description. AI decides everything else.

### Advanced Mode
Full control with 7 parameter categories (A-G):
- A) Base Identity: item type, subtype, rarity, attunement
- B) Passive Bonuses: attack, damage, AC, ability score bonuses
- C) Active Effects: spell-like effects with action economy
- D) Usage Limits: at-will, per rest, charges, single-use
- E) Triggers: on hit, when hit, at 0 HP, etc.
- F) Additional Properties: damage types, resistances, conditions
- G) Restrictions: class/alignment restrictions, curses, side effects

## Power Score Formula

Items are balanced using: `[(ΔDPR × A × U) + D + C] × R − (Kₐ + Kₙ)`

| Variable | Description |
|----------|-------------|
| ΔDPR | Damage per round increase |
| A | Action economy multiplier |
| U | Usage multiplier |
| D | Defensive power |
| C | Control/utility power |
| R | Reliability multiplier |
| Kₐ | Structural constraints (penalty) |
| Kₙ | Negative effects (penalty) |

Power ranges by rarity: Common (0-2), Uncommon (2-5), Rare (5-10), Very Rare (10-18), Legendary (18-30), Artifact (30+)

## Codebase Overview

A Streamlit app (~37k tokens, 35 files) with three AI-powered feature modules plus Patreon OAuth gating. All AI calls go through OpenRouter (model: `deepseek/deepseek-v3.2`) via the OpenAI-compatible SDK. The loot creator follows a UI → prompt → OpenRouter → Pydantic model pipeline; the encounter tracker is self-contained with mutable Pydantic state in session state; the monster generator produces a stat block + dungeon room in a single API call. Patreon OAuth gates Loot Creator and Monster Generator tabs; the Encounter Tracker is always free.

**Stack:** Python, Streamlit, Pydantic v2, openai SDK (OpenRouter), requests, python-dotenv
**Structure:** `app.py` (OAuth + tab routing) → `loot_creator/`, `encounter_tracker/`, `monster_generator/` UI modules → `auth/patreon.py` → shared `config.py` + `utils/` + `data/` JSON files

For detailed architecture, module dependencies, data flow diagrams, and navigation guide, see [docs/CODEBASE_MAP.md](docs/CODEBASE_MAP.md).
