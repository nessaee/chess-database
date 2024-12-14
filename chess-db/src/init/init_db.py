# reinit_db.py
import asyncio
import asyncpg
from typing import Optional
import logging
from datetime import datetime

class DatabaseInitializer:
    """Handles PostgreSQL database reinitialization with proper cleanup and setup."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 5434,
        user: str = "postgres",
        password: str = "chesspass",
        database: str = "chess"
    ):
        """
        Initialize database connection parameters.
        
        Args:
            host: Database host address
            port: Database port number
            user: Database username
            password: Database password
            database: Database name to be (re)created
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        
        # Configure logging
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """Configure logging with timestamp and appropriate format."""
        logger = logging.getLogger("DatabaseInitializer")
        logger.setLevel(logging.INFO)
        
        # Create console handler with formatting
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger

    async def _connect_postgres(self) -> asyncpg.Connection:
        """
        Connect to PostgreSQL server using default 'postgres' database.
        
        Returns:
            asyncpg.Connection: Database connection
            
        Raises:
            Exception: If connection fails
        """
        try:
            return await asyncpg.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database='postgres'  # Connect to default database
            )
        except Exception as e:
            self.logger.error(f"Failed to connect to PostgreSQL: {str(e)}")
            raise

    async def reinitialize(self) -> bool:
        """
        Reinitialize the database by dropping and recreating it.
        
        Returns:
            bool: True if reinitialization was successful
            
        Note:
            This will destroy all existing data in the database.
        """
        start_time = datetime.now()
        self.logger.info(f"Starting database reinitialization: {self.database}")
        
        try:
            # Connect to default postgres database
            conn = await self._connect_postgres()
            
            try:
                # Terminate existing connections
                self.logger.info("Terminating existing connections...")
                await conn.execute(f'''
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = '{self.database}'
                    AND pid <> pg_backend_pid();
                ''')
                
                # Drop database if exists
                self.logger.info(f"Dropping database if exists: {self.database}")
                await conn.execute(f'DROP DATABASE IF EXISTS {self.database}')
                
                # Create fresh database
                self.logger.info(f"Creating new database: {self.database}")
                await conn.execute(f'CREATE DATABASE {self.database}')
                
                elapsed_time = (datetime.now() - start_time).total_seconds()
                self.logger.info(
                    f"Database reinitialization completed successfully in {elapsed_time:.2f} seconds"
                )
                return True
                
            finally:
                # Always close the connection
                await conn.close()
                
        except Exception as e:
            self.logger.error(f"Database reinitialization failed: {str(e)}")
            return False

async def main():
    """Main execution function with error handling."""
    initializer = DatabaseInitializer()
    
    try:
        success = await initializer.reinitialize()
        if not success:
            exit(1)
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())