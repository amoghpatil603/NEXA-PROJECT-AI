from typing import Dict, Any, Optional, List
import re

class DatasetFilter:
    def __init__(self, min_length=50, max_length=100000, allowed_languages: Optional[List[str]]=None):
        self.min_length = min_length
        self.max_length = max_length
        self.allowed_languages = allowed_languages
        self.stats = {"total_processed": 0, "rejected_length": 0, "rejected_lang": 0, "rejected_repetition": 0}
        
    def _detect_language(self, text: str) -> str:
        try:
            from langdetect import detect
            return detect(text)
        except ImportError:
            return "unknown"
        except Exception:
            return "unknown"

    def _has_excessive_repetition(self, text: str) -> bool:
        # Check for simple character repetition
        if re.search(r'(.)\1{20,}', text):
            return True
            
        # Check for word repetition
        words = text.split()
        if len(words) > 10:
            unique_words = len(set(words))
            if unique_words / len(words) < 0.2:
                return True
        return False

    def filter_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        self.stats["total_processed"] += 1
        text = item.get("text", "")
        
        if len(text) < self.min_length or len(text) > self.max_length:
            self.stats["rejected_length"] += 1
            return None
            
        if self.allowed_languages is not None:
            lang = self._detect_language(text)
            item["language"] = lang
            if lang not in self.allowed_languages and lang != "unknown":
                self.stats["rejected_lang"] += 1
                return None
                
        if self._has_excessive_repetition(text):
            self.stats["rejected_repetition"] += 1
            return None
            
        return item
