# KarmaClockIn automation pipeline

Free, fully server-side rendering + posting pipeline for the KarmaClockIn
faceless channel, running on GitHub Actions (no dependency on any local
computer being on).

## What it does

- `publish-short.yml` (daily, 8am Central): pulls the oldest Approved story
  from the Notion Content Queue, generates narration with ElevenLabs, renders
  a 9:16 video (free-licensed looping background + burned-in captions) with
  ffmpeg, uploads it as a GitHub Release asset (for a public URL), and posts
  it to TikTok / YouTube Shorts / Instagram Reels via the Metricool API.
- `publish-long.yml` (weekly, Sundays 9am Central): same idea but pulls a
  story whose `long_form_posted` checkbox isn't set yet, renders 16:9 from
  `script_long`, and posts a regular YouTube video.

## Required repo secrets

Set these under Settings -> Secrets and variables -> Actions:

- `ELEVENLABS_API_KEY` -- from elevenlabs.io account settings -> API Keys.
- `NOTION_API_KEY` -- an internal integration token from
  notion.so/my-integrations, shared with the Content Queue database.
- `METRICOOL_API_TOKEN` -- from Metricool Account Settings -> API
  (requires the Advanced or Custom plan -- separate from MCP access, which
  works on any plan).
- `METRICOOL_USER_ID` -- your Metricool numeric user id (visible in the same
  API settings page, or in any Metricool API URL).

`GITHUB_TOKEN` is provided automatically by Actions -- no setup needed.

## Important: this repo must be public

Rendered videos are published as GitHub Release assets so Metricool's
servers can fetch them by URL. A private repo's release assets require an
authenticated request to download, which Metricool can't do -- so this only
works if the repo is public. No secrets live in the repo itself (they're
encrypted Actions secrets), so this is safe; the videos themselves are about
to be posted publicly on social media anyway.

## Assets

`assets/backgrounds/` holds free, properly-licensed looping background
clips. The renderer picks one deterministically per story (same story always
gets the same clip). Add more clips here for variety -- just make sure each
one is free for commercial use (e.g. Mixkit, Pexels, Pixabay) and drop the
license/source URL in a comment in this file when you add one:

- `liquid_marble.mp4` -- Mixkit "Psychedelic Liquid Marble Background",
  Mixkit Stock Video Free License (free for commercial use, no attribution
  required). https://mixkit.co/free-stock-video/psychedelic-liquid-marble-background-101738/

## Local testing

```
pip install -r requirements.txt
export ELEVENLABS_API_KEY=...
python scripts/render_video.py --hook-line "..." --script-file story.txt --output out.mp4
```
