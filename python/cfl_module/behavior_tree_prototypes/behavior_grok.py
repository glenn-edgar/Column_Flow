import psycopg2
from psycopg2.extras import DictCursor
import re
from fnmatch import fnmatch
from typing import Dict, Any, List, Optional
import json
import uuid

class TreeDataHybridManager:
    def __init__(self, db_config: Optional[Dict[str, str]] = None):
        """Initialize with optional database config for PostgreSQL or in-memory dictionary."""
        self.data: Dict[str, Any] = {}  # In-memory storage
        self.db_enabled = db_config is not None
        if self.db_enabled:
            self.conn = psycopg2.connect(**db_config)
            self.cursor = self.conn.cursor(cursor_factory=DictCursor)
            self._enable_ltree_extension()
            self._create_table()

    def _enable_ltree_extension(self):
        """Enable ltree extension in PostgreSQL."""
        if not self.db_enabled:
            return
        self.cursor.execute("CREATE EXTENSION IF NOT EXISTS ltree")
        self.conn.commit()

    def _create_table(self):
        """Create table for storing tree-structured data."""
        if not self.db_enabled:
            return
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tree_data (
                id SERIAL PRIMARY KEY,
                path ltree UNIQUE,
                data JSONB
            );
            CREATE INDEX IF NOT EXISTS tree_data_path_idx ON tree_data USING GIST (path);
        """)
        self.conn.commit()

    def _validate_path(self, path: str) -> str:
        """Validate ltree-like path format."""
        if not isinstance(path, str):
            raise ValueError("Path must be a string")
        if not re.match(r'^[a-zA-Z0-9_]+(\.[a-zA-Z0-9_]+)*$', path):
            raise ValueError("Invalid path format. Use alphanumeric labels separated by dots.")
        return path

    def _path_to_pattern(self, query_string: str) -> str:
        """Convert ltree query string to fnmatch pattern for in-memory queries."""
        pattern = query_string.replace('.', r'\.').replace('*', '[a-zA-Z0-9_]*')
        return pattern

    def insert_data(self, path: str, data: Any) -> str:
        """Insert or update data at the specified path."""
        path = self._validate_path(path)
        data_id = str(uuid.uuid4())
        
        if self.db_enabled:
            data_json = json.dumps(data)
            self.cursor.execute("""
                INSERT INTO tree_data (path, data)
                VALUES (%s, %s)
                ON CONFLICT (path) DO UPDATE
                SET data = EXCLUDED.data
                RETURNING id
            """, (path, data_json))
            data_id = self.cursor.fetchone()['id']
            self.conn.commit()
        else:
            self.data[path] = data
        
        return data_id

    def get_by_path(self, path: str) -> Optional[Any]:
        """Retrieve data by exact path."""
        path = self._validate_path(path)
        if self.db_enabled:
            self.cursor.execute("SELECT data FROM tree_data WHERE path = %s", (path,))
            result = self.cursor.fetchone()
            return result['data'] if result else None
        return self.data.get(path)

    def query_ltree(self, query_string: str) -> List[Dict[str, Any]]:
        """Query data using ltree query string (e.g., 'a.b.*.c.d')."""
        if not isinstance(query_string, str):
            raise ValueError("Query string must be a string")
        if not re.match(r'^[a-zA-Z0-9_\.\*\@~\{\}<>\[\]\(\)]*$', query_string):
            raise ValueError("Invalid ltree query syntax")

        if self.db_enabled:
            # Full ltree query support in PostgreSQL
            self.cursor.execute("SELECT path, data FROM tree_data WHERE path ~ %s", (query_string,))
            results = [{"path": str(row['path']), "data": row['data']} for row in self.cursor.fetchall()]
        else:
            # Simplified wildcard query for in-memory
            pattern = self._path_to_pattern(query_string)
            results = [
                {"path": path, "data": data}
                for path, data in self.data.items()
                if fnmatch(path, pattern)
            ]
        return results

    def delete_by_path(self, path: str) -> bool:
        """Delete data at the specified path."""
        path = self._validate_path(path)
        if self.db_enabled:
            self.cursor.execute("DELETE FROM tree_data WHERE path = %s RETURNING id", (path,))
            result = self.cursor.fetchone()
            self.conn.commit()
            return bool(result)
        if path in self.data:
            del self.data[path]
            return True
        return False

    def export_to_postgres(self, db_config: Dict[str, str]) -> None:
        """Export in-memory dictionary to PostgreSQL table."""
        if not self.data:
            return
        if not self.db_enabled:
            self.conn = psycopg2.connect(**db_config)
            self.cursor = self.conn.cursor(cursor_factory=DictCursor)
            self.db_enabled = True
            self._enable_ltree_extension()
            self._create_table()

        for path, data in self.data.items():
            data_json = json.dumps(data)
            self.cursor.execute("""
                INSERT INTO tree_data (path, data)
                VALUES (%s, %s)
                ON CONFLICT (path) DO UPDATE
                SET data = EXCLUDED.data
            """, (path, data_json))
        self.conn.commit()

    def import_from_postgres(self, table_name: str = "tree_data") -> None:
        """Import data from a qualifying PostgreSQL table into dictionary."""
        if not self.db_enabled:
            raise ValueError("Database connection required for import")
        
        # Verify table exists and has correct schema
        self.cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = %s
        """, (table_name,))
        columns = {row['column_name']: row['data_type'] for row in self.cursor.fetchall()}
        
        if not (columns.get('path') == 'ltree' and columns.get('data') == 'jsonb'):
            raise ValueError("Table must have 'path' (ltree) and 'data' (jsonb) columns")

        self.cursor.execute(f"SELECT path, data FROM {table_name}")
        for row in self.cursor.fetchall():
            self.data[str(row['path'])] = row['data']
        
        # Optionally clear the table after import
        # self.cursor.execute(f"DELETE FROM {table_name}")
        # self.conn.commit()

    def close(self):
        """Close database connections if active."""
        if self.db_enabled:
            self.cursor.close()
            self.conn.close()
            self.db_enabled = False

# Example usage
if __name__ == "__main__":
    db_config = {
        "dbname": "your_db",
        "user": "your_user",
        "password": "your_password",
        "host": "localhost",
        "port": "5432"
    }

    # Initialize with in-memory storage
    tree_manager = TreeDataHybridManager()

    # Insert sample data in-memory
    tree_manager.insert_data("a.b.c", {"name": "Node C", "value": 100})
    tree_manager.insert_data("a.b.d", {"name": "Node D", "value": 200})
    tree_manager.insert_data("a.b.e.c.d", {"name": "Node D under E", "value": 300})

    # Query in-memory
    results = tree_manager.query_ltree("a.b.*.c.d")
    print("In-memory query a.b.*.c.d:", results)

    # Export to PostgreSQL
    tree_manager.export_to_postgres(db_config)

    # Initialize with database connection
    db_manager = TreeDataHybridManager(db_config)

    # Full ltree query with advanced operators
    results = db_manager.query_ltree("a.b.@*.c.d")  # Descendant with any labels
    print("Database query a.b.@*.c.d:", results)

    # Import back to dictionary
    db_manager.import_from_postgres()
    print("Imported dictionary:", list(db_manager.data.items())[:2])

    # Close connections
    db_manager.close()
