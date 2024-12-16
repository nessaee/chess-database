import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import chess.pgn
import io
import asyncpg
import uuid
from datetime import datetime
import aiofiles
from utils.encode import ChessMoveEncoder

@dataclass
class ChessGameMetadata:
    white_player_id: int
    black_player_id: int
    white_elo: int
    black_elo: int
    date: Optional[datetime]
    result: str
    eco: str
    moves: str

@dataclass
class DatabaseConfig:
    host: str
    port: int
    database: str
    user: str
    password: str

    def get_dsn(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class OpeningProcessor:
    def __init__(self, db_config: DatabaseConfig):
        self.db_config = db_config
        self.logger = self._setup_logger()
        self.encoder = ChessMoveEncoder()
        self.pool = None
        self.stats = {
            'processed': 0,
            'failed': 0,
            'invalid_moves': 0,
            'db_errors': 0
        }

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('OpeningProcessor')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        return logger

    async def initialize(self):
        self.pool = await asyncpg.create_pool(
            dsn=self.db_config.get_dsn(),
            min_size=1,
            max_size=10
        )
        
        # Create openings table if it doesn't exist
        async with self.pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS openings (
                    id SERIAL PRIMARY KEY,
                    eco VARCHAR(3) NOT NULL,
                    name TEXT NOT NULL,
                    moves BYTEA NOT NULL
                );
                
                CREATE INDEX IF NOT EXISTS idx_openings_eco ON openings(eco);
            ''')

    async def close(self):
        if self.pool:
            await self.pool.close()

    def _parse_moves(self, pgn_str: str) -> List[str]:
        """Parse PGN moves into a list of UCI moves"""
        try:
            # Create a complete PGN string
            complete_pgn = f"[Event \"Opening Database\"]\n[Site \"?\"]\n[Date \"????.??.??\"]\n[Round \"1\"]\n[White \"?\"]\n[Black \"?\"]\n[Result \"*\"]\n\n{pgn_str} *\n"
            game = chess.pgn.read_game(io.StringIO(complete_pgn))
            if not game:
                return []
            
            board = game.board()
            moves = []
            for move in game.mainline_moves():
                moves.append(move.uci())
                board.push(move)
            return moves
        except Exception as e:
            self.logger.error(f"Error parsing moves: {e}")
            return []

    async def process_opening(self, eco: str, name: str, pgn: str) -> Optional[bytes]:
        """Process a single opening, returning encoded moves"""
        try:
            moves = self._parse_moves(pgn)
            if not moves:
                self.stats['invalid_moves'] += 1
                return None
            
            # Encode moves using the ChessMoveEncoder
            encoded = self.encoder.encode_moves(moves)
            if encoded is None:
                self.stats['invalid_moves'] += 1
                return None
                
            return encoded  # Return bytes directly since encode_moves returns bytes
            
        except Exception as e:
            self.logger.error(f"Error processing opening {eco} - {name}: {e}")
            self.stats['failed'] += 1
            return None

    async def store_openings_batch(self, openings: List[Tuple[str, str, str]]):
        """Store a batch of openings in the database"""
        if not openings:
            return

        try:
            async with self.pool.acquire() as conn:
                # Process and encode moves for each opening
                values = []
                for eco, name, pgn in openings:
                    encoded_moves = await self.process_opening(eco, name, pgn)
                    if encoded_moves:
                        values.append((
                            eco,
                            name,
                            encoded_moves
                        ))
                        self.stats['processed'] += 1

                if values:
                    # Insert all processed openings in a single transaction
                    async with conn.transaction():
                        await conn.executemany('''
                            INSERT INTO openings (eco, name, moves)
                            VALUES ($1, $2, $3)
                        ''', values)

        except Exception as e:
            self.logger.error(f"Database error: {e}")
            self.stats['db_errors'] += 1

    async def process_tsv_file(self, file_path: Path, batch_size: int = 100):
        """Process a TSV file containing chess openings"""
        try:
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()

            # Split into lines and skip header
            lines = content.strip().split('\n')
            if not lines:
                return
                
            # Skip header if it exists
            if lines[0].startswith('eco\t'):
                lines = lines[1:]

            # Process in batches
            batch = []
            for line in lines:
                try:
                    eco, name, pgn = line.strip().split('\t')
                    batch.append((eco, name, pgn))
                    
                    if len(batch) >= batch_size:
                        await self.store_openings_batch(batch)
                        batch = []
                        
                except Exception as e:
                    self.logger.error(f"Error parsing line: {e}")
                    continue

            # Process remaining openings
            if batch:
                await self.store_openings_batch(batch)

        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {e}")
            self.stats['failed'] += 1

    async def process_directory(self, directory: Path):
        """Process all TSV files in a directory"""
        try:
            files = list(directory.glob('*.tsv'))
            self.logger.info(f"Found {len(files)} files to process")

            for file_path in files:
                self.logger.info(f"Processing {file_path}")
                await self.process_tsv_file(file_path)
                
            self.logger.info("Processing complete")
            self.logger.info(f"Stats: {self.stats}")
            
        except Exception as e:
            self.logger.error(f"Error processing directory {directory}: {e}")

async def main():
    # Create proper DatabaseConfig object instead of dictionary
    db_config = DatabaseConfig(
        host="localhost",
        port=5433,
        database="chess",
        user="postgres",
        password="chesspass"
    )
    
    processor = OpeningProcessor(db_config)
    
    try:
        # Initialize database
        await processor.initialize()
        
        # Process each TSV file
        data_dir = Path("modules/ops/data")
        await processor.process_directory(data_dir)
        
    except Exception as e:
        processor.logger.error(f"Fatal error: {e}")
        raise
        
    finally:
        await processor.close()

if __name__ == "__main__":
    asyncio.run(main())