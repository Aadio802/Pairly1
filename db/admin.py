"""
Admin database operations
"""
from typing import List, Dict, Any
from db import get_connection


async def get_stats() -> Dict[str, int]:
    """Get bot statistics"""
    async with await get_connection() as conn:
        stats = {}
        
        # Total users
        result = await conn.execute("SELECT COUNT(*) FROM users")
        stats['total_users'] = (await result.fetchone())[0]
        
        # Premium users
        result = await conn.execute(
            "SELECT COUNT(*) FROM users WHERE premium_until > CURRENT_TIMESTAMP"
        )
        stats['premium_users'] = (await result.fetchone())[0]
        
        # Active chats
        result = await conn.execute("SELECT COUNT(*) FROM active_chats")
        stats['active_chats'] = (await result.fetchone())[0]
        
        # Searching users
        result = await conn.execute("SELECT COUNT(*) FROM waiting_users")
        stats['searching'] = (await result.fetchone())[0]
        
        # Total ratings
        result = await conn.execute("SELECT COUNT(*) FROM ratings")
        stats['total_ratings'] = (await result.fetchone())[0]
        
        # Total games
        result = await conn.execute("SELECT COUNT(*) FROM active_games")
        stats['total_games'] = (await result.fetchone())[0]
        
        # Banned users
        result = await conn.execute(
            "SELECT COUNT(*) FROM bans WHERE banned_until > CURRENT_TIMESTAMP"
        )
        stats['banned_users'] = (await result.fetchone())[0]
        
        # Total sunflowers
        result = await conn.execute("SELECT SUM(amount) FROM sunflower_ledger")
        stats['total_sunflowers'] = (await result.fetchone())[0] or 0
        
        return stats


async def get_recent_messages(limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent monitored messages"""
    async with await get_connection() as conn:
        result = await conn.execute(
            """
            SELECT chat_id, sender_id, message_type, content, sent_at
            FROM monitored_messages
            ORDER BY sent_at DESC
            LIMIT ?
            """,
            (limit,)
        )
        rows = await result.fetchall()
        
        messages = []
        for row in rows:
            messages.append({
                'chat_id': row[0],
                'sender_id': row[1],
                'message_type': row[2],
                'content': row[3],
                'sent_at': row[4]
            })
        
        return messages


async def get_all_users() -> List[int]:
    """Get all user IDs for broadcasting"""
    async with await get_connection() as conn:
        result = await conn.execute("SELECT user_id FROM users")
        rows = await result.fetchall()
        return [row[0] for row in rows]


async def get_user_details(user_id: int) -> Dict[str, Any]:
    """Get detailed user information"""
    async with await get_connection() as conn:
        result = await conn.execute(
            """
            SELECT user_id, gender, current_state, premium_until, created_at
            FROM users
            WHERE user_id = ?
            """,
            (user_id,)
        )
        row = await result.fetchone()
        
        if not row:
            return None
        
        # Get additional stats
        rating_result = await conn.execute(
            "SELECT AVG(rating), COUNT(*) FROM ratings WHERE rated_user_id = ?",
            (user_id,)
        )
        rating_row = await rating_result.fetchone()
        
        sunflower_result = await conn.execute(
            "SELECT SUM(amount) FROM sunflower_ledger WHERE user_id = ?",
            (user_id,)
        )
        sunflower_row = await sunflower_result.fetchone()
        
        return {
            'user_id': row[0],
            'gender': row[1],
            'state': row[2],
            'premium_until': row[3],
            'created_at': row[4],
            'avg_rating': rating_row[0] if rating_row else None,
            'rating_count': rating_row[1] if rating_row else 0,
            'sunflowers': sunflower_row[0] if sunflower_row else 0
        }


async def get_active_chats_details() -> List[Dict[str, Any]]:
    """Get details of all active chats"""
    async with await get_connection() as conn:
        result = await conn.execute(
            """
            SELECT chat_id, user_a, user_b, started_at
            FROM active_chats
            ORDER BY started_at DESC
            """,
        )
        rows = await result.fetchall()
        
        chats = []
        for row in rows:
            chats.append({
                'chat_id': row[0],
                'user_a': row[1],
                'user_b': row[2],
                'started_at': row[3]
            })
        
        return chats
