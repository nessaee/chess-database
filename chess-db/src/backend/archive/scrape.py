import requests
from bs4 import BeautifulSoup
import os
import wget
import zipfile
import tempfile
from tqdm import tqdm
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import hashlib
import json
from pathlib import Path
import time
import sys
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from parse import ChessProcessor
import chess
from config import DatabaseConfig
from contextlib import contextmanager


@dataclass
class PGNFile:
    url: str
    filename: str
    description: str
    file_size: Optional[int] = None
    hash: Optional[str] = None
    downloaded_at: Optional[str] = None
    processed_at: Optional[str] = None
    status: str = "pending"

class PGNScraper:
    def __init__(self, db_config: Optional[DatabaseConfig] = None, download_dir: Optional[str] = None):
        """
        Initialize enhanced scraper with improved logging and caching
        
        Args:
            db_config: PostgreSQL database configuration
            download_dir: Optional directory for downloads (uses temp dir if not specified)
        """
        self.db_config = db_config or DatabaseConfig()
        self.base_url = "https://www.pgnmentor.com"
        self.download_dir = Path(download_dir) if download_dir else Path(tempfile.mkdtemp())
        self.cache_dir = self.download_dir / ".cache"
        self.metadata_file = self.cache_dir / "metadata.json"
        
        # Initialize directories
        self._init_directories()
        
        # Set up logging
        self._setup_logging()
        
        # Initialize HTTP session
        self.session = self._setup_http_session()
        
        # Initialize parser with database configuration
        self.parser = ChessProcessor(db_config=self.db_config)
        
        # Load metadata
        self.metadata = self._load_metadata()

    @contextmanager
    def _get_db_connection(self):
        """Delegate database connection to parser"""
        with self.parser._get_db_connection() as conn:
            yield conn

    def parse_pgn_file(self, pgn_path: Path):
        """Delegate PGN parsing to parser"""
        return self.parser.parse_pgn_file(pgn_path)

    def process_file(self, pgn_file: PGNFile) -> bool:
        """Process a single PGN file with comprehensive error handling"""
        try:
            self.logger.info(f"Processing: {pgn_file.description} ({pgn_file.filename})")
            
            # Download file
            filepath = self.download_file(pgn_file)
            if not filepath:
                pgn_file.status = "failed"
                return False
            
            # Extract if it's a ZIP file
            if pgn_file.filename.endswith('.zip'):
                pgn_files = self.extract_zip(filepath)
                if not pgn_files:
                    pgn_file.status = "failed"
                    return False
                
                # Process each PGN file
                success = True
                for pgn_path in pgn_files:
                    try:
                        games_processed, failed = self.parser.parse_pgn_file(pgn_path)
                        if games_processed == 0:
                            success = False
                        self.logger.info(
                            f"Parsed {games_processed} games from {pgn_path.name} "
                            f"(Failed: {failed})"
                        )
                    except Exception as e:
                        self.logger.error(f"Error parsing {pgn_path.name}: {str(e)}")
                        success = False
                
                pgn_file.status = "completed" if success else "partial"
            else:
                # Process single PGN file
                try:
                    games_processed, failed = self.parser.parse_pgn_file(filepath)
                    pgn_file.status = "completed" if games_processed > 0 else "failed"
                except Exception as e:
                    self.logger.error(f"Error parsing {filepath.name}: {str(e)}")
                    pgn_file.status = "failed"
                    return False
            
            # Update metadata
            pgn_file.processed_at = datetime.now().isoformat()
            self._save_metadata()
            
            return pgn_file.status == "completed"
            
        except Exception as e:
            self.logger.error(f"Error processing {pgn_file.filename}: {str(e)}")
            pgn_file.status = "failed"
            self._save_metadata()
            return False
              
    def _init_directories(self):
        """Initialize necessary directories"""
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def _setup_logging(self):
        """Set up enhanced logging configuration"""
        log_file = self.download_dir / "pgn_scraper.log"
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler with rotation
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        # Configure root logger
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        self.logger = logging.getLogger("PGNScraper")
    
    def _setup_http_session(self) -> requests.Session:
        """Configure HTTP session with retry strategy"""
        session = requests.Session()
        
        # Configure retry strategy
        retries = Retry(
            total=5,
            backoff_factor=0.1,
            status_forcelist=[500, 502, 503, 504]
        )
        
        # Mount adapter with retry strategy
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _load_metadata(self) -> Dict[str, PGNFile]:
        """Load cached metadata"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                data = json.load(f)
                return {
                    url: PGNFile(**file_data)
                    for url, file_data in data.items()
                }
        return {}
    
    def _save_metadata(self):
        """Save metadata to cache"""
        with open(self.metadata_file, 'w') as f:
            json.dump(
                {url: vars(file_info) for url, file_info in self.metadata.items()},
                f,
                indent=2
            )
    
    def _calculate_file_hash(self, filepath: Path) -> str:
        """Calculate SHA-256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def get_pgn_links(self) -> List[PGNFile]:
        """Scrape PGN file links with enhanced error handling"""
        self.logger.info("Fetching PGN links from website")
        
        try:
            response = self.session.get(f"{self.base_url}/files.html")
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            links = []
            
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.endswith(('.zip', '.pgn')):
                    url = f"{self.base_url}/{href}"
                    
                    # Check if we have cached metadata
                    if url in self.metadata:
                        pgn_file = self.metadata[url]
                    else:
                        pgn_file = PGNFile(
                            url=url,
                            filename=os.path.basename(href),
                            description=a.get_text(strip=True)
                        )
                        self.metadata[url] = pgn_file
                    
                    links.append(pgn_file)
            
            self.logger.info(f"Found {len(links)} PGN files")
            self._save_metadata()
            return links
            
        except requests.RequestException as e:
            self.logger.error(f"Error fetching PGN links: {str(e)}")
            return []
    
    def download_file(self, pgn_file: PGNFile) -> Optional[Path]:
        """Download file with enhanced progress tracking and validation"""
        filepath = self.download_dir / pgn_file.filename
        
        try:
            # Check if file exists and is valid
            if filepath.exists():
                current_hash = self._calculate_file_hash(filepath)
                if pgn_file.hash and current_hash == pgn_file.hash:
                    self.logger.info(f"File already exists and is valid: {pgn_file.filename}")
                    return filepath
            
            # Download with progress tracking
            self.logger.info(f"Downloading: {pgn_file.filename}")
            response = self.session.get(pgn_file.url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(filepath, 'wb') as f, tqdm(
                desc=pgn_file.filename,
                total=total_size,
                unit='iB',
                unit_scale=True
            ) as pbar:
                for data in response.iter_content(chunk_size=1024):
                    size = f.write(data)
                    pbar.update(size)
            
            # Update metadata
            pgn_file.file_size = total_size
            pgn_file.hash = self._calculate_file_hash(filepath)
            pgn_file.downloaded_at = datetime.now().isoformat()
            self._save_metadata()
            
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error downloading {pgn_file.filename}: {str(e)}")
            if filepath.exists():
                filepath.unlink()
            return None
    
    
    def extract_zip(self, zip_path: Path) -> List[Path]:
        """Extract ZIP file with improved error handling"""
        try:
            extract_dir = self.download_dir / 'extracted'
            extract_dir.mkdir(exist_ok=True)
            
            self.logger.info(f"Extracting: {zip_path.name}")
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Return list of extracted PGN files
            pgn_files = list(extract_dir.glob('**/*.pgn'))
            self.logger.info(f"Extracted {len(pgn_files)} PGN files from {zip_path.name}")
            
            return pgn_files
            
        except Exception as e:
            self.logger.error(f"Error extracting {zip_path.name}: {str(e)}")
            return []
    
    def parse_pgn_file(self, pgn_path: Path):
        """
        Parse PGN file and store games in database with optimized batch processing.
        
        Args:
            pgn_path: Path to PGN file to parse
            
        Returns:
            Tuple[int, int]: (successfully_parsed_games, failed_games)
        """
        start_time = time.time()
        games_processed = 0
        failed_games = 0
        batch = []
        BATCH_SIZE = 1000  # Adjust based on memory constraints
        
        self.logger.info(f"Starting to parse: {pgn_path}")
        
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                with open(pgn_path) as pgn_file:
                    while True:
                        try:
                            # Read game from PGN file
                            game = chess.pgn.read_game(pgn_file)
                            if game is None:  # End of file
                                break
                            
                            # Extract game metadata
                            headers = game.headers
                            
                            # Get player IDs (cached operation)
                            white_id = self._get_player_id(
                                headers.get("White", "Unknown"), 
                                cursor
                            )
                            black_id = self._get_player_id(
                                headers.get("Black", "Unknown"), 
                                cursor
                            )
                            
                            # Convert moves to algebraic notation
                            moves_str = " ".join(
                                move.uci() for move in game.mainline_moves()
                            )
                            
                            # Parse Elo ratings
                            white_elo = headers.get("WhiteElo", "")
                            black_elo = headers.get("BlackElo", "")
                            
                            # Clean Elo values
                            white_elo = int(white_elo) if white_elo.isdigit() else None
                            black_elo = int(black_elo) if black_elo.isdigit() else None
                            
                            # Prepare game data tuple
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
                            
                            # Process batch when it reaches the size limit
                            if len(batch) >= BATCH_SIZE:
                                self._insert_games_batch(cursor, batch)
                                batch = []  # Clear batch after insertion
                                
                                # Log progress
                                elapsed = time.time() - start_time
                                rate = games_processed / elapsed
                                self.logger.info(
                                    f"Processed {games_processed} games "
                                    f"({rate:.2f} games/second)"
                                )
                                
                        except chess.pgn.SkipGame:
                            # Skip invalid games
                            failed_games += 1
                            self.logger.warning(
                                f"Skipped invalid game at position {games_processed + failed_games}"
                            )
                            continue
                            
                        except Exception as e:
                            # Log other errors but continue processing
                            failed_games += 1
                            self.logger.error(
                                f"Error processing game at position "
                                f"{games_processed + failed_games}: {str(e)}"
                            )
                            continue
                    
                    # Process remaining games in the last batch
                    if batch:
                        try:
                            self._insert_games_batch(cursor, batch)
                        except Exception as e:
                            self.logger.error(f"Error inserting final batch: {str(e)}")
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

    def cleanup(self):
        """Clean up downloaded and extracted files"""
        try:
            # Save final metadata state
            self._save_metadata()
            
            # Remove downloaded files
            for file in self.download_dir.glob('*'):
                if file.is_file() and file != self.metadata_file:
                    file.unlink()
            
            # Remove extracted directory
            extract_dir = self.download_dir / 'extracted'
            if extract_dir.exists():
                for item in extract_dir.rglob('*'):
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        item.rmdir()
                extract_dir.rmdir()
            
            self.logger.info("Cleanup completed successfully")
        
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")

    def run(self, max_workers: int = 4):
        """Main execution method with enhanced parallel processing"""
        start_time = time.time()
        self.logger.info("Starting PGN scraping process")
        
        try:
            # Get all PGN links
            links = self.get_pgn_links()
            if not links:
                self.logger.error("No PGN links found")
                return
            
            # Process files in parallel
            successful = 0
            failed = 0
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_file = {
                    executor.submit(self.process_file, link): link 
                    for link in links
                }
                
                # Show progress bar
                with tqdm(total=len(links), desc="Processing files") as pbar:
                    for future in as_completed(future_to_file):
                        pgn_file = future_to_file[future]
                        try:
                            if future.result():
                                successful += 1
                            else:
                                failed += 1
                        except Exception as e:
                            self.logger.error(f"Error processing {pgn_file.filename}: {str(e)}")
                            failed += 1
                        pbar.update(1)
            
            # Log final results
            elapsed_time = time.time() - start_time
            self.logger.info(
                f"Processing completed in {elapsed_time:.2f} seconds. "
                f"Successful: {successful}, Failed: {failed}"
            )
            
        except Exception as e:
            self.logger.error(f"Error in main scraper execution: {str(e)}")
        finally:
            self._save_metadata()

from typing import Optional, Dict, List
import argparse
import sys
import tempfile
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from pathlib import Path

def setup_logging(log_file: str = 'pgn_scraper.log') -> logging.Logger:
    """Configure logging with both file and console handlers"""
    logger = logging.getLogger('PGNScraper')
    logger.setLevel(logging.INFO)
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    )
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        logging.Formatter('%(levelname)s - %(message)s')
    )
    logger.addHandler(console_handler)
    
    return logger

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='PGN Scraper and Parser')
    parser.add_argument(
        '--db-config',
        type=str,
        default='postgresql://postgres:chesspass@localhost:5433/chess',
        help='Database connection string'
    )
    parser.add_argument(
        '--download-dir',
        type=str,
        default=None,
        help='Directory for downloading PGN files'
    )
    parser.add_argument(
        '--max-workers',
        type=int,
        default=4,
        help='Maximum number of parallel workers'
    )
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Clean up downloaded files after processing'
    )
    
    return parser.parse_args()

def main():
    """Main execution function with parallel processing and progress tracking"""
    # Parse arguments
    args = parse_arguments()
    
    # Setup logging
    logger = setup_logging()
    
    try:
        # Initialize download directory
        download_dir = args.download_dir or tempfile.mkdtemp()
        Path(download_dir).mkdir(parents=True, exist_ok=True)
        
        # Create database configuration
        db_config = DatabaseConfig(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5433)),
            database=os.getenv('DB_NAME', 'chess'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'chesspass')
        )
        
        # Create scraper instance
        scraper = PGNScraper(
            db_config=db_config,
            download_dir=download_dir
        )
        
        # Get PGN links
        logger.info("Fetching PGN links...")
        links = scraper.get_pgn_links()
        
        if not links:
            logger.error("No PGN files found to process")
            return
        
        logger.info(f"Found {len(links)} PGN files to process")
        
        # Process files in parallel
        successful = 0
        failed = 0
        
        with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
            future_to_link = {
                executor.submit(scraper.process_file, link): link 
                for link in links
            }
            
            with tqdm(total=len(links), desc="Processing files") as pbar:
                for future in as_completed(future_to_link):
                    link = future_to_link[future]
                    try:
                        if future.result():
                            successful += 1
                            logger.info(f"Successfully processed: {link.filename}")
                        else:
                            failed += 1
                            logger.error(f"Failed to process: {link.filename}")
                    except Exception as e:
                        failed += 1
                        logger.error(f"Error processing {link.filename}: {str(e)}")
                    finally:
                        pbar.update(1)
        
        # Log final results
        logger.info(
            f"\nProcessing completed:\n"
            f"Total files: {len(links)}\n"
            f"Successfully processed: {successful}\n"
            f"Failed: {failed}\n"
            f"Success rate: {(successful/len(links)*100):.1f}%"
        )
        
        # Cleanup if requested
        if args.cleanup:
            logger.info("Cleaning up downloaded files...")
            scraper.cleanup()
            logger.info("Cleanup completed")
    
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)
    finally:
        if args.cleanup and 'scraper' in locals():
            try:
                scraper.cleanup()
            except Exception as e:
                logger.error(f"Error during final cleanup: {str(e)}")

if __name__ == "__main__":
    main()