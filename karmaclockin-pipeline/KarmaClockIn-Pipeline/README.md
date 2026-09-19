# KarmaClockIn-Pipeline

Free, self-hosted rendering + publishing for the KarmaClockin content queue.
Runs entirely on GitHub Actions (no local computer, no paid video API):

Notion (Content Queue, oldest `Approved` row)
&nbsp;&nbsp;→ ElevenLabs narration + word timings
&nbsp;&nbsp;→ ffmpeg burns synced captions over a looping background clip
&nbsp;&nbsp;→ video hosted as a GitHub Release asset (Buffer needs a public URL, not a file upload)
&nbsp;&nbsp;→ Buffer schedules it to TikTok/YouTube/Instagram
&nbsp;&nbsp;→ Notion row marked `Posted`

Posting goes through Buffer instead of Metricool: Buffer's Free plan (3 channels)
includes real API access, and Buffer is TikTok's and YouTube's own audited API
partner, so posts publish with normal public visibility — no TikTok audit to
do yourself, no manual privacy toggling, no subscription cost.

## One-time setup

**1. Notion integration**
- Create an internal integration at notion.so/my-integrations, copy its secret.
- Open the Content Queue database in Notion → `...` menu → Connections → add the integration. Without this step every API call 403s even with a valid token.
- Database id: `09bbd101c54343719837a052978c4556`

**2. ElevenLabs voice**
- Pick a calm/steady narrator voice (voice library or your own clone) and copy its voice_id.
- Nothing else to configure — the pipeline calls the `with-timestamps` endpoint directly.

**3. Buffer**
- Sign up at buffer.com (Free plan) and connect your TikTok, YouTube, and Instagram accounts through Buffer's own dashboard (publish.buffer.com) — the API only acts on channels already connected there; it doesn't do the initial OAuth linking.
- Generate a personal API key at publish.buffer.com/settings/api.
- The pipeline looks up your organization and channel ids itself at runtime via the API — no need to hunt those down by hand.
- Free plan: 1 API key, 3,000 requests per 30 days — comfortably covers 3 posts/run × 5 runs/day plus the org/channel lookups each run makes. If Buffer's beta gates API access behind a request-access step when you sign up, that's expected — recent docs suggest it may already be self-serve, but budget a day just in case.
- `scripts/buffer_client.py` and `scripts/pipeline.py` use Buffer's documented GraphQL schema (`CreatePostInput`, `YoutubePostMetadataInput`, `InstagramPostMetadataInput`, `TikTokPostMetadataInput`) directly from developers.buffer.com — **still worth running the workflow once by hand (below) and checking the Buffer dashboard before trusting the cron schedule with it**, since this hasn't been tested against a live account yet.

**4. Background clips**
- Download a handful (3–5+) of licensed, watermark-free Mixkit loops — vertical or croppable to 9:16, ~15–30s each — and commit them into `assets/backgrounds/*.mp4`. The renderer picks one at random and loops it under the narration. This repo ships with none; the pipeline will fail loudly if the folder is empty.

**5. GitHub repo secrets** (Settings → Secrets and variables → Actions)
| Secret | Value |
|---|---|
| `NOTION_TOKEN` | integration secret from step 1 |
| `NOTION_DATABASE_ID` | `09bbd101c54343719837a052978c4556` |
| `ELEVENLABS_API_KEY` | your ElevenLabs API key |
| `ELEVENLABS_VOICE_ID` | voice id from step 2 |
| `BUFFER_API_KEY` | personal API key from step 3 |

`GITHUB_TOKEN` (used to host the rendered video as a Release asset for Buffer to fetch) is provided automatically by Actions — nothing to add for that one. The workflow's `permissions: contents: write` is what lets it create releases.

## Running it

- **On demand:** repo → Actions → "Publish next queue item" → Run workflow. Do this first, once, to smoke-test before relying on the cron.
- **Scheduled:** `.github/workflows/publish.yml` runs ~5x/day automatically once secrets and at least one background clip are in place. Cron times are UTC and will drift an hour across DST — adjust if that matters.
- Every run uploads `final.mp4`, `captions.ass`, and `narration.mp3` as a build artifact (3-day retention) so you can check output without re-running. The video itself also lands as a dated GitHub Release on this repo (that's how Buffer fetches it) — safe to delete old releases periodically to keep the repo tidy, since Buffer only needs each one until that post publishes.

## Known rough edges

- Buffer call shapes (see step 3) — expect to debug the first live run, though the schema is pulled straight from Buffer's own type reference rather than guessed.
- Each queue item posts with `isAiGenerated: true` on all three platforms, disclosing the AI narration per each platform's synthetic-media policies. Flip that off in `scripts/pipeline.py` if you decide it doesn't apply.
- YouTube category defaults to Entertainment (`categoryId: "24"`) — change `YOUTUBE_CATEGORY_ENTERTAINMENT` in `scripts/buffer_client.py` if you'd rather use a different one.
- Caption chunking (`scripts/build_captions.py`) groups words by character count/line, not by clause — fine for the current style, but tune `max_chars`/`max_words` if lines feel too short/long.
- No retry/backoff on any API call yet — a transient failure just fails the run; re-trigger manually or wait for the next scheduled slot.
