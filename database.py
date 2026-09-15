import chromadb

# Created a persistent ChromaDB database
client=chromadb.PersistentClient(path="./chroma_db")

collection=client.get_or_create_collection(
    name="documents_v2"
)

def store_documents(chunks,embeddings,filename):
    ids = [f"{filename}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"filename": filename} for _ in chunks]
    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas
        
    )
    print("Stored", len(chunks), "chunks in ChromaDB")
