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

    # reference
    ref = NexaBPETokenizer(vocab_size=300, min_frequency=1, special_tokens=SPECIAL)
    ref.vocab = ref._get_initial_vocab()
    ref.byte_to_id = {v: k for k, v in ref.vocab.items()}
    ref_seqs = [ref._text_to_byte_ids(p.read_text(encoding='utf-8', errors='replace')) for p in paths]
    ref_counts = Counter()
    for seq in ref_seqs:
        ref_counts.update(ref._count_pairs(seq))
    first_pair, first_count = ref_counts.most_common(1)[0]
    print('ref first pair', first_pair, first_count)
    new_id = len(ref.vocab)
    ref_seqs2 = [ref._merge_pair(seq, first_pair, new_id) for seq in ref_seqs]
    ref_counts2 = Counter()
    for seq in ref_seqs2:
        ref_counts2.update(ref._count_pairs(seq))

    # incremental
    inc = IncrementalBPETokenizer(vocab_size=300, min_frequency=1, special_tokens=SPECIAL)
    inc.vocab = inc._get_initial_vocab()
    inc.byte_to_id = {v: k for k, v in inc.vocab.items()}
    inc_seqs = inc._load_sequences(paths)
    inc_counts = inc._initial_pair_counts(inc_seqs)
    print('inc new_id', len(inc.vocab))
    inc_seqs2 = inc._apply_merge_incremental(inc_seqs, first_pair, len(inc.vocab), inc_counts)
    inc_counts2 = Counter()
    for seq in inc_seqs2:
        inc_counts2.update(inc._count_pairs(seq))

    print('seq0 equal', list(ref_seqs2[0]) == list(inc_seqs2[0]))
    print('seq1 equal', list(ref_seqs2[1]) == list(inc_seqs2[1]))
    print('seq2 equal', list(ref_seqs2[2]) == list(inc_seqs2[2]))
    print('inc counts equal', inc_counts2 == ref_counts2)
    print('inc counts mutated equals recomputed', inc_counts == inc_counts2)
    print('ref counts2 top 10', ref_counts2.most_common(10))
    print('inc counts2 top 10', inc_counts2.most_common(10))
    print('inc mutated top 10', inc_counts.most_common(10))
