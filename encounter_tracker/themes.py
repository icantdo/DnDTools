"""Base CSS for the Encounter Tracker."""

BASE_CSS = """
<style>
.creature-card-bloodied {
    border: 2px solid #e53935 !important;
    background-color: rgba(229, 57, 53, 0.05) !important;
}
.creature-card-active {
    border: 2px solid #4CAF50 !important;
    background-color: rgba(76, 175, 80, 0.04) !important;
}
</style>
"""


def get_encounter_css() -> str:
    """Return the base encounter tracker CSS."""
    return BASE_CSS
