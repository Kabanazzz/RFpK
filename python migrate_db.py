"""Run this ONCE to migrate your existing quiz.db to the new schema."""
import sqlite3

conn = sqlite3.connect("quiz.db")
c = conn.cursor()

migrations = [
    "ALTER TABLE questions ADD COLUMN pack_id INTEGER",
    "ALTER TABLE questions ADD COLUMN image_url TEXT",
    "ALTER TABLE scores ADD COLUMN question_count INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE scores ADD COLUMN pack_id INTEGER",
    'ALTER TABLE scores ADD COLUMN mode TEXT NOT NULL DEFAULT "battle"',
]

for sql in migrations:
    try:
        c.execute(sql)
        print(f"✅ {sql[:50]}")
    except Exception as e:
        print(f"⏭  Skipped (already exists): {e}")

conn.commit()
conn.close()
print("\n✅ Migration done! You can now run app.py")