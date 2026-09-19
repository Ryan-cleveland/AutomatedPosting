"""Minimal direct Metricool API client (no MCP available on a GitHub Actions
runner). Requires an Advanced/Custom-plan API token (Account Settings > API
in the Metricool web app) -- separate from, and not implied by, MCP access."""
import os

import requests

API_BASE = "https://app.metricool.com/api/v2/scheduler/posts"
BLOG_ID = "7028465"


def _headers():
    return {
        "X-Mc-Auth": os.environ["METRICOOL_API_TOKEN"],
        "Content-Type": "application/json",
    }


def _user_id():
    return os.environ["METRICOOL_USER_ID"]


def schedule_post(publish_at_iso, timezone, text, media_url, providers, network_data, autopublish=True):
    """publish_at_iso: 'YYYY-MM-DDTHH:MM:SS' (no offset -- timezone is separate)."""
    params = {"userId": _user_id(), "blogId": BLOG_ID}
    body = {
        "autoPublish": autopublish,
        "draft": False,
        "media": [media_url],
        "providers": [{"network": p} for p in providers],
        "publicationDate": {"dateTime": publish_at_iso, "timezone": timezone},
        "text": text,
    }
    body.update(network_data)  # e.g. {"tiktokData": {...}, "youtubeData": {...}}
    resp = requests.post(API_BASE, headers=_headers(), params=params, json=body, timeout=60)
    resp.raise_for_status()
    return resp.json()
