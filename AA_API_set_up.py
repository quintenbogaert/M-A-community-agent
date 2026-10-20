import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError("OPENAI_API_KEY was not found in .env")

print("API key loaded successfully.")

client = OpenAI()

response = client.responses.create(
    model="gpt-6-luna",
    input="Reply with exactly: API connection successful"
)

print(response.output_text)