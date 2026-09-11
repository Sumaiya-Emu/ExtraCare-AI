"""ChromaDB initialization, local embedding setup, and knowledge-base ingestion."""
from __future__ import annotations

import hashlib
import json
from threading import RLock

from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from backend.config import settings

_lock = RLock()
_ingested: dict[str, str] = {}
_embeddings: Embeddings | None = None
_stores: dict[str, Chroma] = {}


class ChromaLocalEmbeddings(Embeddings):
    """LangChain adapter for Chroma's local all-MiniLM-L6-v2 embedder."""

    def __init__(self) -> None:
        self._embedding_function = DefaultEmbeddingFunction()

    @staticmethod
    def _as_plain_vectors(vectors) -> list[list[float]]:
        return [[float(value) for value in vector] for vector in vectors]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._as_plain_vectors(self._embedding_function(texts))

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


def _get_embeddings() -> Embeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = ChromaLocalEmbeddings()
    return _embeddings


def get_vector_store(collection_name: str) -> Chroma:
    """Return one cached persistent Chroma collection per process."""
    with _lock:
        if collection_name not in _stores:
            settings.VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
            model_id = hashlib.sha256(settings.EMBEDDING_MODEL_NAME.encode()).hexdigest()[:10]
            _stores[collection_name] = Chroma(
                collection_name=f"{collection_name}_{model_id}",
                embedding_function=_get_embeddings(),
                persist_directory=str(settings.VECTOR_STORE_DIR),
            )
        return _stores[collection_name]


def _clinical_entry_to_document(entry: dict) -> Document:
    text = (
        f"Condition: {entry.get('condition')}. Biomarker: {entry.get('biomarker')}. "
        f"Safe range: {entry.get('safe_range')}. Caution range: {entry.get('caution_range')}. "
        f"Danger threshold: {entry.get('danger_threshold')}. "
        f"Dietary guidance: {entry.get('dietary_restriction')}. "
        f"Source: {entry.get('source', 'unspecified')}."
    )
    return Document(page_content=text, metadata={"condition": entry.get("condition", "")})


def _toxicology_entry_to_document(entry: dict) -> Document:
    restriction_rules = entry.get("restriction_rules", [])
    restriction_text = ""
    if restriction_rules:
        parts = []
        for rule in restriction_rules:
            parts.append(
                f"Condition-specific restriction: {rule.get('condition')} = {rule.get('classification')}; "
                f"tolerated dose: {rule.get('tolerated_dose')}; danger threshold: {rule.get('danger_threshold')}; "
                f"mechanism: {rule.get('mechanism')}; source: {rule.get('source')}."
            )
        restriction_text = "\n" + "\n".join(parts)
    text = (
        f"Ingredient: {entry.get('ingredient')}. Category: {entry.get('category')}. "
        f"Flagged for: {', '.join(entry.get('flagged_conditions', []))}. "
        f"Mechanism: {entry.get('mechanism')}. Severity: {entry.get('severity')}. "
        f"Source: {entry.get('source', 'unspecified')}." + restriction_text
    )
    return Document(page_content=text, metadata={"ingredient": entry.get("ingredient", "")})


def ingest_knowledge_base(force: bool = False) -> None:
    """Synchronize the bundled evidence records into persistent Chroma collections."""
    with _lock:
        for collection, filename, key, convert in (
            (settings.CLINICAL_COLLECTION, "clinical_guidelines.json", "condition", _clinical_entry_to_document),
            (settings.TOXICOLOGY_COLLECTION, "toxicology_standards.json", "ingredient", _toxicology_entry_to_document),
        ):
            raw = (settings.KNOWLEDGE_BASE_DIR / filename).read_bytes()
            signature = hashlib.sha256(raw).hexdigest()
            if not force and _ingested.get(collection) == signature:
                continue
            entries = [e for e in json.loads(raw) if isinstance(e, dict) and key in e]
            docs = [convert(e) for e in entries]
            ids = [hashlib.sha256(d.page_content.encode()).hexdigest() for d in docs]
            store = get_vector_store(collection)
            old_ids = set(store.get().get("ids", []))
            pairs = [(i, d) for i, d in zip(ids, docs) if force or i not in old_ids]
            if pairs:
                store.add_documents([d for _, d in pairs], ids=[i for i, _ in pairs])
            stale = old_ids - set(ids)
            if stale:
                store.delete(ids=list(stale))
            _ingested[collection] = signature
