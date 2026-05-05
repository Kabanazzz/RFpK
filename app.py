from flask import Flask, jsonify, request, render_template
import sqlite3
import random

app = Flask(__name__)

# --- INIT DATABASE ---
def init_db():
    conn = sqlite3.connect("quiz.db")
    c = conn.cursor()

    # USERS
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT
    )
    """)

    # SCORES
    c.execute("""
    CREATE TABLE IF NOT EXISTS scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        score INTEGER
    )
    """)

    # QUESTIONS (with category)
    c.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        question TEXT,
        answer1 TEXT,
        answer2 TEXT,
        answer3 TEXT,
        answer4 TEXT,
        correct INTEGER
    )
    """)

    conn.commit()
    conn.close()

init_db()

# --- HOME ---
@app.route("/")
def home():
    return render_template("index.html")

# --- CREATE USER ---
@app.route("/create_user", methods=["POST"])
def create_user():
    name = request.json.get("name")

    conn = sqlite3.connect("quiz.db")
    c = conn.cursor()

    c.execute("INSERT INTO users (name) VALUES (?)", (name,))
    user_id = c.lastrowid

    conn.commit()
    conn.close()

    return jsonify({"user_id": user_id})

# --- GET RANDOM QUESTION (ALL) ---
@app.route("/question")
def get_question():
    conn = sqlite3.connect("quiz.db")
    c = conn.cursor()

    c.execute("SELECT * FROM questions ORDER BY RANDOM() LIMIT 1")
    row = c.fetchone()

    conn.close()

    if not row:
        return jsonify({"error": "No questions in database"})

    return jsonify({
        "question": row[2],
        "answers": [row[3], row[4], row[5], row[6]],
        "correct_answer": row[7]
    })

# --- GET QUESTION BY CATEGORY ---
@app.route("/question/<category>")
def get_question_by_category(category):
    conn = sqlite3.connect("quiz.db")
    c = conn.cursor()

    c.execute("""
    SELECT * FROM questions 
    WHERE category=? 
    ORDER BY RANDOM() 
    LIMIT 1
    """, (category,))

    row = c.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "No questions in this category"})

    return jsonify({
        "question": row[2],
        "answers": [row[3], row[4], row[5], row[6]],
        "correct_answer": row[7]
    })

# --- ADD QUESTION ---
@app.route("/add_question", methods=["POST"])
def add_question():
    data = request.json

    conn = sqlite3.connect("quiz.db")
    c = conn.cursor()

    c.execute("""
    INSERT INTO questions (category, question, answer1, answer2, answer3, answer4, correct)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data["category"],
        data["question"],
        data["answers"][0],
        data["answers"][1],
        data["answers"][2],
        data["answers"][3],
        data["correct"]
    ))

    conn.commit()
    conn.close()

    return jsonify({"status": "added"})

# --- SAVE SCORE ---
@app.route("/save_score", methods=["POST"])
def save_score():
    user_id = request.json.get("user_id")
    score = request.json.get("score")

    conn = sqlite3.connect("quiz.db")
    c = conn.cursor()

    c.execute("INSERT INTO scores (user_id, score) VALUES (?, ?)", (user_id, score))

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})

# --- TOTAL SCORE ---
@app.route("/total_score/<int:user_id>")
def total_score(user_id):
    conn = sqlite3.connect("quiz.db")
    c = conn.cursor()

    c.execute("SELECT SUM(score) FROM scores WHERE user_id=?", (user_id,))
    total = c.fetchone()[0] or 0

    conn.close()

    return jsonify({"total_score": total})

# --- LEADERBOARD ---
@app.route("/leaderboard")
def leaderboard():
    conn = sqlite3.connect("quiz.db")
    c = conn.cursor()

    c.execute("""
    SELECT users.name, SUM(scores.score) as total
    FROM scores
    JOIN users ON users.id = scores.user_id
    GROUP BY users.id
    ORDER BY total DESC
    LIMIT 10
    """)

    data = [{"name": row[0], "score": row[1]} for row in c.fetchall()]

    conn.close()

    return jsonify(data)

# --- RUN ---
if __name__ == "__main__":
    app.run(debug=True)