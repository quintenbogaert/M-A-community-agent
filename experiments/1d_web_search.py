
"""
Step 3.6 — First web-search experiment.

Test OpenAI's hosted web search before
integrating it into our main M&A agent.
"""

from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


# Locate the project folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load our existing API key
load_dotenv(PROJECT_ROOT / ".env")


def main():

    client = OpenAI()

    print("M&A Web Search Experiment")
    print("Researching a real M&A transaction...\n")

    response = client.responses.create(
        model="gpt-6-luna",
        tools=[
            {
                "type": "web_search",
                "search_context_size": "medium"
            }
        ],
        tool_choice="required",
        instructions="""
        You are an M&A research analyst.

        Research the transaction using web sources.

        Identify:
        - Buyer
        - Target
        - Announcement date
        - Financial advisers
        - Legal advisers
        - Buy-side and sell-side roles

        Include source citations.

        Do not invent missing information.
        Distinguish confirmed information
        from uncertain conclusions.
        """,
        input=(
            "Research the acquisition of Roos Groep "
            "by Green Park Investment Partners."
        )
    )

    # Verify whether the web search tool was used
    search_calls = [
        item for item in response.output
        if item.type == "web_search_call"
    ]

    print("Web search tool events:", len(search_calls))

    # Print the final response
    print("\nResearch findings:\n")
    print(response.output_text)


if __name__ == "__main__":
    main()
