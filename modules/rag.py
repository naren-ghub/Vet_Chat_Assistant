from __future__ import annotations

from typing import Dict, List, Tuple

from retrieval.vector_store import query_collection


def retrieve_context(
    collection, query_embedding, top_k: int, where: Dict | None = None
) -> Tuple[str, List[Dict], List[str]]:
    result = query_collection(collection, query_embedding, top_k=top_k, where=where)
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]
    context_chunks = []
    citations = []
    allowed_titles = []
    seen_docs = set()
    for doc, meta, distance in zip(documents, metadatas, distances):
        context_chunks.append(doc)
        similarity = 1.0 - float(distance)
        if similarity < 0.75:
            continue
        meta = meta or {}
        document_id = meta.get("document_id")
        if document_id and document_id in seen_docs:
            continue
        if document_id:
            seen_docs.add(document_id)
        source_title = meta.get("source_title", meta.get("source", ""))
        if source_title:
            allowed_titles.append(source_title)
        citations.append(
            {
                "source_title": source_title,
                "organization": meta.get("organization", ""),
                "publication_year": meta.get("publication_year") or meta.get("year"),
                "section_reference": meta.get("section_reference", ""),
                "url": meta.get("url", ""),
                "similarity_score": similarity,
            }
        )
    return "\n\n".join(context_chunks), citations, allowed_titles


def rag_context(
    collection,
    query_embedding,
    top_k: int,
    where: Dict | None = None,
) -> Tuple[str, List[Dict], List[str]]:
    context, citations, allowed_titles = retrieve_context(
        collection, query_embedding, top_k, where=where
    )
    return context, citations, allowed_titles
