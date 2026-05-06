import os
import io
import chromadb
from PyPDF2 import PdfReader
from openai import AsyncOpenAI
import traceback

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="personal_knowledge")

_knowledge_cache = {}

async def process_document(file_content: bytes, filename: str) -> int:
    global _knowledge_cache
    _knowledge_cache.clear() # Clear cache when new docs are uploaded
    
    try:
        text = ""
        if filename.lower().endswith('.pdf'):
            pdf = PdfReader(io.BytesIO(file_content))
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        else:
            # Assume plain text / markdown
            text = file_content.decode('utf-8')
            
        if not text.strip():
            return 0
            
        # Chunk text (~1500 chars per chunk)
        chunk_size = 1500
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        
        docs = []
        metadatas = []
        ids = []
        
        for idx, chunk in enumerate(chunks):
            docs.append(f"Source: {filename}\n\n{chunk}")
            metadatas.append({"source": filename})
            ids.append(f"{filename}_{idx}")
            
        # Generate embeddings
        response = await client.embeddings.create(
            input=docs,
            model="text-embedding-3-small"
        )
        embeddings = [data.embedding for data in response.data]
        
        collection.upsert(
            documents=docs,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        return len(docs)
    except Exception as e:
        print(f"Error processing document {filename}: {e}")
        traceback.print_exc()
        raise e

async def query_knowledge(query: str) -> str:
    if collection.count() == 0:
        return "You haven't uploaded any documents to your knowledge base yet."
        
    normalized_query = query.strip().lower()
    if normalized_query in _knowledge_cache:
        return _knowledge_cache[normalized_query]
        
    try:
        response = await client.embeddings.create(
            input=[query],
            model="text-embedding-3-small"
        )
        query_embedding = response.data[0].embedding
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=5
        )
        
        if not results['documents'] or not results['documents'][0]:
            return "No relevant information found in your documents."
            
        context = "\n\n---\n\n".join(results['documents'][0])
        
        prompt = f"""
        You are a Personal Knowledge Agent. Answer the user's question based ONLY on their uploaded documents provided below.
        If the answer is not contained in the documents, tell the user politely.
        
        Documents Context:
        {context}
        
        Question: {query}
        """
        
        completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        answer = completion.choices[0].message.content
        
        _knowledge_cache[normalized_query] = answer
        return answer
        
    except Exception as e:
        print(f"Error querying knowledge: {e}")
        return "An error occurred while querying your personal knowledge base."
