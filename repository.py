from __future__ import annotations
import sqlite3
from typing import Optional

DB_PATH = "quiz.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS packs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            description TEXT,
            category    TEXT NOT NULL,
            created_by  INTEGER,
            is_public   INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            pack_id    INTEGER,
            category   TEXT NOT NULL DEFAULT '',
            question   TEXT NOT NULL,
            answer1    TEXT NOT NULL,
            answer2    TEXT NOT NULL,
            answer3    TEXT NOT NULL,
            answer4    TEXT NOT NULL,
            correct    INTEGER NOT NULL,
            image_url  TEXT
        )""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id        INTEGER NOT NULL,
            score          INTEGER NOT NULL DEFAULT 0,
            question_count INTEGER NOT NULL DEFAULT 0,
            pack_id        INTEGER,
            mode           TEXT NOT NULL DEFAULT 'battle',
            created_at     TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL,
            mode            TEXT NOT NULL DEFAULT 'battle',
            pack_id         INTEGER,
            category        TEXT,
            score           INTEGER NOT NULL DEFAULT 0,
            question_count  INTEGER NOT NULL DEFAULT 0,
            used_ids        TEXT NOT NULL DEFAULT '',
            is_active       INTEGER NOT NULL DEFAULT 1,
            created_at      TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )""")
        conn.commit()


# ─── USER REPOSITORY ──────────────────────────────────────────────────────────

class UserRepository:

    @staticmethod
    def create_or_get(name: str) -> dict:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE name = ?", (name,))
            row = c.fetchone()
            if row:
                return {"id": row["id"], "name": row["name"], "is_new": False}
            c.execute("INSERT INTO users (name) VALUES (?)", (name,))
            conn.commit()
            return {"id": c.lastrowid, "name": name, "is_new": True}

    @staticmethod
    def get_by_id(user_id: int):
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            return c.fetchone()


# ─── PACK REPOSITORY ──────────────────────────────────────────────────────────

class PackRepository:

    @staticmethod
    def create(name: str, description: str, category: str, created_by: int) -> int:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO packs (name, description, category, created_by) VALUES (?, ?, ?, ?)",
                (name, description, category, created_by),
            )
            conn.commit()
            return c.lastrowid

    @staticmethod
    def get_all() -> list:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT p.*, u.name as author_name,
                       COUNT(q.id) as question_count
                FROM packs p
                LEFT JOIN users u ON u.id = p.created_by
                LEFT JOIN questions q ON q.pack_id = p.id
                GROUP BY p.id
                ORDER BY p.id DESC
            """)
            return [dict(row) for row in c.fetchall()]

    @staticmethod
    def get_by_id(pack_id: int):
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM packs WHERE id = ?", (pack_id,))
            return c.fetchone()

    @staticmethod
    def delete(pack_id: int):
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM questions WHERE pack_id = ?", (pack_id,))
            c.execute("DELETE FROM packs WHERE id = ?", (pack_id,))
            conn.commit()


# ─── QUESTION REPOSITORY ──────────────────────────────────────────────────────

class QuestionRepository:

    @staticmethod
    def get_random(exclude_ids: list = None) -> Optional[sqlite3.Row]:
        with get_connection() as conn:
            c = conn.cursor()
            if exclude_ids:
                placeholders = ",".join("?" * len(exclude_ids))
                c.execute(f"SELECT * FROM questions WHERE pack_id IS NULL AND id NOT IN ({placeholders}) ORDER BY RANDOM() LIMIT 1", exclude_ids)
            else:
                c.execute("SELECT * FROM questions WHERE pack_id IS NULL ORDER BY RANDOM() LIMIT 1")
            return c.fetchone()

    @staticmethod
    def get_random_by_category(category: str, exclude_ids: list = None) -> Optional[sqlite3.Row]:
        with get_connection() as conn:
            c = conn.cursor()
            if exclude_ids:
                placeholders = ",".join("?" * len(exclude_ids))
                c.execute(f"SELECT * FROM questions WHERE category = ? AND id NOT IN ({placeholders}) ORDER BY RANDOM() LIMIT 1", [category] + exclude_ids)
            else:
                c.execute("SELECT * FROM questions WHERE category = ? ORDER BY RANDOM() LIMIT 1", (category,))
            return c.fetchone()

    @staticmethod
    def get_random_by_pack(pack_id: int, exclude_ids: list = None) -> Optional[sqlite3.Row]:
        with get_connection() as conn:
            c = conn.cursor()
            if exclude_ids:
                placeholders = ",".join("?" * len(exclude_ids))
                c.execute(f"SELECT * FROM questions WHERE pack_id = ? AND id NOT IN ({placeholders}) ORDER BY RANDOM() LIMIT 1", [pack_id] + exclude_ids)
            else:
                c.execute("SELECT * FROM questions WHERE pack_id = ? ORDER BY RANDOM() LIMIT 1", (pack_id,))
            return c.fetchone()

    @staticmethod
    def get_by_pack(pack_id: int) -> list:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM questions WHERE pack_id = ?", (pack_id,))
            return [dict(row) for row in c.fetchall()]

    @staticmethod
    def add(category: str, question: str, answers: list, correct: int,
            pack_id: int = None, image_url: str = None) -> int:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO questions (pack_id, category, question, answer1, answer2, answer3, answer4, correct, image_url) VALUES (?,?,?,?,?,?,?,?,?)",
                (pack_id, category, question, answers[0], answers[1], answers[2], answers[3], correct, image_url),
            )
            conn.commit()
            return c.lastrowid

    @staticmethod
    def delete(question_id: int):
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM questions WHERE id = ?", (question_id,))
            conn.commit()

    @staticmethod
    def get_all_categories() -> list:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT DISTINCT category FROM questions WHERE pack_id IS NULL AND category != '' ORDER BY category")
            return [row["category"] for row in c.fetchall()]

    @staticmethod
    def count_by_pack(pack_id: int) -> int:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM questions WHERE pack_id = ?", (pack_id,))
            return c.fetchone()[0]

    @staticmethod
    def count_battle(category: str = None) -> int:
        with get_connection() as conn:
            c = conn.cursor()
            if category:
                c.execute("SELECT COUNT(*) FROM questions WHERE pack_id IS NULL AND category = ?", (category,))
            else:
                c.execute("SELECT COUNT(*) FROM questions WHERE pack_id IS NULL")
            return c.fetchone()[0]


# ─── SESSION REPOSITORY ───────────────────────────────────────────────────────

class SessionRepository:

    @staticmethod
    def create(user_id: int, mode: str, pack_id: int = None, category: str = None) -> int:
        # deactivate old sessions for this user
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("UPDATE sessions SET is_active = 0 WHERE user_id = ?", (user_id,))
            c.execute(
                "INSERT INTO sessions (user_id, mode, pack_id, category) VALUES (?,?,?,?)",
                (user_id, mode, pack_id, category),
            )
            conn.commit()
            return c.lastrowid

    @staticmethod
    def get_active(user_id: int):
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM sessions WHERE user_id = ? AND is_active = 1 ORDER BY id DESC LIMIT 1", (user_id,))
            return c.fetchone()

    @staticmethod
    def update(session_id: int, score: int, question_count: int, used_ids: list):
        with get_connection() as conn:
            c = conn.cursor()
            c.execute(
                "UPDATE sessions SET score=?, question_count=?, used_ids=? WHERE id=?",
                (score, question_count, ",".join(str(i) for i in used_ids), session_id),
            )
            conn.commit()

    @staticmethod
    def finish(session_id: int):
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("UPDATE sessions SET is_active = 0 WHERE id = ?", (session_id,))
            conn.commit()

    @staticmethod
    def get_by_id(session_id: int):
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
            return c.fetchone()


# ─── SCORE REPOSITORY ─────────────────────────────────────────────────────────

class ScoreRepository:

    @staticmethod
    def save(user_id: int, score: int, question_count: int,
             pack_id: int = None, mode: str = "battle") -> int:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO scores (user_id, score, question_count, pack_id, mode) VALUES (?,?,?,?,?)",
                (user_id, score, question_count, pack_id, mode),
            )
            conn.commit()
            return c.lastrowid

    @staticmethod
    def get_total_by_user(user_id: int) -> int:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT SUM(score) FROM scores WHERE user_id = ?", (user_id,))
            result = c.fetchone()[0]
            return result or 0

    @staticmethod
    def get_leaderboard(limit: int = 10, mode: str = None) -> list:
        with get_connection() as conn:
            c = conn.cursor()
            if mode:
                c.execute("""
                    SELECT users.name, SUM(scores.score) AS total_score,
                           SUM(scores.question_count) AS total_questions
                    FROM scores JOIN users ON users.id = scores.user_id
                    WHERE scores.mode = ?
                    GROUP BY users.id ORDER BY total_score DESC LIMIT ?
                """, (mode, limit))
            else:
                c.execute("""
                    SELECT users.name, SUM(scores.score) AS total_score,
                           SUM(scores.question_count) AS total_questions
                    FROM scores JOIN users ON users.id = scores.user_id
                    GROUP BY users.id ORDER BY total_score DESC LIMIT ?
                """, (limit,))
            return [{"name": r["name"], "score": r["total_score"], "questions": r["total_questions"] or 0}
                    for r in c.fetchall()]