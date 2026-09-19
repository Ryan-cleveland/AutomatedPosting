"""
Thin wrapper around Buffer's GraphQL API (https://developers.buffer.com).

Requires:
  BUFFER_API_KEY - personal API key from publish.buffer.com/settings/api

Buffer must already have TikTok, YouTube, and Instagram channels connected
via its own dashboard (publish.buffer.com) - the API acts on channels you've
already connected there; it doesn't do the initial OAuth linking.

Buffer is TikTok's and YouTube's own audited API partner, so posts created
here publish with normal (public) visibility - no manual privacy toggling,
no separate TikTok audit needed on your end.
"""

import datetime
import os

import requests

BASE = "https://api.buffer.com"

# YouTube category id for workplace/karma story narration content.
YOUTUBE_CATEGORY_ENTERTAINMENT = "24"


def _headers():
    return {
        "Authorization": f"Bearer {os.environ['BUFFER_API_KEY']}",
        "Content-Type": "application/json",
    }


def _gql(query, variables=None):
    resp = requests.post(
        BASE,
        headers=_headers(),
        json={"query": query, "variables": variables or {}},
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("errors"):
        raise RuntimeError(f"Buffer API error: {payload['errors']}")
    return payload["data"]


def get_organization_id():
    data = _gql("query GetOrganizations { account { organizations { id name } } }")
    orgs = data["account"]["organizations"]
    if not orgs:
        raise RuntimeError("No Buffer organizations found for this API key.")
    return orgs[0]["id"]


def list_channels(organization_id):
    query = """
    query GetChannels($organizationId: OrganizationId!) {
      channels(input: { organizationId: $organizationId }) {
        id
        name
        service
      }
    }
    """
    data = _gql(query, {"organizationId": organization_id})
    return data["channels"]


CREATE_POST_MUTATION = """
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    ... on PostActionSuccess {
      post { id text dueAt }
    }
    ... on MutationError {
      message
    }
  }
}
"""


def create_video_post(channel_id, text, video_url, metadata=None, delay_minutes=5):
    """Schedule a video post on one channel, a few minutes out so Buffer's
    publish worker has time to pick it up. metadata is the per-network block,
    e.g. {"youtube": {...}} or {"instagram": {...}} or {"tiktok": {...}}."""
    due_at = (
        datetime.datetime.utcnow() + datetime.timedelta(minutes=delay_minutes)
    ).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    post_input = {
        "channelId": channel_id,
        "text": text,
        "schedulingType": "automatic",
        "mode": "customScheduled",
        "dueAt": due_at,
        "assets": [{"video": {"url": video_url}}],
    }
    if metadata:
        post_input["metadata"] = metadata

    data = _gql(CREATE_POST_MUTATION, {"input": post_input})
    result = data["createPost"]
    if result.get("post"):
        return result["post"]
    raise RuntimeError(f"Buffer rejected the post: {result.get('message', 'unknown error')}")
