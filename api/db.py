# Darbs ar SQLite datubāzi: rezultātu saglabāšana un nolasīšana.
# Šo failu izmanto api/main.py.
import sqlite3
from pathlib import Path

# Datubāzes fails atrodas projekta mapē (blakus mapei api)
DB_PATH = Path(__file__).resolve().parent.parent / "scores.db"


def init_db():
    """Izveido tabulu scores, ja tās vēl nav (droši izsaukt vairākkārt)."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,  -- ieraksta numurs
                player_name TEXT NOT NULL,             -- spēlētāja vārds
                score INTEGER NOT NULL,                -- punkti
                game_time INTEGER NOT NULL,            -- spēles ilgums sekundēs
                max_tile INTEGER NOT NULL,             -- lielākais kvadrāts
                created_at TEXT DEFAULT CURRENT_TIMESTAMP  -- saglabāšanas laiks
            )
        """)


def add_score(data):
    """Pievieno jaunu rezultātu. data — vārdnīca ar name, score, game_time, max_tile."""
    with sqlite3.connect(DB_PATH) as conn:
        # Jautājuma zīmes (?) aizsargā no SQL injekcijām
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
    """Atgriež 10 labākos spēlētājus (saraksts ar name un score).

    Katrs spēlētājs parādās vienu reizi ar savu LABĀKO rezultātu.
    Visas partijas paliek datubāzē (vajadzīgas statistikai), bet tabulā
    tās netiek dublētas.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row  # rindas var nolasīt pēc kolonnu nosaukumiem

        # GROUP BY ... NOCASE — "Oskars" un "oskars" tiek uzskatīti par vienu spēlētāju.
        # MAX(score) — no visām spēlētāja partijām ņem labāko.
        # Ja punkti vienādi, augstāk ir tas, kurš šo rezultātu sasniedza agrāk (MIN(id)).
        rows = conn.execute("""
            SELECT player_name AS name, MAX(score) AS score
            FROM scores
            GROUP BY player_name COLLATE NOCASE
            ORDER BY MAX(score) DESC, MIN(id) ASC
            LIMIT 10
        """).fetchall()

        return [dict(row) for row in rows]


def get_player_stats(name):
    """Atgriež spēlētāja statistiku (spēles, labākais rezultāts, lielākais kvadrāts).

    Ja spēlētājs nav atrasts, atgriež None.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        # COLLATE NOCASE — vārda meklēšana neņem vērā lielos/mazos burtus
        row = conn.execute("""
            SELECT
                player_name AS name,
                COUNT(*) AS games,
                MAX(score) AS best_score,
                MAX(max_tile) AS max_tile
            FROM scores
            WHERE player_name = ? COLLATE NOCASE
            GROUP BY player_name COLLATE NOCASE
        """, (name,)).fetchone()

        return dict(row) if row else None
