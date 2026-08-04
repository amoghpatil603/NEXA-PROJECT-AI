import tempfile
from pathlib import Path
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

    s = NexaBPETokenizer(vocab_size=300, min_frequency=1, special_tokens=SPECIAL)
    s.train(paths, verbose=False)

    it = IncrementalBPETokenizer(vocab_size=300, min_frequency=1, special_tokens=SPECIAL)
    it.train(paths, verbose=False)

    print('s merges first 10', s.merges_order[:10])
    print('it merges first 10', it.merges_order[:10])
    print('s vocab len', len(s.vocab), 'it vocab len', len(it.vocab))
    print('same tokens', set(s.vocab.values()) == set(it.vocab.values()))
    sample = 'Hello world! こんにちは aaab'
    se = s.encode(sample)
    ie = it.encode(sample)
    print('same encoding', se == ie)
    print('s enc', se)
    print('it enc', ie)
    print('s decode', s.decode(se))
    print('it decode', it.decode(ie))
    print('same decoding', s.decode(se) == it.decode(ie))
    print('first 5 merge counts')
    for idx, pair in enumerate(s.merges_order[:5]):
        print(idx, pair, s.merges[pair], it.merges.get(pair), it.merges_order[idx] if idx < len(it.merges_order) else None)
