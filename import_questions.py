import json
import sqlite3

# подключаемся к базе
conn = sqlite3.connect("quiz.db")
c = conn.cursor()

# открываем JSON файл с вопросами
with open("questions.json", "r", encoding="utf-8") as f:
    questions = json.load(f)

# добавляем вопросы в базу
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

# сохраняем изменения
conn.commit()
conn.close()

print(" All questions imported successfully!")