
from datetime import date, timedelta


def calculate_daily_absences(leaves, start_date, end_date):
    """
    Difference Array + Prefix Sum.
    Counts distinct faculty members absent on each date.
    """

    if isinstance(start_date, str):
        start_date = date.fromisoformat(start_date)

    if isinstance(end_date, str):
        end_date = date.fromisoformat(end_date)

    if end_date < start_date:
        return []

    # Merge overlapping leave dates for each faculty member.
    faculty_intervals = {}

    for leave in leaves:
        name = leave["faculty"]
        left = date.fromisoformat(leave["start_date"])
        right = date.fromisoformat(leave["end_date"])

        if right < start_date or left > end_date:
            continue

        left = max(left, start_date)
        right = min(right, end_date)

        faculty_intervals.setdefault(name, []).append((left, right))

    days = (end_date - start_date).days + 1
    difference = [0] * (days + 1)

    for intervals in faculty_intervals.values():
        intervals.sort()

        merged = []

        for left, right in intervals:
            if merged and left <= merged[-1][1] + timedelta(days=1):
                merged[-1] = (
                    merged[-1][0],
                    max(merged[-1][1], right)
                )
            else:
                merged.append((left, right))

        for left, right in merged:
            start_index = (left - start_date).days
            end_index = (right - start_date).days

            difference[start_index] += 1
            difference[end_index + 1] -= 1

    results = []
    current_absences = 0

    for offset in range(days):
        current_absences += difference[offset]

        results.append({
            "date": (start_date + timedelta(days=offset)).isoformat(),
            "absent": current_absences
        })

    return results