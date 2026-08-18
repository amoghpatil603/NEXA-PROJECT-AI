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

    # Reference initial pair counts and first merge sequence transformation
    ref = NexaBPETokenizer(vocab_size=300, min_frequency=1, special_tokens=SPECIAL)
    ref.vocab = ref._get_initial_vocab()
    ref.byte_to_id = {v: k for k, v in ref.vocab.items()}
    ref_seq = [ref._text_to_byte_ids(p.read_text(encoding='utf-8', errors='replace')) for p in paths]
    ref_counts = Counter()
    for seq in ref_seq:
        ref_counts.update(ref._count_pairs(seq))
    first_pair, first_count = ref_counts.most_common(1)[0]
    print('ref first pair', first_pair, first_count)

    new_id = len(ref.vocab)
    ref_seq = [ref._merge_pair(seq, first_pair, new_id) for seq in ref_seq]
    ref_counts2 = Counter()
    for seq in ref_seq:
        ref_counts2.update(ref._count_pairs(seq))
    print('ref after first merge top 10', ref_counts2.most_common(10))
    print('ref next best', ref_counts2.most_common(1)[0])

    # Incremental pair update after first merge
    inc = IncrementalBPETokenizer(vocab_size=300, min_frequency=1, special_tokens=SPECIAL)
    seqs = inc._load_sequences(paths)
    inc_counts = inc._initial_pair_counts(seqs)
    first_pair2, first_count2 = inc_counts.most_common(1)[0]
    print('inc first pair', first_pair2, first_count2)
    inc_new_id = len(inc.vocab)
    seqs2 = inc._apply_merge_incremental(seqs, first_pair2, inc_new_id, inc_counts)
    print('inc after first merge top 10', inc_counts.most_common(10))
    print('inc next best', inc_counts.most_common(1)[0])
    print('counts equal after first merge', inc_counts == ref_counts2)
    print('seqs equal after first merge', [list(s) for s in seqs2] == [list(s) for s in ref_seq])
