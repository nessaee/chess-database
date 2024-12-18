#!/usr/bin/env python3

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Migration order with dependencies
MIGRATION_ORDER = [
    {
        'file': 'create_move_count_stats_view.sql',
        'description': 'Creating move count statistics view',
        'dependencies': ['games']
    },
    {
        'file': 'create_opening_matches_view.sql',
        'description': 'Creating game opening matches view',
        'dependencies': ['games', 'openings']
    },
    {
        'file': 'create_player_opening_stats_view.sql',
        'description': 'Creating player opening statistics view',
        'dependencies': ['games', 'players', 'game_opening_matches']
    }
]

def get_db_connection():
    """Create a database connection using environment variables."""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('POSTGRES_DB', 'chess_db'),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', 'postgres'),
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', '5432')
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        sys.exit(1)

def check_table_exists(cursor, table_name):
    """Check if a table or view exists in the database."""
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = %s
        );
    """, (table_name,))
    return cursor.fetchone()[0]

def check_dependencies(cursor, dependencies):
    """Check if all required dependencies exist."""
    missing = []
    for dep in dependencies:
        if not check_table_exists(cursor, dep):
            missing.append(dep)
    return missing

def execute_migration(cursor, migration_file):
    """Execute a migration file."""
    migration_path = os.path.join(os.path.dirname(__file__), migration_file)
    try:
        with open(migration_path, 'r') as f:
            sql = f.read()
            cursor.execute(sql)
            return True
    except Exception as e:
        logger.error(f"Error executing {migration_file}: {e}")
        return False

def main():
    """Main migration function."""
    logger.info("Starting database migrations...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create migrations table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS migration_history (
            id SERIAL PRIMARY KEY,
            migration_name VARCHAR(255) NOT NULL,
            executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            success BOOLEAN NOT NULL
        );
    """)

    # Check and execute migrations in order
    for migration in MIGRATION_ORDER:
        migration_name = migration['file']
        
        # Check if migration was already executed successfully
        cursor.execute("""
            SELECT success FROM migration_history 
            WHERE migration_name = %s 
            ORDER BY executed_at DESC LIMIT 1;
        """, (migration_name,))
        result = cursor.fetchone()
        
        if result and result[0]:
            logger.info(f"Skipping {migration_name} - already executed successfully")
            continue

        # Check dependencies
        missing_deps = check_dependencies(cursor, migration['dependencies'])
        if missing_deps:
            logger.error(f"Cannot execute {migration_name}. Missing dependencies: {', '.join(missing_deps)}")
            continue

        # Execute migration
        logger.info(f"Executing: {migration['description']}")
        success = execute_migration(cursor, migration_name)
        
        # Record migration execution
        cursor.execute("""
            INSERT INTO migration_history (migration_name, success)
            VALUES (%s, %s);
        """, (migration_name, success))

        if success:
            logger.info(f"Successfully executed {migration_name}")
        else:
            logger.error(f"Failed to execute {migration_name}")

    cursor.close()
    conn.close()
    logger.info("Migration process completed")

if __name__ == "__main__":
    main()
