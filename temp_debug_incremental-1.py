import tempfile
from pathlib import Path
from collections import Counter
from tokenizer.bpe_tokenizer import NexaBPETokenizer
from tokenizer.incremental_bpe import IncrementalBPETokenizer

SPECIAL = {
    "<PAD>": 0,
    "<BOS>": 1,
    "<EOS>": 2,
    "<UNK>": 3,
}

texts = [
    "Hello world! Hello world!",
    "こんにちは 世界! こんにちは 世界!",
    "aaab aaab aaac aaac",
]

with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    paths = []
    for i, txt in enumerate(texts):
        p = td / f"f{i}.txt"
        p.write_text(txt, encoding="utf-8")
        paths.append(p)

    ref = NexaBPETokenizer(vocab_size=300, min_frequency=1, special_tokens=SPECIAL)
    ref_counts = Counter()
    for p in paths:
        txt = p.read_text(encoding="utf-8", errors="replace")
        seq = ref._text_to_byte_ids(txt)
        ref_counts.update(ref._count_pairs(seq))

    print("ref top 10", ref_counts.most_common(10))
    print("ref best", ref_counts.most_common(1)[0])

    inc = IncrementalBPETokenizer(vocab_size=300, min_frequency=1, special_tokens=SPECIAL)
    seqs = inc._load_sequences(paths)
    inc_counts = inc._initial_pair_counts(seqs)
    print("inc top 10", inc_counts.most_common(10))
    print("inc best", inc_counts.most_common(1)[0])
    print("counts equal", ref_counts == inc_counts)
