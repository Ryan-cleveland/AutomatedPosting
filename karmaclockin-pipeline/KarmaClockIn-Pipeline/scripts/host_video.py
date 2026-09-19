"""
Buffer's API has no file-upload endpoint - it fetches media from a public URL
you provide, and that URL must stay reachable (not expire) until the post
actually publishes. A GitHub Release asset on this same repo is a free,
stable, non-expiring public URL, so we use that instead of a signed link
from S3/Cloudinary that would work at creation time but die before Buffer
gets to it.

Requires the `gh` CLI (preinstalled on GitHub-hosted runners) authenticated
via GH_TOKEN, and the workflow's default GITHUB_TOKEN needs
`permissions: contents: write` for release creation to succeed.
"""

import os
import subprocess
import time


def upload_release_asset(file_path, repo=None):
    repo = repo or os.environ["GITHUB_REPOSITORY"]  # "owner/repo", set by Actions
    tag = f"render-{int(time.time())}"

    subprocess.run(
        [
            "gh", "release", "create", tag, file_path,
            "--repo", repo,
            "--title", tag,
            "--notes", "Automated render artifact, hosted here only so Buffer can fetch it.",
        ],
        check=True,
    )

    filename = os.path.basename(file_path)
    return f"https://github.com/{repo}/releases/download/{tag}/{filename}"
