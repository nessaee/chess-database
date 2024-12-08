import asyncpg
import asyncio
import csv
from pathlib import Path
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChessOpeningsLoader:
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.conn = None

    async def connect(self):
        """Establish database connection"""
        try:
            self.conn = await asyncpg.connect(**self.db_config)
            logger.info("Successfully connected to database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    async def create_table(self):
        """Create the openings table if it doesn't exist"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS openings (
            eco VARCHAR(3) NOT NULL,
            name VARCHAR(255) NOT NULL,
            pgn TEXT NOT NULL,
            CONSTRAINT pk_openings PRIMARY KEY (eco, name, pgn)
        );
        
        CREATE INDEX IF NOT EXISTS idx_openings_eco ON openings(eco);
        CREATE INDEX IF NOT EXISTS idx_openings_name ON openings(name);
        """
        try:
            await self.conn.execute(create_table_sql)
            logger.info("Table creation successful")
        except Exception as e:
            logger.error(f"Failed to create table: {e}")
            raise

    async def load_tsv_file(self, file_path: Path) -> List[tuple]:
        """Read TSV file and return list of opening records"""
        openings = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter='\t')
                next(reader)  # Skip header row
                for row in reader:
                    if len(row) == 3:
                        openings.append((row[0], row[1], row[2]))
            logger.info(f"Successfully read {len(openings)} records from {file_path}")
            return openings
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            raise

    async def insert_openings(self, openings: List[tuple]):
        """Insert openings into database using batch processing"""
        insert_sql = """
        INSERT INTO openings (eco, name, pgn)
        VALUES ($1, $2, $3)
        ON CONFLICT DO NOTHING
        """
        try:
            # Using a transaction for batch insert
            async with self.conn.transaction():
                await self.conn.executemany(insert_sql, openings)
            logger.info(f"Successfully inserted {len(openings)} records")
        except Exception as e:
            logger.error(f"Failed to insert records: {e}")
            raise

    async def process_files(self, file_paths: List[Path]):
        """Process multiple TSV files"""
        try:
            await self.connect()
            await self.create_table()
            
            for file_path in file_paths:
                openings = await self.load_tsv_file(file_path)
                await self.insert_openings(openings)
                
            logger.info("All files processed successfully")
        finally:
            if self.conn:
                await self.conn.close()
                logger.info("Database connection closed")

async def main():
    # Database configuration
    db_config = {
        'host': 'localhost',
        'port': 5433,
        'database': 'chess',
        'user': 'postgres',
        'password': 'chesspass'
    }

    # File paths
    tsv_files = [
        Path('data/a.tsv'),
        Path('data/b.tsv'),
        Path('data/c.tsv'), 
        Path('data/d.tsv'),
        Path('data/e.tsv')
    ]

    loader = ChessOpeningsLoader(db_config)
    await loader.process_files(tsv_files)

if __name__ == "__main__":
    asyncio.run(main())