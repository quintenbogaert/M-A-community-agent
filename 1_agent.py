
"""
Main entry point for the AI agent.
"""

from dotenv import load_dotenv
from openai import OpenAI


def main():
    # Load the API key
    load_dotenv()

    # Initialize the client
    client = OpenAI()

    # Define the agent's instructions
    instructions = """
    You are an AI assistant specializing in mergers and acquisitions.
    Provide accurate, concise answers.
    Do not invent financial information.
    """

    print("M&A Agent started!")
    print("Type 'exit' to quit.\n")

    # Keep running until the user exits
    while True:
        user_input = input("You: ")

        if user_input.strip().lower() == "exit":
            print("Agent stopped.")
            break

        response = client.responses.create(
            model="gpt-6-luna",
            instructions=instructions,
            input=user_input
        )

        print("\nAgent:", response.output_text, "\n")


if __name__ == "__main__":
    main()
