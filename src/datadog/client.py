"""Datadog On-Call paging client."""

import os

import requests

# Regional URL — configurable via DATADOG_ONCALL_URL env var
_DEFAULT_URL = "https://navy.oncall.datadoghq.com/api/v2/on-call/pages"


def page_oncall(org_name: str, message_text: str, permalink: str, email: str) -> bool:
    """Send an on-call page via the Datadog On-Call API. Returns True on success."""
    api_key = os.environ.get("DATADOG_API_KEY", "")
    app_key = os.environ.get("DATADOG_APP_KEY", "")
    url = os.environ.get("DATADOG_ONCALL_URL", _DEFAULT_URL)

    payload = {
        "data": {
            "type": "pages",
            "attributes": {
                "target": {
                    "identifier": "customer-success",
                    "type": "team_handle",
                },
                "title": f"New URGENT Page: {org_name}",
                "urgency": "high",
                "description": (
                    f"Title: {message_text[:200]} | "
                    f"Link: {permalink} | "
                    f"Email: {email}"
                ),
                "tags": ["responder:cs"],
            },
        }
    }

    try:
        response = requests.post(
            url,
            json=payload,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "DD-API-KEY": api_key,
                "DD-APPLICATION-KEY": app_key,
            },
            timeout=(5, 15),
        )
        return response.status_code in (200, 201)
    except requests.RequestException:
        return False
