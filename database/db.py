import asyncpg
from bot.config import Config
import logging

class Database:
    def __init__(self):
        self.pool = None
        self.url = Config.DATABASE_URL

    async def connect(self):
        self.pool = await asyncpg.create_pool(self.url)
        await self.create_tables()
        logging.info("Database Connected")

    async def create_tables(self):
        queries = [
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS admins (
                user_id BIGINT PRIMARY KEY,
                name TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS channels (
                id SERIAL PRIMARY KEY,
                channel_id BIGINT UNIQUE,
                anime_name TEXT,
                primary_link TEXT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS active_links (
                token TEXT PRIMARY KEY,
                channel_id BIGINT,
                user_id BIGINT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                link_type TEXT, -- 'request' or 'normal'
                invite_link TEXT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                type TEXT DEFAULT 'string' -- string, bool, int, json
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS broadcasts (
                id SERIAL PRIMARY KEY,
                message_id INT,
                chat_id BIGINT,
                pin BOOLEAN DEFAULT FALSE,
                delete_at TIMESTAMP
            );
            """
        ]
        async with self.pool.acquire() as conn:
            for query in queries:
                await conn.execute(query)

    async def add_user(self, user_id, username):
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users (user_id, username) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET username = $2",
                user_id, username
            )

    async def get_all_users(self):
        async with self.pool.acquire() as conn:
            return await conn.fetch("SELECT user_id FROM users")

    async def get_stats(self):
        async with self.pool.acquire() as conn:
            users = await conn.fetchval("SELECT COUNT(*) FROM users")
            channels = await conn.fetchval("SELECT COUNT(*) FROM channels")
            links = await conn.fetchval("SELECT COUNT(*) FROM active_links")
            return users, channels, links

    async def add_admin(self, user_id, name):
        async with self.pool.acquire() as conn:
            await conn.execute("INSERT INTO admins (user_id, name) VALUES ($1, $2) ON CONFLICT DO NOTHING", user_id, name)

    async def remove_admin(self, user_id):
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM admins WHERE user_id = $1", user_id)
            
    async def is_admin(self, user_id):
        if user_id == Config.OWNER_ID:
            return True
        async with self.pool.acquire() as conn:
            res = await conn.fetchval("SELECT 1 FROM admins WHERE user_id = $1", user_id)
            return bool(res)

    async def get_admins(self):
        async with self.pool.acquire() as conn:
            return await conn.fetch("SELECT * FROM admins")

    async def add_channel(self, anime_name, channel_id, primary_link):
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO channels (anime_name, channel_id, primary_link) VALUES ($1, $2, $3)",
                anime_name, channel_id, primary_link
            )

    async def get_channels(self):
        async with self.pool.acquire() as conn:
            return await conn.fetch("SELECT * FROM channels")
            
    async def get_channel_by_name(self, name):
         async with self.pool.acquire() as conn:
            return await conn.fetch("SELECT * FROM channels WHERE anime_name ILIKE $1", f"%{name}%")

    async def remove_channel(self, channel_id):
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM channels WHERE channel_id = $1", channel_id)

    async def set_setting(self, key, value):
        async with self.pool.acquire() as conn:
            await conn.execute("INSERT INTO settings (key, value) VALUES ($1, $2) ON CONFLICT (key) DO UPDATE SET value = $2", key, value)

    async def get_setting(self, key, default=None):
        async with self.pool.acquire() as conn:
            val = await conn.fetchval("SELECT value FROM settings WHERE key = $1", key)
            return val if val else default
            
    async def save_link(self, token, channel_id, user_id, expires_at, link_type, invite_link):
        async with self.pool.acquire() as conn:
             await conn.execute(
                "INSERT INTO active_links (token, channel_id, user_id, expires_at, link_type, invite_link) VALUES ($1, $2, $3, $4, $5, $6)",
                token, channel_id, user_id, expires_at, link_type, invite_link
            )
            
    async def get_link(self, token):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("SELECT * FROM active_links WHERE token = $1", token)

db = Database()
