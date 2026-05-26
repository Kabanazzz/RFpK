from flask import Flask, jsonify, request, render_template, send_from_directory
import sqlite3, os

from repository import (UserRepository, QuestionRepository, ScoreRepository,
                        PackRepository, SessionRepository, init_db)

app = Flask(__name__)

init_db()

# re-import questions if table is empty
def _maybe_seed():
    import json
    if QuestionRepository.count_battle() == 0:
        with open("questions.json", "r", encoding="utf-8") as f:
            qs = json.load(f)
        for q in qs:
            QuestionRepository.add(q["category"], q["question"], q["answers"], q["correct"])

_maybe_seed()


def _row_to_question(row) -> dict:
    return {
        "id":             row["id"],
        "category":       row["category"],
        "question":       row["question"],
        "answers":        [row["answer1"], row["answer2"], row["answer3"], row["answer4"]],
        "correct_answer": row["correct"],
        "image_url":      row["image_url"] if row["image_url"] else None,
    }


# ─── PAGES ────────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    return render_template("index.html")


# ─── USER ─────────────────────────────────────────────────────────────────────

@app.route("/login", methods=["POST"])
def login():
    name = (request.json or {}).get("name", "").strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400
    result = UserRepository.create_or_get(name)
    return jsonify(result)


@app.route("/create_user", methods=["POST"])
def create_user():
    return login()


# ─── PACKS ────────────────────────────────────────────────────────────────────

@app.route("/packs")
def get_packs():
    return jsonify(PackRepository.get_all())


@app.route("/packs", methods=["POST"])
def create_pack():
    data = request.json or {}
    name        = data.get("name", "").strip()
    description = data.get("description", "")
    category    = data.get("category", "Custom").strip()
    created_by  = data.get("user_id")
    if not name:
        return jsonify({"error": "Pack name required"}), 400
    pack_id = PackRepository.create(name, description, category, created_by)
    return jsonify({"id": pack_id, "name": name}), 201


@app.route("/packs/<int:pack_id>", methods=["DELETE"])
def delete_pack(pack_id: int):
    PackRepository.delete(pack_id)
    return jsonify({"status": "deleted"})


@app.route("/packs/<int:pack_id>/questions")
def get_pack_questions(pack_id: int):
    qs = QuestionRepository.get_by_pack(pack_id)
    return jsonify(qs)


# ─── QUESTIONS ────────────────────────────────────────────────────────────────

@app.route("/question")
def get_question():
    session_id = request.args.get("session_id", type=int)
    exclude = []
    if session_id:
        sess = SessionRepository.get_by_id(session_id)
        if sess and sess["used_ids"]:
            exclude = [int(x) for x in sess["used_ids"].split(",") if x]
    row = QuestionRepository.get_random(exclude_ids=exclude)
    if not row:
        return jsonify({"error": "no_more_questions"}), 404
    return jsonify(_row_to_question(row))


@app.route("/question/<category>")
def get_question_by_category(category: str):
    session_id = request.args.get("session_id", type=int)
    exclude = []
    if session_id:
        sess = SessionRepository.get_by_id(session_id)
        if sess and sess["used_ids"]:
            exclude = [int(x) for x in sess["used_ids"].split(",") if x]
    row = QuestionRepository.get_random_by_category(category, exclude_ids=exclude)
    if not row:
        return jsonify({"error": "no_more_questions"}), 404
    return jsonify(_row_to_question(row))


@app.route("/packs/<int:pack_id>/question")
def get_pack_question(pack_id: int):
    session_id = request.args.get("session_id", type=int)
    exclude = []
    if session_id:
        sess = SessionRepository.get_by_id(session_id)
        if sess and sess["used_ids"]:
            exclude = [int(x) for x in sess["used_ids"].split(",") if x]
    row = QuestionRepository.get_random_by_pack(pack_id, exclude_ids=exclude)
    if not row:
        return jsonify({"error": "no_more_questions"}), 404
    return jsonify(_row_to_question(row))


@app.route("/categories")
def get_categories():
    return jsonify(QuestionRepository.get_all_categories())


@app.route("/add_question", methods=["POST"])
def add_question():
    data = request.json or {}
    required = {"question", "answers", "correct"}
    if required - data.keys():
        return jsonify({"error": f"Missing: {required - data.keys()}"}), 400
    if len(data["answers"]) != 4:
        return jsonify({"error": "Need 4 answers"}), 400
    qid = QuestionRepository.add(
        data.get("category", ""),
        data["question"],
        data["answers"],
        data["correct"],
        pack_id=data.get("pack_id"),
        image_url=data.get("image_url"),
    )
    return jsonify({"status": "added", "id": qid}), 201


@app.route("/questions/<int:question_id>", methods=["DELETE"])
def delete_question(question_id: int):
    QuestionRepository.delete(question_id)
    return jsonify({"status": "deleted"})


# ─── SESSIONS ─────────────────────────────────────────────────────────────────

@app.route("/session/start", methods=["POST"])
def start_session():
    data      = request.json or {}
    user_id   = data.get("user_id")
    mode      = data.get("mode", "battle")   # 'battle' | 'pack' | 'category'
    pack_id   = data.get("pack_id")
    category  = data.get("category")
    if not user_id:
        return jsonify({"error": "user_id required"}), 400
    sid = SessionRepository.create(user_id, mode, pack_id, category)
    return jsonify({"session_id": sid})


@app.route("/session/<int:session_id>")
def get_session(session_id: int):
    sess = SessionRepository.get_by_id(session_id)
    if not sess:
        return jsonify({"error": "not found"}), 404
    used = [int(x) for x in sess["used_ids"].split(",") if x]
    return jsonify({
        "id":             sess["id"],
        "user_id":        sess["user_id"],
        "mode":           sess["mode"],
        "pack_id":        sess["pack_id"],
        "category":       sess["category"],
        "score":          sess["score"],
        "question_count": sess["question_count"],
        "used_ids":       used,
        "is_active":      sess["is_active"],
    })


@app.route("/session/<int:session_id>/answer", methods=["POST"])
def answer_question(session_id: int):
    data       = request.json or {}
    correct    = data.get("correct", False)
    question_id = data.get("question_id")
    sess = SessionRepository.get_by_id(session_id)
    if not sess:
        return jsonify({"error": "session not found"}), 404
    used = [int(x) for x in sess["used_ids"].split(",") if x]
    if question_id and question_id not in used:
        used.append(question_id)
    score = sess["score"] + (1 if correct else 0)
    qcount = sess["question_count"] + 1
    SessionRepository.update(session_id, score, qcount, used)
    return jsonify({"score": score, "question_count": qcount})


@app.route("/session/<int:session_id>/finish", methods=["POST"])
def finish_session(session_id: int):
    sess = SessionRepository.get_by_id(session_id)
    if not sess:
        return jsonify({"error": "not found"}), 404
    ScoreRepository.save(sess["user_id"], sess["score"],
                         sess["question_count"], sess["pack_id"], sess["mode"])
    SessionRepository.finish(session_id)
    return jsonify({"score": sess["score"], "question_count": sess["question_count"]})


@app.route("/session/active/<int:user_id>")
def get_active_session(user_id: int):
    sess = SessionRepository.get_active(user_id)
    if not sess:
        return jsonify(None)
    used = [int(x) for x in sess["used_ids"].split(",") if x]
    return jsonify({
        "id":             sess["id"],
        "user_id":        sess["user_id"],
        "mode":           sess["mode"],
        "pack_id":        sess["pack_id"],
        "category":       sess["category"],
        "score":          sess["score"],
        "question_count": sess["question_count"],
        "used_ids":       used,
        "is_active":      sess["is_active"],
    })


# ─── SCORES / LEADERBOARD ─────────────────────────────────────────────────────

@app.route("/save_score", methods=["POST"])
def save_score():
    data = request.json or {}
    user_id = data.get("user_id")
    score   = data.get("score")
    if user_id is None or score is None:
        return jsonify({"error": "user_id and score required"}), 400
    ScoreRepository.save(user_id, score, data.get("question_count", 0),
                         data.get("pack_id"), data.get("mode", "battle"))
    return jsonify({"status": "ok"})


@app.route("/leaderboard")
def leaderboard():
    mode = request.args.get("mode")
    return jsonify(ScoreRepository.get_leaderboard(limit=10, mode=mode))


if __name__ == "__main__":
    app.run(debug=True)