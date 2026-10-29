from flashrank import Ranker, RerankRequest

#load the reranking model

ranker=Ranker(
    model_name="ms-marco-MiniLM-L-12-v2"
)

def rerank_chunks(question,documents,metadatas):
    """
    Reorder retrived document chunks by relevance
    to the user's question.
    """
    passages=[]

    for document,metadata in zip(documents,metadatas):
        passages.append({
            "text":document,
            "meta":metadata,
        })

    request = RerankRequest(
        query=question,
        passages=passages,
    )

    results=ranker.rerank(request)

    return results