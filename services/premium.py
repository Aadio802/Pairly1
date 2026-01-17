"""
Premium subscription service
"""
from datetime import datetime
from typing import Optional, Tuple
from db.users import update_premium, get_premium_remaining_days, can_use_temp_premium, use_temp_premium
from db.sunflowers import get_sunflower_balance, deduct_sunflowers_smart
from config import settings


def get_premium_plans() -> list:
    """Get available premium plans"""
    return [
        {
            'duration': 7,
            'price': settings.PREMIUM_7D,
            'actual_days': 7,
            'bonus': 0
        },
        {
            'duration': 30,
            'price': settings.PREMIUM_30D,
            'actual_days': 30,
            'bonus': 0
        },
        {
            'duration': 90,
            'price': settings.PREMIUM_90D,
            'actual_days': 104,  # 90 + 14
            'bonus': 14
        },
        {
            'duration': 365,
            'price': settings.PREMIUM_365D,
            'actual_days': 379,  # 365 + 14
            'bonus': 14
        }
    ]


def get_plan_by_duration(duration: int) -> Optional[dict]:
    """Get plan details by duration"""
    plans = get_premium_plans()
    for plan in plans:
        if plan['duration'] == duration:
            return plan
    return None


async def activate_premium(user_id: int, days: int):
    """Activate premium for user"""
    await update_premium(user_id, days)


async def get_premium_status(user_id: int) -> Tuple[bool, int]:
    """Get premium status (is_premium, days_remaining)"""
    days = await get_premium_remaining_days(user_id)
    return (days > 0, days)


async def can_buy_temp_premium(user_id: int) -> Tuple[bool, str]:
    """
    Check if user can buy temp premium
    Returns (can_buy, reason)
    """
    # Check cooldown
    can_use = await can_use_temp_premium(user_id)
    if not can_use:
        return (False, "You can only buy temp premium once every 15 days")
    
    # Check sunflowers
    balance = await get_sunflower_balance(user_id)
    if balance['total'] < settings.TEMP_PREMIUM_COST:
        return (False, f"You need {settings.TEMP_PREMIUM_COST} sunflowers (you have {balance['total']})")
    
    return (True, "")


async def buy_temp_premium(user_id: int) -> bool:
    """
    Purchase temp premium with sunflowers
    Returns True if successful
    """
    can_buy, reason = await can_buy_temp_premium(user_id)
    if not can_buy:
        return False
    
    # Deduct sunflowers
    success = await deduct_sunflowers_smart(user_id, settings.TEMP_PREMIUM_COST)
    if not success:
        return False
    
    # Activate temp premium
    await use_temp_premium(user_id)
    
    return True


def is_temp_premium_eligible(user_id: int, premium_until: Optional[str], temp_last_used: Optional[str]) -> bool:
    """
    Check if current premium is from temp purchase
    Used to restrict garden access
    """
    if not premium_until:
        return False
    
    if not temp_last_used:
        return False
    
    premium_dt = datetime.fromisoformat(premium_until)
    temp_dt = datetime.fromisoformat(temp_last_used)
    
    # If temp was used recently and premium is active, it's temp premium
    days_diff = (datetime.now() - temp_dt).days
    
    return days_diff < settings.TEMP_PREMIUM_DAYS and premium_dt > datetime.now()
