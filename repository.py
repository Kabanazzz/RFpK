from __future__ import annotations
import sqlite3
from typing import Optional

DB_PATH = "quiz.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ─── USER REPOSITORY ─────────────────────────────────────────────────────────

class UserRepository:

    @staticmethod
    def create(name: str) -> int:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("INSERT INTO users (name) VALUES (?)", (name,))
            conn.commit()
            return c.lastrowid

    @staticmethod
    def get_by_id(user_id: int):
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            return c.fetchone()


# ─── QUESTION REPOSITORY ──────────────────────────────────────────────────────

class QuestionRepository:

    @staticmethod
    def get_random() -> Optional[sqlite3.Row]:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM questions ORDER BY RANDOM() LIMIT 1")
            return c.fetchone()

    @staticmethod
    def get_random_by_category(category: str) -> Optional[sqlite3.Row]:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT * FROM questions WHERE category = ? ORDER BY RANDOM() LIMIT 1",
                (category,),
            )
            return c.fetchone()

    @staticmethod
    def add(category: str, question: str, answers: list, correct: int) -> int:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute(
                """
                INSERT INTO questions
                    (category, question, answer1, answer2, answer3, answer4, correct)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (category, question, answers[0], answers[1], answers[2], answers[3], correct),
            )
            conn.commit()
            return c.lastrowid

    @staticmethod
    def get_all_categories() -> list:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT DISTINCT category FROM questions ORDER BY category")
            return [row["category"] for row in c.fetchall()]


# ─── SCORE REPOSITORY ─────────────────────────────────────────────────────────

class ScoreRepository:

    @staticmethod
    def save(user_id: int, score: int, question_count: int) -> int:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO scores (user_id, score, question_count) VALUES (?, ?, ?)",
                (user_id, score, question_count),
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
    def get_leaderboard(limit: int = 10) -> list:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute(
                """
                SELECT
                    users.name,
                    SUM(scores.score)          AS total_score,
                    SUM(scores.question_count) AS total_questions
                FROM scores
                JOIN users ON users.id = scores.user_id
                GROUP BY users.id
                ORDER BY total_score DESC
                LIMIT ?
                """,
                (limit,),
            )
            return [
                {
                    "name": row["name"],
                    "score": row["total_score"],
                    "questions": row["total_questions"] or 0,
                }
                for row in c.fetchall()
            ]