import json
from pathlib import Path


# Always use the memory.json beside this file.
# This prevents Windows/VS Code from accidentally using
# the wrong working directory.

MEMORY_FILE = Path(__file__).resolve().parent / "memory.json"


def _load_data():
    if not MEMORY_FILE.exists():
        return {"facts": []}

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return {"facts": []}

        if not isinstance(data.get("facts"), list):
            data["facts"] = []

        return data

    except (json.JSONDecodeError, OSError):
        return {"facts": []}


def _save_data(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def get_memory():
    data = _load_data()
    return data["facts"]


def add_memory(fact):
    fact = fact.strip()

    if not fact:
        return False

    data = _load_data()

    # Prevent duplicates
    if fact.lower() in [x.lower() for x in data["facts"]]:
        return False

    data["facts"].append(fact)
    _save_data(data)

    return True


def remove_memory(fact):
    fact = fact.strip().lower()

    data = _load_data()

    original_count = len(data["facts"])

    data["facts"] = [
        item for item in data["facts"]
        if item.lower() != fact
    ]

    if len(data["facts"]) == original_count:
        return False

    _save_data(data)

    return True


def clear_memory():
    _save_data({"facts": []})


def memory_count():
    return len(get_memory())