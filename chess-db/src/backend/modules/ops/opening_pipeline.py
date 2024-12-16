import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import chess.pgn
import io
import asyncpg
import uuid, json
from datetime import datetime
from backend.utils.encode import ChessGameEncoder
import aiofiles

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
        self.encoder = ChessGameEncoder()
        self.pool = None
        self.batch_id = str(uuid.uuid4())
        self.stats = {
            'processed': 0,
            'failed': 0,
            'invalid_moves': 0,
            'db_errors': 0
        }

    
    async def initialize_database(self):
        """Initialize database connection and create necessary tables."""
        try:
            self.pool = await asyncpg.create_pool(
                self.db_config.get_dsn(),
                min_size=3,
                max_size=10,
                command_timeout=60
            )
            
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS openings (
                        id SERIAL PRIMARY KEY,
                        name TEXT NOT NULL,
                        moves BYTEA NOT NULL,
                        CONSTRAINT unique_opening_pattern UNIQUE (name, moves)
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_openings_name ON openings(name);
                ''')
            
            self.logger.info("Database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {str(e)}")
            raise

    async def process_batch(self, lines: List[str]):
        """Process a batch of opening lines for storage."""
        if not lines:
            return
            
        processed_openings = []
        for line in lines:
            try:
                parsed = self.parse_opening_line(line)
                if not parsed:
                    self.stats['invalid_moves'] += 1
                    continue
                    
                eco, name, moves = parsed
                uci_moves = self.convert_to_uci(moves)
                
                if not uci_moves:
                    self.stats['invalid_moves'] += 1
                    continue
                
                game_metadata = ChessGameMetadata(
                    white_player_id=0,
                    black_player_id=0,
                    white_elo=0,
                    black_elo=0,
                    date=None,
                    result='*',
                    eco=eco,
                    moves=uci_moves
                )
                
                moves = self.encoder.encode_game(game_metadata)
                processed_openings.append((name, moves))
                self.stats['processed'] += 1
                
            except Exception as e:
                self.stats['failed'] += 1
                self.logger.error(f"Error processing line: {str(e)}")
                continue
        
        if processed_openings:
            await self.store_batch(processed_openings)

    async def store_batch(self, openings: List[Tuple]):
        """Store a batch of processed openings in the database."""
        if not openings:
            return
            
        async with self.pool.acquire() as conn:
            try:
                async with conn.transaction():
                    await conn.executemany('''
                        INSERT INTO openings (name, moves)
                        VALUES ($1, $2)
                        ON CONFLICT (name, moves) DO NOTHING
                    ''', openings)
                    
            except Exception as e:
                self.stats['db_errors'] += 1
                self.logger.error(f"Database error: {str(e)}")
                raise
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("OpeningProcessor")
        logger.setLevel(logging.INFO)
        
        console_handler = logging.StreamHandler()
        console_format = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)
        return logger
    
    def parse_opening_line(self, line: str) -> Optional[Tuple[str, str, str]]:
        """
        Parse a single line from the TSV file containing chess openings.
        Validates the ECO code, name, and move sequence.
        """
        try:
            parts = line.strip().split('\t')
            if len(parts) != 3:
                raise ValueError(f"Invalid line format: expected 3 parts, got {len(parts)}")
            
            eco, name, moves = parts
            
            # Validate ECO code
            if not eco or not eco.isalnum() or len(eco) != 3:
                raise ValueError(f"Invalid ECO code: {eco}")
            
            # Validate name
            if not name or len(name.strip()) == 0:
                raise ValueError("Empty opening name")
            
            # Validate moves
            if not moves or not any(c.isalpha() for c in moves):
                raise ValueError("Invalid move sequence")
            
            return eco, name.strip(), moves.strip()
            
        except Exception as e:
            self.logger.warning(
                f"Error parsing line: {str(e)}\n"
                f"Original line: {line}"
            )
            return None

    def convert_to_uci(self, moves_text: str) -> str:
        """
        Convert traditional chess notation to UCI format.
        Handles standard chess notation with move numbers (e.g., '1. e4 e5 2. Nf3 Nc6').
        """
        try:
            # Clean up the move text
            cleaned_text = moves_text.strip()
            
            # Remove move numbers and their dots more carefully
            move_parts = []
            for part in cleaned_text.split():
                # Skip the move numbers (parts ending with '.')
                if part.endswith('.'):
                    continue
                # Add the actual move
                move_parts.append(part)
            
            # Join moves back together
            moves_only = ' '.join(move_parts)
            
            # Set up a new game and board
            board = chess.Board()
            uci_moves = []
            
            # Process each move
            for move_san in moves_only.split():
                if move_san.strip():
                    try:
                        move = board.parse_san(move_san)
                        uci_moves.append(move.uci())
                        board.push(move)
                    except ValueError as e:
                        self.logger.warning(
                            f"Invalid move {move_san} in sequence {moves_text}\n"
                            f"Error: {str(e)}"
                        )
                        break
            
            if not uci_moves:
                return ""
                
            return ' '.join(uci_moves)
            
        except Exception as e:
            self.logger.error(
                f"Move conversion error: {str(e)}\n"
                f"Original sequence: {moves_text}"
            )
            return ""
    
    async def process_file(self, file_path: Path) -> bool:
        """Process a single TSV file containing chess openings."""
        try:
            self.logger.info(f"Processing file: {file_path}")
            
            async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
                content = await f.read()
            
            lines = content.strip().split('\n')
            if not lines:
                self.logger.warning(f"Empty file: {file_path}")
                return False
                
            # Skip header if present
            if lines[0].lower().startswith('eco') or '\t' not in lines[0]:
                lines = lines[1:]
            
            batch_size = 100
            for i in range(0, len(lines), batch_size):
                batch = lines[i:i + batch_size]
                await self.process_batch(batch)
                
                # Log progress
                total_processed = self.stats['processed'] + self.stats['failed']
                if total_processed > 0:
                    success_rate = (self.stats['processed'] / total_processed) * 100
                    self.logger.info(
                        f"Progress: {i + len(batch)}/{len(lines)} lines processed. "
                        f"Success rate: {success_rate:.2f}%"
                    )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {str(e)}")
            return False


    async def cleanup(self):
        """Cleanup resources and log final statistics."""
        if self.pool:
            await self.pool.close()
        
        self.logger.info(
            f"\nProcessing completed:"
            f"\n- Processed successfully: {self.stats['processed']}"
            f"\n- Invalid moves: {self.stats['invalid_moves']}"
            f"\n- Processing failures: {self.stats['failed']}"
            f"\n- Database errors: {self.stats['db_errors']}"
        )

async def main():
    # Create proper DatabaseConfig object instead of dictionary
    db_config = DatabaseConfig(
        host="localhost",
        port=5433,
        database="chess",
        user="postgres",
        password="chesspass"
    )
    
    # Initialize processor
    processor = OpeningProcessor(db_config)
    
    try:
        # Initialize database
        await processor.initialize_database()
        
        # Process each TSV file
        data_dir = Path("data")
        tsv_files = list(data_dir.glob("*.tsv"))
        
        if not tsv_files:
            processor.logger.error("No TSV files found in the data directory")
            return
        
        for file_path in tsv_files:
            success = await processor.process_file(file_path)
            if not success:
                processor.logger.warning(f"Failed to process {file_path}")
                
    except Exception as e:
        processor.logger.error(f"Fatal error: {str(e)}")
        raise
        
    finally:
        await processor.cleanup()

if __name__ == "__main__":
    asyncio.run(main())