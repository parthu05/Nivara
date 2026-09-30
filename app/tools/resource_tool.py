from app.rag.retriever import format_context, retrieve


def lookup_resources(query: str, k: int = 4) -> str:
    context = format_context(query, k=k)
    if not context:
        return "No local knowledge-base passages were found yet. Ingest documents and try again."
    return context


def search_resources(query: str, k: int = 4) -> list[dict[str, str]]:
    return retrieve(query, k=k)
