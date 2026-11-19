"""Push Hot Prospect leads straight into HubSpot or Salesforce.

HubSpot   — each lead becomes a Contact (lifecycle stage "lead") plus a Note with
            the complaint, urgency and suggested angle. Auth: a private-app
            access token (HUBSPOT_ACCESS_TOKEN) with the
            crm.objects.contacts.read and crm.objects.contacts.write scopes.
Salesforce — each lead becomes a Lead record. Auth: SALESFORCE_INSTANCE_URL plus
            either SALESFORCE_ACCESS_TOKEN, or SALESFORCE_CLIENT_ID and
            SALESFORCE_CLIENT_SECRET of a connected app with the
            client-credentials flow enabled.

A Reddit lead has no e-mail, so the post URL (stored in the CRM's standard
Website field) is the identity used to avoid creating the same lead twice.
"""

import logging
import os
import time
from dataclasses import dataclass, field
from html import escape
from typing import Protocol

import requests

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 15
_SALESFORCE_API_VERSION = os.getenv("SALESFORCE_API_VERSION") or "v60.0"
_HUBSPOT_BASE_URL = "https://api.hubapi.com"
_HUBSPOT_NOTE_TO_CONTACT = 202  # HubSpot-defined association type id


class CRMConfigError(RuntimeError):
    """The requested CRM is not configured (missing credentials)."""


class CRMError(RuntimeError):
    """The CRM rejected a request."""


@dataclass
class LeadResult:
    username: str
    status: str                    # created | exists | skipped | failed
    record_id: str | None = None
    record_url: str | None = None
    error: str | None = None


@dataclass
class PushResult:
    target: str
    results: list[LeadResult] = field(default_factory=list)

    def summary(self) -> dict:
        counts = {s: sum(r.status == s for r in self.results) for s in ("created", "exists", "skipped", "failed")}
        return {
            "target": self.target,
            **counts,
            "results": [vars(r) for r in self.results],
        }


# ── Shared lead formatting ────────────────────────────────────────────────────


def lead_summary_lines(lead: dict) -> list[str]:
    """Plain-text description of a lead, shared by both CRMs."""
    signals = ", ".join(lead.get("company_signals") or []) or "none detected"
    return [
        "Switching-intent prospect found by RivalSense.",
        f"Competitor: {lead.get('competitor_name', '')}",
        f"Urgency score: {float(lead.get('urgency_score') or 0):.2f}",
        f"Posted: {lead.get('created_at', '')} by {lead.get('username', '')}",
        f"Post: {lead.get('post_url', '')}",
        "",
        f"Complaint: {lead.get('complaint_summary', '')}",
        "",
        f"Suggested angle: {lead.get('suggested_angle', '')}",
        f"Company signals: {signals}",
    ]


def _company_placeholder(lead: dict) -> str:
    return f"Unknown ({lead.get('competitor_name') or 'competitor'} user via Reddit)"


def _error_text(resp: requests.Response) -> str:
    try:
        body = resp.json()
    except ValueError:
        return f"HTTP {resp.status_code}"
    if isinstance(body, list) and body:              # Salesforce: [{message, errorCode}]
        body = body[0]
    if isinstance(body, dict):
        msg = body.get("message") or body.get("error_description") or body.get("error")
        if msg:
            return f"HTTP {resp.status_code}: {msg}"
    return f"HTTP {resp.status_code}"


def _send(session: requests.Session, method: str, url: str, **kwargs) -> requests.Response:
    """One request with a single polite retry on HTTP 429 (both CRMs rate-limit)."""
    resp = session.request(method, url, timeout=_TIMEOUT_SECONDS, **kwargs)
    if resp.status_code == 429:
        wait = min(float(resp.headers.get("Retry-After") or 2), 10.0)
        time.sleep(wait)
        resp = session.request(method, url, timeout=_TIMEOUT_SECONDS, **kwargs)
    if resp.status_code >= 400:
        raise CRMError(_error_text(resp))
    return resp


class CRMClient(Protocol):
    name: str

    def find_existing(self, post_url: str) -> str | None: ...
    def create(self, lead: dict) -> tuple[str, str | None]: ...


# ── HubSpot ───────────────────────────────────────────────────────────────────


class HubSpotClient:
    name = "hubspot"

    def __init__(self, token: str, session: requests.Session | None = None) -> None:
        self._session = session or requests.Session()
        self._session.headers.update(
            {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        )

    @classmethod
    def from_env(cls) -> "HubSpotClient":
        token = os.getenv("HUBSPOT_ACCESS_TOKEN", "")
        if not token:
            raise CRMConfigError("HUBSPOT_ACCESS_TOKEN is not set.")
        return cls(token)

    def find_existing(self, post_url: str) -> str | None:
        resp = _send(
            self._session, "POST", f"{_HUBSPOT_BASE_URL}/crm/v3/objects/contacts/search",
            json={
                "filterGroups": [
                    {"filters": [{"propertyName": "website", "operator": "EQ", "value": post_url}]}
                ],
                "properties": ["website"],
                "limit": 1,
            },
        )
        results = resp.json().get("results") or []
        return str(results[0]["id"]) if results else None

    def create(self, lead: dict) -> tuple[str, str | None]:
        contact = _send(
            self._session, "POST", f"{_HUBSPOT_BASE_URL}/crm/v3/objects/contacts",
            json={
                "properties": {
                    "firstname": lead.get("username") or "Reddit prospect",
                    "company": _company_placeholder(lead),
                    "website": lead.get("post_url", ""),
                    "lifecyclestage": "lead",
                }
            },
        ).json()
        contact_id = str(contact["id"])

        # The context a rep needs lives in a note on the contact.
        _send(
            self._session, "POST", f"{_HUBSPOT_BASE_URL}/crm/v3/objects/notes",
            json={
                "properties": {
                    "hs_timestamp": str(int(time.time() * 1000)),
                    "hs_note_body": "<br>".join(escape(line) for line in lead_summary_lines(lead)),
                },
                "associations": [
                    {
                        "to": {"id": contact_id},
                        "types": [
                            {
                                "associationCategory": "HUBSPOT_DEFINED",
                                "associationTypeId": _HUBSPOT_NOTE_TO_CONTACT,
                            }
                        ],
                    }
                ],
            },
        )
        return contact_id, None


# ── Salesforce ────────────────────────────────────────────────────────────────


def _soql_literal(value: str) -> str:
    """Quote a string for SOQL (backslash and single quote must be escaped)."""
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


class SalesforceClient:
    name = "salesforce"

    def __init__(self, instance_url: str, token: str, session: requests.Session | None = None) -> None:
        self._base = instance_url.rstrip("/")
        self._api = f"{self._base}/services/data/{_SALESFORCE_API_VERSION}"
        self._session = session or requests.Session()
        self._session.headers.update(
            {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        )

    @staticmethod
    def is_configured() -> bool:
        has_auth = os.getenv("SALESFORCE_ACCESS_TOKEN") or (
            os.getenv("SALESFORCE_CLIENT_ID") and os.getenv("SALESFORCE_CLIENT_SECRET")
        )
        return bool(os.getenv("SALESFORCE_INSTANCE_URL") and has_auth)

    @classmethod
    def from_env(cls, session: requests.Session | None = None) -> "SalesforceClient":
        instance = os.getenv("SALESFORCE_INSTANCE_URL", "").rstrip("/")
        if not instance:
            raise CRMConfigError("SALESFORCE_INSTANCE_URL is not set.")

        token = os.getenv("SALESFORCE_ACCESS_TOKEN", "")
        if not token:
            client_id = os.getenv("SALESFORCE_CLIENT_ID", "")
            secret = os.getenv("SALESFORCE_CLIENT_SECRET", "")
            if not (client_id and secret):
                raise CRMConfigError(
                    "Set SALESFORCE_ACCESS_TOKEN, or SALESFORCE_CLIENT_ID and SALESFORCE_CLIENT_SECRET."
                )
            session = session or requests.Session()
            resp = session.post(
                f"{instance}/services/oauth2/token",
                data={"grant_type": "client_credentials", "client_id": client_id, "client_secret": secret},
                timeout=_TIMEOUT_SECONDS,
            )
            if resp.status_code >= 400:
                raise CRMError(f"Salesforce login failed: {_error_text(resp)}")
            token = resp.json()["access_token"]
            instance = resp.json().get("instance_url", instance).rstrip("/")
        return cls(instance, token, session)

    def find_existing(self, post_url: str) -> str | None:
        soql = f"SELECT Id FROM Lead WHERE Website = {_soql_literal(post_url)} LIMIT 1"
        records = _send(self._session, "GET", f"{self._api}/query", params={"q": soql}).json().get("records") or []
        return str(records[0]["Id"]) if records else None

    def create(self, lead: dict) -> tuple[str, str | None]:
        body = {
            "LastName": (lead.get("username") or "Reddit prospect")[:80],
            "Company": _company_placeholder(lead)[:255],
            "Website": (lead.get("post_url") or "")[:255],
            "LeadSource": "Web",
            "Description": "\n".join(lead_summary_lines(lead))[:32000],
        }
        created = _send(self._session, "POST", f"{self._api}/sobjects/Lead/", json=body).json()
        record_id = str(created["id"])
        return record_id, f"{self._base}/lightning/r/Lead/{record_id}/view"


# ── Public API ────────────────────────────────────────────────────────────────


TARGETS = ("hubspot", "salesforce")


def crm_status() -> dict[str, bool]:
    """Which CRMs have credentials configured."""
    return {
        "hubspot": bool(os.getenv("HUBSPOT_ACCESS_TOKEN")),
        "salesforce": SalesforceClient.is_configured(),
    }


def client_for(target: str) -> CRMClient:
    if target == "hubspot":
        return HubSpotClient.from_env()
    if target == "salesforce":
        return SalesforceClient.from_env()
    raise ValueError(f"Unknown CRM target '{target}'")


def push_leads(
    client: CRMClient,
    leads: list[dict],
    is_synthetic=lambda lead: bool(lead.get("is_synthetic")),
) -> PushResult:
    """Create every lead that is not already in the CRM.

    Synthetic sample leads are never sent — they would pollute a real CRM.
    One failing lead does not stop the rest; its error is reported per lead.
    """
    result = PushResult(target=client.name)

    for lead in leads:
        username = str(lead.get("username") or "")
        post_url = str(lead.get("post_url") or "")

        if is_synthetic(lead):
            result.results.append(LeadResult(username, "skipped", error="Sample data — not sent to the CRM."))
            continue
        if not post_url:
            result.results.append(LeadResult(username, "failed", error="Lead has no post URL."))
            continue

        try:
            existing = client.find_existing(post_url)
            if existing:
                result.results.append(LeadResult(username, "exists", record_id=existing))
                continue
            record_id, record_url = client.create(lead)
            result.results.append(LeadResult(username, "created", record_id, record_url))
        except (CRMError, requests.RequestException, KeyError, ValueError) as exc:
            logger.warning("[%s] Could not push lead %s: %s", client.name, username, exc)
            result.results.append(LeadResult(username, "failed", error=str(exc)))

    logger.info("[%s] CRM push: %s", client.name, {k: v for k, v in result.summary().items() if k != "results"})
    return result
