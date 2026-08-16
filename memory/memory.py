import json
from pathlib import Path


MEMORY_FILE = Path(__file__).parent.parent / "memory.json"


def load_memory_data():

    if not MEMORY_FILE.exists():
        return {"facts": []}

    try:

        with open(
            MEMORY_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if not isinstance(data, dict):
            return {"facts": []}

        if not isinstance(data.get("facts"), list):
            data["facts"] = []

        return data

    except (
        json.JSONDecodeError,
        OSError
    ):

        return {"facts": []}


def save_memory_data(data):

    with open(
        MEMORY_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )


def get_memory():

    data = load_memory_data()

    return data["facts"]


def add_memory(fact):

    fact = fact.strip()

    if not fact:
        return False

    data = load_memory_data()

    for existing in data["facts"]:

        if (
            existing.lower().strip()
            == fact.lower().strip()
        ):
            return False

    data["facts"].append(fact)

    save_memory_data(data)

    return True


def remove_memory(fact):

    fact = fact.strip()

    data = load_memory_data()

    original_length = len(data["facts"])

    data["facts"] = [
        existing
        for existing in data["facts"]
        if existing.lower().strip()
        != fact.lower().strip()
    ]

    if len(data["facts"]) == original_length:
        return False

    save_memory_data(data)

    return True


def clear_memory():

    save_memory_data({
        "facts": []
    })