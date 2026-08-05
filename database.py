import aiosqlite

DB_NAME = "catcus_bot.db"


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:

        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            mode TEXT DEFAULT 'anonymous',
            banned INTEGER DEFAULT 0
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message_id INTEGER,
            mode TEXT
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """)

        await db.commit()


async def add_user(user_id, username, full_name):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO users
            (user_id, username, full_name)
            VALUES (?, ?, ?)
            """,
            (user_id, username, full_name)
        )
        await db.commit()


async def get_user_mode(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT mode FROM users WHERE user_id=?",
            (user_id,)
        )
        result = await cursor.fetchone()

        return result[0] if result else "anonymous"


async def change_mode(user_id, mode):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET mode=? WHERE user_id=?",
            (mode, user_id)
        )
        await db.commit()


async def save_message(user_id, message_id, mode):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT INTO messages
            (user_id, message_id, mode)
            VALUES (?, ?, ?)
            """,
            (user_id, message_id, mode)
        )
        await db.commit()


async def ban_user(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET banned=1 WHERE user_id=?",
            (user_id,)
        )
        await db.commit()


async def unban_user(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET banned=0 WHERE user_id=?",
            (user_id,)
        )
        await db.commit()


async def is_banned(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT banned FROM users WHERE user_id=?",
            (user_id,)
        )

        result = await cursor.fetchone()

        return bool(result and result[0] == 1)


async def get_users_count():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM users"
        )

        result = await cursor.fetchone()

        return result[0]
