# CLAUDE.md

## Codebase Overview

**DnDTools** is a **Streamlit** web app offering two D&D 5e tools in one tabbed
page: a **Loot Creator** (generates balanced magic items via the Google Gemini
API, with a quantitative power-scoring system) and an **Encounter Tracker**
(combat/initiative tracker). Pure Python; JSON files in `data/` for persistence.

**Stack**: Python, Streamlit, google-genai (Gemini), Pydantic v2, python-dotenv.

**Structure**:
- `app.py` — entry point (`streamlit run app.py`): page config, sidebar API-key
  input, and the two feature tabs.
- `config.py` — file paths, D&D reference lists, `GEMINI_MODEL`, `.env` loading.
- `loot_creator/` — `models.py`, `balance.py` (power-score formula),
  `templates.py` (prompts), `generator.py` (Gemini calls), `ui.py`.
- `encounter_tracker/` — `models.py`, `combat.py`, `ui.py`.
- `utils/storage.py` — shared `load_json` / `save_json`.
- `data/` — `srd_monsters.json` (read-only), `saved_encounters.json`,
  `saved_items.json`.

**Run**: `pip install -r requirements.txt` then `streamlit run app.py` from the
repo root (paths are relative). Gemini needs an API key — entered in the sidebar
at runtime or set as `GEMINI_API_KEY` in `.env`.

**Conventions**: Feature packages each have `models.py` + `ui.py` + a logic
module. Pydantic v2 models (`.model_dump()` to persist). Enums inherit
`(str, Enum)`. UI entry points are named `render_*`. All file I/O goes through
`utils`.

For detailed architecture, data-flow diagrams, gotchas, and a navigation guide,
see [docs/CODEBASE_MAP.md](docs/CODEBASE_MAP.md).
