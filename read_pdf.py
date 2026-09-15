from pypdf import PdfReader
import ollama
import os
from database import store_documents


def process_pdf(file):

    # Read PDF
    filename = os.path.basename(file)
    reader = PdfReader(file)

    # Extract text from all pages
    full_text = ""

    for page_number, page in enumerate(reader.pages):
        text = page.extract_text() or ""

        print(f"Page {page_number + 1} extracted characters:", len(text))

        full_text += text + "\n"

    print("Total extracted characters:", len(full_text))

    # Stop if PDF has no readable text
    if not full_text.strip():
        raise ValueError(
            "Could not extract text from this PDF."
        )

    # Create chunks
    chunk_size = 500
    overlap = 50

    chunks = []
    start = 0

    while start < len(full_text):

        end = start + chunk_size

        chunk = full_text[start:end]

        if chunk.strip():
            chunks.append(chunk)

        start = end - overlap

    print("Created chunks:", len(chunks))

    # Create embeddings
    embeddings = []

    for chunk in chunks:

        response = ollama.embed(
            model="nomic-embed-text",
            input=chunk
        )

        embeddings.append(response["embeddings"][0])

    print("Created embeddings:", len(embeddings))

    # Store in ChromaDB
    store_documents(
        chunks,
        embeddings,
        filename
    )

    return len(chunks)