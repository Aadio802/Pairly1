"""
Admin handlers - monitoring and moderation
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.admin import get_stats, get_recent_messages, get_all_users, get_user_details, get_active_chats_details
from db.moderation import ban_user, unban_user, is_banned
from config import settings

router = Router()


def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id == settings.ADMIN_ID


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Admin panel"""
    if not is_admin(message.from_user.id):
        return
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Statistics", callback_data="admin_stats")
    builder.button(text="👁️ Recent Messages", callback_data="admin_messages")
    builder.button(text="💬 Active Chats", callback_data="admin_chats")
    builder.button(text="👤 User Info", callback_data="admin_user_info")
    builder.adjust(2)
    
    await message.answer(
        "🔐 Admin Panel\n\nSelect an action:",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == "admin_stats")
async def admin_stats_callback(callback: CallbackQuery):
    """Show detailed statistics"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    stats = await get_stats()
    
    text = (
        f"📊 Bot Statistics\n\n"
        f"👥 Total Users: {stats['total_users']}\n"
        f"⭐ Premium Users: {stats['premium_users']}\n"
        f"💬 Active Chats: {stats['active_chats']}\n"
        f"🔍 Searching: {stats['searching']}\n"
        f"⭐ Total Ratings: {stats['total_ratings']}\n"
        f"🎮 Total Games: {stats['total_games']}\n"
        f"🚫 Banned Users: {stats['banned_users']}\n"
        f"🌻 Total Sunflowers: {stats['total_sunflowers']}"
    )
    
    await callback.message.edit_text(text)
    await callback.answer()


@router.callback_query(F.data == "admin_messages")
async def admin_messages_callback(callback: CallbackQuery):
    """Show recent monitored messages"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    messages = await get_recent_messages(20)
    
    if not messages:
        await callback.message.edit_text("No recent messages.")
        await callback.answer()
        return
    
    text = "👁️ Recent Messages\n\n"
    
    for msg in messages[:20]:
        timestamp = msg['sent_at'][:19] if msg['sent_at'] else "unknown"
        
        if msg['message_type'] == 'text':
            content = msg['content'][:50] + "..." if msg['content'] and len(msg['content']) > 50 else msg['content']
            text += f"User {msg['sender_id']} ({timestamp}):\n{content}\n\n"
        else:
            text += f"User {msg['sender_id']} ({timestamp}): [{msg['message_type']}]\n\n"
        
        if len(text) > 3000:
            break
    
    await callback.message.edit_text(text)
    await callback.answer()


@router.callback_query(F.data == "admin_chats")
async def admin_chats_callback(callback: CallbackQuery):
    """Show active chats"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    chats = await get_active_chats_details()
    
    if not chats:
        await callback.message.edit_text("No active chats.")
        await callback.answer()
        return
    
    text = "💬 Active Chats\n\n"
    
    for chat in chats[:20]:
        text += f"Chat {chat['chat_id']}: {chat['user_a']} ↔ {chat['user_b']}\n"
        text += f"Started: {chat['started_at'][:19]}\n\n"
    
    await callback.message.edit_text(text)
    await callback.answer()


@router.callback_query(F.data == "admin_user_info")
async def admin_user_info_prompt(callback: CallbackQuery):
    """Prompt for user ID"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    await callback.message.edit_text(
        "Send command:\n`/userinfo <user_id>`"
    )
    await callback.answer()


@router.message(Command("userinfo"))
async def cmd_userinfo(message: Message):
    """Get user info"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer("Usage: /userinfo <user_id>")
            return
        
        user_id = int(parts[1])
        details = await get_user_details(user_id)
        
        if not details:
            await message.answer("User not found.")
            return
        
        text = (
            f"👤 User {user_id}\n\n"
            f"Gender: {details['gender']}\n"
            f"State: {details['state']}\n"
            f"Premium: {details['premium_until'][:10] if details['premium_until'] else 'No'}\n"
            f"Joined: {details['created_at'][:10]}\n"
            f"Rating: {details['avg_rating']:.1f} ({details['rating_count']} ratings)\n" if details['avg_rating'] else f"Rating: None\n"
            f"Sunflowers: {details['sunflowers']}"
        )
        
        await message.answer(text)
    
    except ValueError:
        await message.answer("Invalid user ID.")


@router.message(Command("ban"))
async def cmd_ban(message: Message):
    """Ban a user"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        parts = message.text.split(maxsplit=3)
        if len(parts) < 4:
            await message.answer("Usage: /ban <user_id> <hours> <reason>")
            return
        
        user_id = int(parts[1])
        hours = int(parts[2])
        reason = parts[3]
        
        await ban_user(user_id, hours, reason)
        
        await message.answer(f"✅ User {user_id} banned for {hours} hours.\nReason: {reason}")
        
        # Notify user
        try:
            await message.bot.send_message(
                user_id,
                f"🚫 You have been banned for {hours} hours.\n\nReason: {reason}"
            )
        except:
            pass
    
    except (ValueError, IndexError):
        await message.answer("Invalid format. Usage: /ban <user_id> <hours> <reason>")


@router.message(Command("unban"))
async def cmd_unban(message: Message):
    """Unban a user"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer("Usage: /unban <user_id>")
            return
        
        user_id = int(parts[1])
        await unban_user(user_id)
        
        await message.answer(f"✅ User {user_id} unbanned.")
        
        # Notify user
        try:
            await message.bot.send_message(
                user_id,
                "✅ You have been unbanned. You can use the bot again."
            )
        except:
            pass
    
    except ValueError:
        await message.answer("Invalid user ID.")


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    """Broadcast message to all users"""
    if not is_admin(message.from_user.id):
        return
    
    text = message.text.replace("/broadcast", "", 1).strip()
    
    if not text:
        await message.answer("Usage: /broadcast <message>")
        return
    
    users = await get_all_users()
    
    success = 0
    failed = 0
    
    status_msg = await message.answer(f"Broadcasting to {len(users)} users...")
    
    for user_id in users:
        try:
            await message.bot.send_message(user_id, f"📢 Announcement:\n\n{text}")
            success += 1
        except:
            failed += 1
    
    await status_msg.edit_text(
        f"✅ Broadcast complete!\n\n"
        f"Sent: {success}\n"
        f"Failed: {failed}"
    )
