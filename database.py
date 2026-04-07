import sqlite3
from typing import Optional


class Database:
    def __init__(self, path: str = "bot.db"):
        self.path = path

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def init(self):
        """Створює таблиці якщо їх немає."""
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id         INTEGER PRIMARY KEY,
                    name       TEXT,
                    username   TEXT,
                    active     INTEGER DEFAULT 1,
                    joined_at  TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS user_categories (
                    user_id  INTEGER,
                    category TEXT,
                    PRIMARY KEY (user_id, category)
                );

                CREATE TABLE IF NOT EXISTS watchlist (
                    id       INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id  INTEGER,
                    name     TEXT,
                    added_at TEXT DEFAULT (datetime('now'))
                );
            """)

    # ── Користувачі ───────────────────────────────────────────
    def add_user(self, uid: int, name: str, username: str):
        with self._conn() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO users (id, name, username) VALUES (?,?,?)",
                (uid, name, username)
            )
            # Оновлюємо ім'я якщо вже існує
            conn.execute(
                "UPDATE users SET name=?, username=?, active=1 WHERE id=?",
                (name, username, uid)
            )

    def get_active_users(self) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT id, name FROM users WHERE active=1"
            ).fetchall()
        return [dict(r) for r in rows]

    # ── Категорії ─────────────────────────────────────────────
    def get_user_categories(self, uid: int) -> list[str]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT category FROM user_categories WHERE user_id=?", (uid,)
            ).fetchall()
        return [r["category"] for r in rows]

    def toggle_category(self, uid: int, category: str):
        """Додає категорію якщо нема, видаляє якщо є."""
        with self._conn() as conn:
            exists = conn.execute(
                "SELECT 1 FROM user_categories WHERE user_id=? AND category=?",
                (uid, category)
            ).fetchone()
            if exists:
                conn.execute(
                    "DELETE FROM user_categories WHERE user_id=? AND category=?",
                    (uid, category)
                )
            else:
                conn.execute(
                    "INSERT INTO user_categories (user_id, category) VALUES (?,?)",
                    (uid, category)
                )

    # ── Watchlist ─────────────────────────────────────────────
    def get_watchlist(self, uid: int) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT id, name FROM watchlist WHERE user_id=? ORDER BY added_at DESC",
                (uid,)
            ).fetchall()
        return [dict(r) for r in rows]

    def add_to_watchlist(self, uid: int, name: str):
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO watchlist (user_id, name) VALUES (?,?)",
                (uid, name)
            )

    def remove_from_watchlist(self, uid: int, item_id: int):
        with self._conn() as conn:
            conn.execute(
                "DELETE FROM watchlist WHERE id=? AND user_id=?",
                (item_id, uid)
            )

    # ── Статистика (адмін) ────────────────────────────────────
    def get_stats(self) -> dict:
        with self._conn() as conn:
            users     = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            active    = conn.execute("SELECT COUNT(*) FROM users WHERE active=1").fetchone()[0]
            watchlist = conn.execute("SELECT COUNT(*) FROM watchlist").fetchone()[0]
        return {"users": users, "active": active, "watchlist": watchlist}
