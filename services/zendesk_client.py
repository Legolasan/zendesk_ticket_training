"""
Zendesk API client for fetching ticket data
"""
import requests
from typing import Dict, List, Optional
import time


class ZendeskClient:
    """Client for interacting with Zendesk API"""

    def __init__(self, subdomain: str, email: str, api_token: str):
        self.subdomain = subdomain
        self.email = email
        self.api_token = api_token
        self.base_url = f"https://{subdomain}.zendesk.com/api/v2"
        self.session = requests.Session()
        self.session.auth = (f"{email}/token", api_token)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make GET request to Zendesk API with rate limit handling"""
        url = f"{self.base_url}/{endpoint}"

        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params)

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', retry_delay))
                    print(f"⚠️  Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue

                response.raise_for_status()
                return response.json()

            except requests.exceptions.HTTPError as e:
                if attempt < max_retries - 1:
                    print(f"⚠️  HTTP error on attempt {attempt + 1}: {e}. Retrying...")
                    time.sleep(retry_delay)
                else:
                    print(f"❌ Failed after {max_retries} attempts: {e}")
                    raise

            except requests.exceptions.RequestException as e:
                print(f"❌ Request failed: {e}")
                raise

        raise Exception("Max retries exceeded")

    def get_ticket(self, ticket_id: int) -> Dict:
        """
        Fetch ticket details
        GET /api/v2/tickets/{ticket_id}
        """
        print(f"📥 Fetching ticket {ticket_id}...")
        data = self._get(f"tickets/{ticket_id}")
        return data.get('ticket', {})

    def get_ticket_comments(self, ticket_id: int) -> List[Dict]:
        """
        Fetch all comments for a ticket
        GET /api/v2/tickets/{ticket_id}/comments
        """
        print(f"💬 Fetching comments for ticket {ticket_id}...")
        comments = []
        url = f"tickets/{ticket_id}/comments"

        while url:
            data = self._get(url)
            comments.extend(data.get('comments', []))

            # Handle pagination
            next_page = data.get('next_page')
            if next_page:
                # Extract just the endpoint from the full URL
                url = next_page.split('/api/v2/')[-1]
            else:
                url = None

        print(f"   Found {len(comments)} comments")
        return comments

    def get_ticket_audits(self, ticket_id: int) -> List[Dict]:
        """
        Fetch complete ticket audit trail
        GET /api/v2/tickets/{ticket_id}/audits
        """
        print(f"📋 Fetching audits for ticket {ticket_id}...")
        audits = []
        url = f"tickets/{ticket_id}/audits"

        while url:
            data = self._get(url)
            audits.extend(data.get('audits', []))

            # Handle pagination
            next_page = data.get('next_page')
            if next_page:
                url = next_page.split('/api/v2/')[-1]
            else:
                url = None

        print(f"   Found {len(audits)} audit records")
        return audits

    def get_ticket_metrics(self, ticket_id: int) -> Dict:
        """
        Fetch ticket metrics (SLA, timing data)
        GET /api/v2/tickets/{ticket_id}/metrics
        """
        print(f"⏱️  Fetching metrics for ticket {ticket_id}...")
        data = self._get(f"tickets/{ticket_id}/metrics")
        return data.get('ticket_metric', {})

    def get_custom_fields(self) -> List[Dict]:
        """
        Fetch all custom ticket fields
        GET /api/v2/ticket_fields
        """
        print(f"🔧 Fetching custom ticket fields...")
        fields = []
        url = "ticket_fields"

        while url:
            data = self._get(url)
            fields.extend(data.get('ticket_fields', []))

            # Handle pagination
            next_page = data.get('next_page')
            if next_page:
                url = next_page.split('/api/v2/')[-1]
            else:
                url = None

        # Filter only custom fields (not system fields)
        custom_fields = [
            f for f in fields
            if f.get('type') in ['text', 'textarea', 'checkbox', 'date',
                                  'integer', 'decimal', 'regexp', 'tagger',
                                  'multiselect', 'dropdown', 'lookup']
        ]

        print(f"   Found {len(custom_fields)} custom fields")
        return custom_fields

    def get_sla_policies(self) -> List[Dict]:
        """
        Fetch SLA policies
        GET /api/v2/slas/policies
        """
        print(f"📊 Fetching SLA policies...")
        data = self._get("slas/policies")
        policies = data.get('sla_policies', [])
        print(f"   Found {len(policies)} SLA policies")
        return policies

    def get_user(self, user_id: int) -> Dict:
        """
        Fetch user details
        GET /api/v2/users/{user_id}
        """
        data = self._get(f"users/{user_id}")
        return data.get('user', {})

    def get_group(self, group_id: int) -> Dict:
        """
        Fetch group details
        GET /api/v2/groups/{group_id}
        """
        data = self._get(f"groups/{group_id}")
        return data.get('group', {})

    def get_organization(self, org_id: int) -> Dict:
        """
        Fetch organization details
        GET /api/v2/organizations/{org_id}
        """
        data = self._get(f"organizations/{org_id}")
        return data.get('organization', {})

    def fetch_complete_ticket_data(self, ticket_id: int) -> Dict:
        """
        Fetch ALL data for a ticket in one go
        Returns a complete dictionary with all ticket information
        """
        print(f"\n🎯 Fetching complete data for ticket {ticket_id}...")

        complete_data = {
            'ticket': None,
            'comments': [],
            'audits': [],
            'metrics': None,
            'custom_fields_mapping': []
        }

        try:
            # Fetch core ticket data
            complete_data['ticket'] = self.get_ticket(ticket_id)

            # Fetch comments (conversation)
            complete_data['comments'] = self.get_ticket_comments(ticket_id)

            # Fetch audits (timeline)
            complete_data['audits'] = self.get_ticket_audits(ticket_id)

            # Fetch metrics (SLA data)
            complete_data['metrics'] = self.get_ticket_metrics(ticket_id)

            # Fetch custom field mappings (only once per session, can be cached)
            complete_data['custom_fields_mapping'] = self.get_custom_fields()

            print(f"✅ Complete data fetched for ticket {ticket_id}")

        except Exception as e:
            print(f"❌ Error fetching ticket data: {e}")
            raise

        return complete_data

    def test_connection(self) -> bool:
        """Test Zendesk API connection"""
        try:
            print("🔍 Testing Zendesk API connection...")
            self._get("tickets", params={'per_page': 1})
            print("✅ Zendesk API connection successful!")
            return True
        except Exception as e:
            print(f"❌ Zendesk API connection failed: {e}")
            return False
