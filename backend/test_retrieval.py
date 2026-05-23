import os
from langchain_text_splitters import RecursiveCharacterTextSplitter

sample_text = "This is a document about a very specific topic. " * 5 + """
Let's introduce a critical piece of information that might get chopped up if we use a rigid boundary.
CRITICAL INFORMATION: The main passcode for the database is "SECURE-PASS-99". Keep this secret!
""" + "This is more padding text. " * 5

def fixed_size_chunking(text, chunk_size=100):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def recursive_chunking(text, chunk_size=100, chunk_overlap=25):
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_text(text)

def test():
    print("Testing Retrieval Quality Improvement")
    print("-" * 50)
    
    chunk_size = 100
    overlap = 25
    
    fixed_chunks = fixed_size_chunking(sample_text, chunk_size)
    recursive_chunks = recursive_chunking(sample_text, chunk_size, overlap)
    
    print("\n--- Fixed-size Chunks with Target ---")
    for i, c in enumerate(fixed_chunks):
        if "CRITICAL" in c or "SECURE-PASS-99" in c:
            print(f"Chunk {i}: {repr(c)}")
            
    print("\n--- Recursive Chunks with Target ---")
    for i, c in enumerate(recursive_chunks):
        if "CRITICAL" in c or "SECURE-PASS-99" in c:
            print(f"Chunk {i}: {repr(c)}")

if __name__ == "__main__":
    test()
