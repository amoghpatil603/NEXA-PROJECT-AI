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
    first_pair, _ = ref_counts.most_common(1)[0]
    new_id = len(ref.vocab)
    ref_new_seqs = [ref._merge_pair(seq, first_pair, new_id) for seq in ref_seqs]
    ref_counts2 = Counter()
    for seq in ref_new_seqs:
        ref_counts2.update(ref._count_pairs(seq))

    # incremental
    inc = IncrementalBPETokenizer(vocab_size=300, min_frequency=1, special_tokens=SPECIAL)
    inc_seqs = inc._load_sequences(paths)
    inc_counts = inc._initial_pair_counts(inc_seqs)
    inc_new_seqs = inc._apply_merge_incremental(inc_seqs, first_pair, len(inc.vocab), inc_counts)
    inc_counts2 = Counter()
    for seq in inc_new_seqs:
        inc_counts2.update(inc._count_pairs(seq))

    print('ref seq0', list(ref_new_seqs[0]))
    print('inc seq0', list(inc_new_seqs[0]))
    print('seq0 equal', list(ref_new_seqs[0]) == list(inc_new_seqs[0]))
    print('ref seq1', list(ref_new_seqs[1]))
    print('inc seq1', list(inc_new_seqs[1]))
    print('seq1 equal', list(ref_new_seqs[1]) == list(inc_new_seqs[1]))
    print('ref seq2', list(ref_new_seqs[2]))
    print('inc seq2', list(inc_new_seqs[2]))
    print('seq2 equal', list(ref_new_seqs[2]) == list(inc_new_seqs[2]))

    print('ref counts2 top 20', ref_counts2.most_common(20))
    print('inc counts2 top 20', inc_counts2.most_common(20))
    print('counts2 equal', ref_counts2 == inc_counts2)
    print('inc_counts mutated equals ref_counts2?', inc_counts == ref_counts2)
    print('inc_counts2 computed equals inc_counts? ', inc_counts2 == inc_counts)

    def diff(c1,c2):
        keys = set(c1) | set(c2)
        return [(k, c1.get(k,0), c2.get(k,0)) for k in keys if c1.get(k,0)!=c2.get(k,0)]

    print('diff after first merge:', diff(ref_counts2, inc_counts2))
    print('diff mutated pair counts vs recompute:', diff(ref_counts2, inc_counts))
