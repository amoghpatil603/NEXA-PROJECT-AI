import unittest
from backend.memory.interfaces import MemoryItem, MemoryQuery, MemoryResult

class TestMemoryContracts(unittest.TestCase):
    def test_valid_memory_item(self):
        item = MemoryItem(
            memory_id="mem-123",
            scope="session-abc",
            content="Today is a sunny day",
            importance=7.5,
            metadata={"source": "user_input"}
        )
        self.assertEqual(item.memory_id, "mem-123")
        self.assertEqual(item.scope, "session-abc")
        self.assertEqual(item.content, "Today is a sunny day")
        self.assertEqual(item.importance, 7.5)
        self.assertEqual(item.metadata["source"], "user_input")

        # Serialization / Deserialization
        d = item.to_dict()
        self.assertEqual(d["memory_id"], "mem-123")
        self.assertEqual(d["importance"], 7.5)

        item2 = MemoryItem.from_dict(d)
        self.assertEqual(item2.content, item.content)
        self.assertEqual(item2.importance, item.importance)

    def test_invalid_memory_item(self):
        # Empty fields
        with self.assertRaises(ValueError):
            MemoryItem(memory_id="", scope="s", content="c", importance=1.0)
        with self.assertRaises(ValueError):
            MemoryItem(memory_id="id", scope="", content="c", importance=1.0)
        with self.assertRaises(ValueError):
            MemoryItem(memory_id="id", scope="s", content="  ", importance=1.0)

        # Invalid importance score
        with self.assertRaises(ValueError):
            MemoryItem(memory_id="id", scope="s", content="c", importance=-0.1)
        with self.assertRaises(ValueError):
            MemoryItem(memory_id="id", scope="s", content="c", importance=10.1)

    def test_memory_query(self):
        query = MemoryQuery(query="weather info", scope="global", top_k=3)
        self.assertEqual(query.query, "weather info")
        self.assertEqual(query.scope, "global")
        self.assertEqual(query.top_k, 3)

        with self.assertRaises(ValueError):
            MemoryQuery(query="", scope="global")
        with self.assertRaises(ValueError):
            MemoryQuery(query="q", scope="")
        with self.assertRaises(ValueError):
            MemoryQuery(query="q", scope="   ")
        with self.assertRaises(ValueError):
            MemoryQuery(query="q", scope="global", top_k=0)

    def test_memory_result(self):
        item = MemoryItem(
            memory_id="m1",
            scope="session",
            content="test content",
            importance=5.0
        )
        res = MemoryResult(item=item, score=0.85)
        self.assertEqual(res.item.memory_id, "m1")
        self.assertEqual(res.score, 0.85)

    def test_memory_engine_strict_user_isolation(self):
        import os
        prev_mock = os.environ.get("USE_MOCK_DB")
        os.environ["USE_MOCK_DB"] = "1"
        try:
            from backend.memory.memory_engine import MemoryEngine
            from backend.database.pg_database import MockPgConnection
            MockPgConnection._db_store = {"memories": [], "documents": [], "chunks": []}

            engine = MemoryEngine()

            # 1. Create memories for user_a and user_b
            mem_a_id = engine.create_memory(type="fact", content="User A secret notes", user_id="user_a")
            mem_b_id = engine.create_memory(type="fact", content="User B confidential info", user_id="user_b")
            self.assertIsNotNone(mem_a_id)
            self.assertIsNotNone(mem_b_id)

            # 2. User A cannot read User B's memory
            mem_b_read_by_a = engine.get_memory(mem_b_id, user_id="user_a")
            self.assertIsNone(mem_b_read_by_a, "User A must not be able to get User B memory")

            mem_a_read_by_a = engine.get_memory(mem_a_id, user_id="user_a")
            self.assertIsNotNone(mem_a_read_by_a)
            self.assertEqual(mem_a_read_by_a["metadata"]["user_id"], "user_a")

            # 3. User A cannot search User B's memory
            results_a = engine.search_memory(query="confidential", user_id="user_a")
            for res in results_a:
                self.assertEqual(res["metadata"]["user_id"], "user_a")
                self.assertNotEqual(res["metadata"]["user_id"], "user_b")

            results_b = engine.search_memory(query="confidential", user_id="user_b")
            for res in results_b:
                self.assertEqual(res["metadata"]["user_id"], "user_b")

            # 4. User A cannot update User B's memory
            update_success = engine.update_memory(mem_b_id, user_id="user_a", content="Hacked content")
            self.assertFalse(update_success, "User A must not be able to update User B memory")

            # Verify content was not modified
            mem_b_intact = engine.get_memory(mem_b_id, user_id="user_b")
            self.assertIn("User B", mem_b_intact["content"])

            # 5. User A cannot delete User B's memory
            delete_success = engine.delete_memory(mem_b_id, user_id="user_a")
            self.assertFalse(delete_success, "User A must not be able to delete User B memory")

            # Verify User B memory still exists
            self.assertIsNotNone(engine.get_memory(mem_b_id, user_id="user_b"))

            # 6. User B can delete own memory
            delete_b = engine.delete_memory(mem_b_id, user_id="user_b")
            self.assertTrue(delete_b)
            self.assertIsNone(engine.get_memory(mem_b_id, user_id="user_b"))
        finally:
            if prev_mock is not None:
                os.environ["USE_MOCK_DB"] = prev_mock
            else:
                os.environ.pop("USE_MOCK_DB", None)

    def test_missing_owner_scope_rejection(self):
        from backend.memory.memory_engine import MemoryEngine
        engine = MemoryEngine()

        with self.assertRaises(ValueError):
            engine.create_memory(type="fact", content="Test", user_id="")
        with self.assertRaises(ValueError):
            engine.create_memory(type="fact", content="Test", user_id="   ")
        with self.assertRaises(ValueError):
            engine.create_memory(type="fact", content="Test", user_id=None)

        with self.assertRaises(ValueError):
            engine.get_memory(1, user_id="")
        with self.assertRaises(ValueError):
            engine.search_memory("query", user_id="")
        with self.assertRaises(ValueError):
            engine.update_memory(1, user_id="")
        with self.assertRaises(ValueError):
            engine.delete_memory(1, user_id="")

if __name__ == "__main__":
    unittest.main()
