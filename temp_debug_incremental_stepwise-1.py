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

    # Reference in-memory training stepwise
    s = NexaBPETokenizer(vocab_size=300, min_frequency=1, special_tokens=SPECIAL)
    s.vocab = s._get_initial_vocab()
    s.byte_to_id = {v: k for k, v in s.vocab.items()}
    ref_seqs = [s._text_to_byte_ids(p.read_text(encoding='utf-8', errors='replace')) for p in paths]
    ref_counts = Counter()
    for seq in ref_seqs:
        ref_counts.update(s._count_pairs(seq))

    inc = IncrementalBPETokenizer(vocab_size=300, min_frequency=1, special_tokens=SPECIAL)
    inc.vocab = inc._get_initial_vocab()
    inc.byte_to_id = {v: k for k, v in inc.vocab.items()}
    inc_seqs = inc._load_sequences(paths)
    inc_counts = inc._initial_pair_counts(inc_seqs)

    for step in range(15):
        if not ref_counts or not inc_counts:
            break
        ref_best, ref_freq = ref_counts.most_common(1)[0]
        inc_best, inc_freq = inc_counts.most_common(1)[0]
        print(f"STEP {step}: ref_best={ref_best} freq={ref_freq}; inc_best={inc_best} freq={inc_freq}")
        if ref_best != inc_best or ref_freq != inc_freq:
            print('DIVERGENCE AT SELECTION')
            break
        new_id = len(s.vocab)
        s.vocab[new_id] = s.vocab[ref_best[0]] + s.vocab[ref_best[1]]
        s.merges[ref_best] = new_id
        s.merges_order.append(ref_best)
        ref_seqs = [s._merge_pair(seq, ref_best, new_id) for seq in ref_seqs]
        ref_counts = Counter()
        for seq in ref_seqs:
            ref_counts.update(s._count_pairs(seq))

        inc.vocab[new_id] = inc.vocab[ref_best[0]] + inc.vocab[ref_best[1]]
        inc.merges[ref_best] = new_id
        inc.merges_order.append(ref_best)
        inc_seqs = inc._apply_merge_incremental(inc_seqs, ref_best, new_id, inc_counts)

        if [list(x) for x in ref_seqs] != [list(x) for x in inc_seqs]:
            print('DIVERGENCE AFTER MERGE', step)
            for idx, (r, i) in enumerate(zip(ref_seqs, inc_seqs)):
                if list(r) != list(i):
                    print('seq', idx, 'ref', list(r), 'inc', list(i))
                    break
            break
        print('  sequences equal after merge')
    print('done')
