from flask import Flask, jsonify, request, render_template
import sqlite3

from repository import UserRepository, QuestionRepository, ScoreRepository

app = Flask(__name__)


# ─── DATABASE INIT ────────────────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect("quiz.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id   INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS scores (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id        INTEGER NOT NULL,
        score          INTEGER NOT NULL DEFAULT 0,
        question_count INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT    NOT NULL,
        question TEXT    NOT NULL,
        answer1  TEXT    NOT NULL,
        answer2  TEXT    NOT NULL,
        answer3  TEXT    NOT NULL,
        answer4  TEXT    NOT NULL,
        correct  INTEGER NOT NULL
    )
    """)

    conn.commit()
    conn.close()


init_db()


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def _row_to_question(row) -> dict:
    """Convert a DB question row to a JSON-serialisable dict."""
    return {
        "id":             row["id"],
        "category":       row["category"],
        "question":       row["question"],
        "answers":        [row["answer1"], row["answer2"], row["answer3"], row["answer4"]],
        "correct_answer": row["correct"],
    }


# ─── PAGES ────────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    return render_template("index.html")


# ─── USER CONTROLLER ──────────────────────────────────────────────────────────

@app.route("/create_user", methods=["POST"])
def create_user():
    name = (request.json or {}).get("name", "").strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400

    user_id = UserRepository.create(name)
    return jsonify({"user_id": user_id})


# ─── QUESTION CONTROLLER ──────────────────────────────────────────────────────

@app.route("/question")
def get_question():
    row = QuestionRepository.get_random()
    if not row:
        return jsonify({"error": "No questions in database"}), 404
    return jsonify(_row_to_question(row))


@app.route("/question/<category>")
def get_question_by_category(category: str):
    row = QuestionRepository.get_random_by_category(category)
    if not row:
        return jsonify({"error": f"No questions in category '{category}'"}), 404
    return jsonify(_row_to_question(row))


@app.route("/categories")
def get_categories():
    categories = QuestionRepository.get_all_categories()
    return jsonify(categories)


@app.route("/add_question", methods=["POST"])
def add_question():
    data = request.json or {}
    required = {"category", "question", "answers", "correct"}
    missing = required - data.keys()
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    if len(data["answers"]) != 4:
        return jsonify({"error": "Exactly 4 answers required"}), 400

    question_id = QuestionRepository.add(
        data["category"],
        data["question"],
        data["answers"],
        data["correct"],
    )
    return jsonify({"status": "added", "id": question_id}), 201


# ─── SCORE CONTROLLER ─────────────────────────────────────────────────────────

@app.route("/save_score", methods=["POST"])
def save_score():
    data = request.json or {}
    user_id        = data.get("user_id")
    score          = data.get("score")
    question_count = data.get("question_count", 0)   # <-- new required field

    if user_id is None or score is None:
        return jsonify({"error": "user_id and score are required"}), 400

    ScoreRepository.save(user_id, score, question_count)
    return jsonify({"status": "ok"})


@app.route("/total_score/<int:user_id>")
def total_score(user_id: int):
    total = ScoreRepository.get_total_by_user(user_id)
    return jsonify({"total_score": total})


@app.route("/leaderboard")
def leaderboard():
    data = ScoreRepository.get_leaderboard(limit=10)
    return jsonify(data)


# ─── RUN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True)