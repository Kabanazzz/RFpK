import json
import sqlite3

DB_PATH = "quiz.db"

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Clear existing questions to avoid duplicates on re-import
c.execute("DELETE FROM questions")

with open("questions.json", "r", encoding="utf-8") as f:
    questions = json.load(f)

for q in questions:
    c.execute("""
    INSERT INTO questions (category, question, answer1, answer2, answer3, answer4, correct)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        q["category"],
        q["question"],
        q["answers"][0],
        q["answers"][1],
        q["answers"][2],
        q["answers"][3],
        q["correct"]
    ))

conn.commit()
conn.close()

print(f"✅ Imported {len(questions)} questions successfully!")