
import json
from pathlib import Path

DATA_FILE = Path(__file__).with_name("leave_alert_data.json")

DEFAULT_DATA = {
    "faculty_groups": {
        "Rahul Sharma": ["CSE-A", "CSE-B"],
        "Priya Verma": ["CSE-A"],
        "Aman Kumar": ["CSE-B"],
        "Neha Singh": ["CSE-A", "CSE-C"],
        "Arjun Patel": ["CSE-C"]
    },
    "minimum_required": {
        "CSE-A": 2,
        "CSE-B": 1,
        "CSE-C": 1
    },
    "leaves": []
}


def load_data():
    if not DATA_FILE.exists():
        save_data(DEFAULT_DATA)
        return json.loads(json.dumps(DEFAULT_DATA))

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError) as error:
        raise RuntimeError(
            "Could not read leave_alert_data.json. "
            "Please check the file."
        ) from error

    for key, value in DEFAULT_DATA.items():
        data.setdefault(key, json.loads(json.dumps(value)))

    return data


def save_data(data):
    temporary_file = DATA_FILE.with_suffix(".tmp")

    with temporary_file.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    temporary_file.replace(DATA_FILE)