"""
Zendesk API client for creating support tickets.
"""

import os
import requests
from dataclasses import dataclass
from typing import Optional


@dataclass
class TicketResult:
    """Result of a ticket creation."""
    success: bool
    ticket_id: Optional[int] = None
    ticket_url: Optional[str] = None
    error: Optional[str] = None


class ZendeskClient:
    """Client for interacting with Zendesk API."""
    
    def __init__(
        self,
        subdomain: str = None,
        email: str = None,
        api_token: str = None
    ):
        self.subdomain = subdomain or os.environ.get("ZENDESK_SUBDOMAIN")
        self.email = email or os.environ.get("ZENDESK_EMAIL")
        self.api_token = api_token or os.environ.get("ZENDESK_API_TOKEN")
        
        if not all([self.subdomain, self.email, self.api_token]):
            raise ValueError(
                "Zendesk credentials required. Set ZENDESK_SUBDOMAIN, "
                "ZENDESK_EMAIL, and ZENDESK_API_TOKEN environment variables."
            )
        
        self.base_url = f"https://{self.subdomain}.zendesk.com/api/v2"
        self.auth = (f"{self.email}/token", self.api_token)
    
    def create_ticket(
        self,
        subject: str,
        description: str,
        requester_name: str = None,
        requester_email: str = None,
        priority: str = "normal",
        tags: list[str] = None
    ) -> TicketResult:
        """
        Create a support ticket in Zendesk.
        
        Args:
            subject: Ticket subject/title
            description: Ticket description/body
            requester_name: Name of the person requesting support
            requester_email: Email of the requester
            priority: low, normal, high, or urgent
            tags: List of tags to add to the ticket
        
        Returns:
            TicketResult with ticket ID and URL if successful
        """
        url = f"{self.base_url}/tickets.json"
        
        ticket_data = {
            "ticket": {
                "subject": subject,
                "comment": {"body": description},
                "priority": priority,
            }
        }
        
        # Add requester if provided
        if requester_name and requester_email:
            ticket_data["ticket"]["requester"] = {
                "name": requester_name,
                "email": requester_email
            }
        
        # Add tags if provided
        if tags:
            ticket_data["ticket"]["tags"] = tags
        
        try:
            response = requests.post(
                url,
                json=ticket_data,
                auth=self.auth,
                headers={"Content-Type": "application/json"},
                timeout=(5, 30)
            )
            
            if response.status_code == 201:
                data = response.json()
                ticket = data.get("ticket", {})
                return TicketResult(
                    success=True,
                    ticket_id=ticket.get("id"),
                    ticket_url=f"https://{self.subdomain}.zendesk.com/agent/tickets/{ticket.get('id')}"
                )
            else:
                error_msg = response.json().get("error", response.text)
                return TicketResult(success=False, error=str(error_msg))
                
        except requests.RequestException as e:
            return TicketResult(success=False, error=str(e))
    
    def get_ticket(self, ticket_id: int) -> dict:
        """Get a ticket by ID. Reserved for future use."""
        url = f"{self.base_url}/tickets/{ticket_id}.json"
        response = requests.get(url, auth=self.auth)
        
        if response.status_code == 200:
            return response.json().get("ticket", {})
        return {}


# Singleton instance
_client: ZendeskClient | None = None


def get_zendesk_client() -> ZendeskClient:
    """Get or create the Zendesk client instance."""
    global _client
    if _client is None:
        _client = ZendeskClient()
    return _client


def create_support_ticket(
    subject: str,
    description: str,
    requester_name: str = None,
    requester_email: str = None,
    priority: str = "normal",
    tags: list[str] = None
) -> TicketResult:
    """Convenience function to create a support ticket."""
    client = get_zendesk_client()
    return client.create_ticket(
        subject=subject,
        description=description,
        requester_name=requester_name,
        requester_email=requester_email,
        priority=priority,
        tags=tags
    )
