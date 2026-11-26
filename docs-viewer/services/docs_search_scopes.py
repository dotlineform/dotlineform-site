"""Names for the completed Search artifacts shared by Working and Public."""

COLLECTION_SEARCH_SCOPES = ("works", "concepts", "moments", "library", "book")
PORTFOLIO_DOCUMENT_COLLECTIONS = frozenset(("works", "concepts", "moments", "texts"))
PORTFOLIO_HOST_COLLECTIONS = PORTFOLIO_DOCUMENT_COLLECTIONS | {"catalogue"}
SEARCH_DOCUMENT_COLLECTIONS = PORTFOLIO_DOCUMENT_COLLECTIONS.union(COLLECTION_SEARCH_SCOPES)


def search_artifact(scope: str) -> tuple[str, str]:
    """Return the exact queue identity and filename for a Search scope."""
    if scope == "portfolio":
        return "search", "index.json"
    if scope in COLLECTION_SEARCH_SCOPES:
        return f"search-{scope}", f"{scope}.json"
    raise ValueError(f"Unknown Search scope: {scope}")
