from pypdf import PdfReader
import ollama
from database import store_documents


#read pdf
reader=PdfReader("documents/notes.pdf")

#extract all page first
full_text=""

for page in reader.pages:
    text=page.extract_text()
    full_text+=text

chunk_size=500
overlap=50

chunks=[]

start=0

# create chunks until the end
while start<len(full_text):
        end=start+chunk_size #0+500=500
        chunk=full_text[start:end]
        chunks.append(chunk)

        start=end-overlap#500-50=450 which will again go at end=450+500[450:950]

       

embeddings=[]

for chunk in chunks:
    response=ollama.embed(
        model="nomic-embed-text",
        input=chunk
    )

    embeddings.append(response["embeddings"][0])

store_documents(chunks, embeddings)

print("Number of chunks:",len(chunks))
print("Number of embeddings:",len(embeddings))
print("First",embeddings[0])