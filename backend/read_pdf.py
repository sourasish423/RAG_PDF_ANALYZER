from pypdf import PdfReader
import ollama
import os
from database import store_documents


OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
client = ollama.Client(host=OLLAMA_HOST)


def process_pdf(file):

    # Read PDF
    filename = os.path.basename(file)
    reader = PdfReader(file)



    # Create chunks
    chunk_size = 500
    overlap = 50

    chunks = []
    chunk_pages = []

    # Extract and chunk page by page
    for page_number, page in enumerate(reader.pages):

        text = page.extract_text() or ""

        print(
            f"Page {page_number + 1} extracted characters:",
            len(text)
        )

        if not text.strip():
            continue

        start = 0

        while start < len(text):

            end = start + chunk_size

            chunk = text[start:end]

            if chunk.strip():
                chunks.append(chunk)
                chunk_pages.append(page_number + 1)

            start = end - overlap

    print("Created chunks:", len(chunks))

    # Stop if PDF has no readable text
    if not chunks:
        raise ValueError(
            "Could not extract text from this PDF."
        )

    # Create embeddings
    embeddings = []

    for chunk in chunks:

        response = client.embed(
            model="nomic-embed-text",
            input=chunk
        )

        embeddings.append(response["embeddings"][0])

    print("Created embeddings:", len(embeddings))

    # Store in ChromaDB
    store_documents(
        chunks,
        embeddings,
        filename,
        chunk_pages
    )

    return len(chunks)