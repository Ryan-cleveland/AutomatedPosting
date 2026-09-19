"""Minimal direct Notion API client for the KarmaClockIn Content Queue
database (no MCP available on a GitHub Actions runner)."""
import datetime
import os

import requests

NOTION_VERSION = "2022-06-28"
DATA_SOURCE_ID = "749722ff-e939-46e8-b193-a852f146e21d"
API_BASE = "https://api.notion.com/v1"


def _headers():
    return {
        "Authorization": f"Bearer {os.environ['NOTION_API_KEY']}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _prop_text(page, name):
    prop = page["properties"].get(name, {})
    rich = prop.get("rich_text") or prop.get("title") or []
    return "".join(t.get("plain_text", "") for t in rich)


def get_next_short_form_item():
    """Oldest Approved item not yet posted (status still 'Approved')."""
    body = {
        "filter": {"property": "status", "select": {"equals": "Approved"}},
        "sorts": [{"property": "created_date", "direction": "ascending"}],
        "page_size": 1,
    }
    resp = requests.post(
        f"{API_BASE}/data_sources/{DATA_SOURCE_ID}/query",
        headers=_headers(), json=body, timeout=30,
    )
    resp.raise_for_status()
    results = resp.json().get("results", [])
    if not results:
        return None
    page = results[0]
    return {
        "page_id": page["id"],
        "hook_line": _prop_text(page, "hook_line"),
        "script_short": _prop_text(page, "script_short"),
        "script_long": _prop_text(page, "script_long"),
    }


def get_next_long_form_item():
    """Oldest Approved item whose long_form_posted checkbox is not set."""
    body = {
        "filter": {
            "and": [
                {"property": "status", "select": {"equals": "Approved"}},
                {"property": "long_form_posted", "checkbox": {"equals": False}},
            ]
        },
        "sorts": [{"property": "created_date", "direction": "ascending"}],
        "page_size": 1,
    }
    resp = requests.post(
        f"{API_BASE}/data_sources/{DATA_SOURCE_ID}/query",
        headers=_headers(), json=body, timeout=30,
    )
    resp.raise_for_status()
    results = resp.json().get("results", [])
    if not results:
        return None
    page = results[0]
    return {
        "page_id": page["id"],
        "hook_line": _prop_text(page, "hook_line"),
        "script_short": _prop_text(page, "script_short"),
        "script_long": _prop_text(page, "script_long"),
    }


def mark_short_form_posted(page_id, platforms):
    today = datetime.date.today().isoformat()
    body = {
        "properties": {
            "status": {"select": {"name": "Posted"}},
            "posted_date": {"date": {"start": today}},
            "platforms_posted": {"multi_select": [{"name": p} for p in platforms]},
        }
    }
    resp = requests.patch(
        f"{API_BASE}/pages/{page_id}", headers=_headers(), json=body, timeout=30,
    )
    resp.raise_for_status()


def mark_long_form_posted(page_id):
    today = datetime.date.today().isoformat()
    body = {
        "properties": {
            "long_form_posted": {"checkbox": True},
            "long_form_posted_date": {"date": {"start": today}},
        }
    }
    resp = requests.patch(
        f"{API_BASE}/pages/{page_id}", headers=_headers(), json=body, timeout=30,
    )
    resp.raise_for_status()
