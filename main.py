from fastapi import FastAPI
import ollama
from pydantic import BaseModel
from database import collection
from generate_answer import generate_answer

app=FastAPI()

class Question(BaseModel):
    question:str

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
        n_results=3
    )
    #gets the relevant chunks

    documents=results["documents"][0]

    #ask llama to gen ans by sending question and chunks

    answer=generate_answer(
        data.question,
        documents
    )

    return {"answer": answer}
   
