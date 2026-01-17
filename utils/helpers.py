"""
Utility helper functions
"""
from datetime import datetime, date, timedelta
from typing import Optional


def format_datetime(dt: Optional[str]) -> str:
    """Format datetime string for display"""
    if not dt:
        return "Never"
    
    try:
        parsed = datetime.fromisoformat(dt)
        return parsed.strftime("%Y-%m-%d %H:%M")
    except:
        return "Invalid"


def format_date(d: Optional[str]) -> str:
    """Format date string for display"""
    if not d:
        return "Never"
    
    try:
        parsed = date.fromisoformat(d)
        return parsed.strftime("%Y-%m-%d")
    except:
        return "Invalid"


def time_until(target_dt: datetime) -> str:
    """Get human-readable time until target"""
    now = datetime.now()
    
    if target_dt <= now:
        return "Expired"
    
    delta = target_dt - now
    
    if delta.days > 0:
        return f"{delta.days} day{'s' if delta.days != 1 else ''}"
    
    hours = delta.seconds // 3600
    if hours > 0:
        return f"{hours} hour{'s' if hours != 1 else ''}"
    
    minutes = (delta.seconds % 3600) // 60
    return f"{minutes} minute{'s' if minutes != 1 else ''}"


def time_since(past_dt: datetime) -> str:
    """Get human-readable time since past datetime"""
    now = datetime.now()
    
    if past_dt > now:
        return "In the future"
    
    delta = now - past_dt
    
    if delta.days > 365:
        years = delta.days // 365
        return f"{years} year{'s' if years != 1 else ''} ago"
    
    if delta.days > 30:
        months = delta.days // 30
        return f"{months} month{'s' if months != 1 else ''} ago"
    
    if delta.days > 0:
        return f"{delta.days} day{'s' if delta.days != 1 else ''} ago"
    
    hours = delta.seconds // 3600
    if hours > 0:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    
    minutes = (delta.seconds % 3600) // 60
    if minutes > 0:
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    
    return "Just now"


def format_number(num: int) -> str:
    """Format large numbers with commas"""
    return f"{num:,}"


def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate text with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def validate_user_input(text: str, min_length: int = 1, max_length: int = 200) -> bool:
    """Validate user text input"""
    if not text:
        return False
    
    text = text.strip()
    
    if len(text) < min_length or len(text) > max_length:
        return False
    
    return True


def escape_markdown(text: str) -> str:
    """Escape special markdown characters"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    
    return text


def get_multiplier_text(streak_days: int) -> str:
    """Get streak multiplier display text"""
    from config import settings
    
    if streak_days >= 30:
        return f"{settings.STREAK_30D_MULTIPLIER}×"
    elif streak_days >= 7:
        return f"{settings.STREAK_7D_MULTIPLIER}×"
    else:
        return "1×"


def calculate_percentage(part: int, total: int) -> float:
    """Calculate percentage safely"""
    if total == 0:
        return 0.0
    return round((part / total) * 100, 1)


def is_valid_user_id(user_id: any) -> bool:
    """Validate Telegram user ID"""
    try:
        uid = int(user_id)
        return uid > 0
    except:
        return False
