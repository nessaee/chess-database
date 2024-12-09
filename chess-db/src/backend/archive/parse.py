import chess.pgn
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict
from contextlib import contextmanager
import time
from functools import lru_cache

class ChessProcessor:
    def __init__(self, db_config):
        self.db_config = db_config
        self.setup_logger()
        self._initialize_database()
        self.player_cache: Dict[str, int] = {}

    def setup_logger(self):
        self.logger = logging.getLogger('ChessProcessor')
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _initialize_database(self):
        with self._get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS players (
                        id SERIAL PRIMARY KEY,
                        name TEXT NOT NULL,
                        first_played DATE,
                        last_played DATE,
                        total_games INTEGER DEFAULT 0,
                        CONSTRAINT unique_player_name UNIQUE (name)
                    );

                    CREATE TABLE IF NOT EXISTS games (
                        id SERIAL PRIMARY KEY,
                        white_player_id INTEGER REFERENCES players(id),
                        black_player_id INTEGER REFERENCES players(id),
                        date DATE,
                        result VARCHAR(10),
                        eco VARCHAR(10),
                        moves TEXT
                    );

                    CREATE INDEX IF NOT EXISTS idx_players_name ON players(name);
                    CREATE INDEX IF NOT EXISTS idx_games_players ON games(white_player_id, black_player_id);
                """)
                conn.commit()

    @contextmanager
    def _get_db_connection(self):
        conn = None
        try:
            conn = psycopg2.connect(
                host=self.db_config.host,
                port=self.db_config.port,
                database=self.db_config.database,
                user=self.db_config.user,
                password=self.db_config.password
            )
            # Set higher isolation level for player operations
            conn.set_session(isolation_level='REPEATABLE READ', autocommit=False)
            yield conn
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _get_or_create_player(self, name: str, conn) -> int:
        """Get or create player with proper concurrency handling"""
        max_retries = 3
        retry_delay = 0.1

        for attempt in range(max_retries):
            try:
                with conn.cursor() as cursor:
                    # First try to select the player
                    cursor.execute(
                        "SELECT id FROM players WHERE name = %s",
                        (name,)
                    )
                    result = cursor.fetchone()
                    
                    if result:
                        return result[0]
                    
                    # Player doesn't exist, create new one
                    cursor.execute("""
                        INSERT INTO players (name)
                        VALUES (%s)
                        ON CONFLICT (name) DO UPDATE
                            SET name = EXCLUDED.name
                        RETURNING id
                    """, (name,))
                    
                    player_id = cursor.fetchone()[0]
                    conn.commit()
                    return player_id

            except psycopg2.Error as e:
                conn.rollback()
                if attempt == max_retries - 1:
                    raise
                time.sleep(retry_delay * (attempt + 1))

        raise RuntimeError("Failed to get or create player after retries")

    def parse_pgn_file(self, pgn_path: Path) -> Tuple[int, int]:
        games_processed = 0
        failed_games = 0
        batch = []
        BATCH_SIZE = 100  # Reduced batch size for better concurrency

        with self._get_db_connection() as conn:
            try:
                with open(pgn_path) as pgn_file:
                    while True:
                        try:
                            game = chess.pgn.read_game(pgn_file)
                            if game is None:
                                break

                            # Process each game in its own transaction
                            game_data = self._process_game(game, conn)
                            if game_data:
                                batch.append(game_data)
                                games_processed += 1

                                if len(batch) >= BATCH_SIZE:
                                    self._insert_games_batch(conn, batch)
                                    batch = []

                        except Exception as e:
                            failed_games += 1
                            self.logger.error(f"Error processing game: {str(e)}")
                            continue

                    # Process remaining games
                    if batch:
                        self._insert_games_batch(conn, batch)

            except Exception as e:
                self.logger.error(f"Error processing file {pgn_path}: {str(e)}")
                raise

        return games_processed, failed_games

    def _process_game(self, game, conn) -> Optional[tuple]:
        """Process single game with proper transaction handling"""
        try:
            headers = game.headers
            
            # Get player IDs with retries
            white_id = self._get_or_create_player(headers.get("White", "Unknown"), conn)
            black_id = self._get_or_create_player(headers.get("Black", "Unknown"), conn)

            moves = []
            board = game.board()
            for move in game.mainline_moves():
                moves.append(move.uci())

            return (
                white_id,
                black_id,
                self._parse_date(headers.get("Date", "")),
                headers.get("Result", "*"),
                headers.get("ECO", ""),
                " ".join(moves)
            )

        except Exception as e:
            self.logger.error(f"Error processing game data: {str(e)}")
            return None

    def _insert_games_batch(self, conn, batch):
        """Insert batch of games with retry logic"""
        if not batch:
            return

        max_retries = 3
        retry_delay = 0.1

        for attempt in range(max_retries):
            try:
                with conn.cursor() as cursor:
                    execute_values(
                        cursor,
                        """
                        INSERT INTO games (
                            white_player_id, black_player_id, date,
                            result, eco, moves
                        ) VALUES %s
                        """,
                        batch,
                        page_size=100
                    )
                conn.commit()
                return
            except psycopg2.Error as e:
                conn.rollback()
                if attempt == max_retries - 1:
                    raise
                time.sleep(retry_delay * (attempt + 1))

    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        if not date_str or date_str == "???":
            return None
            
        try:
            for fmt in ("%Y.%m.%d", "%Y/%m/%d", "%Y-%m-%d"):
                try:
                    return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
                except ValueError:
                    continue
            
            if len(date_str.replace(".", "")) == 4:
                return f"{date_str.replace('.', '')}-01-01"
            
            return None
        except Exception:
            return None