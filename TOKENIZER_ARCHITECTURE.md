# Tokenizer Architecture

## Design Overview
The NEXA Foundation Model uses a custom **Byte-Pair Encoding (BPE)** tokenizer operating directly at the byte level. This tokenizer completely avoids the need to predefine a comprehensive character vocabulary or rely on `<UNK>` tokens for out-of-vocabulary characters since all 256 possible byte values are included in the base vocabulary.

## Core Components
- **Tokenizer Trainer**: Computes the most frequent adjacent byte pairs and incrementally merges them until the target vocabulary size is reached.
- **Vocabulary Builder**: Constructs the mappings between integer token IDs and their corresponding byte sequences.
- **Encoder**: Converts strings to bytes, splits into words using a regex heuristic, and greedily applies learned merges.
- **Decoder**: Reconstructs the string by concatenating the byte sequences of token IDs, safely handling invalid utf-8 sequences via replacement characters.

## Features
- **Regex Word Boundaries**: Uses a simple regular expression to split text into words before applying BPE merges. This prevents merges across word boundaries, keeping semantic units intact.
- **Unicode Support**: By relying exclusively on utf-8 byte streams, the tokenizer losslessly encodes and decodes any Unicode string (emojis, CJK characters, non-Latin scripts) without needing dedicated vocabulary slots.
- **Whitespace Handling**: Trailing, leading, and continuous whitespaces are managed correctly through the regex rules and byte preservation.
