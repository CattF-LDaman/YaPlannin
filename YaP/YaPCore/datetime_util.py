
from datetime import datetime, date, timedelta

def is_iso_date(dt_str: str):
    try:
        datetime.fromisoformat(dt_str)
        return True
    except (ValueError, TypeError):
        return False

def iso_today():
    return date.today().isoformat()

def format_minutes(total_minutes: int) -> str:
    if total_minutes == 0:
        return "0m"

    # Constants for conversion
    MIN_IN_HOUR = 60
    MIN_IN_DAY = 60 * 24

    days = total_minutes // MIN_IN_DAY
    remaining_min = total_minutes % MIN_IN_DAY
    
    hours = remaining_min // MIN_IN_HOUR
    minutes = remaining_min % MIN_IN_HOUR

    # Create parts only if they are greater than zero
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")

    return " ".join(parts)

def now_time():

    return datetime.now().strftime("%H:%M")

def time_ago(minutes):
    # Calculate the time difference
    past_time = datetime.now() - timedelta(minutes=minutes)
    
    # Return formatted string
    return past_time.strftime("%H:%M")