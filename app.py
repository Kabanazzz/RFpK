from flask import Flask, jsonify, request, send_from_directory
import sqlite3
import random
import requests



app = Flask(__name__)


@app.route("/")
def home():
    return send_from_directory(".", "index.html")


def init_db():
    conn = sqlite3.connect("quiz.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        score INTEGER
    )
    """)

    conn.commit()
    conn.close()

init_db()


questions = [
    {
        "question": "What is the capital of France?",
        "answers": ["Berlin", "Paris", "Rome", "Madrid"],
        "correct": 1
    },
    {
        "question": "What is 2 + 2?",
        "answers": ["3", "4", "5", "22"],
        "correct": 1
    },
    {
        "question": "Which planet is the largest?",
        "answers": ["Earth", "Mars", "Jupiter", "Venus"],
        "correct": 2
    },
    {
        "question": "Who wrote 'Romeo and Juliet'?",
        "answers": ["Shakespeare", "Tolstoy", "Hemingway", "Dante"],
        "correct": 0
    },
    {
        "question": "What is the boiling point of water?",
        "answers": ["90°C", "100°C", "120°C", "80°C"],
        "correct": 1
    }
]


@app.route("/question")
def get_question():
    q = random.choice(questions)
    return jsonify({
        "question": q["question"],
        "answers": q["answers"],
        "correct_answer": q["correct"]
    })


@app.route("/save_score", methods=["POST"])
def save_score():
    data = request.json
    score = data.get("score", 0)

    conn = sqlite3.connect("quiz.db")
    c = conn.cursor()
    c.execute("INSERT INTO scores (score) VALUES (?)", (score,))
    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})


@app.route("/leaderboard")
def leaderboard():
    conn = sqlite3.connect("quiz.db")
    c = conn.cursor()
    c.execute("SELECT score FROM scores ORDER BY score DESC LIMIT 10")
    scores = [row[0] for row in c.fetchall()]
    conn.close()

    return jsonify(scores)

@app.route("/wiki")
def wiki_question():
    url = "https://en.wikipedia.org/api/rest_v1/page/random/summary"
    res = requests.get(url).json()

    title = res.get("title", "Unknown")

    return jsonify({
        "question": "What is this article about?",
        "answers": [title, "Technology", "Animal", "City"],
        "correct_answer": 0
    })

if __name__ == "__main__":
    app.run(debug=True)