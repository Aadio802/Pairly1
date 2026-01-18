from typing import Optional
from datetime import datetime, timedelta
from db import get_connection
from config import settings


async def join_waiting_pool(
    user_id: int,
    gender: str,
    is_premium: bool,
    rating: Optional[float] = None,
    rating_count: int = 0,
    gender_pref: Optional[str] = None
):
    conn = await get_connection()
    try:
        await conn.execute(
            """
            INSERT OR REPLACE INTO waiting_users 
            (user_id, gender, is_premium, rating, rating_count, gender_preference, joined_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (user_id, gender, int(is_premium), rating, rating_count, gender_pref)
        )
        await conn.commit()
    finally:
        await conn.close()


async def leave_waiting_pool(user_id: int):
    conn = await get_connection()
    try:
        await conn.execute(
            "DELETE FROM waiting_users WHERE user_id = ?",
            (user_id,)
        )
        await conn.commit()
    finally:
        await conn.close()


async def get_waiting_candidates(user_id: int, my_gender: str):
    cutoff_time = datetime.now() - timedelta(
        seconds=settings.MATCH_HISTORY_WINDOW_SECONDS
    )

    conn = await get_connection()
    try:
        cursor = await conn.execute(
            """
            SELECT w.user_id, w.gender, w.is_premium, w.rating, w.rating_count, w.joined_at
            FROM waiting_users w
            WHERE w.user_id != ?
            AND w.user_id NOT IN (
                SELECT partner_id
                FROM match_history
                WHERE user_id = ?
                AND last_matched_at > ?
            )
            """,
            (user_id, user_id, cutoff_time.isoformat())
        )
        return await cursor.fetchall()
    finally:
        await conn.close()


async def create_match_atomic(user_a: int, user_b: int) -> int:
    conn = await get_connection()
    try:
        await conn.execute("BEGIN IMMEDIATE")

        await conn.execute(
            "DELETE FROM waiting_users WHERE user_id IN (?, ?)",
            (user_a, user_b)
        )

        cursor = await conn.execute(
            """
            INSERT INTO active_chats (user_a, user_b, started_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            """,
            (user_a, user_b)
        )
        chat_id = cursor.lastrowid

        await conn.execute(
            "UPDATE users SET partner_id = ?, current_state='CHATTING' WHERE user_id=?",
            (user_b, user_a)
        )
        await conn.execute(
            "UPDATE users SET partner_id = ?, current_state='CHATTING' WHERE user_id=?",
            (user_a, user_b)
        )

        now = datetime.now().isoformat()
        await conn.execute(
            """
            INSERT OR REPLACE INTO match_history
            (user_id, partner_id, last_matched_at)
            VALUES (?, ?, ?)
            """,
            (user_a, user_b, now)
        )
        await conn.execute(
            """
            INSERT OR REPLACE INTO match_history
            (user_id, partner_id, last_matched_at)
            VALUES (?, ?, ?)
            """,
            (user_b, user_a, now)
        )

        await conn.commit()
        return chat_id

    except Exception:
        await conn.rollback()
        return 0

    finally:
        await conn.close()
