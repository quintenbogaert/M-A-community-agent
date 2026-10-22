
"""
Step 3.6.3 — Test our standardized web-search module.
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

# 1. Locate the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 2. Make project modules importable
sys.path.insert(0, str(PROJECT_ROOT))

# 3. Import our reusable search interface
from AA_search import search_web



def main():

    load_dotenv(PROJECT_ROOT / ".env")

    query = (
        "Research the acquisition of Roos Groep "
        "by Green Park Investment Partners. "
        "Identify the M&A advisers and sources."
    )

    print("TEST 1 — Search or retrieve cached result")

    result = search_web(query, provider="openai")

    print("From cache:", result.from_cache)
    print("Search events:", result.search_events)
    print("Cited sources:", len(result.sources))
    print(
        "Non-cited sources:",
        len(result.consulted_sources)
    )

    print("\nCited sources:")
    for source in result.sources:
        print("-", source.title or "Untitled")
        print(" ", source.url)

    print("\nTEST 2 — Repeat identical search")

    repeated = search_web(query, provider="openai")

    print("From cache:", repeated.from_cache)

    assert repeated.from_cache is True

    print("Cache reuse successful.")

    print("\nTEST 3 — Search previous source records")

    from AA_search import find_previous_sources

    leads = find_previous_sources("Roos Groep")

    print("Previously found source URLs:", len(leads))

    for source in leads[:5]:
        print("-", source.url)

    print("\nAll tests completed.")


if __name__ == "__main__":
    main()
