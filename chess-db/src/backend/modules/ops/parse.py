import chess.pgn
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import io
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass
import logging
from contextlib import contextmanager
from pathlib import Path
import time
from functools import lru_cache
import os
from dotenv import load_dotenv
from config import DatabaseConfig
# Load environment variables
load_dotenv()



@dataclass
class PlayerStats:
    total_games: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    white_games: int = 0
    black_games: int = 0
    avg_elo: float = 0.0
    highest_elo: int = 0
    lowest_elo: int = 0
    last_played: Optional[str] = None

class ChessGameParser:
    def __init__(self, db_config: Optional[DatabaseConfig] = None):
        """Initialize parser with PostgreSQL connection"""
        self.db_config = db_config or DatabaseConfig()
        self._setup_logging()
        self.setup_database()
        
    def _setup_logging(self):
        """Configure logging"""
        self.logger = logging.getLogger('ChessParser')
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    @contextmanager
    def _get_db_connection(self):
        """Context manager for PostgreSQL connections with proper transaction handling"""
        conn = psycopg2.connect(
            host=self.db_config.host,
            port=self.db_config.port,
            database=self.db_config.database,
            user=self.db_config.user,
            password=self.db_config.password
        )
        
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Database error: {str(e)}")
            raise
        finally:
            conn.close()

    def setup_database(self):
        """Create PostgreSQL schema"""
        with self._get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Create tables
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS players (
                        id SERIAL PRIMARY KEY,
                        name TEXT UNIQUE NOT NULL
                    );
                    
                    CREATE TABLE IF NOT EXISTS games (
                        id SERIAL PRIMARY KEY,
                        white_player_id INTEGER NOT NULL REFERENCES players(id),
                        black_player_id INTEGER NOT NULL REFERENCES players(id),
                        event TEXT,
                        site TEXT,
                        date DATE,
                        round TEXT,
                        result TEXT,
                        white_elo INTEGER,
                        black_elo INTEGER,
                        eco TEXT,
                        moves TEXT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        
                        CONSTRAINT fk_white_player
                            FOREIGN KEY (white_player_id)
                            REFERENCES players(id)
                            ON DELETE CASCADE,
                            
                        CONSTRAINT fk_black_player
                            FOREIGN KEY (black_player_id)
                            REFERENCES players(id)
                            ON DELETE CASCADE
                    );
                    
                    -- Indexes
                    CREATE INDEX IF NOT EXISTS idx_players_name ON players(name);
                    CREATE INDEX IF NOT EXISTS idx_games_white_player ON games(white_player_id);
                    CREATE INDEX IF NOT EXISTS idx_games_black_player ON games(black_player_id);
                    CREATE INDEX IF NOT EXISTS idx_games_date ON games(date);
                    CREATE INDEX IF NOT EXISTS idx_games_eco ON games(eco);
                ''')

    @lru_cache(maxsize=1000)
    def _get_player_id(self, player_name: str, cursor) -> int:
        """Get player ID with caching and upsert"""
        cursor.execute('''
            INSERT INTO players (name)
            VALUES (%s)
            ON CONFLICT (name) DO UPDATE
                SET name = EXCLUDED.name
            RETURNING id
        ''', (player_name,))
        return cursor.fetchone()[0]

    def parse_pgn_file(self, pgn_path: Path):
        """Parse PGN file with proper transaction handling"""
        start_time = time.time()
        games_processed = 0
        failed_games = 0
        
        self.logger.info(f"Starting to parse: {pgn_path}")
        
        try:
            with self._get_db_connection() as conn:
                batch = []
                BATCH_SIZE = 1000
                
                with conn.cursor() as cursor:
                    with open(pgn_path) as pgn_file:
                        while True:
                            try:
                                game = chess.pgn.read_game(pgn_file)
                                if game is None:
                                    break
                                
                                try:
                                    # Start a new transaction for each game
                                    cursor.execute("BEGIN")
                                    
                                    headers = game.headers
                                    if not headers:
                                        raise ValueError("Missing game headers")
                                    
                                    # Get player IDs
                                    white_id = self._get_player_id(
                                        headers.get("White", "Unknown"), 
                                        cursor
                                    )
                                    black_id = self._get_player_id(
                                        headers.get("Black", "Unknown"), 
                                        cursor
                                    )
                                    
                                    # Parse moves
                                    board = game.board()
                                    moves = []
                                    for move in game.mainline_moves():
                                        try:
                                            board.push(move)
                                            moves.append(move.uci())
                                        except ValueError:
                                            cursor.execute("ROLLBACK")
                                            raise ValueError(f"Invalid move: {move}")
                                    
                                    moves_str = " ".join(moves)
                                    
                                    # Parse Elo ratings
                                    white_elo = headers.get("WhiteElo", "")
                                    black_elo = headers.get("BlackElo", "")
                                    
                                    white_elo = int(white_elo) if white_elo.isdigit() else None
                                    black_elo = int(black_elo) if black_elo.isdigit() else None
                                    
                                    game_data = (
                                        white_id,
                                        black_id,
                                        headers.get("Event", ""),
                                        headers.get("Site", ""),
                                        self._parse_date(headers.get("Date", "")),
                                        headers.get("Round", ""),
                                        headers.get("Result", ""),
                                        white_elo,
                                        black_elo,
                                        headers.get("ECO", ""),
                                        moves_str
                                    )
                                    
                                    batch.append(game_data)
                                    games_processed += 1
                                    
                                    # Commit the transaction for this game
                                    cursor.execute("COMMIT")
                                    
                                    # Process batch if needed
                                    if len(batch) >= BATCH_SIZE:
                                        try:
                                            cursor.execute("BEGIN")
                                            self._insert_games_batch(cursor, batch)
                                            cursor.execute("COMMIT")
                                            batch = []
                                            
                                            elapsed = time.time() - start_time
                                            rate = games_processed / elapsed
                                            self.logger.info(
                                                f"Processed {games_processed} games "
                                                f"({rate:.2f} games/second)"
                                            )
                                        except Exception as e:
                                            cursor.execute("ROLLBACK")
                                            self.logger.error(f"Batch insert failed: {str(e)}")
                                            failed_games += len(batch)
                                            batch = []
                                    
                                except Exception as e:
                                    cursor.execute("ROLLBACK")
                                    failed_games += 1
                                    self.logger.error(f"Error processing game: {str(e)}")
                                    continue
                                
                            except Exception as e:
                                failed_games += 1
                                self.logger.error(f"Error reading game: {str(e)}")
                                continue
                        
                        # Process remaining games in the batch
                        if batch:
                            try:
                                cursor.execute("BEGIN")
                                self._insert_games_batch(cursor, batch)
                                cursor.execute("COMMIT")
                            except Exception as e:
                                cursor.execute("ROLLBACK")
                                self.logger.error(f"Final batch insert failed: {str(e)}")
                                failed_games += len(batch)
        
        except Exception as e:
            self.logger.error(f"Fatal error processing PGN file: {str(e)}")
            raise
        
        finally:
            # Log final statistics
            elapsed_time = time.time() - start_time
            success_rate = (games_processed - failed_games) / games_processed * 100 if games_processed > 0 else 0
            
            self.logger.info(
                f"PGN parsing completed:\n"
                f"Total games processed: {games_processed}\n"
                f"Successfully parsed: {games_processed - failed_games}\n"
                f"Failed to parse: {failed_games}\n"
                f"Success rate: {success_rate:.1f}%\n"
                f"Total time: {elapsed_time:.2f} seconds\n"
                f"Average speed: {games_processed/elapsed_time:.2f} games/second"
            )
        
        return games_processed - failed_games, failed_games
        
    
    def _insert_games_batch(self, cursor, batch: list):
        """Insert batch of games with error handling"""
        if not batch:
            return
            
        try:
            execute_values(
                cursor,
                '''
                INSERT INTO games (
                    white_player_id, black_player_id, event, site, date,
                    round, result, white_elo, black_elo, eco, moves
                ) VALUES %s
                ''',
                batch,
                template=None,
                page_size=100
            )
        except Exception as e:
            self.logger.error(f"Error inserting batch: {str(e)}")
            raise

    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """Parse PGN date format"""
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
            elif len(date_str.split(".")) == 2:
                year, month = date_str.split(".")
                return f"{year}-{month.zfill(2)}-01"
                
            return None
        except Exception:
            return None

def main():
    # Create scraper instance with PostgreSQL configuration
    parser = ChessGameParser(
        DatabaseConfig(
            host='localhost',
            port=5433,
            database='chess',
            user='postgres',
            password='chesspass'
        )
    )
    
    # Example usage
    pgn_file = Path("example.pgn")
    successful, failed = parser.parse_pgn_file(pgn_file)
    print(f"Successfully parsed {successful} games, {failed} failed")

if __name__ == "__main__":
    main()