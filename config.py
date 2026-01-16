"""
Configuration for Pairly Bot
"""
import os
from dataclasses import dataclass
from typing import List


@dataclass
class Settings:
    # Bot credentials
    BOT_TOKEN: str
    ADMIN_ID: int
    
    # Database
    DATABASE_PATH: str = "pairly.db"
    
    # Premium pricing (Telegram Stars)
    PREMIUM_7D: int = 25
    PREMIUM_30D: int = 50
    PREMIUM_90D: int = 140
    PREMIUM_365D: int = 600
    
    # Temporary premium
    TEMP_PREMIUM_COST: int = 1000
    TEMP_PREMIUM_DAYS: int = 3
    TEMP_PREMIUM_COOLDOWN_DAYS: int = 15
    
    # Streak system
    STREAK_START_THRESHOLD: int = 3
    STREAK_7D_MULTIPLIER: float = 1.5
    STREAK_30D_MULTIPLIER: float = 2.0
    BASE_STREAK_REWARD: int = 10
    
    # Pet system
    MAX_PETS: int = 7
    PET_TYPES: List[str] = None
    
    # Game rewards
    GAME_BASE_REWARD: int = 50
    
    # Moderation
    PREMIUM_DAILY_LINK_LIMIT: int = 5
    MIN_RATINGS_FOR_DISPLAY: int = 5
    
    # Matchmaking
    MATCH_HISTORY_WINDOW_SECONDS: int = 1800  # 30 minutes
    WAITING_TIME_BONUS_INTERVAL: int = 10  # 1 point per 10 seconds
    
    def __post_init__(self):
        if self.PET_TYPES is None:
            self.PET_TYPES = ["Panda", "Fox", "Dog", "Snake", "Alligator", "Dragon", "Parrot"]


settings = Settings(
    BOT_TOKEN=os.getenv("BOT_TOKEN", ""),
    ADMIN_ID=int(os.getenv("ADMIN_ID", "0"))
)
