
from storage import load_data, save_data

_initial_data = load_data()

FACULTY_GROUPS = {
    name: set(groups)
    for name, groups in _initial_data["faculty_groups"].items()
}

MINIMUM_REQUIRED = {
    group: int(count)
    for group, count in _initial_data["minimum_required"].items()
}


def save_configuration():
    data = load_data()

    data["faculty_groups"] = {
        name: sorted(groups)
        for name, groups in FACULTY_GROUPS.items()
    }

    data["minimum_required"] = MINIMUM_REQUIRED.copy()
    save_data(data)


def add_faculty(name, groups):
    name = name.strip()

    if not name:
        return False, "Faculty name cannot be empty."

    if name in FACULTY_GROUPS:
        return False, "Faculty already exists."

    groups = {
        group.strip().upper()
        for group in groups
        if group.strip()
    }

    if not groups:
        return False, "Enter at least one group."

    for group in groups:
        MINIMUM_REQUIRED.setdefault(group, 1)

    FACULTY_GROUPS[name] = groups
    save_configuration()

    return True, f"{name} added successfully."


def get_faculty_count(group):
    return sum(
        1 for groups in FACULTY_GROUPS.values()
        if group in groups
    )


def get_minimum_requirements():
    return MINIMUM_REQUIRED.copy()


def set_minimum_required(group, count):
    group = group.strip().upper()

    if not group:
        return False, "Group name cannot be empty."

    if count < 1:
        return False, "Minimum must be at least 1."

    MINIMUM_REQUIRED[group] = count
    save_configuration()

    return True, f"{group} minimum updated to {count}."


def display_faculty():
    print("\nFACULTY DIRECTORY")
    print("-" * 60)

    if not FACULTY_GROUPS:
        print("No faculty members configured.")
        return

    print(f"{'Faculty Name':<25} Assigned Groups")
    print("-" * 60)

    for name in sorted(FACULTY_GROUPS):
        groups = ", ".join(sorted(FACULTY_GROUPS[name]))
        print(f"{name:<25} {groups}")

    print("-" * 60)