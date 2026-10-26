import chromadb

from rank_bm25 import BM25Okapi
import re

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


def tokenize(text):
    """Convert text into lowercase word tokens."""
    return re.findall(r"\b[\w-]+\b", text.lower())


def search_bm25(question, filename, top_k=5):
    """Find document chunks using keyword relevance."""
    results = collection.get(
        where={"filename": filename},
        include=["documents", "metadatas"]
    )

    documents = results["documents"] or []
    metadatas = results["metadatas"] or []

    if not documents:
        return []

    tokenized_documents = [tokenize(doc) for doc in documents]
    bm25 = BM25Okapi(tokenized_documents)
    scores = bm25.get_scores(tokenize(question))

    ranked_indices = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True
    )

    matches = []
    for i in ranked_indices:
        if scores[i] <= 0:
            continue

        matches.append({
            "document": documents[i],
            "metadata": metadatas[i],
            "score": float(scores[i])
        })

        if len(matches) >= top_k:
            break

    return matches
