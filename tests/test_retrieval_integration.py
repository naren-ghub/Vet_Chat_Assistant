from pathlib import Path

from retrieval.embedding import BGEEmbedder
from retrieval.ingest import ingest_kb
from retrieval.vector_store import get_collection, query_collection


def test_full_retrieval_pipeline(tmp_path: Path):
    kb_root = tmp_path / "kb_raw"
    kb_root.mkdir()
    doc_path = kb_root / "sample.txt"
    doc_path.write_text(
        "Dogs can have vomiting due to dietary changes or infection.", encoding="utf-8"
    )

    chroma_path = tmp_path / "chroma"
    ingest_kb(
        kb_raw_path=str(kb_root),
        chroma_path=str(chroma_path),
        embedding_model="BAAI/bge-base-en-v1.5",
        chunk_size=50,
        chunk_overlap=10,
    )

    collection = get_collection(str(chroma_path))
    embedder = BGEEmbedder("BAAI/bge-base-en-v1.5")
    query_vec = embedder.encode(["vomiting in dogs"])[0]
    result = query_collection(collection, query_vec, top_k=3)

    docs = result.get("documents", [[]])[0]
    assert docs
