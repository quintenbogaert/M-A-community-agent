
"""
Step 3.6.3 — Test reuse of historical research leads.

No OpenAI API calls are made.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from AA_search import find_research_leads


def main():

    print("Historical research reuse experiment\n")

    company = "Roos Groep"

    print("Searching local history for:", company)

    leads = find_research_leads(
        company_name=company,
        limit=20
    )

    cited = [source for source in leads if source.cited]
    non_cited = [
        source for source in leads if not source.cited
    ]

    print("\nTotal relevant leads:", len(leads))
    print("Previously cited:", len(cited))
    print("Previously non-cited:", len(non_cited))

    print("\nPotential research leads:\n")

    for source in leads:

        label = (
            "CITED" if source.cited
            else "NON-CITED"
        )

        print(f"[{label}] {source.title or 'Untitled'}")
        print(source.url)
        print()

    print("No external search was performed.")


if __name__ == "__main__":
    main()
