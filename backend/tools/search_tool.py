"""Live web-search grounding for current product recalls and guideline discovery."""
from typing import List, TypedDict

from backend.config import settings
from backend.core.tracing import traceable


class SearchResult(TypedDict):
    title: str
    url: str
    content: str


class SearchUnavailableError(RuntimeError):
    """Raised when no search API key is configured; callers should degrade gracefully."""


def is_available() -> bool:
    return settings.has_tavily_api_key()


@traceable("tool", name="search_tool.search_web", tags=["internet-search", "grounding"])
def search_web(query: str, max_results: int = 5) -> List[SearchResult]:
    if not is_available():
        raise SearchUnavailableError("TAVILY_API_KEY is not configured.")

    from tavily import TavilyClient

    try:
        client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        response = client.search(query=query, max_results=max_results, timeout=30)
    except Exception as exc:
        # Live search is supplementary. An expired/placeholder Tavily key must never
        # crash OCR/RAG/product analysis.
        raise SearchUnavailableError("Live search is unavailable; check the search service configuration.") from exc

    return [
        SearchResult(title=r.get("title", ""), url=r.get("url", ""), content=r.get("content", ""))
        for r in response.get("results", [])
    ]
