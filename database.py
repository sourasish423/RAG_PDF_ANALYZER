import chromadb

# Created a persistent ChromaDB database
client=chromadb.PersistentClient(path="./chroma_db")

collection=client.get_or_create_collection(
    name="documents"
)

def store_documents(chunks,embeddings):
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings
    )
    print("Stored", len(chunks), "chunks in ChromaDB")
