import os
import shutil
import tempfile
import chromadb
from git import Repo
from openai import AsyncOpenAI
import traceback
from langchain_text_splitters import RecursiveCharacterTextSplitter

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize ChromaDB client (persistent storage locally)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="repo_intelligence")

ALLOWED_EXTENSIONS = {'.py', '.js', '.jsx', '.ts', '.tsx', '.md', '.html', '.css'}

# Basic in-memory cache for queries to save API credits and respond faster
_query_cache = {}

def get_files_to_index(repo_path: str):
    file_paths = []
    for root, dirs, files in os.walk(repo_path):
        # Skip hidden directories like .git
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext in ALLOWED_EXTENSIONS:
                file_paths.append(os.path.join(root, file))
    return file_paths

async def index_repository(repo_url: str) -> int:
    global _query_cache
    _query_cache.clear() # Clear cache when new data is indexed
    
    temp_dir = tempfile.mkdtemp()
    try:
        print(f"Cloning {repo_url} into {temp_dir}...")
        Repo.clone_from(repo_url, temp_dir)
        
        files = get_files_to_index(temp_dir)
        print(f"Found {len(files)} files to index.")
        
        docs = []
        metadatas = []
        ids = []
        
        splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=400)
        
        for idx, file_path in enumerate(files):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                chunks = splitter.split_text(content)
                
                rel_path = os.path.relpath(file_path, temp_dir)
                for c_idx, chunk in enumerate(chunks):
                    docs.append(f"File: {rel_path}\n\n{chunk}")
                    metadatas.append({"file": rel_path})
                    ids.append(f"{repo_url}_{rel_path}_{c_idx}")
                    
            except Exception as e:
                print(f"Failed to read {file_path}: {e}")

        if docs:
            # Generate embeddings
            print("Generating embeddings...")
            response = await client.embeddings.create(
                input=docs,
                model="text-embedding-3-small"
            )
            embeddings = [data.embedding for data in response.data]
            
            print("Adding to ChromaDB...")
            collection.upsert(
                documents=docs,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
        return len(docs)
    except Exception as e:
        print(f"Error indexing repo: {e}")
        traceback.print_exc()
        raise e
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

async def query_repository(query: str) -> str:
    if collection.count() == 0:
        return "No repositories have been indexed yet."
        
    # Check cache first
    normalized_query = query.strip().lower()
    if normalized_query in _query_cache:
        print("Returning cached answer for:", query)
        return _query_cache[normalized_query]
        
    try:
        # Embed query
        response = await client.embeddings.create(
            input=[query],
            model="text-embedding-3-small"
        )
        query_embedding = response.data[0].embedding
        
        # Query ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=15
        )
        
        if not results['documents'] or not results['documents'][0]:
            return "No relevant code snippets found."
            
        context = "\n\n---\n\n".join(results['documents'][0])
        
        prompt = f"""
        You are a Repository Intelligence Agent. Answer the user's question based on the provided code snippets. 
        You are allowed to infer general project details (like what the project is about) from the filenames, imports, and code structure provided.
        If the snippets are completely irrelevant and you cannot deduce an answer, say "I don't have enough context in the indexed repository to answer this."
        
        Code Context:
        {context}
        
        Question: {query}
        """
        
        completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        answer = completion.choices[0].message.content
        
        # Save to cache
        _query_cache[normalized_query] = answer
        return answer
        
    except Exception as e:
        print(f"Error querying repo: {e}")
        return "An error occurred while querying the repository."
