import os
import io
import chromadb
from PyPDF2 import PdfReader
from openai import AsyncOpenAI
import traceback
from langchain_text_splitters import RecursiveCharacterTextSplitter

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="personal_knowledge")

_knowledge_cache = {}

async def process_document(file_content: bytes, filename: str) -> int:
    global _knowledge_cache
    _knowledge_cache.clear() # Clear cache when new docs are uploaded
    
    try:
        splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
        docs = []
        metadatas = []
        ids = []
        global_idx = 0
        
        if filename.lower().endswith('.pdf'):
            pdf = PdfReader(io.BytesIO(file_content))
            for page_num, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    chunks = splitter.split_text(page_text)
                    for chunk in chunks:
                        docs.append(f"Source: {filename} (Page {page_num})\n\n{chunk}")
                        metadatas.append({
                            "source": filename,
                            "page": page_num,
                            "chunk_index": global_idx
                        })
                        ids.append(f"{filename}_{global_idx}")
                        global_idx += 1
        else:
            # Assume plain text / markdown
            text = file_content.decode('utf-8')
            if text.strip():
                chunks = splitter.split_text(text)
                for chunk in chunks:
                    docs.append(f"Source: {filename}\n\n{chunk}")
                    metadatas.append({
                        "source": filename,
                        "page": 1,
                        "chunk_index": global_idx
                    })
                    ids.append(f"{filename}_{global_idx}")
                    global_idx += 1
            
        if not docs:
            return 0
            
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
