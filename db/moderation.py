"""
Moderation system - violations, bans, link tracking
"""
from typing import Optional, Tuple
from datetime import datetime, timedelta, date
from db import get_connection


async def log_violation(user_id: int, violation_type: str):
    """Log user violation"""
    async with await get_connection() as conn:
        await conn.execute(
            """
            INSERT INTO violations (user_id, violation_type)
            VALUES (?, ?)
            """,
            (user_id, violation_type)
        )
        await conn.commit()


async def get_violation_count(user_id: int, violation_type: str, hours: int = 24) -> int:
    """Get violation count in last N hours"""
    cutoff = datetime.now() - timedelta(hours=hours)
    
    async with await get_connection() as conn:
        result = await conn.execute(
            """
            SELECT COUNT(*)
            FROM violations
            WHERE user_id = ? AND violation_type = ? AND occurred_at > ?
            """,
            (user_id, violation_type, cutoff.isoformat())
        )
        return (await result.fetchone())[0]


async def ban_user(user_id: int, hours: int, reason: str):
    """Ban user for specified hours"""
    banned_until = datetime.now() + timedelta(hours=hours)
    
    async with await get_connection() as conn:
        await conn.execute(
            """
            INSERT OR REPLACE INTO bans (user_id, reason, banned_until)
            VALUES (?, ?, ?)
            """,
            (user_id, reason, banned_until.isoformat())
        )
        await conn.commit()


async def unban_user(user_id: int):
    """Remove ban from user"""
    async with await get_connection() as conn:
        await conn.execute(
            "DELETE FROM bans WHERE user_id = ?",
            (user_id,)
        )
        await conn.commit()


async def is_banned(user_id: int) -> Optional[Tuple[datetime, str]]:
    """Check if user is banned, returns (banned_until, reason) or None"""
    async with await get_connection() as conn:
        result = await conn.execute(
            """
            SELECT banned_until, reason
            FROM bans
            WHERE user_id = ? AND banned_until > ?
            """,
            (user_id, datetime.now().isoformat())
        )
        row = await result.fetchone()
        
        if row:
            return (datetime.fromisoformat(row[0]), row[1])
        
        return None


async def get_link_count_today(user_id: int) -> int:
    """Get number of links sent today"""
    today = date.today()
    
    async with await get_connection() as conn:
        result = await conn.execute(
            """
            SELECT count
            FROM link_tracking
            WHERE user_id = ? AND date = ?
            """,
            (user_id, today.isoformat())
        )
        row = await result.fetchone()
        return row[0] if row else 0


async def increment_link_count(user_id: int):
    """Increment today's link count"""
    today = date.today()
    
    async with await get_connection() as conn:
        await conn.execute(
            """
            INSERT INTO link_tracking (user_id, date, count)
            VALUES (?, ?, 1)
            ON CONFLICT(user_id, date)
            DO UPDATE SET count = count + 1
            """,
            (user_id, today.isoformat())
        )
        await conn.commit()


async def log_monitored_message(
    chat_id: int,
    sender_id: int,
    message_type: str,
    content: Optional[str] = None,
    media_file_id: Optional[str] = None
):
    """Log message for admin monitoring"""
    async with await get_connection() as conn:
        await conn.execute(
            """
            INSERT INTO monitored_messages (chat_id, sender_id, message_type, content, media_file_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (chat_id, sender_id, message_type, content, media_file_id)
        )
        await conn.commit()


async def clean_expired_bans():
    """Remove expired bans (run periodically)"""
    async with await get_connection() as conn:
        await conn.execute(
            "DELETE FROM bans WHERE banned_until <= ?",
            (datetime.now().isoformat(),)
        )
        await conn.commit()
