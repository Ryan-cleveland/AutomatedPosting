"""Daily short-form pipeline: pull the next approved story, render a 9:16
video, post it to TikTok / YouTube Shorts / Instagram Reels via Metricool,
and mark it Posted in Notion."""
import datetime
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
from render_video import render  # noqa: E402
from github_release import publish_release_asset  # noqa: E402
import notion_client  # noqa: E402
import metricool_client  # noqa: E402

REPO = os.environ.get("GITHUB_REPOSITORY", "")  # auto-set by Actions
TIMEZONE = "America/Chicago"


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

    now = datetime.datetime.now()
    publish_at = now.strftime("%Y-%m-%dT%H:%M:%S")

    providers = ["tiktok", "youtube", "instagram"]
    network_data = {
        "youtubeData": {"title": item["hook_line"][:95], "type": "short", "privacy": "public",
                          "madeForKids": False, "isAiGeneratedContent": True},
        "tiktokData": {"privacyOption": "PUBLIC_TO_EVERYONE", "isAigc": True},
        "instagramData": {"type": "REEL", "isAiGenerated": True},
    }
    metricool_client.schedule_post(
        publish_at, TIMEZONE, item["hook_line"], media_url, providers, network_data,
    )

    notion_client.mark_short_form_posted(item["page_id"], ["TikTok", "YouTube", "Instagram"])
    print(f"Posted short-form video for page {item['page_id']}")


if __name__ == "__main__":
    main()
