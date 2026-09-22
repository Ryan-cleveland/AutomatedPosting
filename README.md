# KarmaClockIn automation pipeline

Free, fully server-side rendering + posting pipeline for the KarmaClockIn
faceless channel, running on GitHub Actions (no dependency on any local
computer being on).

## What it does

- `publish-short.yml` (daily, 8am Central): pulls the oldest Approved story
  from the Notion Content Queue, generates narration with ElevenLabs, renders
  a 9:16 video (free-licensed looping background + burned-in captions) with
  ffmpeg, uploads it as a GitHub Release asset (for a public URL), and posts
  it to TikTok / YouTube Shorts / Instagram Reels via the Buffer API.
- `publish-long.yml` (weekly, Sundays 9am Central): same idea but pulls a
  story whose `long_form_posted` checkbox isn't set yet, renders 16:9 from
  `script_long`, and posts a regular YouTube video.

Posting goes through Buffer rather than Metricool: Buffer's Free plan (3
channels) includes real API access, and Buffer is TikTok's and YouTube's own
audited API partner, so posts publish with normal public visibility - no
TikTok audit to do yourself, no subscription cost.

**Heads up on cadence:** the short-form workflow currently runs once a day.
If you want the 4-5x/day posting rate from the original plan, that means
either adding more `cron` lines to `publish-short.yml` or changing the
Notion query to pull more than one item per run - it's a small change, just
flagging that today's schedule doesn't match that goal yet.

## Required repo secrets

Set these under Settings -> Secrets and variables -> Actions:

- `ELEVENLABS_API_KEY` -- from elevenlabs.io account settings -> API Keys.
- `ELEVENLABS_VOICE_ID` -- `mF5WrdU1593fy3PUKaSW` (Dean - Calm, Authoritative),
  the channel's locked-in narrator voice.
- `NOTION_TOKEN` -- an internal integration token from
  notion.so/my-integrations, shared with the Content Queue database.
- `BUFFER_API_KEY` -- personal API key from publish.buffer.com/settings/api.
  TikTok, YouTube, and Instagram need to already be connected to Buffer
  through its own dashboard first - the API only acts on channels connected
  there, it doesn't do the initial OAuth linking.

`GITHUB_TOKEN` is provided automatically by Actions -- no setup needed.

## Important: this repo must be public

Rendered videos are published as GitHub Release assets so Buffer's servers
can fetch them by URL. A private repo's release assets require an
authenticated request to download, which Buffer can't do -- so this only
works if the repo is public. No secrets live in the repo itself (they're
encrypted Actions secrets), so this is safe; the videos themselves are about
to be posted publicly on social media anyway. Old releases are safe to
delete periodically to keep the repo tidy - Buffer only needs each one until
that post actually publishes.

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
export ELEVENLABS_VOICE_ID=mF5WrdU1593fy3PUKaSW
python scripts/render_video.py --hook-line "..." --script-file story.txt --output out.mp4
```

## Known rough edges

- Buffer call shapes in `scripts/buffer_client.py` are built from Buffer's
  own GraphQL type reference (`CreatePostInput`, `YoutubePostMetadataInput`,
  `InstagramPostMetadataInput`, `TikTokPostMetadataInput`), not confirmed
  against a live account yet - run each workflow once by hand
  (`workflow_dispatch`) and check the Buffer dashboard before trusting the
  cron schedule with it.
- Captions (`scripts/captions.py`) time each line proportionally by
  character count over the narration's total duration, not real word-level
  alignment - good enough for readable static lines, but not frame-perfect
  sync.
- No retry/backoff on any API call -- a transient failure just fails the
  run; re-trigger manually or wait for the next scheduled slot.
