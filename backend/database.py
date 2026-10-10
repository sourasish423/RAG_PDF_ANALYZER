import chromadb

# Created a persistent ChromaDB database
client=chromadb.PersistentClient(path="./chroma_db")

collection=client.get_or_create_collection(
    name="documents_v2"
)

def store_documents(chunks,embeddings,filename,chunk_pages):
    ids = [f"{filename}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{
                "filename": filename,
                   "page":page
                }
                   for page in chunk_pages
                   ]
    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas
        
    )
    print("Stored", len(chunks), "chunks in ChromaDB")

    #"Search ChromaDB for this filename. 
    # If at least one chunk exists, return True; otherwise return False."

def document_exists(filename):

    results=collection.get(
        where={"filename":filename},
        limit=1
    )
    return len(results["ids"]) > 0
