#here i am using the question and retrieved chunks to llm to generate the ans
import ollama

def generate_answer(question,documents):
    context="\n\n".join(documents)

    prompt=f"""
Answer the question using only the information
provided in the context.

Context:
{context}

Question:
{question}

Answer:
"""

    response=ollama.chat(
        model="llama3.2",
        messages=[
            {
                "role":"user",
                "content":prompt
            }
        ]
    )

    return response["message"]["content"]