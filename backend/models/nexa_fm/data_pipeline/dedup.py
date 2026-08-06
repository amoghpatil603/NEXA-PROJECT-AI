import hashlib
from typing import Dict, Any, Optional

class Deduplicator:
    def __init__(self, use_near_dedup=False):
        self.exact_seen = set()
        self.stats = {"exact_duplicates": 0, "near_duplicates": 0}
        self.use_near_dedup = use_near_dedup
        self.lsh = None
        
        if self.use_near_dedup:
            try:
                from datasketch import MinHash, MinHashLSH
                self.lsh = MinHashLSH(threshold=0.8, num_perm=128)
                self.minhash_cls = MinHash
            except ImportError:
                print("datasketch not installed. Near deduplication disabled.")
                self.use_near_dedup = False

    def check_and_add(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        text = item.get("text", "")
        
        # Exact deduplication
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        if text_hash in self.exact_seen:
            self.stats["exact_duplicates"] += 1
            return None
            
        self.exact_seen.add(text_hash)
        
        # Near deduplication
        if self.use_near_dedup and self.lsh is not None:
            words = set(text.lower().split())
            m = self.minhash_cls(num_perm=128)
            for d in words:
                m.update(d.encode('utf8'))
                
            result = self.lsh.query(m)
            if result:
                self.stats["near_duplicates"] += 1
                return None
            self.lsh.insert(text_hash, m)
            
        return item
