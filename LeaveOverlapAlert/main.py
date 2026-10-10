
from datetime import date, timedelta

from storage import load_data, save_data
from group_manager import (
    FACULTY_GROUPS,
    add_faculty,
    display_faculty,
    get_faculty_count,
    get_minimum_requirements,
    set_minimum_required
)
from alerts import generate_alerts, sweep_line_overlaps


def divider(char="=", width=72):
    print(char * width)


def pause():
    # Return to the main menu automatically.
    pass


def read_date(prompt):
    while True:
        value = input(prompt).strip()

        try:
            return date.fromisoformat(value)
        except ValueError:
            print("Invalid date. Use YYYY-MM-DD, e.g. 2026-10-10.")


def register_faculty():
    divider()
    print("FACULTY MANAGEMENT")

    name = input("Faculty name: ").strip()

    groups = [
        group.strip().upper()
        for group in input(
            "Assigned groups (comma-separated, e.g. CSE-A,CSE-B): "
        ).split(",")
        if group.strip()
    ]

    success, message = add_faculty(name, groups)
    print(("\nSUCCESS: " if success else "\nNOTICE: ") + message)


def register_leave():
    data = load_data()

    divider()
    print("REGISTER FACULTY LEAVE")

    if not FACULTY_GROUPS:
        print("No faculty configured. Add faculty first.")
        return

    print("\nAvailable faculty:")

    for index, name in enumerate(sorted(FACULTY_GROUPS), start=1):
        groups = ", ".join(sorted(FACULTY_GROUPS[name]))
        print(f"{index}. {name} ({groups})")

    name = input("\nFaculty name: ").strip()

    if name not in FACULTY_GROUPS:
        print("Faculty not found. Please check the name.")
        return

    assigned_groups = sorted(FACULTY_GROUPS[name])

    start = read_date("Leave start date (YYYY-MM-DD): ")
    end = read_date("Leave end date   (YYYY-MM-DD): ")

    if end < start:
        print("End date cannot be earlier than start date.")
        return

    leaves = data.setdefault("leaves", [])
    added_groups = []
    duplicate_groups = []

    for group in assigned_groups:
        duplicate = any(
            leave["faculty"] == name
            and leave["group"] == group
            and leave["start_date"] == start.isoformat()
            and leave["end_date"] == end.isoformat()
            for leave in leaves
        )

        if duplicate:
            duplicate_groups.append(group)
        else:
            leaves.append({
                "faculty": name,
                "group": group,
                "start_date": start.isoformat(),
                "end_date": end.isoformat()
            })
            added_groups.append(group)

    if added_groups:
        save_data(data)
        print(f"\nSUCCESS: Leave registered for {name}.")
        print("Groups:", ", ".join(added_groups))
        print(f"Leave period: {start.isoformat()} to {end.isoformat()}")

    if duplicate_groups:
        print(
            "Identical leave records already exist for: "
            + ", ".join(duplicate_groups)
        )

    if not added_groups:
        print("No new leave records were added.")


def mark_faculty_returned():
    data = load_data()
    leaves = data.get("leaves", [])

    divider()
    print("MARK FACULTY AS RETURNED")

    today = date.today()

    # Show faculty whose leave records include today.
    faculty_on_leave = sorted({
        leave["faculty"]
        for leave in leaves
        if date.fromisoformat(leave["start_date"]) <= today
        <= date.fromisoformat(leave["end_date"])
    })

    if not faculty_on_leave:
        print("No faculty leave records cover today.")
        print("You can still check saved records using option 6.")
        return

    print("\nFaculty currently recorded as on leave:")

    for index, name in enumerate(faculty_on_leave, start=1):
        print(f"{index}. {name}")

    name = input("\nFaculty name: ").strip()

    if name not in faculty_on_leave:
        print("Faculty not found in the list.")
        return

    return_date = read_date("Actual return date (YYYY-MM-DD): ")

    if return_date > today:
        print("Return date cannot be in the future.")
        return

    updated = 0

    for leave in leaves:
        if leave["faculty"] != name:
            continue

        start = date.fromisoformat(leave["start_date"])
        end = date.fromisoformat(leave["end_date"])

        # Only update leave records covering the return date.
        if start <= return_date <= end:
            new_end = return_date - timedelta(days=1)

            if new_end < start:
                print(
                    f"Cannot shorten the {leave['group']} leave record: "
                    "return date is on or before its start date."
                )
                continue

            leave["end_date"] = new_end.isoformat()
            updated += 1

    if updated:
        save_data(data)
        print(f"\n{name} marked as returned on {return_date.isoformat()}.")
        print(f"Updated leave records: {updated}")
        print("The return date will count as an available day.")
    else:
        print("No matching leave records were updated.")


def configure_requirements():
    divider()
    print("GROUP STAFFING SETTINGS")

    requirements = get_minimum_requirements()

    groups = sorted(
        set(requirements)
        | {
            group
            for assigned in FACULTY_GROUPS.values()
            for group in assigned
        }
    )

    if not groups:
        print("No groups available. Add faculty first.")
        return

    print("\nCurrent requirements:")

    for group in groups:
        print(f"  {group}: minimum {requirements.get(group, 1)} faculty")

    group = input(
        "\nGroup to update (press Enter to cancel): "
    ).strip().upper()

    if not group:
        return

    if group not in groups:
        print("Unknown group.")
        return

    try:
        count = int(input(f"New minimum for {group}: ").strip())
    except ValueError:
        print("Please enter a whole number.")
        return

    success, message = set_minimum_required(group, count)
    print(message)


def show_dashboard():
    data = load_data()
    leaves = data.get("leaves", [])
    requirements = get_minimum_requirements()

    divider()
    print("              LEAVE OVERLAP ALERT DASHBOARD")
    divider()

    print(f"Faculty members : {len(FACULTY_GROUPS)}")
    print(f"Leave records   : {len(leaves)}")
    print(f"Dashboard date  : {date.today().isoformat()}")

    if not leaves:
        print("\nNo leave records yet.")
        print("Choose option 1 to register a faculty leave.")
        divider()
        return

    shortage_total = 0
    overlap_total = 0

    groups = sorted(
        set(requirements)
        | {leave["group"] for leave in leaves}
    )

    for group in groups:
        group_leaves = [
            leave for leave in leaves
            if leave["group"] == group
        ]

        total_faculty = get_faculty_count(group)
        minimum = requirements.get(group, 1)

        print("\n" + "=" * 72)
        print(f"GROUP NAME: {group}")
        print(f"Total Faculty: {total_faculty}")
        print(f"Minimum Required: {minimum}")
        print("=" * 72)

        if not group_leaves:
            print("No leaves registered for this group.")
            continue

        start = min(
            date.fromisoformat(leave["start_date"])
            for leave in group_leaves
        )
        end = max(
            date.fromisoformat(leave["end_date"])
            for leave in group_leaves
        )

        alerts = generate_alerts(
            group_leaves,
            start,
            end,
            total_faculty,
            minimum
        )

        overlaps, peak = sweep_line_overlaps(group_leaves)

        if alerts:
            shortage_total += len(alerts)
            print(f"\nSHORTAGE ALERTS: {len(alerts)} date(s)")

            for alert in alerts:
                print(
                    f"  ! {alert['date']} — "
                    f"{alert['available']} available, "
                    f"{alert['required']} required; "
                    f"{alert['absent']} absent"
                )
        else:
            print("Staffing status: OK — minimum staffing maintained.")

        if overlaps:
            overlap_total += len(overlaps)
            print("\nOVERLAPPING LEAVES:")

            for period in overlaps:
                if period["start_date"] == period["end_date"]:
                    date_range = period["start_date"]
                else:
                    date_range = (
                        f"{period['start_date']} to {period['end_date']}"
                    )

                print(
                    f"  ! {date_range} — "
                    f"{period['faculty_count']} faculty absent: "
                    f"{', '.join(period['faculty'])}"
                )

            print(f"Peak simultaneous absences: {peak}")
        else:
            print("Overlap status: No overlapping leaves detected.")

    divider("-")
    print(
        f"SUMMARY: {shortage_total} shortage-alert date(s) | "
        f"{overlap_total} overlapping period(s)"
    )
    print("Alerts are recalculated from saved leave records.")
    divider()


def view_leave_records():
    data = load_data()
    leaves = data.get("leaves", [])

    divider()
    print("SAVED LEAVE RECORDS")
    divider("-")

    if not leaves:
        print("No leave records saved.")
        return

    for index, leave in enumerate(leaves, start=1):
        print(
            f"{index:>3}. {leave['faculty']:<22} "
            f"{leave['group']:<8} "
            f"{leave['start_date']} to {leave['end_date']}"
        )


def main():
    while True:
        divider()
        print("              LEAVE OVERLAP ALERT SYSTEM")
        print("        Faculty Leave Monitoring & Staffing Alerts")
        divider()

        print("  1. Register Faculty Leave")
        print("  2. View Alert Dashboard")
        print("  3. Faculty Management")
        print("  4. View Faculty Directory")
        print("  5. Configure Group Requirements")
        print("  6. View Saved Leave Records")
        print("  7. Mark Faculty as Returned")
        print("  8. Exit")

        divider("-")
        choice = input("Select an option (1-8): ").strip()

        if choice == "1":
            register_leave()
        elif choice == "2":
            show_dashboard()
        elif choice == "3":
            register_faculty()
        elif choice == "4":
            display_faculty()
        elif choice == "5":
            configure_requirements()
        elif choice == "6":
            view_leave_records()
        elif choice == "7":
            mark_faculty_returned()
        elif choice == "8":
            print("\nYour data is saved. Goodbye!")
            break
        else:
            print("Invalid choice. Please select 1-8.")


if __name__ == "__main__":
    main()