"""
Rating system database operations
"""
from typing import Optional, Tuple
from db import get_connection
from config import settings


async def add_rating(rated_user_id: int, rater_user_id: int, rating: int):
    """Add or update rating"""
    async with await get_connection() as conn:
        await conn.execute(
            """
            INSERT OR REPLACE INTO ratings (rated_user_id, rater_user_id, rating)
            VALUES (?, ?, ?)
            """,
            (rated_user_id, rater_user_id, rating)
        )
        
        # Remove from pending ratings
        await conn.execute(
            """
            DELETE FROM pending_ratings
            WHERE rater_id = ? AND rated_user_id = ?
            """,
            (rater_user_id, rated_user_id)
        )
        
        await conn.commit()


async def get_average_rating(user_id: int) -> Optional[Tuple[float, int]]:
    """Get average rating and count (None if < MIN_RATINGS_FOR_DISPLAY)"""
    async with await get_connection() as conn:
        result = await conn.execute(
            """
            SELECT AVG(rating), COUNT(*)
            FROM ratings
            WHERE rated_user_id = ?
            """,
            (user_id,)
        )
        row = await result.fetchone()
        
        if row and row[1] >= settings.MIN_RATINGS_FOR_DISPLAY:
            return (round(row[0], 1), row[1])
        
        return None


async def get_pending_ratings(user_id: int) -> list:
    """Get users that this user needs to rate"""
    async with await get_connection() as conn:
        result = await conn.execute(
            """
            SELECT rated_user_id
            FROM pending_ratings
            WHERE rater_id = ?
            ORDER BY created_at ASC
            """,
            (user_id,)
        )
        rows = await result.fetchall()
        return [row[0] for row in rows]


async def has_pending_rating(user_id: int, rated_user_id: int) -> bool:
    """Check if user has pending rating for specific user"""
    async with await get_connection() as conn:
        result = await conn.execute(
            """
            SELECT 1 FROM pending_ratings
            WHERE rater_id = ? AND rated_user_id = ?
            """,
            (user_id, rated_user_id)
        )
        return await result.fetchone() is not None
