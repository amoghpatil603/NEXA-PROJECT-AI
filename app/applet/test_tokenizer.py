from backend.models.nexa_fm.bpe_tokenizer import NexaBPETokenizer

def test_tokenizer():
    texts = [
        "Hello world! This is the NEXA Foundation Model.",
        "Tokenization is fascinating.",
        "Testing unicode: 🚀 你好, мир!",
        "Handling whitespaces   and\nnewlines."
    ]
    
    tokenizer = NexaBPETokenizer(vocab_size=300)
    tokenizer.train(texts)
    
    # Test encode decode
    for text in texts:
        tokens = tokenizer.encode(text)
        decoded = tokenizer.decode(tokens)
        assert text == decoded, f"Failed on: {text}, got: {decoded}"
        
    # Test special tokens
    tokens = tokenizer.encode("Hello", add_special_tokens=True)
    assert tokens[0] == tokenizer.special_tokens["<BOS>"]
    assert tokens[-1] == tokenizer.special_tokens["<EOS>"]
    
    # Test unknown token fallback
    decoded_unk = tokenizer.decode([tokenizer.special_tokens["<UNK>"]], skip_special_tokens=False)
    assert decoded_unk == "<UNK>"
    
    # Test serialization
    tokenizer.save("test_vocab.json")
    loaded_tokenizer = NexaBPETokenizer.load("test_vocab.json")
    
    for text in texts:
        tokens1 = tokenizer.encode(text)
        tokens2 = loaded_tokenizer.encode(text)
        assert tokens1 == tokens2
        
    print("Tokenizer validation passed!")

if __name__ == "__main__":
    test_tokenizer()
