<<<<<<< HEAD
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

    # initialize both
    s = NexaBPETokenizer(vocab_size=300, min_frequency=1, special_tokens=SPECIAL)
    s.vocab = s._get_initial_vocab(); s.byte_to_id = {v: k for k, v in s.vocab.items()}
    ref_seqs = [s._text_to_byte_ids(p.read_text(encoding='utf-8', errors='replace')) for p in paths]
    ref_counts = Counter();
    for seq in ref_seqs: ref_counts.update(s._count_pairs(seq))

    inc = IncrementalBPETokenizer(vocab_size=300, min_frequency=1, special_tokens=SPECIAL)
    inc.vocab = inc._get_initial_vocab(); inc.byte_to_id = {v: k for k, v in inc.vocab.items()}
    inc_seqs = inc._load_sequences(paths)
    inc_counts = inc._initial_pair_counts(inc_seqs)

    for step in range(6):
        if step > 0:
            # apply same merge from previous step
            pair, freq = ref_counts.most_common(1)[0]
            new_id = len(s.vocab)
            s.vocab[new_id] = s.vocab[pair[0]] + s.vocab[pair[1]]
            s.merges[pair] = new_id; s.merges_order.append(pair)
            ref_seqs = [s._merge_pair(seq, pair, new_id) for seq in ref_seqs]
            ref_counts = Counter();
            for seq in ref_seqs: ref_counts.update(s._count_pairs(seq))
            inc.vocab[new_id] = inc.vocab[pair[0]] + inc.vocab[pair[1]]
            inc.merges[pair] = new_id; inc.merges_order.append(pair)
            inc_seqs = inc._apply_merge_incremental(inc_seqs, pair, new_id, inc_counts)
            # recompute ref and inc counts at same state

        print('STEP', step)
        print('ref best', ref_counts.most_common(1)[0])
        print('inc best', inc_counts.most_common(1)[0])
        print('ref order top 15', list(ref_counts.keys())[:15])
        print('inc order top 15', list(inc_counts.keys())[:15])
        print('ref top 15', ref_counts.most_common(15))
        print('inc top 15', inc_counts.most_common(15))
        print('---')
        if step < 5:
            # also compare counts equality
            print('counts equal', ref_counts == inc_counts)
            print('---')
=======
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

    # initialize both
    s = NexaBPETokenizer(vocab_size=300, min_frequency=1, special_tokens=SPECIAL)
    s.vocab = s._get_initial_vocab(); s.byte_to_id = {v: k for k, v in s.vocab.items()}
    ref_seqs = [s._text_to_byte_ids(p.read_text(encoding='utf-8', errors='replace')) for p in paths]
    ref_counts = Counter();
    for seq in ref_seqs: ref_counts.update(s._count_pairs(seq))

    inc = IncrementalBPETokenizer(vocab_size=300, min_frequency=1, special_tokens=SPECIAL)
    inc.vocab = inc._get_initial_vocab(); inc.byte_to_id = {v: k for k, v in inc.vocab.items()}
    inc_seqs = inc._load_sequences(paths)
    inc_counts = inc._initial_pair_counts(inc_seqs)

    for step in range(6):
        if step > 0:
            # apply same merge from previous step
            pair, freq = ref_counts.most_common(1)[0]
            new_id = len(s.vocab)
            s.vocab[new_id] = s.vocab[pair[0]] + s.vocab[pair[1]]
            s.merges[pair] = new_id; s.merges_order.append(pair)
            ref_seqs = [s._merge_pair(seq, pair, new_id) for seq in ref_seqs]
            ref_counts = Counter();
            for seq in ref_seqs: ref_counts.update(s._count_pairs(seq))
            inc.vocab[new_id] = inc.vocab[pair[0]] + inc.vocab[pair[1]]
            inc.merges[pair] = new_id; inc.merges_order.append(pair)
            inc_seqs = inc._apply_merge_incremental(inc_seqs, pair, new_id, inc_counts)
            # recompute ref and inc counts at same state

        print('STEP', step)
        print('ref best', ref_counts.most_common(1)[0])
        print('inc best', inc_counts.most_common(1)[0])
        print('ref order top 15', list(ref_counts.keys())[:15])
        print('inc order top 15', list(inc_counts.keys())[:15])
        print('ref top 15', ref_counts.most_common(15))
        print('inc top 15', inc_counts.most_common(15))
        print('---')
        if step < 5:
            # also compare counts equality
            print('counts equal', ref_counts == inc_counts)
            print('---')
>>>>>>> origin/main
