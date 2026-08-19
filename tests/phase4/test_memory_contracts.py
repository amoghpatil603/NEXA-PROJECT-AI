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
            MemoryQuery(query="")
        with self.assertRaises(ValueError):
            MemoryQuery(query="q", top_k=0)

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

        with self.assertRaises(ValueError):
            MemoryResult(item=None, score=0.85)

if __name__ == "__main__":
    unittest.main()
