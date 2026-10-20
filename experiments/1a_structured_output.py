
"""
Step 3.2 — Structured M&A transaction extraction.
"""

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

# Define the structure of an M&A transaction
class Transaction(BaseModel):
    buyer: str | None
    target: str | None
    announcement_date: str | None
    transaction_value: str | None
    buy_side_advisor: str | None
    sell_side_advisor: str | None


def main():
    load_dotenv()
    client = OpenAI()

    print("M&A Structured Data Agent")
    print("Enter a transaction description.\n")

    user_input = input("Transaction: ")

    response = client.responses.parse(
        model="gpt-6-luna",
        instructions="""
        Extract M&A transaction information from the user's text.

        Only use information explicitly provided in the text.
        If information is missing, return null for that field.
        Do not invent information.
        """,
        input=user_input,
        text_format=Transaction
    )

    transaction = response.output_parsed

    if transaction is None:
        print("No structured result was returned.")
        return

    print("\nStructured transaction data:")
    print(transaction.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
