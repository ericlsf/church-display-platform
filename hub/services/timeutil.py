from datetime import datetime


def human_age(iso_value):
    try:
        dt = datetime.fromisoformat(iso_value)
        age = int((datetime.now() - dt).total_seconds())
        if age < 5:
            return "Just now"
        if age < 60:
            return f"{age}s ago"
        if age < 3600:
            return f"{age // 60}m ago"
        if age < 86400:
            return f"{age // 3600}h ago"
        return dt.strftime("%Y-%m-%d %I:%M:%S %p")
    except Exception:
        return "Unknown"


def seconds_old(iso_value):
    try:
        dt = datetime.fromisoformat(iso_value)
        return int((datetime.now() - dt).total_seconds())
    except Exception:
        return None


def is_fresh(iso_value, max_age=90):
    age = seconds_old(iso_value)
    return age is not None and age <= max_age
