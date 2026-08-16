import json
from pathlib import Path


MEMORY_FILE = Path(__file__).parent / "memory.json"


def load_memory():
    """Load persistent memories from disk."""

    if not MEMORY_FILE.exists():
        return {"facts": []}

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            return {"facts": []}

        if "facts" not in data or not isinstance(data["facts"], list):
            data["facts"] = []

        return data

    except (json.JSONDecodeError, OSError):
        return {"facts": []}


def save_memory(memory):
    """Save persistent memories to disk."""

    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(MEMORY_FILE, "w", encoding="utf-8") as file:
        json.dump(memory, file, indent=4, ensure_ascii=False)


def add_memory(fact):
    """Add a fact to persistent memory."""

    fact = fact.strip()

    if not fact:
        return False

    memory = load_memory()

    # Avoid duplicates
    if fact.lower() in [item.lower() for item in memory["facts"]]:
        return False

    memory["facts"].append(fact)
    save_memory(memory)

    return True


def remove_memory(fact):
    """Remove a matching memory."""

    memory = load_memory()

    original_count = len(memory["facts"])

    memory["facts"] = [
        item for item in memory["facts"]
        if item.lower() != fact.lower()
    ]

    if len(memory["facts"]) != original_count:
        save_memory(memory)
        return True

    return False


def get_memory():
    """Return all stored memories."""

    return load_memory()["facts"]


def clear_memory():
    """Clear all persistent memories."""

    save_memory({"facts": []})