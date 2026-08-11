# Publishing Setup

Three modes. Start at A, move to B or C only when the manual step becomes the bottleneck.

All platform details verified against official documentation in August 2026. Platform terms change often — X repriced twice in 2026 — so re-check before building anything expensive on top of this.

---

## Mode A — Copy-paste pack (default, no setup)

The forge emits per-platform copy, hashtags and an image prompt. You paste it. This is genuinely the right answer for most people: it keeps a human eye on the post before it goes public, and it costs nothing.

Everything below is for when you are posting often enough that pasting is the annoying part.

---

## Mode B — Postiz (self-hosted, free, open source)

**Why this one.** AGPL-3.0, roughly 30 platforms, and no feature gating on the self-hosted build — the maintainers state there is no difference between hosted and self-hosted. LinkedIn, Instagram, X, TikTok and Threads are all in the free self-hosted build.

**The alternative, and why not.** Mixpost Lite is free but only covers X, Facebook Pages and Mastodon. LinkedIn, Instagram, TikTok and Threads all sit behind Mixpost Pro (~$299 one-time, per domain). For this project's platform set, Postiz is the one that is actually free.

### Install

Clone the official compose repo rather than copying a snapshot — services change between releases:

```bash
git clone https://github.com/gitroomhq/postiz-docker-compose
cd postiz-docker-compose
docker compose up -d
```

Stack: the Postiz app image (`ghcr.io/gitroomhq/postiz-app`), PostgreSQL 14+, Redis 6+, and Temporal (mandatory since v2.12.0). Default host mapping is `4007:5000`; Temporal UI sits on 8080 and gRPC on 7233.

**RAM:** 2 GB works for a single user with occasional posting and leaves no headroom. 4 GB is the realistic figure.

**No serverless.** The backend embeds a Temporal worker and needs a persistent host. Vercel will not work.

Required environment:

```env
DATABASE_URL="postgresql://postiz-user:postiz-password@localhost:5432/postiz-db-local"
REDIS_URL="redis://localhost:6379"
JWT_SECRET="<long random string>"
FRONTEND_URL="http://localhost:4200"
NEXT_PUBLIC_BACKEND_URL="http://localhost:3000"
BACKEND_INTERNAL_URL="http://localhost:3000"
IS_GENERAL="true"
STORAGE_PROVIDER="local"
API_LIMIT=200
```

Set `API_LIMIT` deliberately. It defaults to 30, which is a single global rate limit for the whole instance and is low enough to bite during any real automation.

### Connect the networks

Postiz brokers posting; it does not supply credentials. You still create your own developer app per network and paste its keys into Postiz's environment — `LINKEDIN_CLIENT_ID` / `LINKEDIN_CLIENT_SECRET`, `FACEBOOK_APP_ID` / `FACEBOOK_APP_SECRET` for Instagram, `X_API_KEY` / `X_API_SECRET`, `TIKTOK_CLIENT_ID` / `TIKTOK_CLIENT_SECRET`, `THREADS_APP_ID` / `THREADS_APP_SECRET`. No provider is enabled by default. So Postiz removes the per-platform *code*, not the per-platform *paperwork* described in Mode C.

Then connect each account through the Postiz UI.

### Use it

```bash
export POSTIZ_URL=http://localhost:3000     # backend port, not the 4007 UI port
export POSTIZ_API_KEY=...                   # Settings > Developers > Public API

python3 scripts/publish_postiz.py --list-channels
python3 scripts/publish_postiz.py --pack pack.json --when now --dry-run
python3 scripts/publish_postiz.py --pack pack.json --when 2026-09-01T10:00:00Z
```

Auth is a raw `Authorization: <key>` header with **no** `Bearer` prefix. This trips people up constantly.

### Gotchas

- **TikTok needs publicly reachable HTTPS media.** TikTok pulls from a URL, so `STORAGE_PROVIDER=local` with no public domain fails, sometimes silently. Put a reverse proxy in front, or use Cloudflare R2.
- **Media goes through `/upload` or `/upload-from-url`**, never inlined in the post body. The posts endpoint caps at 50 MB and returns 413.
- **SSRF protection is on by default** and blocks the backend from fetching private or loopback addresses. Relevant if you self-host Mastodon or WordPress on the same network. Only disable it on a trusted single-tenant install.
- **Cloudflare R2** is effectively required for avatar caching even though local storage handles post media.

---

## Mode C — Native APIs

Free of middleware, but each platform has its own gate. Setup friction, easiest first:

### Threads — easiest

Free. Two-step publish: create a container at `POST https://graph.threads.net/v1.0/{user-id}/threads`, wait about 30 seconds, then `POST .../threads_publish` with the `creation_id`. Scopes: `threads_basic`, `threads_content_publish`.

No App Review needed as long as the posting account is added as a Tester on your own Meta app. Tokens: 1 hour short-lived, exchange for a 60-day long-lived token, refreshable before expiry. 250 posts per 24 hours, 500 characters, max 5 unique URLs per post.

### LinkedIn — easy, but re-auth every 60 days

Free. `POST https://api.linkedin.com/rest/posts` with `LinkedIn-Version: 202607` and `X-Restli-Protocol-Version: 2.0.0`.

`w_member_social` needs **no review** and works immediately on your own account. Posting as a company page uses `w_organization_social` and works if you are a page administrator. Note that `r_member_social` — reading your own posts back — *does* require partner approval, so design around not needing it.

The real friction: access tokens last 60 days, and refresh tokens are only issued to Marketing Developer Platform partners. Without partner status you re-run the OAuth flow every 60 days. Set a calendar reminder; this is the thing that silently breaks automations.

Images are a separate step: `POST /rest/images?action=initializeUpload`, PUT the bytes to the returned URL, then attach the returned `urn:li:image:...` as `content.media.id`.

### Instagram — free, but heavy prerequisites

Free, and no App Review for publishing to an account you own. The prerequisites are the cost:

- The account must be **Professional** (Business or Creator). Personal accounts cannot use this API.
- For the Facebook Login path, it must be linked to a **Facebook Page**.
- Media must sit at a **public HTTPS URL** — Instagram fetches it. You cannot upload bytes.
- **JPEG only** for images.
- There is **no text-only feed post**. Every post needs media.

Two-step publish: `POST /{ig-user-id}/media` with `image_url` and `caption`, then `POST /{ig-user-id}/media_publish` with the returned `creation_id`. Scopes: `instagram_business_basic` and `instagram_business_content_publish` on the Instagram Login path, or `instagram_basic` + `instagram_content_publish` + `pages_read_engagement` via Facebook Login.

Limit: 100 API posts per 24 hours; a carousel counts as one. Check remaining quota at `GET /{ig-user-id}/content_publishing_limit`. Long-lived tokens last 60 days and need refreshing before expiry.

In this environment, `PublishFilePublicly` on a generated image gives you the public HTTPS URL Instagram requires.

### X — works fine, but costs money

**X is pay-per-use as of 6 February 2026.** The old Free, Basic and Pro subscription tiers are closed to new signups; existing subscribers are grandfathered. Roughly $0.01 per post, and about **$0.20 per post containing a URL** after an April 2026 repricing.

For ten link-free posts a day, that is a few dollars a month. For a link-heavy schedule it is not.

`POST https://api.x.com/2/tweets` with `{"text": "..."}` and an OAuth 2.0 user token. Scopes: `tweet.write`, `tweet.read`, `users.read`, `offline.access`. App-only bearer tokens **cannot** post.

No App Review, but the app must be in the **production** environment — a sandbox app returns a confusing `403 client-forbidden` on write. Access tokens last 2 hours, so you need working refresh logic; `offline.access` gets you the refresh token.

Given the cost, the copy-paste pack is often the honest recommendation for X.

### TikTok — hardest

Free, but gated by an audit.

`video.publish` requires app approval. **Unaudited apps can only post `SELF_ONLY`** (private), capped at 5 users per 24 hours, and the posting account must be private at the time. To post publicly, your client has to pass TikTok's audit.

Worth reading their content-sharing guidelines before you invest time — the policy states API clients "should be intended for a wide audience, not limited to internal groups/private use", and explicitly names "a utility tool to help upload contents to the account(s) you or your team manages" as **not acceptable**. How strictly that is enforced against solo developers is unclear, but it is their stated position.

Other constraints: `PULL_FROM_URL` requires verifying domain ownership in the dashboard; 6 requests per minute on the init endpoint; about 15 posts per day per creator via Direct Post; 24-hour access tokens with 365-day refresh tokens; no text-only posts, and your interface must let the user pick a privacy level with no default and toggle comments, duets and stitches.

For most solo operators, TikTok stays copy-paste.

---

## Friction summary

| Platform | Cost | Review for own account | Token life | Main obstacle |
|---|---|---|---|---|
| Threads | free | no | 60 days, refreshable | none worth naming |
| LinkedIn | free | no | 60 days, **no refresh** | manual re-auth every 60 days |
| Instagram | free | no | 60 days, refreshable | Business account + FB Page + public JPEG URL |
| X | **paid** | no | 2 hours, refreshable | ~$0.01/post, ~$0.20 with a URL |
| TikTok | free | **yes, audit** | 24 hours, refreshable | private-only until audited |

---

## Which mode to pick

Posting a few times a week across two or three platforms: **Mode A**. The setup will cost you more time than pasting ever will.

Posting daily across four platforms: **Mode B**. One Docker stack, one API, and the per-platform paperwork done once.

You already have one platform's OAuth app and only care about that platform: **Mode C** for it, Mode A for the rest.

Whatever you pick, tell the user about X's per-post charge and TikTok's audit gate *before* they invest an afternoon. Those two surprises are the reason most "just automate my posting" projects stall.
