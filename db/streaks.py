"""
Streak management with pet protection
"""
from datetime import datetime, date
from db import get_connection
from db.sunflowers import add_sunflowers, reset_streak_sunflowers
from db.pets import use_pet
from config import settings


async def update_streak(user_id: int):
    """
    Update user's streak based on activity
    Awards sunflowers if eligible
    Uses pets if needed
    """
    today = date.today()
    
    async with await get_connection() as conn:
        # Get current streak
        result = await conn.execute(
            "SELECT current_days, last_active_date FROM streaks WHERE user_id = ?",
            (user_id,)
        )
        row = await result.fetchone()
        
        if not row:
            # First time - create streak
            await conn.execute(
                "INSERT INTO streaks (user_id, current_days, last_active_date) VALUES (?, 1, ?)",
                (user_id, today.isoformat())
            )
            await conn.commit()
            return
        
        current_days, last_active = row
        last_date = date.fromisoformat(last_active)
        days_diff = (today - last_date).days
        
        if days_diff == 0:
            # Same day, no update
            return
        elif days_diff == 1:
            # Continue streak
            new_days = current_days + 1
            await conn.execute(
                "UPDATE streaks SET current_days = ?, last_active_date = ? WHERE user_id = ?",
                (new_days, today.isoformat(), user_id)
            )
            await conn.commit()
            
            # Award sunflowers if eligible
            if new_days >= settings.STREAK_START_THRESHOLD:
                await award_streak_sunflowers(user_id, new_days)
        else:
            # Streak broken - try to use pet
            pet_used = await use_pet(user_id)
            
            if pet_used:
                # Pet saved streak
                await conn.execute(
                    "UPDATE streaks SET last_active_date = ? WHERE user_id = ?",
                    (today.isoformat(), user_id)
                )
                await conn.commit()
            else:
                # Reset streak
                await conn.execute(
                    "UPDATE streaks SET current_days = 1, last_active_date = ? WHERE user_id = ?",
                    (today.isoformat(), user_id)
                )
                await conn.commit()
                
                # Remove streak sunflowers
                await reset_streak_sunflowers(user_id)
                
                # Destroy garden
                await destroy_garden(user_id)


async def award_streak_sunflowers(user_id: int, streak_days: int):
    """Award sunflowers based on streak"""
    multiplier = 1.0
    
    if streak_days >= 30:
        multiplier = settings.STREAK_30D_MULTIPLIER
    elif streak_days >= 7:
        multiplier = settings.STREAK_7D_MULTIPLIER
    
    reward = int(settings.BASE_STREAK_REWARD * multiplier)
    await add_sunflowers(user_id, reward, 'streak')


async def get_streak_days(user_id: int) -> int:
    """Get current streak days"""
    async with await get_connection() as conn:
        result = await conn.execute(
            "SELECT current_days FROM streaks WHERE user_id = ?",
            (user_id,)
        )
        row = await result.fetchone()
        return row[0] if row else 0


async def destroy_garden(user_id: int):
    """Destroy user's garden on streak loss"""
    async with await get_connection() as conn:
        await conn.execute(
            "DELETE FROM gardens WHERE user_id = ?",
            (user_id,)
        )
        await conn.commit()


async def degrade_garden(user_id: int):
    """Downgrade garden by one level"""
    async with await get_connection() as conn:
        await conn.execute(
            "UPDATE gardens SET level = MAX(1, level - 1) WHERE user_id = ?",
            (user_id,)
        )
        await conn.commit()
