-- Pairly Database Schema
-- WAL mode enabled, foreign keys enforced

-- User states: NEW, AGREED, IDLE, SEARCHING, CHATTING, RATING
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    gender TEXT NOT NULL CHECK(gender IN ('male', 'female')),
    current_state TEXT NOT NULL DEFAULT 'NEW' CHECK(current_state IN ('NEW', 'AGREED', 'IDLE', 'SEARCHING', 'CHATTING', 'RATING')),
    partner_id INTEGER,
    premium_until TIMESTAMP,
    temp_premium_last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_state ON users(current_state);
CREATE INDEX IF NOT EXISTS idx_users_partner ON users(partner_id);

-- Waiting pool (table-backed, no memory)
CREATE TABLE IF NOT EXISTS waiting_users (
    user_id INTEGER PRIMARY KEY,
    gender TEXT NOT NULL,
    is_premium INTEGER NOT NULL DEFAULT 0,
    rating REAL,
    rating_count INTEGER DEFAULT 0,
    gender_preference TEXT CHECK(gender_preference IN ('male', 'female', NULL)),
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_waiting_premium ON waiting_users(is_premium);
CREATE INDEX IF NOT EXISTS idx_waiting_rating ON waiting_users(rating);

-- Active chats
CREATE TABLE IF NOT EXISTS active_chats (
    chat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_a INTEGER NOT NULL,
    user_b INTEGER NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_a) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (user_b) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE(user_a, user_b)
);

CREATE INDEX IF NOT EXISTS idx_active_chats_users ON active_chats(user_a, user_b);

-- Match history (prevent immediate rematches)
CREATE TABLE IF NOT EXISTS match_history (
    user_id INTEGER NOT NULL,
    partner_id INTEGER NOT NULL,
    last_matched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, partner_id)
);

CREATE INDEX IF NOT EXISTS idx_match_history_time ON match_history(last_matched_at);

-- Ratings
CREATE TABLE IF NOT EXISTS ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rated_user_id INTEGER NOT NULL,
    rater_user_id INTEGER NOT NULL,
    rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(rated_user_id, rater_user_id),
    FOREIGN KEY (rated_user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (rater_user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_ratings_user ON ratings(rated_user_id);

-- Sunflower ledger (source-based tracking)
CREATE TABLE IF NOT EXISTS sunflower_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    source TEXT NOT NULL CHECK(source IN ('streak', 'game', 'gift', 'rating')),
    amount INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sunflower_user ON sunflower_ledger(user_id, source);

-- Streaks
CREATE TABLE IF NOT EXISTS streaks (
    user_id INTEGER PRIMARY KEY,
    current_days INTEGER NOT NULL DEFAULT 0,
    last_active_date DATE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Pets (guardian angels)
CREATE TABLE IF NOT EXISTS pets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    pet_type TEXT NOT NULL,
    saves_remaining INTEGER NOT NULL DEFAULT 1,
    acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_pets_user ON pets(user_id);

-- Gardens
CREATE TABLE IF NOT EXISTS gardens (
    user_id INTEGER PRIMARY KEY,
    level INTEGER NOT NULL DEFAULT 1 CHECK(level >= 1 AND level <= 3),
    last_harvest_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Active games
CREATE TABLE IF NOT EXISTS active_games (
    game_id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    game_type TEXT NOT NULL CHECK(game_type IN ('tictactoe', 'wordchain_easy', 'wordchain_hard', 'hangman')),
    player1_id INTEGER NOT NULL,
    player2_id INTEGER NOT NULL,
    bet_amount INTEGER NOT NULL DEFAULT 0,
    game_state TEXT NOT NULL,
    current_turn INTEGER NOT NULL,
    winner_id INTEGER,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    FOREIGN KEY (chat_id) REFERENCES active_chats(chat_id) ON DELETE CASCADE,
    FOREIGN KEY (player1_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (player2_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_games_chat ON active_games(chat_id);
CREATE INDEX IF NOT EXISTS idx_games_active ON active_games(winner_id) WHERE winner_id IS NULL;

-- Violations
CREATE TABLE IF NOT EXISTS violations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    violation_type TEXT NOT NULL CHECK(violation_type IN ('link', 'spam', 'abuse')),
    occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_violations_user ON violations(user_id);

-- Bans (visible only)
CREATE TABLE IF NOT EXISTS bans (
    user_id INTEGER PRIMARY KEY,
    reason TEXT NOT NULL,
    banned_until TIMESTAMP NOT NULL,
    banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_bans_expiry ON bans(banned_until);

-- Link tracking (for premium users)
CREATE TABLE IF NOT EXISTS link_tracking (
    user_id INTEGER NOT NULL,
    date DATE NOT NULL,
    count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, date),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Admin message monitoring
CREATE TABLE IF NOT EXISTS monitored_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    sender_id INTEGER NOT NULL,
    message_type TEXT NOT NULL,
    content TEXT,
    media_file_id TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_monitored_chat ON monitored_messages(chat_id);
CREATE INDEX IF NOT EXISTS idx_monitored_time ON monitored_messages(sent_at);

-- Pending ratings (track who needs to rate whom)
CREATE TABLE IF NOT EXISTS pending_ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rater_id INTEGER NOT NULL,
    rated_user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rater_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (rated_user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_pending_ratings_rater ON pending_ratings(rater_id);
