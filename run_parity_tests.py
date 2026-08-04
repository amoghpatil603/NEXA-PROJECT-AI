"""
Differential Parity Testing Suite for IncrementalBPETokenizer vs NexaBPETokenizer.
"""

import json
import time
import unittest
from pathlib import Path
from typing import Dict, List, Tuple

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent / "nexa-model"))

from tokenizer.bpe_tokenizer import NexaBPETokenizer
from tokenizer.incremental_bpe import IncrementalBPETokenizer


# Synthetic corpora generators
def get_synthetic_corpora() -> Dict[str, List[str]]:
    return {
        "ascii_prose": [
            "The quick brown fox jumps over the lazy dog.",
            "Pack my box with five dozen liquor jugs.",
            "How vexingly quick waft zephyr vanquish jack.",
            "Sphinx of black quartz, judge my vow.",
        ],
        "utf8_multilingual": [
            "Bonjour le monde! Comment ça va aujourd'hui?",
            "Hola mundo! ¿Cómo estás hoy?",
            "こんにちは世界！今日の調子はどうですか？",
            "Hallo Welt! Wie geht es dir heute?",
            "你好世界！今天感觉怎么样？",
            "Привет, мир! Как Ваши дела сегодня?",
        ],
        "repetitive_patterns": [
            "banana " * 100,
            "ab" * 250,
            "aaaaa" * 100,
            "abc" * 150 + "xyz" * 150,
            "1234567890" * 50,
        ],
        "code_snippets": [
            "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)\n",
            "#include <iostream>\nint main() {\n    std::cout << \"Hello NEXA!\" << std::endl;\n    return 0;\n}\n",
            "function sum(a, b) {\n  return a + b;\n}\nconsole.log(sum(5, 10));\n",
        ],
        "edge_cases": [
            "a",
            "b",
            "a b c d e f g h i j k l m n o p q r s t u v w x y z",
            "",
            "   \n\t   ",
            "x" * 1000,
            "!!???@@@###$$$%%%^^^&&&***((()))",
        ]
    }


def test_corpus_parity(name: str, docs: List[str], target_vocab: int = 350, min_freq: int = 2) -> dict:
    t0 = time.perf_counter()
    ref_tok = NexaBPETokenizer(vocab_size=target_vocab, min_frequency=min_freq)
    ref_tok.train(docs)
    t1 = time.perf_counter()

    inc_tok = IncrementalBPETokenizer(vocab_size=target_vocab, min_frequency=min_freq)
    inc_tok.train(docs)
    t2 = time.perf_counter()

    merges_match = (ref_tok.merges == inc_tok.merges)
    vocab_match = (ref_tok.vocab == inc_tok.vocab)
    ranks_match = (ref_tok.merge_ranks == inc_tok.merge_ranks)

    encode_matches = True
    decode_matches = True

    for doc in docs:
        if not doc:
            continue
        ref_enc = ref_tok.encode(doc)
        inc_enc = inc_tok.encode(doc)
        if ref_enc != inc_enc:
            encode_matches = False

        ref_dec = ref_tok.decode(ref_enc)
        inc_dec = inc_tok.decode(inc_enc)
        if ref_dec != inc_dec:
            decode_matches = False

    passed = merges_match and vocab_match and ranks_match and encode_matches and decode_matches

    return {
        "corpus_name": name,
        "docs_count": len(docs),
        "total_chars": sum(len(d) for d in docs),
        "merges_count": len(ref_tok.merges),
        "merges_match": merges_match,
        "vocab_match": vocab_match,
        "ranks_match": ranks_match,
        "encode_matches": encode_matches,
        "decode_matches": decode_matches,
        "passed": passed,
        "ref_time_sec": round(t1 - t0, 4),
        "inc_time_sec": round(t2 - t1, 4),
    }


def main():
    # 1. Run unit test suite
    print("Running unit test suite (nexa-model/tests/test_incremental_bpe.py)...")
    loader = unittest.TestLoader()
    suite = loader.discover("nexa-model/tests")
    runner = unittest.TextTestRunner(verbosity=1)
    test_result = runner.run(suite)
    unit_tests_passed = test_result.wasSuccessful()

    # 2. Run differential tests on synthetic corpora
    print("\nRunning differential parity tests on synthetic corpora...")
    corpora = get_synthetic_corpora()
    diff_results = []
    all_diff_passed = True

    for name, docs in corpora.items():
        res = test_corpus_parity(name, docs, target_vocab=350, min_freq=2)
        diff_results.append(res)
        if not res["passed"]:
            all_diff_passed = False
        print(f"  [{'PASS' if res['passed'] else 'FAIL'}] {name}: merges={res['merges_count']}, ref_time={res['ref_time_sec']}s, inc_time={res['inc_time_sec']}s")

    report_data = {
        "phase": "3F.1B",
        "description": "IncrementalBPETokenizer Parity and Differential Testing Report",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "unit_tests_run": test_result.testsRun,
        "unit_tests_passed": unit_tests_passed,
        "differential_tests_passed": all_diff_passed,
        "overall_parity_certified": unit_tests_passed and all_diff_passed,
        "synthetic_corpora_results": diff_results,
    }

    out_path = Path("data/reports/phase3f1b_parity_test.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    print(f"\nSaved parity test report to {out_path}")
    if unit_tests_passed and all_diff_passed:
        print("ALL PARITY AND DIFFERENTIAL TESTS CERTIFIED PASSED (100% PARITY)!")
    else:
        print("PARITY TEST FAILURE DETECTED!")
        sys.exit(1)


if __name__ == "__main__":
    main()
