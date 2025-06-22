from langchain.text_splitter import RecursiveCharacterTextSplitter

def chunk_text(text):
    # Return the entire text as a single chunk
    return [text]

# Alternative: If you want to keep the original function but add a new one
def chunk_text_single(text):
    """Chunk text as a single chunk (entire file as one chunk)"""
    return [text]

def chunk_text_multiple(text):
    """Original chunking function that splits text into multiple chunks"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " "]
    )
    return splitter.split_text(text)
