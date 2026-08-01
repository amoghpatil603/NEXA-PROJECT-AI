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

    # set up incremental object and load sequences
    inc = IncrementalBPETokenizer(vocab_size=300, min_frequency=1, special_tokens=SPECIAL)
    inc.vocab = inc._get_initial_vocab(); inc.byte_to_id = {v:k for k,v in inc.vocab.items()}
    seqs = inc._load_sequences(paths)
    counts = inc._initial_pair_counts(seqs)

    # apply first 5 merges same as reference
    merges = []
    for step in range(5):
        pair, freq = counts.most_common(1)[0]
        merges.append(pair)
        new_id = len(inc.vocab)
        inc.vocab[new_id] = inc.vocab[pair[0]] + inc.vocab[pair[1]]
        inc.merges[pair] = new_id; inc.merges_order.append(pair)
        seqs = inc._apply_merge_incremental(seqs, pair, new_id, counts)
    print('applied merges', merges)
    # now compute pair_counts from current seqs
    recomputed = Counter()
    for seq in seqs:
        recomputed.update(inc._count_pairs(seq))
    print('recomputed top 15', recomputed.most_common(15))
    print('current incremental pair_counts top 15', counts.most_common(15))
    maxc = counts.most_common(1)[0][1]
    tie_candidates = [p for p,c in counts.items() if c==maxc]
    print('tie candidates', tie_candidates)
    best_pair_recomputed = recomputed.most_common(1)[0]
    print('recomputed best', best_pair_recomputed)
    # show whether our selection logic picks recomputed best when tie exists
    if len(tie_candidates)>1:
        print('tie exists, recomputed best ->', best_pair_recomputed)
    else:
        print('no tie, selection is', counts.most_common(1)[0])
