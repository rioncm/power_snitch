#!/usr/bin/env python3
"""
Power Snitch Database Initialization Script
Creates the database and loads default settings.
"""

import os
import sys
import logging
import time
from contextlib import contextmanager
from datetime import datetime, time as dt_time
from sqlalchemy import text, create_engine, inspect
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import OperationalError

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./init_db.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DatabaseInitializer:
    def __init__(self, db_path):
        self.db_path = db_path
        self.engine = create_engine(
            f'sqlite:///{db_path}',
            connect_args={'timeout': 30},
            poolclass=None  # SQLite doesn't need connection pooling
        )
        self.db = Database(db_path)
        self.install_dir = os.path.dirname(os.path.abspath(__file__))
        self.Session = scoped_session(sessionmaker(bind=self.engine))
        self.stats = {
            'total_commands': 0,
            'successful_commands': 0,
            'failed_commands': 0,
            'retried_commands': 0
        }

    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations."""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def verify_table_exists(self, table_name):
        """Verify that a table exists in the database."""
        inspector = inspect(self.engine)
        return table_name in inspector.get_table_names()

    def verify_data_inserted(self, table_name, expected_count=None):
        """Verify that data was inserted into a table."""
        with self.session_scope() as session:
            result = session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            count = result.scalar()
            logger.info(f"Table {table_name} contains {count} rows")
            if expected_count is not None and count < expected_count:
                logger.warning(f"Table {table_name} has fewer rows than expected: {count} < {expected_count}")
            return count

    def execute_with_retry(self, command, max_retries=3, delay=1):
        """Execute a SQL command with retries."""
        self.stats['total_commands'] += 1
        start_time = time.time()
        
        for attempt in range(max_retries):
            try:
                with self.session_scope() as session:
                    # Execute the command and ensure it's committed
                    result = session.execute(text(command))
                    session.commit()
                    execution_time = time.time() - start_time
                    
                    # Log success with details
                    logger.info(f"Successfully executed SQL command (attempt {attempt + 1}/{max_retries})")
                    logger.info(f"Command: {command[:100]}...")  # Log first 100 chars of command
                    logger.info(f"Execution time: {execution_time:.3f} seconds")
                    
                    # Log result details if available
                    if hasattr(result, 'rowcount') and result.rowcount is not None:
                        logger.info(f"Rows affected: {result.rowcount}")
                    
                    self.stats['successful_commands'] += 1
                    if attempt > 0:
                        self.stats['retried_commands'] += 1
                    return result
                    
            except OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    logger.warning(f"Database locked, retrying in {delay} seconds... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                else:
                    self.stats['failed_commands'] += 1
                    raise
            except Exception as e:
                self.stats['failed_commands'] += 1
                raise

    def execute_sql_file(self, sql_file):
        """Execute a SQL file."""
        file_start_time = time.time()
        logger.info(f"Starting execution of SQL file: {sql_file}")
        
        try:
            with open(sql_file, 'r') as f:
                content = f.read()
                logger.info(f"Read SQL file content, length: {len(content)} bytes")
                
                # Split on semicolons and execute each statement
                statements = content.split(';')
                logger.info(f"Found {len(statements)} SQL statements to execute")
                
                for i, statement in enumerate(statements, 1):
                    statement = statement.strip()
                    if statement:  # Skip empty statements
                        logger.info(f"Executing statement {i}/{len(statements)}")
                        self.execute_with_retry(statement)
                            
            file_execution_time = time.time() - file_start_time
            logger.info(f"Completed execution of SQL file: {sql_file}")
            logger.info(f"Total file execution time: {file_execution_time:.3f} seconds")
            logger.info(f"File execution stats: {self.stats}")
            
        except Exception as e:
            logger.error(f"Error executing SQL file {sql_file}: {str(e)}")
            raise

    def initialize(self):
        """Initialize the database with schema and default data."""
        start_time = time.time()
        logger.info("Starting database initialization process")
        
        try:
            # Create database directory if it doesn't exist
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            logger.info(f"Created database directory: {os.path.dirname(self.db_path)}")
            
            # Initialize database
            self.db.init_db()
            logger.info("Database initialized with SQLAlchemy models")
            
            # Execute SQL files
            self.execute_sql_file(os.path.join(self.install_dir, 'tables.sql'))
            
            # Verify tables were created
            required_tables = [
                'web_interface', 'ups_config', 'health_check', 'battery_health_config',
                'battery_health_history', 'battery_alerts', 'notification_services',
                'webhook_config', 'email_config', 'email_recipients', 'sms_config',
                'sms_recipients', 'triggers', 'always_notify_events'
            ]
            
            for table in required_tables:
                if not self.verify_table_exists(table):
                    raise Exception(f"Required table {table} was not created")
                logger.info(f"Verified table exists: {table}")
            
            # Execute defaults file
            self.execute_sql_file(os.path.join(self.install_dir, 'defaults.sql'))
            
            # Verify default data was inserted
            self.verify_data_inserted('web_interface', 1)
            self.verify_data_inserted('ups_config', 1)
            self.verify_data_inserted('health_check', 1)
            self.verify_data_inserted('battery_health_config', 1)
            self.verify_data_inserted('notification_services', 3)  # webhook, email, sms
            self.verify_data_inserted('triggers', 4)  # battery_level_change, load_change, always_notify, health_check
            
            total_time = time.time() - start_time
            logger.info("Database initialization completed successfully")
            logger.info(f"Total initialization time: {total_time:.3f} seconds")
            logger.info("Final statistics:")
            logger.info(f"Total commands executed: {self.stats['total_commands']}")
            logger.info(f"Successful commands: {self.stats['successful_commands']}")
            logger.info(f"Failed commands: {self.stats['failed_commands']}")
            logger.info(f"Retried commands: {self.stats['retried_commands']}")
            
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
        finally:
            # Clean up the scoped session
            self.Session.remove()
            logger.info("Database sessions cleaned up")

def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: init_db.py <db_path>")
        sys.exit(1)
    
    db_path = sys.argv[1]
    initializer = DatabaseInitializer(db_path)
    initializer.initialize()

if __name__ == '__main__':
    main() 