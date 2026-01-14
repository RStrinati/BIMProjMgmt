"""
Enhanced database connection manager with connection pooling and improved error handling.

This module provides:
- Connection pooling for better performance
- Context managers for safe connection handling
- Retry logic for transient failures
- Proper resource cleanup
- Connection health checks
"""

import logging
import pyodbc
import threading
import time
from contextlib import contextmanager
from queue import Queue, Empty
from typing import Optional, Generator

from config import Config

logger = logging.getLogger(__name__)


class ConnectionPool:
    """Thread-safe connection pool for SQL Server."""
    
    def __init__(self, database_name: str, min_size: int = 2, max_size: int = 10):
        """
        Initialize connection pool.
        
        Args:
            database_name: Name of the database to connect to
            min_size: Minimum number of connections to maintain
            max_size: Maximum number of connections allowed
        """
        self.database_name = database_name
        self.min_size = min_size
        self.max_size = max_size
        self._pool: Queue = Queue(maxsize=max_size)
        self._lock = threading.Lock()
        self._created_connections = 0
        self._conn_string = self._build_connection_string()
        
        # Pre-create minimum connections
        for _ in range(min_size):
            try:
                conn = self._create_connection()
                self._pool.put(conn)
            except Exception as e:
                logger.error(f"Failed to create initial connection for {database_name}: {e}")
    
    def _build_connection_string(self) -> str:
        """Build SQL Server connection string."""
        return (
            f"DRIVER={{{Config.DB_DRIVER}}};"
            f"SERVER={Config.DB_SERVER};"
            f"UID={Config.DB_USER};"
            f"PWD={Config.DB_PASSWORD};"
            f"DATABASE={self.database_name};"
            "TrustServerCertificate=yes;"
            "MARS_Connection=yes;"  # Multiple Active Result Sets
        )
    
    def _create_connection(self) -> pyodbc.Connection:
        """Create a new database connection."""
        try:
            conn = pyodbc.connect(self._conn_string, timeout=10)
            conn.autocommit = False  # Use explicit transactions
            with self._lock:
                self._created_connections += 1
            logger.debug(f"Created new connection for {self.database_name} (total: {self._created_connections})")
            return conn
        except pyodbc.Error as e:
            logger.error(f"Failed to create connection to {self.database_name}: {e}")
            raise

    def stats(self) -> dict[str, int]:
        with self._lock:
            created = self._created_connections
        return {
            "created": created,
            "available": self._pool.qsize(),
            "max_size": self.max_size,
        }
    
    def _is_connection_alive(self, conn: pyodbc.Connection) -> bool:
        """Check if a connection is still alive."""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except Exception:
            return False
    
    def get_connection(self, timeout: int = 5) -> pyodbc.Connection:
        """
        Get a connection from the pool.
        
        Args:
            timeout: Maximum seconds to wait for a connection
            
        Returns:
            Active database connection
            
        Raises:
            Empty: If no connection available within timeout
            pyodbc.Error: If connection creation fails
        """
        try:
            # Try to get connection from pool
            conn = self._pool.get(timeout=timeout)
            
            # Check if connection is still alive
            if not self._is_connection_alive(conn):
                logger.warning(f"Stale connection detected for {self.database_name}, creating new one")
                conn.close()
                conn = self._create_connection()
            
            logger.debug(
                "Acquired connection db=%s created=%s available=%s max=%s",
                self.database_name,
                self.stats()["created"],
                self.stats()["available"],
                self.max_size,
            )
            return conn
            
        except Empty:
            # Pool is empty, create new connection if under max_size
            with self._lock:
                can_create = self._created_connections < self.max_size
            if can_create:
                logger.info(f"Creating new connection for {self.database_name} (pool exhausted)")
                conn = self._create_connection()
                logger.debug(
                    "Acquired new connection db=%s created=%s available=%s max=%s",
                    self.database_name,
                    self.stats()["created"],
                    self.stats()["available"],
                    self.max_size,
                )
                return conn
            raise Exception(f"Connection pool exhausted for {self.database_name} (max={self.max_size})")
    
    def return_connection(self, conn: pyodbc.Connection):
        """
        Return a connection to the pool.
        
        Args:
            conn: Connection to return
        """
        if conn is None:
            return
        
        try:
            # Rollback any uncommitted transaction
            if not conn.autocommit:
                conn.rollback()
            
            # Return to pool if it's still alive
            if self._is_connection_alive(conn):
                self._pool.put_nowait(conn)
                logger.debug(
                    "Returned connection db=%s created=%s available=%s max=%s",
                    self.database_name,
                    self.stats()["created"],
                    self.stats()["available"],
                    self.max_size,
                )
            else:
                logger.warning(f"Discarding dead connection for {self.database_name}")
                conn.close()
                with self._lock:
                    self._created_connections -= 1
                    
        except Exception as e:
            logger.error(f"Error returning connection to pool: {e}")
            try:
                conn.close()
            except:
                pass
            with self._lock:
                self._created_connections -= 1
    
    def close_all(self):
        """Close all connections in the pool."""
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                conn.close()
            except Empty:
                break
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
        
        with self._lock:
            self._created_connections = 0
        
        logger.info(f"Closed all connections for {self.database_name}")


class DatabaseManager:
    """Centralized database connection manager with pooling."""
    
    def __init__(self):
        """Initialize connection pools for each database."""
        self._pools = {}
        self._initialized = False
        self._lock = threading.Lock()
    
    def _ensure_initialized(self):
        """Lazy initialization of connection pools."""
        if self._initialized:
            return
        
        with self._lock:
            if self._initialized:
                return
            
            try:
                # Create pools for each database
                self._pools[Config.PROJECT_MGMT_DB] = ConnectionPool(
                    Config.PROJECT_MGMT_DB, min_size=3, max_size=15
                )
                self._pools[Config.ACC_DB] = ConnectionPool(
                    Config.ACC_DB, min_size=1, max_size=5
                )
                self._pools[Config.REVIT_HEALTH_DB] = ConnectionPool(
                    Config.REVIT_HEALTH_DB, min_size=1, max_size=5
                )
                
                self._initialized = True
                logger.info("Database connection pools initialized")
                
            except Exception as e:
                logger.error(f"Failed to initialize connection pools: {e}")
                raise
    
    def get_pool(self, database_name: Optional[str] = None) -> ConnectionPool:
        """
        Get connection pool for specified database.
        
        Args:
            database_name: Database name, defaults to PROJECT_MGMT_DB
            
        Returns:
            ConnectionPool instance
        """
        self._ensure_initialized()
        
        db_name = database_name or Config.PROJECT_MGMT_DB
        
        if db_name not in self._pools:
            # Create pool on-demand for unknown databases
            logger.info(f"Creating on-demand pool for {db_name}")
            with self._lock:
                if db_name not in self._pools:
                    self._pools[db_name] = ConnectionPool(db_name, min_size=1, max_size=5)
        
        return self._pools[db_name]
    
    @contextmanager
    def get_connection(self, database_name: Optional[str] = None, 
                       timeout: int = 5) -> Generator[pyodbc.Connection, None, None]:
        """
        Context manager for safe connection handling.
        
        Args:
            database_name: Database name, defaults to PROJECT_MGMT_DB
            timeout: Connection acquisition timeout in seconds
            
        Yields:
            Database connection
            
        Example:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tblProjects")
                results = cursor.fetchall()
                conn.commit()
        """
        pool = self.get_pool(database_name)
        conn = None
        
        try:
            conn = pool.get_connection(timeout=timeout)
            yield conn
            
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            logger.error(f"Error in database operation: {e}")
            raise
            
        finally:
            if conn:
                pool.return_connection(conn)
    
    def execute_with_retry(self, func, database_name: Optional[str] = None, 
                          max_retries: int = 3, retry_delay: float = 1.0):
        """
        Execute a database operation with retry logic.
        
        Args:
            func: Function that takes a connection and returns a result
            database_name: Database name
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            
        Returns:
            Result from func
            
        Example:
            def get_projects(conn):
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tblProjects")
                return cursor.fetchall()
            
            projects = db_manager.execute_with_retry(get_projects)
        """
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                with self.get_connection(database_name) as conn:
                    return func(conn)
                    
            except (pyodbc.OperationalError, pyodbc.InterfaceError) as e:
                # Transient errors - retry
                last_exception = e
                logger.warning(f"Transient database error (attempt {attempt + 1}/{max_retries}): {e}")
                
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                    
            except Exception as e:
                # Non-retryable error
                logger.error(f"Non-retryable database error: {e}")
                raise
        
        # All retries exhausted
        logger.error(f"Database operation failed after {max_retries} attempts")
        raise last_exception
    
    def close_all_pools(self):
        """Close all connection pools."""
        with self._lock:
            for pool in self._pools.values():
                pool.close_all()
            self._pools.clear()
            self._initialized = False
        
        logger.info("All database connection pools closed")


# Global instance
db_manager = DatabaseManager()


# Backwards compatibility wrapper
def connect_to_db(db_name: Optional[str] = None) -> Optional[pyodbc.Connection]:
    """
    Legacy connection function for backwards compatibility.
    
    NOTE: This creates a new connection each time. For better performance,
    use db_manager.get_connection() context manager instead.
    
    Args:
        db_name: Database name, defaults to PROJECT_MGMT_DB
        
    Returns:
        Database connection or None if failed
    """
    try:
        pool = db_manager.get_pool(db_name)
        return pool.get_connection(timeout=5)
    except Exception as e:
        logger.error(f"Failed to get connection: {e}")
        return None


@contextmanager
def get_db_connection(database_name: Optional[str] = None) -> Generator[pyodbc.Connection, None, None]:
    """
    Context manager for database connections (recommended approach).
    
    Args:
        database_name: Database name, defaults to PROJECT_MGMT_DB
        
    Yields:
        Database connection
        
    Example:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tblProjects")
            results = cursor.fetchall()
            conn.commit()
    """
    with db_manager.get_connection(database_name) as conn:
        yield conn
