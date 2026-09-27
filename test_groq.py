import os

from dotenv import load_dotenv
from groq import Groq


load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise RuntimeError("GROQ_API_KEY is missing from the .env file.")

client = Groq(api_key=api_key)

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {
            "role": "system",
            "content": (
                "You are a careful software incident-response assistant. "
                "Do not invent facts or claim that an unverified cause is confirmed."
            ),
        },
        {
            "role": "user",
            "content": (
                "A checkout service started returning HTTP 500 errors "
                "immediately after deployment. Give three initial investigation steps."
            ),
        },
    ],
    temperature=0.2,
    max_completion_tokens=300,
)

print("Groq connection successful.\n")
print(response.choices[0].message.content)