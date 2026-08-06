# Vocabulary Specification

## Overview
The NEXA Tokenizer vocabulary is fully configurable. It starts with a fixed base and expands dynamically during training to reach any target vocabulary size (e.g., 8K, 16K, 32K, 50K).

## Token ID Layout

The token IDs are allocated deterministically to ensure forward compatibility:

1. **Special Tokens (IDs 0-4)**
   - `0`: `<PAD>` - Used to pad sequences for batch processing.
   - `1`: `<BOS>` - Beginning of sequence.
   - `2`: `<EOS>` - End of sequence.
   - `3`: `<UNK>` - Unknown token (reserved for legacy compatibility or forced corruption; naturally avoided by byte-level fallback).
   - `4`: `<MASK>` - Mask token, reserved for bidirectional or masked language modeling objectives if explored later.

2. **Base Vocabulary (IDs 5-260)**
   - Represents all 256 possible byte values (0x00 to 0xFF).
   - Guarantees that any arbitrary string can be tokenized.

3. **Merged Tokens (IDs 261+)**
   - Sequentially assigned IDs for byte-pair merges identified during training.
   - The final ID corresponds to `vocab_size - 1`.

## Configurability
The `NexaBPETokenizer` class accepts a `vocab_size` parameter. The vocabulary size can be seamlessly adjusted during training without needing to modify any internal encoding/decoding logic.
