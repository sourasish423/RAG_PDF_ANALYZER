import ollama
from database import collection
from generate_answer import generate_answer

question=input("Ask a question")

#create an embedding for the question

response=ollama.embed(
    model="nomic-embed-text",
    input=question
)#question converted to embeddings

question_embedding=response["embeddings"][0]#taking the first question embedding and putting here

result=collection.query(
    query_embeddings=[question_embedding],
    n_results=3
)

print("\nRelevant chunks:\n")

for i, document in enumerate(result["documents"][0]):
    print(f"--- Result {i + 1} ---")
    print(document)

answer=generate_answer(
    question,
    result["documents"][0]
    )

print("\nAnswer:")
print(answer)