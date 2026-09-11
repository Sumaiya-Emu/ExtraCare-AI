"""Context-aware retrieval over the clinical and toxicology vector collections."""
from typing import List

from backend.config import settings
from backend.core.tracing import traceable
from backend.rag.vector_store import get_vector_store, ingest_knowledge_base


@traceable("retriever", name="retriever.retrieve_clinical_context", tags=["rag", "clinical"])
def retrieve_clinical_context(query: str, k: int = 4) -> List[str]:
    ingest_knowledge_base()
    store = get_vector_store(settings.CLINICAL_COLLECTION)
    docs = store.similarity_search(query, k=k)
    return [doc.page_content for doc in docs]


@traceable("retriever", name="retriever.retrieve_toxicology_context", tags=["rag", "toxicology"])
def retrieve_toxicology_context(query: str, k: int = 4) -> List[str]:
    ingest_knowledge_base()
    store = get_vector_store(settings.TOXICOLOGY_COLLECTION)
    docs = store.similarity_search(query, k=k)
    return [doc.page_content for doc in docs]
