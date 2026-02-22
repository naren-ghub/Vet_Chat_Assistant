from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Dict, List, Tuple

from retrieval.chunking import chunk_text
from retrieval.embedding import BGEEmbedder
from retrieval.vector_store import get_collection, add_documents


def _extract_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except Exception as exc:  # pragma: no cover - import guard
        raise RuntimeError(
            "Missing dependency: pypdf. Install with `pip install pypdf`."
        ) from exc
    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


def _extract_txt_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _infer_metadata(path: Path) -> Dict:
    category = path.parent.name
    source = path.name
    year = None
    for token in path.stem.split("_"):
        if token.isdigit() and len(token) == 4:
            year = int(token)
    lowered = path.stem.lower()
    if "cat" in lowered or "feline" in lowered:
        species = "cat"
    elif "dog" in lowered or "canine" in lowered:
        species = "dog"
    else:
        species = "all"
    return {
        "document_id": path.stem,
        "chunk_id": "",
        "source_title": path.stem,
        "organization": "unknown",
        "publication_year": year or 0,
        "section_reference": "",
        "url": "",
        "evidence_level": "unknown",
        "last_updated": "",
        "species": species,
        "category": category,
        "source": source,
        "year": year or 0,
    }


def _sanitize_metadata(meta: Dict) -> Dict:
    cleaned = {}
    for key, value in meta.items():
        if value is None:
            continue
        cleaned[key] = value
    return cleaned


def ingest_kb(
    kb_raw_path: str,
    chroma_path: str,
    embedding_model: str,
    chunk_size: int,
    chunk_overlap: int,
) -> None:
    embedder = BGEEmbedder(embedding_model)
    collection = get_collection(chroma_path)

    kb_path = Path(kb_raw_path)
    docs: List[str] = []
    metas: List[Dict] = []
    ids: List[str] = []

    for path in kb_path.rglob("*"):
        if path.is_dir():
            continue
        if path.suffix.lower() == ".pdf":
            text = _extract_pdf_text(path)
        elif path.suffix.lower() in [".txt", ".md"]:
            text = _extract_txt_text(path)
        else:
            continue
        if not text.strip():
            continue
        chunks = chunk_text(text, chunk_size, chunk_overlap)
        for idx, chunk in enumerate(chunks):
            docs.append(chunk)
            meta = _sanitize_metadata(_infer_metadata(path))
            meta["chunk_id"] = f"{path.stem}-{idx}"
            metas.append(meta)
            ids.append(str(uuid.uuid4()))

    if not docs:
        return

    embeddings = embedder.encode(docs)
    embeddings_list = embeddings.tolist() if hasattr(embeddings, "tolist") else embeddings
    add_documents(collection, docs, metas, embeddings_list, ids)
