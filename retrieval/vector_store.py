from __future__ import annotations

from typing import Dict, List, Tuple


def get_collection(chroma_path: str, name: str = "vet_kb"):
    try:
        import chromadb
    except Exception as exc:  # pragma: no cover - import guard
        raise RuntimeError(
            "Missing dependency: chromadb. Install with `pip install chromadb`."
        ) from exc

    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_or_create_collection(name=name)
    return collection


def add_documents(
    collection,
    documents: List[str],
    metadatas: List[Dict],
    embeddings: List[List[float]],
    ids: List[str],
) -> None:
    collection.add(
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings,
        ids=ids,
    )


def query_collection(collection, query_embedding, top_k: int = 5, where: Dict | None = None):
    params = {
        "query_embeddings": [query_embedding],
        "n_results": top_k,
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        params["where"] = where
    return collection.query(**params)
