"""Patreon OAuth 2.0 helpers — no Streamlit dependency."""

import requests
from urllib.parse import urlencode

AUTHORIZE_URL = "https://www.patreon.com/oauth2/authorize"
TOKEN_URL = "https://www.patreon.com/api/oauth2/token"
IDENTITY_URL = "https://www.patreon.com/api/oauth2/v2/identity"


def build_auth_url(client_id: str, redirect_uri: str) -> str:
    """Return the Patreon OAuth authorization URL."""
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "identity memberships",
    }
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


def exchange_code(code: str, client_id: str, client_secret: str, redirect_uri: str) -> str:
    """Exchange an authorization code for an access token.

    Returns the access token string.
    Raises requests.HTTPError on failure.
    """
    resp = requests.post(
        TOKEN_URL,
        data={
            "code": code,
            "grant_type": "authorization_code",
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def is_active_patron(access_token: str, campaign_id: str) -> bool:
    """Return True if the token owner is an active patron of the given campaign.

    Calls the Patreon v2 identity endpoint with memberships included and checks
    whether any membership record has patron_status == 'active_patron' and
    belongs to campaign_id.
    """
    resp = requests.get(
        IDENTITY_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        params={
            "include": "memberships",
            "fields[member]": "patron_status",
            "fields[user]": "email,full_name",
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    for item in data.get("included", []):
        if item.get("type") != "member":
            continue
        attrs = item.get("attributes", {})
        campaign = item.get("relationships", {}).get("campaign", {}).get("data", {})
        if (
            attrs.get("patron_status") == "active_patron"
            and campaign.get("id") == campaign_id
        ):
            return True

    return False
