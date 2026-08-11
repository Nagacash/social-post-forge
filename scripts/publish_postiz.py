#!/usr/bin/env python3
"""
publish_postiz.py — publish a pack through a self-hosted Postiz instance.

Postiz (AGPL-3.0) is the free open-source bridge: one local API, ~30 platforms,
no feature gating on self-hosted, no per-post fee. It brokers the posting; you
still create your own developer app per network.

Setup: see references/publishing-setup.md

Environment:
    POSTIZ_URL       e.g. http://localhost:3000   (the backend, not the UI port)
    POSTIZ_API_KEY   Settings > Developers > Public API

Note: Postiz auth uses a raw `Authorization: <key>` header, NOT `Bearer <key>`.

Usage:
    python3 publish_postiz.py --list-channels
    python3 publish_postiz.py --pack pack.json --when now
    python3 publish_postiz.py --pack pack.json --when 2026-09-01T10:00:00Z
    python3 publish_postiz.py --pack pack.json --when now --dry-run
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

API_BASE = "/public/v1"

# Postiz settings.__type per platform, with the required per-provider fields.
PROVIDER_SETTINGS = {
    "x": {"__type": "x", "who_can_reply_post": "everyone",
          "made_with_ai": False, "paid_partnership": False},
    "linkedin": {"__type": "linkedin"},
    "linkedin-page": {"__type": "linkedin-page"},
    "instagram": {"__type": "instagram", "post_type": "post"},
    "threads": {"__type": "threads"},
    "tiktok": {"__type": "tiktok", "privacy_level": "PUBLIC_TO_EVERYONE",
               "disable_duet": False, "disable_stitch": False,
               "disable_comment": False, "brand_content_toggle": False,
               "brand_organic_toggle": False},
    "facebook": {"__type": "facebook"},
    "youtube": {"__type": "youtube"},
    "pinterest": {"__type": "pinterest"},
    "mastodon": {"__type": "mastodon"},
    "bluesky": {"__type": "bluesky"},
}


def env(name):
    v = os.environ.get(name)
    if not v:
        sys.exit("Missing %s. Export it or add it to .env (see .env.example)." % name)
    return v.rstrip("/") if name.endswith("URL") else v


def call(method, path, payload=None, files=None):
    url = env("POSTIZ_URL") + API_BASE + path
    key = env("POSTIZ_API_KEY")
    headers = {"Authorization": key}  # raw key, not Bearer

    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body.strip() else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:500]
        if e.code == 401:
            sys.exit("401 from Postiz. Check POSTIZ_API_KEY, and note the header "
                     "is a raw key with no 'Bearer ' prefix.")
        if e.code == 413:
            sys.exit("413 too large. Upload media via /upload first rather than "
                     "inlining it in the post body.")
        sys.exit("Postiz %s %s -> HTTP %d: %s" % (method, path, e.code, detail))
    except urllib.error.URLError as e:
        sys.exit("Cannot reach Postiz at %s (%s). Is the container up, and is "
                 "POSTIZ_URL the backend port rather than the UI port?"
                 % (env("POSTIZ_URL"), e.reason))


def list_channels():
    return call("GET", "/integrations")


def upload_from_url(image_url):
    return call("POST", "/upload-from-url", {"url": image_url})


def resolve_when(when):
    if when == "now":
        # Postiz still wants a date on the payload; "now" is the type.
        return "now", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if when == "tomorrow":
        d = datetime.now(timezone.utc) + timedelta(days=1)
        return "schedule", d.replace(hour=9, minute=0, second=0, microsecond=0
                                     ).isoformat().replace("+00:00", "Z")
    return "schedule", when


def build_post(integration_id, platform, copy, media=None):
    settings = dict(PROVIDER_SETTINGS.get(platform, {"__type": platform}))
    value = {"content": copy, "image": media or []}
    return {
        "integration": {"id": integration_id},
        "value": [value],
        "settings": settings,
    }


def main():
    ap = argparse.ArgumentParser(description="Publish a pack via self-hosted Postiz.")
    ap.add_argument("--pack", help="pack.json produced by the forge")
    ap.add_argument("--when", default="now",
                    help="'now', 'tomorrow', or an ISO-8601 UTC timestamp")
    ap.add_argument("--list-channels", action="store_true")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the payload without sending")
    ap.add_argument("--only", help="comma-separated platforms to publish")
    args = ap.parse_args()

    if args.list_channels:
        channels = list_channels()
        if not channels:
            print("No channels connected. Connect them in the Postiz UI first.")
            return 0
        print("%-38s %-14s %s" % ("ID", "PLATFORM", "NAME"))
        for c in channels:
            print("%-38s %-14s %s" % (c.get("id", "?"),
                                      c.get("identifier", c.get("providerIdentifier", "?")),
                                      c.get("name", "?")))
        return 0

    if not args.pack:
        ap.error("--pack is required unless using --list-channels")

    pack = json.load(open(args.pack, encoding="utf-8"))
    posts_in = pack.get("posts", pack)
    only = {p.strip() for p in args.only.split(",")} if args.only else None

    channels = list_channels()
    by_platform = {}
    for c in channels:
        ident = c.get("identifier") or c.get("providerIdentifier")
        by_platform.setdefault(ident, []).append(c)

    post_type, when = resolve_when(args.when)
    payload_posts = []
    skipped = []

    for platform, entry in posts_in.items():
        if only and platform not in only:
            continue
        copy = entry.get("copy", "") if isinstance(entry, dict) else str(entry)
        if not copy.strip():
            continue

        matches = by_platform.get(platform)
        if not matches:
            skipped.append(platform)
            continue

        media = []
        image_url = entry.get("image_url") if isinstance(entry, dict) else None
        if image_url:
            uploaded = upload_from_url(image_url) if not args.dry_run else {
                "id": "<uploaded-id>", "path": image_url}
            media = [{"id": uploaded.get("id"), "path": uploaded.get("path", image_url)}]

        payload_posts.append(build_post(matches[0]["id"], platform, copy, media))

    if skipped:
        print("Skipped (no connected Postiz channel): %s" % ", ".join(skipped),
              file=sys.stderr)

    if not payload_posts:
        sys.exit("Nothing to publish. Connect channels in Postiz, or check --only.")

    payload = {
        "type": post_type,
        "date": when,
        "shortLink": False,
        "tags": [],
        "posts": payload_posts,
    }

    if args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    result = call("POST", "/posts", payload)
    print("Submitted %d post(s), type=%s date=%s" % (len(payload_posts), post_type, when))
    print(json.dumps(result, indent=2, ensure_ascii=False)[:1000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
