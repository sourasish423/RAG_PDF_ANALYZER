from fastapi import FastAPI,UploadFile,File
import ollama
import shutil
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
    allow_origins=["http://localhost:5173"],
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
    file_path = "documents/" + file.filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

   

    number_of_chunks = process_pdf(file_path)

    return {
        "filename": file.filename,
        "chunks": number_of_chunks,
        "message": "PDF Received"
    }