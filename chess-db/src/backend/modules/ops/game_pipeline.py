import asyncio
import aiohttp
import asyncpg
import chess.pgn
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
import logging
import re
import tempfile
import io
from bs4 import BeautifulSoup
import zipfile
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp
from tqdm.asyncio import tqdm
import time
import aiofiles, os
from urllib.parse import urljoin

class TemporaryDirectory:
    def __init__(self, prefix=None):
        self.prefix = prefix
        self.path = None

    async def __aenter__(self):
        self.path = Path(tempfile.mkdtemp(prefix=self.prefix))
        return self.path

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.path and self.path.exists():
            for dirpath, _, filenames in os.walk(self.path, topdown=False):
                for filename in filenames:
                    try:
                        os.remove(os.path.join(dirpath, filename))
                    except:
                        pass
                try:
                    os.rmdir(dirpath)
                except:
                    pass

@dataclass
class DatabaseConfig:
    host: str
    port: int
    database: str
    user: str
    password: str

    def get_dsn(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

@dataclass
class ProcessingConfig:
    max_open_files: int = 5
    db_batch_size: int = 1000
    parsing_chunk_size: int = 50_000
    download_concurrency: int = 1
    process_pool_size: Optional[int] = None
    progress_update_interval: float = 0.5

    def __post_init__(self):
        if self.process_pool_size is None:
            self.process_pool_size = max(1, mp.cpu_count() - 1)

def parse_pgn_chunk(chunk: str) -> List[Dict]:
    games = []
    pgn = io.StringIO(chunk)
    while True:
        try:
            game = chess.pgn.read_game(pgn)
            if game is None:
                break
            headers = game.headers
            moves = [move.uci() for move in game.mainline_moves()]
            games.append({
                'white': headers.get('White', 'Unknown'),
                'black': headers.get('Black', 'Unknown'),
                'white_elo': int(headers.get("WhiteElo", "")),
                'black_elo': int(headers.get("BlackElo", "")),
                'date': headers.get('Date', ''),
                'result': headers.get('Result', '*'),
                'eco': headers.get('ECO', ''),
                'moves': ' '.join(moves)
            })
        except:
            continue
    return games

class PipelineMetrics:
    def __init__(self):
        self.start_time = time.time()
        self.files_processed = 0
        self.files_failed = 0
        self.games_processed = 0
        self.games_failed = 0
        self.db_operations = 0
        self.db_retries = 0
        self.processing_times = []
        self.current_rate = 0

    def log_metrics(self, logger):
        elapsed = time.time() - self.start_time
        avg_speed = self.games_processed / elapsed if elapsed > 0 else 0
        avg_time = sum(self.processing_times) / max(len(self.processing_times), 1)
        success_rate = (self.games_processed / (self.games_processed + self.games_failed) * 100) if (self.games_processed + self.games_failed) > 0 else 0
        logger.info(
            f"\nPipeline Metrics:"
            f"\n----------------"
            f"\nElapsed Time: {elapsed:.2f} seconds"
            f"\nFiles Processed: {self.files_processed}"
            f"\nFiles Failed: {self.files_failed}"
            f"\nGames Processed: {self.games_processed}"
            f"\nGames Failed: {self.games_failed}"
            f"\nDatabase Operations: {self.db_operations}"
            f"\nDatabase Retries: {self.db_retries}"
            f"\nAverage Processing Speed: {avg_speed:.2f} games/second"
            f"\nCurrent Processing Rate: {self.current_rate:.2f} games/second"
            f"\nAverage File Processing Time: {avg_time:.2f} seconds"
            f"\nSuccess Rate: {success_rate:.2f}%"
        )

class ChessDataPipeline:
    def __init__(self, db_config: DatabaseConfig, processing_config: ProcessingConfig):
        self.db_config = db_config
        self.config = processing_config
        self.db_pool = None
        self.process_pool = ProcessPoolExecutor(max_workers=self.config.process_pool_size)
        self.download_dir = Path(tempfile.mkdtemp())
        self.base_url = "https://www.pgnmentor.com"
        self.logger = self._setup_logger()
        self.metrics = PipelineMetrics()

        self.file_semaphore = asyncio.Semaphore(self.config.max_open_files)
        self.file_lock = asyncio.Lock()
        self.download_sem = asyncio.Semaphore(self.config.download_concurrency)
        self.http_session = None

        self.processed_files = set()

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("ChessPipeline")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def log_metrics(self):
        self.metrics.log_metrics(self.logger)

    async def initialize(self):
        self.db_pool = await asyncpg.create_pool(
            self.db_config.get_dsn(),
            min_size=3,
            max_size=10,
            command_timeout=60
        )
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS players (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    CONSTRAINT unique_player_name UNIQUE (name)
                );
                CREATE TABLE IF NOT EXISTS games (
                    id SERIAL PRIMARY KEY,
                    white_player_id INTEGER REFERENCES players(id),
                    black_player_id INTEGER REFERENCES players(id),
                    white_elo INTEGER,
                    black_elo INTEGER,
                    date DATE,
                    result VARCHAR(10),
                    eco VARCHAR(10),
                    moves TEXT,
                    CONSTRAINT valid_result CHECK (result IN ('1-0', '0-1', '1/2-1/2', '*')),
                    CONSTRAINT unique_game UNIQUE (white_player_id, black_player_id, date, moves)
                );
                CREATE INDEX IF NOT EXISTS idx_players_name ON players(name);
                CREATE INDEX IF NOT EXISTS idx_games_players ON games(white_player_id, black_player_id);
            ''')

    async def get_pgn_links(
        self,
        start_id: Optional[int] = None,
        end_id: Optional[int] = None
    ) -> List[Dict]:
        """
        A more robust link collection method that takes advantage of the structure on pgnmentor.com:
        - Specifically targets the player section and associated `.zip` download links.
        - Filters links based on their file extensions and known directory structure.
        - Uses CSS selectors for more precise targeting.
        """

        target_url = urljoin(self.base_url, "files.html")
        async with self.http_session.get(target_url) as response:
            if response.status != 200:
                raise Exception(f"Failed to fetch PGN links: {response.status}")

            content = await response.text()
            soup = BeautifulSoup(content, 'html.parser')

            # The players section is identified by an anchor with id="players"
            # Player files are listed under tables after this anchor.
            # We'll select all 'a' tags that point to a .zip or .pgn file inside the "players" directory.
            link_candidates = soup.select('a[href^="players/"]')
            
            # Extract and filter valid links
            valid_extensions = ('.zip', '.pgn')
            all_links = []
            for a in link_candidates:
                href = a.get('href', '').strip()
                if href.lower().endswith(valid_extensions):
                    full_url = urljoin(self.base_url, href)
                    all_links.append(full_url)

            # Ensure links are unique and sorted for consistent indexing
            unique_links = sorted(set(all_links))

            # Slice based on optional start_id, end_id
            selected_links = []
            for idx, link in enumerate(unique_links):
                if (start_id is None or idx >= start_id) and (end_id is None or idx <= end_id):
                    selected_links.append({
                        'url': link,
                        'filename': Path(link).name,
                        'id': idx
                    })

            self.logger.info(f"Found {len(selected_links)} PGN files in selected range")
            return selected_links


    async def download_file(self, url: str, filename: str, pbar: tqdm) -> Optional[Path]:
        filepath = self.download_dir / filename
        async with self.download_sem:
            try:
                async with self.http_session.get(url) as response:
                    if response.status != 200:
                        raise Exception(f"Download failed with status: {response.status}")
                    total_size = int(response.headers.get('content-length', 0))
                    if total_size == 0:
                        raise Exception("Content length is zero")
                    pbar.total = total_size
                    downloaded_size = 0
                    async with aiofiles.open(filepath, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            if chunk:
                                await f.write(chunk)
                                downloaded_size += len(chunk)
                                pbar.update(len(chunk))
                    if downloaded_size != total_size:
                        raise Exception(f"Incomplete download: {downloaded_size}/{total_size}")
                    if not filepath.exists() or filepath.stat().st_size != total_size:
                        raise Exception("File size verification failed")
                    return filepath
            except Exception as e:
                self.logger.error(f"Download error for {filename}: {str(e)}")
                if filepath.exists():
                    try:
                        os.remove(filepath)
                    except:
                        pass
                return None

    async def extract_zip(self, zip_path: Path) -> List[Path]:
        if not zip_path.exists():
            self.logger.error(f"ZIP file not found: {zip_path}")
            return []
        extract_dir = self.download_dir / 'extracted'
        extract_dir.mkdir(exist_ok=True)
        def _extract():
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            return list(extract_dir.glob('**/*.pgn'))
        loop = asyncio.get_event_loop()
        try:
            pgn_files = await loop.run_in_executor(None, _extract)
            pgn_files = [p for p in pgn_files if p.exists()]    
            return pgn_files
        except Exception as e:
            self.logger.error(f"Error extracting {zip_path}: {str(e)}")
            return []
        finally:
            if zip_path.exists():
                try:
                    os.remove(zip_path)
                except Exception as e:
                    self.logger.error(f"Error removing zip file {zip_path}: {str(e)}")

    async def store_games_batch(self, games: List[Dict], games_pbar: Optional[tqdm] = None):
        if not games:
            return
        batch_start = time.time()
        max_retries = 5
        base_delay = 0.1
        async with self.db_pool.acquire() as conn:
            unique_players = sorted({g['white'] for g in games} | {g['black'] for g in games})
            player_ids = {}
            for player_name in unique_players:
                for attempt in range(max_retries):
                    try:
                        self.metrics.db_operations += 1
                        player_id = await conn.fetchval('''
                            INSERT INTO players (name)
                            VALUES ($1)
                            ON CONFLICT (name) DO UPDATE 
                            SET name = EXCLUDED.name
                            RETURNING id
                        ''', player_name)
                        player_ids[player_name] = player_id
                        break
                    except Exception as e:
                        self.metrics.db_retries += 1
                        if attempt == max_retries - 1:
                            self.logger.error(f"Failed to process player {player_name}: {str(e)}")
                            raise
                        await asyncio.sleep(base_delay * (2 ** attempt))

            sub_batch_size = 50
            successful_games = 0
            for i in range(0, len(games), sub_batch_size):
                sub_batch = games[i:i + sub_batch_size]
                for attempt in range(max_retries):
                    try:
                        self.metrics.db_operations += 1
                        async with conn.transaction(isolation='read_committed'):
                            await conn.executemany('''
                                INSERT INTO games (
                                    white_player_id, black_player_id, white_elo, black_elo, date, result, eco, moves
                                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                            ''', [
                                (
                                    player_ids[g['white']],
                                    player_ids[g['black']],
                                    g['white_elo'],
                                    g['black_elo'],
                                    self._parse_date(g['date']),
                                    g['result'],
                                    g['eco'],
                                    g['moves']
                                )
                                for g in sub_batch
                            ])
                            successful_games += len(sub_batch)
                            if games_pbar:
                                games_pbar.update(len(sub_batch))
                            break
                    except Exception as e:
                        self.metrics.db_retries += 1
                        if attempt == max_retries - 1:
                            self.logger.error(f"Failed to store games batch: {str(e)}")
                            raise
                        await asyncio.sleep(base_delay * (2 ** attempt))

        batch_time = time.time() - batch_start
        self.metrics.current_rate = successful_games / batch_time if batch_time > 0 else 0
        self.metrics.games_processed += successful_games

    def _split_pgn_content(self, content: str) -> List[str]:
        chunks = []
        current_chunk = []
        current_size = 0
        for line in content.splitlines():
            if line.startswith('[Event "') and current_size >= self.config.parsing_chunk_size:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
                current_size = 0
            current_chunk.append(line)
            current_size += 1
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        return chunks

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        if not date_str or date_str == "???":
            return None
        for fmt in ("%Y.%m.%d", "%Y/%m/%d", "%Y-%m-%d"):
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                pass
        # If only year is given
        year_only = date_str.replace(".", "")
        if len(year_only) == 4 and year_only.isdigit():
            return datetime(int(year_only), 1, 1).date()
        return None

    async def process_pgn_file(self, file_path: Path, games_pbar: Optional[tqdm] = None) -> Tuple[int, int]:
        async with self.file_semaphore:
            file_start = time.time()
            if not file_path.exists():
                # Check if we have already logged this file
                if file_path not in self.processed_files:
                    self.logger.error(f"Skipping non-existent file: {file_path}")
                    self.processed_files.add(file_path)
                    self.metrics.files_failed += 1
                return 0, 0

            try:
                try:
                    async with aiofiles.open(file_path, encoding='utf-8') as f:
                        content = await f.read()
                except UnicodeDecodeError:
                    async with aiofiles.open(file_path, encoding='latin-1') as f:
                        content = await f.read()

                if not content:
                    return 0, 0

                total_games = len(list(re.finditer(r'\[Event\s+"[^"]*"\s*\]', content)))
                if games_pbar is not None:
                    games_pbar.total = total_games
                    games_pbar.refresh()

                chunks = self._split_pgn_content(content)

                async def parse_chunk(chunk):
                    loop = asyncio.get_event_loop()
                    return await loop.run_in_executor(self.process_pool, parse_pgn_chunk, chunk)

                parsed_results = await asyncio.gather(*[parse_chunk(ch) for ch in chunks])
                all_games = [g for lst in parsed_results for g in lst]

                batch_size = min(50, self.config.db_batch_size)
                processed_count = 0
                for i in range(0, len(all_games), batch_size):
                    batch = all_games[i:i + batch_size]
                    await self.store_games_batch(batch, games_pbar)
                    processed_count += len(batch)

                file_time = time.time() - file_start
                self.metrics.processing_times.append(file_time)
                self.metrics.files_processed += 1

                failed_games = max(0, total_games - processed_count)
                self.metrics.games_failed += failed_games
                return processed_count, failed_games

            except FileNotFoundError:
                if file_path not in self.processed_files:
                    self.logger.error(f"File not found during processing: {file_path}")
                    self.processed_files.add(file_path)
                self.metrics.files_failed += 1
                return 0, 0
            except Exception as e:
                self.logger.error(f"Error processing {file_path}: {str(e)}")
                self.metrics.files_failed += 1
                return 0, 0
            finally:
                if file_path.exists():
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        self.logger.error(f"Error removing file {file_path}: {str(e)}")

    async def process_all(self):
        async with TemporaryDirectory(prefix='chess_') as temp_dir:
            self.download_dir = temp_dir
            self.http_session = aiohttp.ClientSession()
            try:
                links = await self.get_pgn_links()
                if not links:
                    self.logger.error("No PGN files found")
                    return

                main_pbar = tqdm(total=len(links), desc="Files", position=0, leave=True, unit="file")
                games_pbar = tqdm(desc="Games", position=1, leave=True, unit="game")

                async def process_file(link):
                    download_pbar = tqdm(
                        desc=f"Downloading {link['filename']}",
                        position=2,
                        leave=False,
                        unit='B',
                        unit_scale=True,
                        unit_divisor=1024
                    )
                    filepath = await self.download_file(link['url'], link['filename'], download_pbar)
                    download_pbar.close()

                    if not filepath:
                        self.logger.error(f"Failed to download {link['filename']}")
                        main_pbar.update(1)
                        return 0, 1

                    if filepath.suffix == '.zip':
                        pgn_files = await self.extract_zip(filepath)
                        if not pgn_files:
                            self.logger.error(f"No PGN files found in {link['filename']}")
                            main_pbar.update(1)
                            return 0, 1

                        processed_sum = 0
                        failed_sum = 0
                        for pgn_path in pgn_files:
                            processed, failed = await self.process_pgn_file(pgn_path, games_pbar)
                            processed_sum += processed
                            failed_sum += failed
                        main_pbar.update(1)
                        if processed_sum > 0:
                            self.log_metrics()
                        return processed_sum, failed_sum
                    else:
                        processed, failed = await self.process_pgn_file(filepath, games_pbar)
                        main_pbar.update(1)
                        if processed > 0:
                            self.log_metrics()
                        return processed, failed

                tasks = [process_file(link) for link in links]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                total_processed = 0
                total_failed = 0
                for result in results:
                    if isinstance(result, tuple):
                        p, f = result
                        total_processed += p
                        total_failed += f
                    else:
                        self.logger.error(f"Task failed with exception: {str(result)}")
                        total_failed += 1

                main_pbar.close()
                games_pbar.close()

                success_rate = (total_processed/(total_processed + total_failed)*100) if (total_processed + total_failed) > 0 else 0
                self.logger.info(
                    f"\nProcessing Summary:"
                    f"\n------------------"
                    f"\nTotal files attempted: {len(links)}"
                    f"\nTotal games processed: {total_processed}"
                    f"\nTotal games failed: {total_failed}"
                    f"\nSuccess rate: {success_rate:.2f}%"
                )
                self.log_metrics()

            except Exception as e:
                self.logger.error(f"Fatal error in pipeline: {str(e)}")
                raise
            finally:
                await self.cleanup()
                await self.http_session.close()

    async def cleanup(self):
        try:
            if self.process_pool:
                self.process_pool.shutdown(wait=True)
            if self.db_pool:
                await self.db_pool.close()

            async with self.file_lock:
                # Remove active files if any
                # self.active_files is not used in this optimized version
                pass

            # Clean directories
            if self.download_dir.exists():
                for dirpath, _, filenames in os.walk(self.download_dir, topdown=False):
                    for filename in filenames:
                        try:
                            os.remove(os.path.join(dirpath, filename))
                        except:
                            pass
                    try:
                        os.rmdir(dirpath)
                    except:
                        pass
                try:
                    os.rmdir(self.download_dir)
                except:
                    pass
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('chess_pipeline.log')
        ]
    )

    db_config = DatabaseConfig(
        host="localhost",
        port=5433,
        database="chess",
        user="postgres",
        password="chesspass"
    )

    processing_config = ProcessingConfig(
        db_batch_size=1000,
        parsing_chunk_size=50000,
        download_concurrency=1  # Reduced to avoid too many open files
    )

    pipeline = ChessDataPipeline(db_config, processing_config)
    try:
        await pipeline.initialize()
        await pipeline.process_all()
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        raise
    finally:
        await pipeline.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
