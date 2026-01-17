"""
Garden system - passive sunflower generation for premium users
"""
from typing import Optional, Tuple
from datetime import date
from db import get_connection
from db.sunflowers import add_sunflowers


async def create_garden(user_id: int) -> bool:
    """Create garden for user (premium only)"""
    async with await get_connection() as conn:
        try:
            await conn.execute(
                """
                INSERT INTO gardens (user_id, level, last_harvest_date)
                VALUES (?, 1, ?)
                """,
                (user_id, date.today().isoformat())
            )
            await conn.commit()
            return True
        except:
            return False


async def get_garden(user_id: int) -> Optional[Tuple[int, str]]:
    """Get garden info (level, last_harvest_date)"""
    async with await get_connection() as conn:
        result = await conn.execute(
            "SELECT level, last_harvest_date FROM gardens WHERE user_id = ?",
            (user_id,)
        )
        row = await result.fetchone()
        return (row[0], row[1]) if row else None


async def harvest_garden(user_id: int) -> Optional[int]:
    """
    Harvest garden sunflowers
    Returns amount harvested or None if already harvested today
    """
    garden = await get_garden(user_id)
    if not garden:
        return None
    
    level, last_harvest = garden
    today = date.today()
    
    if last_harvest:
        last_date = date.fromisoformat(last_harvest)
        if last_date >= today:
            return None  # Already harvested today
    
    # Calculate reward based on level
    rewards = {1: 20, 2: 40, 3: 60}
    reward = rewards.get(level, 20)
    
    # Award sunflowers
    await add_sunflowers(user_id, reward, 'game')
    
    # Update last harvest
    async with await get_connection() as conn:
        await conn.execute(
            "UPDATE gardens SET last_harvest_date = ? WHERE user_id = ?",
            (today.isoformat(), user_id)
        )
        await conn.commit()
    
    return reward


async def upgrade_garden(user_id: int) -> bool:
    """Upgrade garden to next level (max 3)"""
    async with await get_connection() as conn:
        result = await conn.execute(
            "UPDATE gardens SET level = MIN(3, level + 1) WHERE user_id = ?",
            (user_id,)
        )
        await conn.commit()
        return result.rowcount > 0


async def downgrade_garden(user_id: int) -> bool:
    """Downgrade garden by one level"""
    async with await get_connection() as conn:
        result = await conn.execute(
            "UPDATE gardens SET level = MAX(1, level - 1) WHERE user_id = ?",
            (user_id,)
        )
        await conn.commit()
        return result.rowcount > 0


async def destroy_garden(user_id: int):
    """Destroy user's garden completely"""
    async with await get_connection() as conn:
        await conn.execute(
            "DELETE FROM gardens WHERE user_id = ?",
            (user_id,)
        )
        await conn.commit()


async def has_garden(user_id: int) -> bool:
    """Check if user has a garden"""
    garden = await get_garden(user_id)
    return garden is not None
