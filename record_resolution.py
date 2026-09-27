import os
from datetime import date

from dotenv import load_dotenv
from hindsight_client import Hindsight


load_dotenv()

api_url = os.getenv("HINDSIGHT_API_URL")
api_key = os.getenv("HINDSIGHT_API_KEY")
bank_id = os.getenv("HINDSIGHT_BANK_ID")

missing_variables = [
    name
    for name, value in {
        "HINDSIGHT_API_URL": api_url,
        "HINDSIGHT_API_KEY": api_key,
        "HINDSIGHT_BANK_ID": bank_id,
    }.items()
    if not value
]

if missing_variables:
    raise RuntimeError(
        "Missing environment variables: " + ", ".join(missing_variables)
    )

print("=== RECORD A CONFIRMED INCIDENT RESOLUTION ===")

service = input("Service name: ").strip()
symptoms = input("Observed symptoms: ").strip()
impact = input("Confirmed impact: ").strip()
root_cause = input("Confirmed root cause: ").strip()
resolution = input("Resolution applied: ").strip()
prevention = input("Prevention or follow-up action: ").strip()

required_fields = {
    "service name": service,
    "observed symptoms": symptoms,
    "confirmed impact": impact,
    "confirmed root cause": root_cause,
    "resolution": resolution,
}

empty_fields = [name for name, value in required_fields.items() if not value]

if empty_fields:
    raise ValueError(
        "The following required fields cannot be empty: "
        + ", ".join(empty_fields)
    )

incident_memory = f"""
Confirmed software incident record.

Incident date: {date.today().isoformat()}
Service: {service}
Observed symptoms: {symptoms}
Confirmed impact: {impact}
Confirmed root cause: {root_cause}
Resolution applied: {resolution}
Prevention or follow-up action: {prevention or "Not provided"}

The root cause and resolution in this record were confirmed by the engineering team.
""".strip()

client = Hindsight(base_url=api_url, api_key=api_key)

try:
    client.retain(
        bank_id=bank_id,
        content=incident_memory,
    )
    print("\nConfirmed incident resolution saved to Hindsight successfully.")
finally:
    client.close()