import os

from dotenv import load_dotenv
from hindsight_client import Hindsight


load_dotenv()

api_url = os.getenv("HINDSIGHT_API_URL")
api_key = os.getenv("HINDSIGHT_API_KEY")
bank_id = os.getenv("HINDSIGHT_BANK_ID")

client = Hindsight(
    base_url=api_url,
    api_key=api_key,
)

try:
    response = client.recall(
        bank_id=bank_id,
        query="What previously caused checkout HTTP 500 errors?",
    )

    if not response.results:
        print("No matching memories found.")
    else:
        print("Relevant memories found:")

        for number, memory in enumerate(response.results, start=1):
            print(f"\nMemory {number}:")
            print(memory.text)

finally:
    client.close()