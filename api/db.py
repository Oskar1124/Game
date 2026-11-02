import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "scores.db"


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT NOT NULL,
                score INTEGER NOT NULL,
                game_time INTEGER NOT NULL,
                max_tile INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)


def add_score(data):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO scores
            (player_name, score, game_time, max_tile)
            VALUES (?, ?, ?, ?)
        """, (
            data["name"],
            data["score"],
            data["game_time"],
            data["max_tile"]
        ))


def get_top_scores():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute("""
            SELECT player_name AS name, score
            FROM scores
            ORDER BY score DESC
            LIMIT 10
        """).fetchall()

        return [dict(row) for row in rows]


def get_player_stats(name):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        row = conn.execute("""
            SELECT
                player_name AS name,
                COUNT(*) AS games,
                MAX(score) AS best_score,
                MAX(max_tile) AS max_tile
            FROM scores
            WHERE player_name = ? COLLATE NOCASE
            GROUP BY player_name
        """, (name,)).fetchone()

        return dict(row) if row else None