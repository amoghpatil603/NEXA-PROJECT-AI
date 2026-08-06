import re
import unicodedata
from typing import Dict, Any, Optional

class TextCleaner:
    def __init__(self, normalize_unicode=True, clean_whitespace=True, remove_html=True, remove_control_chars=True):
        self.normalize_unicode = normalize_unicode
        self.clean_whitespace = clean_whitespace
        self.remove_html = remove_html
        self.remove_control_chars = remove_control_chars
        
        self.html_pattern = re.compile(r'<[^>]+>')
        self.control_char_pattern = re.compile(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]')

    def clean(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        text = item.get("text", "")
        if not text:
            return None
            
        if self.remove_html:
            text = self.html_pattern.sub('', text)
            
        if self.remove_control_chars:
            text = self.control_char_pattern.sub('', text)
            
        if self.normalize_unicode:
            text = unicodedata.normalize('NFKC', text)
            
        if self.clean_whitespace:
            text = re.sub(r'\s+', ' ', text).strip()
            
        if not text:
            return None
            
        item["text"] = text
        return item
