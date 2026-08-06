import os
import json
from typing import Dict, Any, List, Optional
from .loaders import DatasetLoader
from .cleaners import TextCleaner
from .filters import DatasetFilter
from .dedup import Deduplicator
from .sharding import DatasetSharder

class DatasetPipeline:
    def __init__(
        self,
        input_dir: str,
        output_dir: str,
        shard_size: int = 10000,
        min_length: int = 50,
        max_length: int = 100000,
        allowed_languages: Optional[List[str]] = None,
        use_near_dedup: bool = False
    ):
        self.input_dir = input_dir
        self.output_dir = output_dir
        
        self.loader = DatasetLoader(input_dir)
        self.cleaner = TextCleaner()
        self.filter = DatasetFilter(min_length=min_length, max_length=max_length, allowed_languages=allowed_languages)
        self.deduplicator = Deduplicator(use_near_dedup=use_near_dedup)
        self.sharder = DatasetSharder(output_dir=output_dir, shard_size=shard_size)
        
        self.stats = {
            "total_documents": 0,
            "processed_documents": 0,
            "failed_cleaning": 0,
        }

    def run(self):
        print(f"Starting pipeline on {self.input_dir}")
        for item in self.loader.scan_and_load():
            self.stats["total_documents"] += 1
            
            # 1. Clean
            cleaned_item = self.cleaner.clean(item)
            if cleaned_item is None:
                self.stats["failed_cleaning"] += 1
                continue
                
            # 2. Filter
            filtered_item = self.filter.filter_item(cleaned_item)
            if filtered_item is None:
                continue
                
            # 3. Deduplicate
            dedup_item = self.deduplicator.check_and_add(filtered_item)
            if dedup_item is None:
                continue
                
            # 4. Save to Shards
            self.sharder.write(dedup_item)
            self.stats["processed_documents"] += 1
            
        self.sharder.close()
        self._save_report()
        print("Pipeline finished.")
        print(self._generate_report_str())

    def _generate_report_str(self) -> str:
        report = []
        report.append("--- Dataset Pipeline Report ---")
        report.append(f"Total documents found: {self.stats['total_documents']}")
        report.append(f"Successfully processed: {self.stats['processed_documents']}")
        report.append(f"Failed cleaning: {self.stats['failed_cleaning']}")
        report.append(f"Rejected by length: {self.filter.stats['rejected_length']}")
        report.append(f"Rejected by language: {self.filter.stats['rejected_lang']}")
        report.append(f"Rejected by repetition: {self.filter.stats['rejected_repetition']}")
        report.append(f"Exact duplicates removed: {self.deduplicator.stats['exact_duplicates']}")
        report.append(f"Near duplicates removed: {self.deduplicator.stats['near_duplicates']}")
        return "\n".join(report)

    def _save_report(self):
        report_data = {
            "pipeline_stats": self.stats,
            "filter_stats": self.filter.stats,
            "deduplicator_stats": self.deduplicator.stats
        }
        with open(os.path.join(self.output_dir, "report.json"), "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)

    def stream_dataset(self):
        return self.sharder.stream_shards(self.output_dir)
