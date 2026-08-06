# Tokenizer Training Guide

## Pre-requisites
The NEXA Tokenizer requires raw text datasets representing the distributions the foundation model will encounter (e.g., source code, web text, domain-specific corpora).

## Training Process

1. **Initialization**: Instantiate the tokenizer with the desired final vocabulary size.
   ```python
   from backend.models.nexa_fm.bpe_tokenizer import NexaBPETokenizer
   tokenizer = NexaBPETokenizer(vocab_size=32000)
   ```

2. **Data Ingestion**: Pass an iterator of string documents into the `train` method.
   ```python
   def document_iterator(dataset):
       for doc in dataset:
           yield doc["text"]

   tokenizer.train(document_iterator(my_dataset))
   ```

3. **Incremental Merging**:
   - The tokenizer will split the corpus using its internal regex.
   - It computes byte-pair frequencies across the entire corpus.
   - It performs greedy merging incrementally until the offset + merges reaches the `vocab_size`.

4. **Saving the Vocabulary**:
   - The vocabulary mappings and merge rules must be saved to disk.
   - Serialization is handled via native JSON.
   ```python
   tokenizer.save("checkpoints/tokenizer.json")
   ```

5. **Loading the Vocabulary**:
   - At inference or training time, reload the configured tokenizer instantly.
   ```python
   tokenizer = NexaBPETokenizer.load("checkpoints/tokenizer.json")
   ```
