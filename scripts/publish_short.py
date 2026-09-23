"""Short-form (3x daily) pipeline: pull the next approved story, render a 9:16
video, post it to TikTok / YouTube Shorts / Instagram Reels via Buffer,
and mark it Posted in Notion."""
import datetime
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
from render_video import render  # noqa: E402
from github_release import publish_release_asset  # noqa: E402
import notion_client  # noqa: E402
import buffer_client  # noqa: E402

REPO = os.environ.get("GITHUB_REPOSITORY", "")  # auto-set by Actions


def main():
    item = notion_client.get_next_short_form_item()
    if item is None:
        print("No Approved short-form items in the queue. Nothing to do.")
        return

    with tempfile.TemporaryDirectory() as tmp:
        out_path = os.path.join(tmp, "short.mp4")
        render(item["hook_line"], item["script_short"], out_path, orientation="vertical")

        tag = f"short-{item['page_id'][:8]}-{datetime.date.today().isoformat()}"
        media_url = publish_release_asset(
            REPO, tag, f"KarmaClockIn short {datetime.date.today().isoformat()}",
            out_path, "short.mp4",
        )

    caption = item["hook_line"]
    org_id = buffer_client.get_organization_id()
    channels = buffer_client.get_channel_ids(org_id)
    for service in ("tiktok", "youtube", "instagram"):
        if service not in channels:
            raise RuntimeError(
                f"No {service} channel connected in Buffer yet - connect it at "
                "publish.buffer.com before running this pipeline."
            )

    buffer_client.create_video_post(
        channels["tiktok"], caption, media_url,
        metadata={"tiktok": {"isAiGenerated": True}},
    )
    buffer_client.create_video_post(
        channels["youtube"], caption, media_url,
        metadata={"youtube": {
            "title": item["hook_line"][:95],
            "categoryId": buffer_client.YOUTUBE_CATEGORY_ENTERTAINMENT,
            "privacy": "public",
            "madeForKids": False,
            "isAiGenerated": True,
        }},
    )
    buffer_client.create_video_post(
        channels["instagram"], caption, media_url,
        metadata={"instagram": {
            "type": "reel",
            "shouldShareToFeed": True,
            "isAiGenerated": True,
        }},
    )

    notion_client.mark_short_form_posted(item["page_id"], ["TikTok", "YouTube", "Instagram"])
    print(f"Posted short-form video for page {item['page_id']}")


if __name__ == "__main__":
    main()
