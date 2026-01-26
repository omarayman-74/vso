"""Database service for MySQL operations."""
import json
import decimal
import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Any, Optional, Tuple

from config import settings


def safe_serialize(obj):
    """Serialize objects for JSON conversion."""
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    return str(obj)


class DatabaseService:
    """Service for MySQL database operations with connection pooling."""
    
    def __init__(self):
        """Initialize database service with connection pool."""
        self.config = settings.db_config
        self.pool = None
        self._initialize_pool()
        
    def _initialize_pool(self):
        """Initialize or re-initialize the connection pool."""
        try:
            # Create a connection pool to reuse connections
            # This saves ~0.1-0.3s per query by avoiding handshake overhead
            if not self.pool:
                self.pool = mysql.connector.pooling.MySQLConnectionPool(
                    pool_name="eshtri_pool",
                    pool_size=5,  # Keep 5 connections ready
                    pool_reset_session=True,
                    **self.config
                )
                print("Database connection pool initialized")
        except Error as e:
            print(f"Error initializing connection pool: {e}")
            self.pool = None

    def execute_query(self, sql: str) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Execute SQL query using a pooled connection.
        
        Returns:
            Tuple of (results, error_message)
        """
        connection = None
        cursor = None
        try:
            # Get connection from pool
            if not self.pool:
                self._initialize_pool()
            
            # If pool is still not available, try direct connection
            if not self.pool:
                connection = mysql.connector.connect(**self.config)
            else:
                connection = self.pool.get_connection()
                
            if not connection.is_connected():
                connection.reconnect(attempts=3, delay=1)
                
            cursor = connection.cursor(dictionary=True)
            cursor.execute(sql)
            rows = cursor.fetchall()
            return rows, None
            
        except Error as e:
            error_msg = str(e)
            print(f"Database error: {error_msg}")
            # Force pool reset on vital errors
            if "lost connection" in error_msg.lower() or "gone away" in error_msg.lower():
                self.pool = None 
            return [], error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"{error_msg}")
            return [], error_msg
        finally:
            # Always return connection to pool
            if cursor:
                try:
                    cursor.close()
                except:
                    pass
            if connection:
                try:
                    connection.close()  # This returns it to pool, doesn't actually close
                except:
                    pass
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            if not self.pool:
                self._initialize_pool()
                
            if self.pool:
                try:
                    conn = self.pool.get_connection()
                    if conn.is_connected():
                        # print("Database connection successful via pool")
                        conn.close()
                        return True
                except:
                    pass
            
            # Fallback test
            with mysql.connector.connect(**self.config) as connection:
                if connection.is_connected():
                    print("Database connection successful (direct)")
                    return True
        except Error as e:
            print(f"Database connection failed: {e}")
            return False
        return False


# Global database service instance
db_service = DatabaseService()
