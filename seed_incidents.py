import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from hindsight_client import Hindsight


load_dotenv()

hindsight_url = os.getenv("HINDSIGHT_API_URL")
hindsight_key = os.getenv("HINDSIGHT_API_KEY")
bank_id = os.getenv("HINDSIGHT_BANK_ID")

required_values = {
    "HINDSIGHT_API_URL": hindsight_url,
    "HINDSIGHT_API_KEY": hindsight_key,
    "HINDSIGHT_BANK_ID": bank_id,
}

missing_values = [
    name for name, value in required_values.items() if not value
]

if missing_values:
    raise RuntimeError(
        f"Missing environment variables: {', '.join(missing_values)}"
    )


INCIDENTS = [
    {
        "document_id": "incident-auth-db-pool-2026-08-12",
        "timestamp": datetime(
            2026, 8, 12, 10, 30, tzinfo=timezone.utc
        ),
        "content": """
Service: authentication-service
Symptom: Login requests returned HTTP 503 errors after a traffic spike.
Impact: Users could not sign in for approximately 18 minutes.
Root cause: The PostgreSQL connection pool reached its maximum limit.
Resolution: Increased the connection-pool limit and restarted the
authentication-service.
Prevention: Added database connection-pool utilization alerts.
""".strip(),
        "tags": ["incident", "authentication", "database", "resolved"],
    },
    {
        "document_id": "incident-inventory-redis-2026-08-20",
        "timestamp": datetime(
            2026, 8, 20, 14, 15, tzinfo=timezone.utc
        ),
        "content": """
Service: inventory-service
Symptom: Product stock information was unavailable and requests timed out.
Impact: Customers could not confirm product availability.
Root cause: The Redis hostname was incorrectly changed during deployment.
Resolution: Restored the correct Redis hostname and redeployed the service.
Prevention: Added configuration validation to the deployment pipeline.
""".strip(),
        "tags": ["incident", "inventory", "redis", "deployment", "resolved"],
    },
    {
        "document_id": "incident-orders-migration-2026-08-29",
        "timestamp": datetime(
            2026, 8, 29, 9, 45, tzinfo=timezone.utc
        ),
        "content": """
Service: order-service
Symptom: New order creation returned HTTP 500 errors after deployment.
Impact: Customers could not place new orders for 22 minutes.
Root cause: A required database migration was not executed.
Resolution: Applied the missing migration and restarted the order-service.
Prevention: Added an automatic migration verification step before release.
""".strip(),
        "tags": ["incident", "orders", "database", "deployment", "resolved"],
    },
    {
        "document_id": "incident-payment-timeout-2026-09-04",
        "timestamp": datetime(
            2026, 9, 4, 16, 20, tzinfo=timezone.utc
        ),
        "content": """
Service: payment-service
Symptom: Payment requests timed out during checkout.
Impact: Some customers could not complete transactions.
Root cause: The external payment provider increased API response latency.
Resolution: Increased the client timeout temporarily and enabled retry
with exponential backoff.
Prevention: Added payment-provider latency monitoring and a circuit breaker.
""".strip(),
        "tags": ["incident", "payment", "timeout", "external-api", "resolved"],
    },
    {
        "document_id": "incident-worker-disk-2026-09-09",
        "timestamp": datetime(
            2026, 9, 9, 12, 10, tzinfo=timezone.utc
        ),
        "content": """
Service: image-processing-worker
Symptom: Uploaded product images remained in the processing queue.
Impact: New product images were not displayed.
Root cause: Temporary image files filled the worker's available disk space.
Resolution: Removed old temporary files and restarted the worker.
Prevention: Added scheduled cleanup and disk-usage alerts at 75 percent.
""".strip(),
        "tags": ["incident", "worker", "disk-space", "queue", "resolved"],
    },
    {
        "document_id": "incident-search-index-2026-09-14",
        "timestamp": datetime(
            2026, 9, 14, 8, 35, tzinfo=timezone.utc
        ),
        "content": """
Service: search-service
Symptom: Recently added products did not appear in search results.
Impact: Customers received outdated search results.
Root cause: The search indexing consumer stopped after an unhandled event.
Resolution: Restarted the consumer and rebuilt the missing index entries.
Prevention: Added consumer health checks, dead-letter handling and alerts.
""".strip(),
        "tags": ["incident", "search", "indexing", "consumer", "resolved"],
    },
    {
        "document_id": "incident-api-rate-limit-2026-09-19",
        "timestamp": datetime(
            2026, 9, 19, 17, 5, tzinfo=timezone.utc
        ),
        "content": """
Service: customer-profile-service
Symptom: Profile updates failed with HTTP 429 responses.
Impact: Customers could view profiles but could not save changes.
Root cause: A retry loop generated excessive requests to an external API.
Resolution: Disabled the faulty retry loop and deployed a corrected version.
Prevention: Added bounded retries, backoff and outgoing request-rate alerts.
""".strip(),
        "tags": ["incident", "profile", "rate-limit", "retry", "resolved"],
    },
    {
        "document_id": "incident-webhook-certificate-2026-09-23",
        "timestamp": datetime(
            2026, 9, 23, 11, 50, tzinfo=timezone.utc
        ),
        "content": """
Service: webhook-service
Symptom: Partner webhook deliveries failed with TLS verification errors.
Impact: Partners did not receive real-time transaction updates.
Root cause: The webhook endpoint certificate had expired.
Resolution: Renewed the certificate and retried failed webhook events.
Prevention: Added certificate-expiry monitoring with alerts 30 days before
expiration.
""".strip(),
        "tags": ["incident", "webhook", "certificate", "tls", "resolved"],
    },
]


hindsight = Hindsight(
    base_url=hindsight_url,
    api_key=hindsight_key,
)

try:
    items = []

    for incident in INCIDENTS:
        items.append(
            {
                "content": incident["content"],
                "timestamp": incident["timestamp"],
                "context": "Confirmed production incident report",
                "document_id": incident["document_id"],
                "tags": incident["tags"],
                "metadata": {
                    "source": "hackathon-demo-seed",
                    "status": "resolved",
                },
                "update_mode": "replace",
            }
        )

    result = hindsight.retain_batch(
        bank_id=bank_id,
        items=items,
    )

    print("Historical incident dataset stored successfully.")
    print(f"Bank ID: {bank_id}")
    print(f"Incidents submitted: {len(INCIDENTS)}")

    if hasattr(result, "items_count"):
        print(f"Incidents accepted: {result.items_count}")

finally:
    hindsight.close()