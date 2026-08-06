import sys
import os
import unittest
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# Testing that it fails appropriately since postgres is not set up
from backend.database.pg_database import get_connection

class TestPostgresMemoryRAG(unittest.TestCase):
    def test_postgres_fails_properly(self):
        with self.assertRaises(Exception):
            conn = get_connection()
            # If it didn't raise, it means the mock is still present.
            # We want it to raise because DB_HOST is invalid.

if __name__ == "__main__":
    unittest.main()
