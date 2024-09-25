
import logging, sqlite3
from datetime import datetime

class Connection:
    def __init__(self, path):
        self.connect = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)

    def __enter__(self):
        return self.connect.cursor()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connect.commit()
        self.connect.close()

class Database:
    def __init__(self, path):
        self.path = path

    def initalise(self):
        with Connection(self.path) as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS songs (
                    hash int NOT NULL PRIMARY KEY,
                    play_count INTEGER NOT NULL,
                    last_played TIMESTAMP NOT NULL
                )
                """
            )

        logging.debug("Initialised database")

    def update(self, song):
        with Connection(self.path) as cursor:
            now = datetime.now()
            cursor.execute(
                """
                INSERT OR REPLACE INTO songs
                VALUES (?, 1, ?)
                ON CONFLICT (hash) DO
                UPDATE SET
                    play_count = play_count + 1,
                    last_played = ?
                """,
                (hash(song), now, now)
            )

        logging.debug(f"Updated database: {hash(song)}")

    def select(self, song):
        with Connection(self.path) as cursor:
            result = cursor.execute(
                """
                SELECT
                    play_count,
                    last_played
                FROM songs
                WHERE hash = ?
                """,
                (hash(song),)
            ).fetchone()

        logging.debug(f"Retrieved from database: {hash(song)}: {result}")

        if result:
            return result

        return 0, None
