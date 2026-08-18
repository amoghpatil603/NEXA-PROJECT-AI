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
    # initial counts and first merge
    ref_counts = Counter()
    ref_sequences = []
    for p in paths:
        txt = p.read_text(encoding="utf-8", errors="replace")
        seq = ref._text_to_byte_ids(txt)
        ref_sequences.append(seq)
        ref_counts.update(ref._count_pairs(seq))

    print('ref initial best', ref_counts.most_common(1)[0])
    ref_best = ref_counts.most_common(1)[0][0]
    ref_new_id = len(ref.vocab)
    ref.vocab[ref_new_id] = ref.vocab[ref_best[0]] + ref.vocab[ref_best[1]]
    ref.merges[ref_best] = ref_new_id
    ref.merges_order.append(ref_best)
    ref_sequences = [ref._merge_pair(seq, ref_best, ref_new_id) for seq in ref_sequences]
    ref_counts2 = Counter()
    for seq in ref_sequences:
        ref_counts2.update(ref._count_pairs(seq))
    print('ref next top 10', ref_counts2.most_common(10))
    print('ref next best', ref_counts2.most_common(1)[0])

    inc = IncrementalBPETokenizer(vocab_size=300, min_frequency=1, special_tokens=SPECIAL)
    seqs = inc._load_sequences(paths)
    inc_counts = inc._initial_pair_counts(seqs)
    print('inc initial best', inc_counts.most_common(1)[0])
    inc_new_id = len(inc.vocab)
    inc.vocab[inc_new_id] = inc.vocab[ref_best[0]] + inc.vocab[ref_best[1]]
    inc.merges[ref_best] = inc_new_id
    inc.merges_order.append(ref_best)
    seqs2 = inc._apply_merge_incremental(seqs, ref_best, inc_new_id, inc_counts)
    print('inc next top 10', inc_counts.most_common(10))
    print('inc next best', inc_counts.most_common(1)[0])
    
    print('counts equal after first merge', inc_counts == ref_counts2)
    
    # compare sequences lengths and the first sequence
    print('ref seq0', list(ref_sequences[0])[:50])
    print('inc seq0', list(seqs2[0])[:50])
    print('ref seq0 len', len(ref_sequences[0]), 'inc seq0 len', len(seqs2[0]))
    print('seq0 equal', list(ref_sequences[0]) == list(seqs2[0]))
