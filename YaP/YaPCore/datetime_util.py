
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

def is_this_week(iso_str):
    """
    Checks if an ISO format string (YYYY-MM-DD) falls within the 
    current ISO week (Monday to Sunday).
    """
    try:
        # Parse the input string into a date object
        target_date = datetime.fromisoformat(iso_str).date()
        
        # Get today's date
        today = date.today()
        
        # Find the start of the current week (Monday)
        # weekday() returns 0 for Monday, 6 for Sunday
        start_of_week = today - timedelta(days=today.weekday())
        
        # Find the end of the current week (Sunday)
        end_of_week = start_of_week + timedelta(days=6)
        
        return start_of_week <= target_date <= end_of_week
    
    except ValueError, TypeError:
        # Returns False if the string format is invalid
        return False
    
def is_within_next_week(iso_str):
    """
    Checks if an ISO format string is today or within the next 7 days.
    """
    try:
        # 1. Convert the string to a date object
        target_date = datetime.fromisoformat(iso_str).date()
        
        # 2. Define our sliding window
        today = date.today()
        seven_days_from_now = today + timedelta(days=7)
        
        # 3. Check if target falls in that range (inclusive)
        return today <= target_date <= seven_days_from_now
        
    except (ValueError, TypeError):
        # Returns False if input is not a valid ISO string or not a string at all
        return False
    
def get_week_days(d):
    """
    Returns list of 7 days (YYYY-MM-DD) for the week containing date d.
    Week starts on Monday. Like it fucking should be.
    """
    monday = d - timedelta(days=d.weekday())
    return [(monday + timedelta(days=i)).isoformat() for i in range(7)]

def this_week():

    return get_week_days(date.today())

def has_passed(iso_date_string):
    """
    Checks if an ISO-format date string represents a point in time that has passed.
    """
    try:
        # Parse the ISO string into a datetime object
        target_date = datetime.fromisoformat(iso_date_string)
        
        # Compare against current local time (for naive strings)
        return target_date < datetime.now()
            
    except ValueError as e:
        return f"Invalid ISO format: {e}"
    
def days_until(iso_date_string, clamped: int = None):
    """Calculates the number of days from today until a specific date."""
    # Get today's date
    today = date.today()
    
    # Create a date object for the target
    target_date = date.fromisoformat(iso_date_string)
    
    # Subtracting two dates returns a timedelta object
    delta = target_date - today
    
    return delta.days if not clamped else max(clamped, delta.days)

def from_today(days: int) -> str:
    return (date.today() + timedelta(days=days)).isoformat()