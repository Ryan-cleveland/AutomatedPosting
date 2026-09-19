"""
Thin wrapper around Notion's public REST API for the Content Queue database.

Requires two env vars:
  NOTION_TOKEN        - an Internal Integration secret (from notion.so/my-integrations)
  NOTION_DATABASE_ID  - the Content Queue database id
                        (09bbd101c54343719837a052978c4556, dashes optional)

IMPORTANT: the integration must be explicitly shared with the Content Queue
database in Notion ("..." menu -> Connections -> add your integration), or
every call below will 404/403 even with a valid token.
"""

import datetime
import os

import requests

NOTION_VERSION = "2022-06-28"
BASE = "https://api.notion.com/v1"


def _headers():
    return {
        "Authorization": f"Bearer {os.environ['NOTION_TOKEN']}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _plain_text(prop):
    """Extract plain text from a title or rich_text property, whichever it is."""
    ptype = prop["type"]
    return "".join(t["plain_text"] for t in prop.get(ptype, []))


def get_next_approved_item():
    """Return the oldest queue item with status=Approved (by the 'id' number
    property), or None if there isn't one."""
    database_id = os.environ["NOTION_DATABASE_ID"]
    payload = {
        "filter": {"property": "status", "select": {"equals": "Approved"}},
        "sorts": [{"property": "id", "direction": "ascending"}],
        "page_size": 1,
    }
    resp = requests.post(
        f"{BASE}/databases/{database_id}/query",
        headers=_headers(),
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    results = resp.json()["results"]
    if not results:
        return None

    page = results[0]
    props = page["properties"]
    return {
        "page_id": page["id"],
        "id": props["id"]["number"],
        "hook_line": _plain_text(props["hook_line"]),
        "script_short": _plain_text(props["script_short"]),
    }


def mark_posted(page_id, platforms):
    """Set status=Posted, posted_date=today, platforms_posted=platforms
    (a list of strings matching the existing multi_select options exactly,
    e.g. ["TikTok", "YouTube", "Instagram"])."""
    payload = {
        "properties": {
            "status": {"select": {"name": "Posted"}},
            "posted_date": {"date": {"start": datetime.date.today().isoformat()}},
            "platforms_posted": {"multi_select": [{"name": p} for p in platforms]},
        }
    }
    resp = requests.patch(
        f"{BASE}/pages/{page_id}", headers=_headers(), json=payload, timeout=30
    )
    resp.raise_for_status()
    return resp.json()
