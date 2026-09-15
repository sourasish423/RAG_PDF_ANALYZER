from fastapi import FastAPI,UploadFile,File
import ollama
import shutil
from pydantic import BaseModel
from database import collection
from generate_answer import generate_answer
from read_pdf import process_pdf
from fastapi.middleware.cors import CORSMiddleware


app=FastAPI()

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
        n_results=3,
        where={"filename": data.filename}
    )
    #gets the relevant chunks

    documents=results["documents"][0]

    #ask llama to gen ans by sending question and chunks

    answer=generate_answer(
        data.question,
        documents
    )

    return {"answer": answer}


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