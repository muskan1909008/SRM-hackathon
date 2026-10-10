
from datetime import date, timedelta
from difference_array import calculate_daily_absences


def generate_alerts(
    group_leaves,
    start_date,
    end_date,
    total_faculty,
    minimum_required
):
    daily_counts = calculate_daily_absences(
        group_leaves, start_date, end_date
    )

    alerts = []

    for item in daily_counts:
        available = total_faculty - item["absent"]

        if available < minimum_required:
            alerts.append({
                "date": item["date"],
                "absent": item["absent"],
                "available": available,
                "required": minimum_required
            })

    return alerts


def merge_intervals(leaves):
    """Merge overlapping or adjacent intervals per faculty member."""

    faculty_intervals = {}

    for leave in leaves:
        name = leave["faculty"]
        start = date.fromisoformat(leave["start_date"])
        end = date.fromisoformat(leave["end_date"])

        faculty_intervals.setdefault(name, []).append((start, end))

    result = []

    for faculty, intervals in faculty_intervals.items():
        intervals.sort()
        current_start = None
        current_end = None

        for start, end in intervals:
            if current_start is None:
                current_start, current_end = start, end

            elif start <= current_end + timedelta(days=1):
                current_end = max(current_end, end)

            else:
                result.append((faculty, current_start, current_end))
                current_start, current_end = start, end

        if current_start is not None:
            result.append((faculty, current_start, current_end))

    return result


def sweep_line_overlaps(group_leaves):
    """
    Sweep Line Algorithm:
    +1 on leave start, -1 on the day after leave end.
    """

    events = {}

    for faculty, start, end in merge_intervals(group_leaves):
        events.setdefault(start, []).append((faculty, 1))
        events.setdefault(
            end + timedelta(days=1), []
        ).append((faculty, -1))

    active_faculty = set()
    overlap_periods = []
    peak_absences = 0
    previous_day = None

    for current_day in sorted(events):
        # The active set applies to dates before current_day.
        if (
            previous_day is not None
            and previous_day < current_day
            and len(active_faculty) >= 2
        ):
            overlap_periods.append({
                "start_date": previous_day.isoformat(),
                "end_date": (
                    current_day - timedelta(days=1)
                ).isoformat(),
                "faculty_count": len(active_faculty),
                "faculty": sorted(active_faculty)
            })

        # Process endings before beginnings for this date.
        for faculty, change in events[current_day]:
            if change == -1:
                active_faculty.discard(faculty)

        for faculty, change in events[current_day]:
            if change == 1:
                active_faculty.add(faculty)

        peak_absences = max(peak_absences, len(active_faculty))
        previous_day = current_day

    # Combine adjacent periods with the same faculty absent.
    compact = []

    for period in overlap_periods:
        if compact:
            previous = compact[-1]
            adjacent = (
                date.fromisoformat(previous["end_date"])
                + timedelta(days=1)
                == date.fromisoformat(period["start_date"])
            )

            if adjacent and previous["faculty"] == period["faculty"]:
                previous["end_date"] = period["end_date"]
                continue

        compact.append(period)

    return compact, peak_absences