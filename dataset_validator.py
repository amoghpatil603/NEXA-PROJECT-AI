import json
import hashlib
from typing import Dict, List, Any
import re
from pathlib import Path

class DatasetValidator:
    def __init__(self, config=None):
        self.config = config or {}
        self.min_length = self.config.get("min_length", 10)
        self.max_length = self.config.get("max_length", 10000)
        self.pass_threshold = self.config.get("pass_threshold", 70)
        self.exact_seen = set()
        self.near_seen = set()
        
        # Stats
        self.total = 0
        self.accepted = 0
        self.rejected = 0
        self.duplicates = 0
        self.lengths = []
        self.domains = {}
        self.difficulties = {}
        self.quality_scores = []
        self.score_distribution = {"0-50": 0, "51-70": 0, "71-90": 0, "91-100": 0}

    def _near_hash(self, text: str) -> str:
        # Simple near-duplicate hash by removing spaces, punctuation, and lowering
        clean_text = re.sub(r'\W+', '', text.lower())
        return hashlib.sha256(clean_text.encode('utf-8')).hexdigest()

    def _exact_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def validate_sample(self, raw_line: str) -> Dict[str, Any]:
        self.total += 1
        result = {"valid": True, "reasons": [], "score": 100}

        # 1. UTF-8 Validation
        try:
            raw_line.encode('utf-8').decode('utf-8')
        except UnicodeError:
            result["valid"] = False
            result["reasons"].append("UTF-8 encoding error")
            result["score"] -= 100
            self._finalize_sample(result, 0)
            return result

        # 2. JSON schema validation
        try:
            sample = json.loads(raw_line)
        except json.JSONDecodeError:
            result["valid"] = False
            result["reasons"].append("Invalid JSON")
            result["score"] -= 100
            self._finalize_sample(result, 0)
            return result

        # 3. Required field validation
        # Determine dataset type
        if "chosen" in sample or "rejected" in sample:
            req_fields = ["instruction", "chosen", "rejected"]
        else:
            req_fields = ["instruction", "output"]
            
        for f in req_fields:
            if f not in sample:
                result["reasons"].append(f"Missing required field: {f}")
                result["score"] -= 50
                continue
            
            # 4. Empty field detection
            val = sample[f]
            if val is None or (isinstance(val, str) and not val.strip()):
                result["reasons"].append(f"Empty field: {f}")
                result["score"] -= 50

        # if already failing badly, abort further expensive checks
        if result["score"] < self.pass_threshold:
            result["valid"] = False
            self._finalize_sample(result, 0)
            return result

        # Extract textual content for length & dup checking
        text_content = " ".join([str(sample.get(f, "")) for f in req_fields])
        total_len = len(text_content)
        
        # 5. Length validation
        if total_len < self.min_length or total_len > self.max_length:
            result["reasons"].append(f"Length out of bounds: {total_len}")
            result["score"] -= 20
            
        # 6. Duplicate detection
        ehash = self._exact_hash(text_content)
        if ehash in self.exact_seen:
            result["reasons"].append("Exact duplicate")
            result["score"] -= 50
            self.duplicates += 1
        else:
            self.exact_seen.add(ehash)

        # 7. Near-duplicate detection
        nhash = self._near_hash(text_content)
        if nhash in self.near_seen and "Exact duplicate" not in result["reasons"]:
            result["reasons"].append("Near duplicate")
            result["score"] -= 20
        else:
            self.near_seen.add(nhash)
        
        # 8 & 9 & 10. Metadata, Domain, Difficulty validation
        domain = sample.get("domain", "general")
        self.domains[domain] = self.domains.get(domain, 0) + 1
        
        difficulty = sample.get("difficulty", "medium")
        if difficulty not in ["easy", "medium", "hard"]:
            result["reasons"].append("Invalid difficulty")
            result["score"] -= 10
        self.difficulties[difficulty] = self.difficulties.get(difficulty, 0) + 1
        
        if result["score"] < self.pass_threshold:
            result["valid"] = False

        self._finalize_sample(result, total_len)
        return result

    def _finalize_sample(self, result, length):
        self.lengths.append(length)
        self.quality_scores.append(result["score"])
        
        if result["score"] <= 50:
            self.score_distribution["0-50"] += 1
        elif result["score"] <= 70:
            self.score_distribution["51-70"] += 1
        elif result["score"] <= 90:
            self.score_distribution["71-90"] += 1
        else:
            self.score_distribution["91-100"] += 1
            
        if result["valid"]:
            self.accepted += 1
        else:
            self.rejected += 1

    def generate_report(self) -> str:
        avg_len = sum(self.lengths) / len(self.lengths) if self.lengths else 0
        dup_pct = (self.duplicates / self.total * 100) if self.total else 0
        
        report = f"""# Dataset Validation Report

## Overview
- **Total Samples**: {self.total}
- **Accepted**: {self.accepted}
- **Rejected**: {self.rejected}
- **Duplicate %**: {dup_pct:.2f}%
- **Average Length**: {avg_len:.2f} chars

## Domain Distribution
"""
        for d, c in sorted(self.domains.items(), key=lambda x: x[1], reverse=True):
            report += f"- **{d}**: {c}\n"
            
        report += "\n## Difficulty Distribution\n"
        for d, c in sorted(self.difficulties.items(), key=lambda x: x[1], reverse=True):
            report += f"- **{d}**: {c}\n"
            
        report += "\n## Quality Score Distribution\n"
        for bucket, count in self.score_distribution.items():
            report += f"- **{bucket}**: {count}\n"
            
        return report

if __name__ == "__main__":
    validator = DatasetValidator()
    path = Path("test_dataset.jsonl")
    if path.exists():
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if not line.strip(): continue
                validator.validate_sample(line)
        
        report = validator.generate_report()
        with open("DATASET_VALIDATION_REPORT.md", "w") as f:
            f.write(report)
        print("Validation report generated.")
