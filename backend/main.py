from fastapi import FastAPI, UploadFile, File, HTTPException
from reranker import rerank_chunks
import ollama
import shutil
import os
from pydantic import BaseModel
from database import collection, document_exists, search_bm25
from generate_answer import generate_answer
from read_pdf import process_pdf
from fastapi.middleware.cors import CORSMiddleware

# .\venv\Scripts\Activate.ps1


app=FastAPI()


def load_default_document():
    filename="Project_Overview.pdf"
    file_path = "documents/" + filename

    if document_exists(filename):
        print("Default document already exists in chromadb")

        return
    
    print("indexing default project document...")
    process_pdf(file_path)


load_default_document()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174","http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Question(BaseModel):
    question:str
    filename: str

@app.get("/")

def home():
    return {"message":"RAG backend is working!"}


def reciprocal_rank_fusion(vector_results, bm25_results, k=60):
    """Combine vector and BM25 rankings using RRF."""

    fused_scores = {}
    chunk_data = {}

    # Add scores from vector search
    for rank, item in enumerate(vector_results, start=1):
        document = item["document"]  # This extracts the chunk's text.
        key = document

        # The part fused_scores.get(key, 0) means: "Get the score this chunk already has, or use zero if it has no score yet."
        # That's important because later BM25 may find the same chunk and add another contribution.
        fused_scores[key] = fused_scores.get(key, 0) + 1 / (k + rank)
        chunk_data[key] = item

    # Add scores from BM25 search
    for rank, item in enumerate(bm25_results, start=1):
        document = item["document"]
        key = document

        fused_scores[key] = fused_scores.get(key, 0) + 1 / (k + rank)
        chunk_data[key] = item

    # Sort chunks by their combined score
    ranked_keys = sorted(
        fused_scores,
        key=lambda key: fused_scores[key],
        reverse=True,
    )

    return [chunk_data[key] for key in ranked_keys]


@app.post("/ask")
def ask_question(data: Question):
    # converting the question coming from frontend into embedding
    response = ollama.embed(
        model="nomic-embed-text",
        input=data.question,  # question receiving from frontend
    )
    question_embedding = response["embeddings"][0]

    # searching chromadb
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=10,  # 3 most popular chunks
        where={"filename": data.filename},
        # include=["distances"]# for knowing the distance of chunks
    )

    # Check whether ChromaDB found any matching chunks
    if not results["documents"] or not results["documents"][0]:
        return {
            "answer": "No matching chunks found. Please check that the filename matches the uploaded PDF.",
            "sources": [],
        }

    vector_results = []

    for i, document in enumerate(results["documents"][0]):
        vector_results.append({
            "document": document,
            "metadata": results["metadatas"][0][i],
        })

    bm25_results = search_bm25(
        data.question,
        data.filename,
        top_k=10,
    )

    
    print("\n=== VECTOR SEARCH RESULTS ===")
    for rank, item in enumerate(vector_results, start=1):
        print(f"Rank {rank}: {item['metadata']}")
        print(item["document"][:200])

    print("\n=== BM25 SEARCH RESULTS ===")
    for rank, item in enumerate(bm25_results, start=1):
        print(f"Rank {rank}: {item['metadata']}")
        print(item["document"][:200])


    # gets the relevant chunks

    # Combine the vector and BM25 search rankings
    fused_results = reciprocal_rank_fusion(
        vector_results,
        bm25_results,
    )


    
    print("\n=== COMBINED RRF RESULTS ===")
    for rank, item in enumerate(fused_results, start=1):
        print(f"Rank {rank}: {item['metadata']}")
        print(item["document"][:200])

    # Rerank all combined candidates using FlashRank
    candidate_documents = [
        item["document"] for item in fused_results
    ]

    candidate_metadatas = [
        item["metadata"] for item in fused_results
    ]

    reranked_results = rerank_chunks(
        data.question,
        candidate_documents,
        candidate_metadatas,
    )

    print("\n=== FLASHRANK RESULTS ===")

    for rank, item in enumerate(reranked_results, start=1):
        print(f"Rank {rank}: Score {item['score']:.4f}")
        print("Metadata:", item["meta"])
        print(item["text"][:200])

    # Keep the three highest-ranked chunks
    reranked_results = reranked_results[:3]

    # Extract text and metadata in the format used by the rest of main.py
    documents = [item["text"] for item in reranked_results]
    metadatas = [item["meta"] for item in reranked_results]

    

    for i, doc in enumerate(documents):
        print(f"\n--- Retrieved Chunk {i + 1} ---")
        print(doc)

    # along with chunks i want to print the metadata such as from which page the answer is given
    print("Retrieved metadata:", metadatas)

    # ask llama to gen answer by sending question and chunks
    # if distances[0] > 1.0:
    #     return {
    #     "answer": "I couldn't find that information in the document.",
    #     "sources": []
    #          }

    answer = generate_answer(
        data.question,
        documents,
    )

    unique_sources = []
    seen_pages = set()

    for metadata in metadatas:
        page = metadata.get("page")

        if page not in seen_pages:
            unique_sources.append(metadata)
            seen_pages.add(page)

    return {
        "answer": answer,
        "sources": unique_sources,
    }



@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    # Check that a file was provided
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Accept PDF files only
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Use only the filename, not any supplied directory path
    filename = os.path.basename(file.filename)
    file_path = os.path.join("documents", filename)

    try:
        # Save the uploaded PDF
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Extract text, create chunks and store embeddings
        number_of_chunks = process_pdf(file_path)

        if not number_of_chunks:
            raise HTTPException(
                status_code=422,
                detail="No readable text or chunks could be extracted from the PDF"
            )

        return {
            "filename": filename,
            "chunks": number_of_chunks,
            "message": "PDF received and processed successfully"
        }

    
    except HTTPException:
        raise

    except Exception as e:
        print(f"PDF processing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process the uploaded PDF"
        )

    finally:
        await file.close()
