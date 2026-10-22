
"""
Provider-independent M&A web research.

Current provider: OpenAI Web Search.

Features:
- Standardized search results
- Cited and consulted source separation
- URL deduplication
- Local SQLite search history
- Reuse of recent search results

Future providers: Exa, Tavily.
"""
import re
from urllib.parse import unquote
import json
import sqlite3

from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import (
    urlsplit,
    urlunsplit,
    parse_qsl,
    urlencode
)

from openai import OpenAI

from AA_config import (
    MODEL,
    SEARCH_PROVIDER,
    SEARCH_CACHE_ENABLED,
    SEARCH_CACHE_DAYS
)

from AA_schemas import SearchSource, SearchResult

# 1. Local storage configuration

PROJECT_ROOT = Path(__file__).resolve().parent
DATABASE_PATH = PROJECT_ROOT / "data" / "search_history.sqlite3"

# Increment when changing the research format or instructions
CACHE_VERSION = "v1"


def get_database():
    """
    Open the local search-history database.
    Create its table if necessary.
    """

    DATABASE_PATH.parent.mkdir(
        parents=True, exist_ok=True
    )

    connection = sqlite3.connect(DATABASE_PATH)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS searches (
            provider TEXT NOT NULL,
            query_key TEXT NOT NULL,
            searched_at TEXT NOT NULL,
            result_json TEXT NOT NULL,
            PRIMARY KEY (provider, query_key)
        )
    """)

    connection.commit()
    return connection


def make_query_key(query):
    """
    Normalize query text for exact-query caching.
    """

    normalized = " ".join(
        query.lower().split()
    )

    return f"{CACHE_VERSION}:{normalized}"


# 2. URL normalization

def normalize_url(url):
    """
    Remove common tracking parameters.

    Preserve query parameters that could affect
    the actual webpage being requested.
    """

    parts = urlsplit(url)

    parameters = [
        (key, value)
        for key, value in parse_qsl(
            parts.query, keep_blank_values=True
        )
        if not key.lower().startswith("utm_")
    ]

    return urlunsplit((
        parts.scheme.lower(),
        parts.netloc.lower(),
        parts.path,
        urlencode(parameters),
        ""
    ))


# 3. Source extraction

def extract_sources(response, provider):
    """
    Return two collections:
    - Sources cited in the final answer
    - Sources consulted but not cited
    """

    sources = {}

    # Collect sources encountered by web search
    for item in response.output:

        if item.type != "web_search_call":
            continue

        action = getattr(item, "action", None)

        for source in (
            getattr(action, "sources", None) or []
        ):
            raw_url = getattr(source, "url", None)

            if not raw_url:
                continue

            url = normalize_url(raw_url)

            if url not in sources:
                sources[url] = SearchSource(
                    title=getattr(source, "title", None),
                    url=url,
                    provider=provider,
                    cited=False
                )

    # Identify sources cited in the final answer
    for item in response.output:

        if item.type != "message":
            continue

        for content in item.content:

            annotations = (
                getattr(content, "annotations", None) or []
            )

            for annotation in annotations:

                if annotation.type != "url_citation":
                    continue

                raw_url = getattr(annotation, "url", None)

                if not raw_url:
                    continue

                url = normalize_url(raw_url)

                existing = sources.get(url)

                sources[url] = SearchSource(
                    title=(
                        getattr(annotation, "title", None)
                        or (
                            existing.title
                            if existing else None
                        )
                    ),
                    url=url,
                    provider=provider,
                    cited=True
                )

    cited = [
        source for source in sources.values()
        if source.cited
    ]

    consulted = [
        source for source in sources.values()
        if not source.cited
    ]

    return cited, consulted


# 4. Save and retrieve search history

def save_search(result):
    """
    Save the research result to SQLite.

    Both cited and non-cited source metadata
    are retained.
    """

    query_key = make_query_key(result.query)

    searched_at = datetime.now(
        timezone.utc
    ).isoformat()

    with get_database() as connection:

        connection.execute("""
            INSERT OR REPLACE INTO searches
            (provider, query_key, searched_at, result_json)
            VALUES (?, ?, ?, ?)
        """, (
            result.provider,
            query_key,
            searched_at,
            result.model_dump_json()
        ))


def get_cached_search(query, provider):
    """
    Return a previous result if it is still fresh.

    Otherwise return None.
    """

    query_key = make_query_key(query)

    with get_database() as connection:

        row = connection.execute("""
            SELECT searched_at, result_json
            FROM searches
            WHERE provider = ? AND query_key = ?
        """, (provider, query_key)).fetchone()

    if row is None:
        return None

    searched_at = datetime.fromisoformat(row[0])

    expiry = searched_at + timedelta(
        days=SEARCH_CACHE_DAYS
    )

    if datetime.now(timezone.utc) > expiry:
        return None

    result = SearchResult.model_validate_json(row[1])
    result.from_cache = True

    return result


# 5. Search OpenAI

def search_openai(query, client=None):
    """
    Perform live research through OpenAI.

    Return a standardized SearchResult.
    """

    if client is None:
        client = OpenAI()

    response = client.responses.create(
        model=MODEL,
        instructions="""
        You are an M&A research analyst.

        Research the requested transaction.

        Identify, where available:
        - Buyer and target
        - Announcement date
        - Transaction value
        - Financial advisers
        - Legal advisers
        - Buy-side and sell-side roles
        - Individual deal-team members

        Prioritize primary sources.

        Cite supporting evidence.
        Do not invent missing information.
        Clearly identify uncertainty.
        """,
        input=query,
        tools=[
            {
                "type": "web_search",
                "search_context_size": "medium"
            }
        ],
        tool_choice="required",
        include=[
            "web_search_call.action.sources"
        ]
    )

    if response.status != "completed":
        raise RuntimeError(
            f"Search status: {response.status}"
        )

    cited, consulted = extract_sources(
        response, "openai"
    )

    search_events = sum(
        item.type == "web_search_call"
        for item in response.output
    )

    return SearchResult(
        query=query,
        provider="openai",
        answer=response.output_text,
        sources=cited,
        consulted_sources=consulted,
        search_events=search_events
    )


# 6. Provider-independent entry point

def search_web(
    query,
    provider=None,
    client=None,
    force_refresh=False
):
    """
    Search using the selected provider.

    Reuse local results when possible unless
    force_refresh is True.

    Provider switching happens here.
    """

    provider = provider or SEARCH_PROVIDER

    if SEARCH_CACHE_ENABLED and not force_refresh:

        cached = get_cached_search(
            query, provider
        )

        if cached is not None:
            return cached

    if provider == "openai":

        result = search_openai(
            query, client=client
        )

    else:
        raise ValueError(
            f"Unsupported provider: {provider}"
        )

    if SEARCH_CACHE_ENABLED:
        save_search(result)

    return result


# 7. Find historical source leads

def find_previous_sources(term, limit=20):
    """
    Find source URLs associated with earlier
    queries containing the search term.

    This performs a LOCAL database lookup.
    It does not call OpenAI.

    These are research leads, not verified facts.
    """

    if not term.strip() or limit <= 0:
        return []

    matches = []
    seen = set()

    with get_database() as connection:
        rows = connection.execute("""
            SELECT result_json
            FROM searches
            ORDER BY searched_at DESC
        """).fetchall()

    term = term.casefold()

    for (result_json,) in rows:

        result = SearchResult.model_validate_json(
            result_json
        )

        # Match query or source metadata
        query_matches = term in result.query.casefold()

        for source in (
            result.sources + result.consulted_sources
        ):

            source_matches = (
                term in (source.title or "").casefold()
                or term in source.url.casefold()
            )

            if not (query_matches or source_matches):
                continue

            if source.url in seen:
                continue

            seen.add(source.url)
            matches.append(source)

            if len(matches) >= limit:
                return matches

    return matches


def find_research_leads(company_name, limit=20):
    """
    Find historical sources that directly match
    a company name.

    Prioritize cited sources over non-cited sources.

    This function only reads local SQLite data.
    It makes no API calls.
    """

    if not company_name.strip() or limit <= 0:
        return []

    def normalize_text(text):
        """
        Make titles and URL paths easier to match.
        """
        text = unquote(text).casefold()
        text = re.sub(r"[\W_]+", " ", text)
        return " ".join(text.split())

    target = normalize_text(company_name)

    matches = {}

    with get_database() as connection:
        rows = connection.execute("""
            SELECT result_json
            FROM searches
            ORDER BY searched_at DESC
        """).fetchall()

    for (result_json,) in rows:

        result = SearchResult.model_validate_json(
            result_json
        )

        all_sources = (
            result.sources + result.consulted_sources
        )

        for source in all_sources:

            # Match against the title and URL,
            # not merely the original search query.
            parsed_url = urlsplit(source.url)

            searchable_text = normalize_text(
                (source.title or "")
                + " "
                + parsed_url.path
                + " "
                + parsed_url.netloc
            )

            if target not in searchable_text:
                continue

            existing = matches.get(source.url)

            # Prefer cited records when a URL appears
            # in several historical search results.
            if existing is None or (
                source.cited and not existing.cited
            ):
                matches[source.url] = source

    # Cited sources first, then non-cited sources
    ranked = sorted(
        matches.values(),
        key=lambda source: not source.cited
    )

    return ranked[:limit]
