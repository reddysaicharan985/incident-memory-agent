import os

from dotenv import load_dotenv
from groq import Groq
from hindsight_client import Hindsight


load_dotenv()

hindsight_url = os.getenv("HINDSIGHT_API_URL")
hindsight_key = os.getenv("HINDSIGHT_API_KEY")
bank_id = os.getenv("HINDSIGHT_BANK_ID")
groq_key = os.getenv("GROQ_API_KEY")

required_values = {
    "HINDSIGHT_API_URL": hindsight_url,
    "HINDSIGHT_API_KEY": hindsight_key,
    "HINDSIGHT_BANK_ID": bank_id,
    "GROQ_API_KEY": groq_key,
}

missing_values = [
    name for name, value in required_values.items() if not value
]

if missing_values:
    raise RuntimeError(
        f"Missing environment variables: {', '.join(missing_values)}"
    )

hindsight = Hindsight(
    base_url=hindsight_url,
    api_key=hindsight_key,
)

groq = Groq(api_key=groq_key)

print("=== INCIDENT MEMORY AGENT ===")

current_incident = input(
    "Describe the current incident: "
).strip()

if not current_incident:
    hindsight.close()
    raise ValueError("Current incident description cannot be empty.")

try:
    memory_response = hindsight.recall(
        bank_id=bank_id,
        query=current_incident,
    )

    recalled_memories = [
        memory.text for memory in memory_response.results
    ]

    if recalled_memories:
        memory_context = "\n".join(
            f"- {memory}" for memory in recalled_memories
        )
    else:
        memory_context = "No relevant past incidents were found."

    prompt = f"""
You are given two evidence blocks.

CURRENT INCIDENT:
{current_incident}

HISTORICAL MEMORIES:
{memory_context}

Create a concise incident investigation brief.

STRICT RULES:
- Current facts must contain only information explicitly written in
  CURRENT INCIDENT.
- If scope, logs, impact, actions, or root cause are not provided,
  label them as unknown.
- Historical memories are relevant evidence, not proof of the current cause.
- Do not claim that an investigation or remediation action has happened.
- Do not invent logs, endpoints, systems, users, or technical results.
- Keep the complete answer below 450 words.
- Use short bullet points, not tables.

Use these sections:
1. Confirmed current facts
2. Unknown information
3. Relevant historical evidence
4. Top three investigation steps
5. Uncertainty warning
"""

    response = groq.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a careful software incident-response agent. "
                    "Use historical memories as evidence, not as proof. "
                    "Never invent facts, logs, causes, or completed actions."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
        max_completion_tokens=1000,
    )

    print("\n=== HINDSIGHT MEMORIES USED ===")
    print(memory_context)

    print("\n=== GROQ INVESTIGATION BRIEF ===")
    print(response.choices[0].message.content)

finally:
    hindsight.close()