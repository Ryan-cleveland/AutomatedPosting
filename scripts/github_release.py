"""Publish a rendered video as a GitHub Release asset so it has a public,
directly-downloadable, non-expiring URL Buffer's servers can fetch. Buffer
has no upload endpoint of its own - it fetches media by URL, and that URL
must stay reachable until the post actually publishes, so a signed/expiring
link (S3 presigned, Cloudinary signed delivery) would fail silently later.

Requires the repo to be PUBLIC -- a private repo's release assets require
an authenticated request to download, which Buffer's fetcher can't do.
Uses the GITHUB_TOKEN that Actions injects automatically; no extra secret
needed for this part.
"""
import os
import time
import requests

API_BASE = "https://api.github.com"
UPLOAD_ATTEMPTS = 4


def _headers():
    return {
        "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def publish_release_asset(repo, tag, name, file_path, asset_name, content_type="video/mp4"):
    """repo: 'owner/name'. Creates (or reuses) a release at `tag` and
    uploads file_path as an asset, returning its public download URL."""
    resp = requests.post(
        f"{API_BASE}/repos/{repo}/releases",
        headers=_headers(),
        json={"tag_name": tag, "name": name, "body": "Automated KarmaClockIn render.", "draft": False, "prerelease": False},
        timeout=30,
    )
    if resp.status_code == 422:
        # Release for this tag already exists -- fetch it instead.
        resp = requests.get(f"{API_BASE}/repos/{repo}/releases/tags/{tag}", headers=_headers(), timeout=30)
    resp.raise_for_status()
    release = resp.json()

    upload_url = release["upload_url"].split("{")[0]
    size = os.path.getsize(file_path)
    last_err = None
    for attempt in range(1, UPLOAD_ATTEMPTS + 1):
        # A previous failed attempt (or a re-run of the workflow) can leave an
        # asset with the same name behind, which makes the upload 422.
        _delete_existing_asset(repo, release["id"], asset_name)
        try:
            with open(file_path, "rb") as f:
                upload_resp = requests.post(
                    upload_url,
                    headers={**_headers(), "Content-Type": content_type, "Content-Length": str(size)},
                    params={"name": asset_name},
                    data=f,
                    timeout=(30, 600),
                )
            if upload_resp.status_code >= 500:
                raise requests.HTTPError(f"{upload_resp.status_code}: {upload_resp.text[:200]}")
            upload_resp.raise_for_status()
            return upload_resp.json()["browser_download_url"]
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
            if isinstance(e, requests.HTTPError) and e.response is not None and e.response.status_code < 500:
                raise
            last_err = e
            print(f"Asset upload attempt {attempt}/{UPLOAD_ATTEMPTS} failed: {e}")
            if attempt < UPLOAD_ATTEMPTS:
                time.sleep(10 * attempt)
    raise RuntimeError(f"Asset upload failed after {UPLOAD_ATTEMPTS} attempts") from last_err


def _delete_existing_asset(repo, release_id, asset_name):
    resp = requests.get(
        f"{API_BASE}/repos/{repo}/releases/{release_id}/assets",
        headers=_headers(), params={"per_page": 100}, timeout=30,
    )
    resp.raise_for_status()
    for asset in resp.json():
        if asset["name"] == asset_name:
            requests.delete(
                f"{API_BASE}/repos/{repo}/releases/assets/{asset['id']}",
                headers=_headers(), timeout=30,
            ).raise_for_status()
