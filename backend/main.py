from fastapi import FastAPI, UploadFile, File, HTTPException
import ollama
import shutil
import os
from pydantic import BaseModel
from database import collection,document_exists
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

@app.post("/ask")
def ask_question(data:Question):
    #converting the question coming from frontend into embedding

    response=ollama.embed(
    model="nomic-embed-text",
    input=data.question #question recieving from frontend
)
    question_embedding=response["embeddings"][0]

# searching chromadb 

    results=collection.query(
        query_embeddings=[question_embedding],
        n_results=3,#3most popular chunks
        where={"filename": data.filename},

        # include=["distances"]# for knowing the distance of chunks
    )

# Check whether ChromaDB found any matching chunks
    if not results["documents"] or not results["documents"][0]:
        return {
            "answer": "No matching chunks found. Please check that the filename matches the uploaded PDF.",
            "sources": []
            }

    #gets the relevant chunks

    documents=results["documents"][0]
    #along with chunks i want to print the meatadatas such as from which page the ans is given
    metadatas = results["metadatas"][0]
    distances=results["distances"][0]

    print("Retrieved metadata:", metadatas)
    print("Retrieved distance:", distances)


    #ask llama to gen ans by sending question and chunks

    if distances[0] > 1.0:
        return {
        "answer": "I couldn't find that information in the document.",
        "sources": []
             }

    answer=generate_answer(
        data.question,
        documents
    )

    return {"answer": answer,
            "sources": metadatas}



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
