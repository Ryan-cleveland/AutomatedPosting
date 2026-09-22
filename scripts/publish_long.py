"""Weekly long-form pipeline: pull the next approved story whose
long_form_posted flag isn't set, render a 16:9 video from script_long, post
it to YouTube as a regular long-form video via Buffer, and mark
long_form_posted in Notion. Deliberately does not touch status /
platforms_posted / posted_date -- those belong to the daily short-form run."""
import datetime
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
from render_video import render  # noqa: E402
from github_release import publish_release_asset  # noqa: E402
import notion_client  # noqa: E402
import buffer_client  # noqa: E402

REPO = os.environ.get("GITHUB_REPOSITORY", "")


def main():
    item = notion_client.get_next_long_form_item()
    if item is None:
        print("No Approved long-form-eligible items in the queue. Nothing to do.")
        return

    with tempfile.TemporaryDirectory() as tmp:
        out_path = os.path.join(tmp, "long.mp4")
        render(item["hook_line"], item["script_long"], out_path, orientation="horizontal")

        tag = f"long-{item['page_id'][:8]}-{datetime.date.today().isoformat()}"
        media_url = publish_release_asset(
            REPO, tag, f"KarmaClockIn long-form {datetime.date.today().isoformat()}",
            out_path, "long.mp4",
        )

    org_id = buffer_client.get_organization_id()
    channels = buffer_client.get_channel_ids(org_id)
    if "youtube" not in channels:
        raise RuntimeError(
            "No youtube channel connected in Buffer yet - connect it at "
            "publish.buffer.com before running this pipeline."
        )

    buffer_client.create_video_post(
        channels["youtube"], item["hook_line"], media_url,
        metadata={"youtube": {
            "title": item["hook_line"][:95],
            "categoryId": buffer_client.YOUTUBE_CATEGORY_ENTERTAINMENT,
            "privacy": "public",
            "madeForKids": False,
            "isAiGenerated": True,
        }},
    )

    notion_client.mark_long_form_posted(item["page_id"])
    print(f"Posted long-form video for page {item['page_id']}")


if __name__ == "__main__":
    main()
