import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from notion_client import get_next_approved_item, mark_posted
from generate_narration import generate_narration
from build_captions import chars_to_words, group_into_lines, build_ass
from render_video import render
from host_video import upload_release_asset
from buffer_client import (
    get_organization_id,
    list_channels,
    create_video_post,
    YOUTUBE_CATEGORY_ENTERTAINMENT,
)

# Must match the exact multi_select option names on platforms_posted in Notion.
PLATFORM_LABELS = ["TikTok", "YouTube", "Instagram"]


def main():
    item = get_next_approved_item()
    if item is None:
        print("No Approved items in the queue. Nothing to do.")
        return

    print(f"Processing queue item #{item['id']}: {item['hook_line']}")
    caption = item["hook_line"]

    alignment = generate_narration(item["script_short"], "narration.mp3")
    words = chars_to_words(alignment)
    lines = group_into_lines(words)
    build_ass(lines, "captions.ass")

    video_path = render("narration.mp3", "captions.ass", "final.mp4")

    video_url = upload_release_asset(video_path)
    print(f"Video hosted at {video_url}")

    org_id = get_organization_id()
    channels = {c["service"]: c["id"] for c in list_channels(org_id)}
    for service in ("tiktok", "youtube", "instagram"):
        if service not in channels:
            raise RuntimeError(
                f"No {service} channel connected in Buffer yet - connect it at "
                "publish.buffer.com before running this pipeline."
            )

    create_video_post(
        channels["tiktok"], caption, video_url,
        metadata={"tiktok": {"isAiGenerated": True}},
    )

    create_video_post(
        channels["youtube"], caption, video_url,
        metadata={"youtube": {
            "title": caption[:100],
            "categoryId": YOUTUBE_CATEGORY_ENTERTAINMENT,
            "privacy": "public",
            "madeForKids": False,
            "isAiGenerated": True,
        }},
    )

    create_video_post(
        channels["instagram"], caption, video_url,
        metadata={"instagram": {
            "type": "reel",
            "shouldShareToFeed": True,
            "isAiGenerated": True,
        }},
    )

    mark_posted(item["page_id"], PLATFORM_LABELS)
    print(f"Done: queue item #{item['id']} posted to all three platforms and marked in Notion.")


if __name__ == "__main__":
    main()
