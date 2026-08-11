#!/usr/bin/env python3
"""
publish_native.py — post directly via each platform's own API. No middleman.

Verified against platform docs, August 2026. Read references/publishing-setup.md
before using this; the setup gates differ sharply per platform:

  threads    free, no review for your own account   easiest
  linkedin   free, no review (w_member_social)      60-day token, manual re-auth
  instagram  free, no review, but needs a Business/Creator account linked to a
             Facebook Page and a public HTTPS JPEG URL
  x          PAID. Pay-per-use since Feb 2026, roughly $0.01/post and about
             $0.20 if the post contains a URL. No free tier for new developers.
  tiktok     free, but an unaudited app can only post SELF_ONLY (private).
             Public posting requires passing TikTok's audit.

Usage:
    python3 publish_native.py --platform linkedin --text "..."
    python3 publish_native.py --platform instagram --text "..." --image-url https://...
    python3 publish_native.py --platform threads --text "..."
    python3 publish_native.py --pack pack.json --platform linkedin
    python3 publish_native.py --platform x --text "..." --confirm-paid
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

LINKEDIN_VERSION = "202607"  # bump as LinkedIn sunsets versions
GRAPH_VERSION = "v25.0"


def need(name, why):
    v = os.environ.get(name)
    if not v:
        sys.exit("Missing %s — %s. See references/publishing-setup.md" % (name, why))
    return v


def http(url, method="GET", headers=None, data=None, form=None):
    headers = dict(headers or {})
    body = None
    if form is not None:
        body = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read().decode("utf-8")
            return json.loads(raw) if raw.strip() else {}, dict(r.headers)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:600]
        sys.exit("HTTP %d from %s\n%s" % (e.code, url, detail))


# ---------------------------------------------------------------- LinkedIn

def post_linkedin(text, image_url=None):
    token = need("LINKEDIN_ACCESS_TOKEN", "60-day token from the 3-legged OAuth flow")
    person = need("LINKEDIN_PERSON_URN",
                  "your URN, e.g. urn:li:person:AbC123 (or urn:li:organization:123)")

    headers = {
        "Authorization": "Bearer " + token,
        "LinkedIn-Version": LINKEDIN_VERSION,
        "X-Restli-Protocol-Version": "2.0.0",
    }

    payload = {
        "author": person,
        "commentary": text,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }

    if image_url:
        # Two-step: register an upload, PUT the bytes, then attach the URN.
        init, _ = http(
            "https://api.linkedin.com/rest/images?action=initializeUpload",
            method="POST", headers=headers,
            data={"initializeUploadRequest": {"owner": person}},
        )
        value = init.get("value", {})
        upload_url = value.get("uploadUrl")
        image_urn = value.get("image")
        if not upload_url or not image_urn:
            sys.exit("LinkedIn did not return an upload URL: %s" % json.dumps(init)[:300])

        with urllib.request.urlopen(image_url, timeout=60) as src:
            blob = src.read()
        put = urllib.request.Request(
            upload_url, data=blob,
            headers={"Authorization": "Bearer " + token}, method="PUT")
        urllib.request.urlopen(put, timeout=120)

        payload["content"] = {"media": {"id": image_urn}}

    res, hdrs = http("https://api.linkedin.com/rest/posts",
                     method="POST", headers=headers, data=payload)
    return {"id": hdrs.get("x-restli-id", "posted"), "response": res}


# --------------------------------------------------------------- Instagram

def post_instagram(text, image_url=None):
    token = need("IG_ACCESS_TOKEN", "long-lived token, 60 days")
    ig_id = need("IG_USER_ID", "your Instagram professional account id")

    if not image_url:
        sys.exit("Instagram has no text-only feed post. Supply --image-url "
                 "(a public HTTPS JPEG).")

    base = "https://graph.facebook.com/%s/%s" % (GRAPH_VERSION, ig_id)

    container, _ = http(base + "/media", method="POST",
                        form={"image_url": image_url, "caption": text,
                              "access_token": token})
    cid = container.get("id")
    if not cid:
        sys.exit("No container id returned: %s" % json.dumps(container)[:300])

    time.sleep(5)  # containers are not instantly ready

    published, _ = http(base + "/media_publish", method="POST",
                        form={"creation_id": cid, "access_token": token})
    return published


# ----------------------------------------------------------------- Threads

def post_threads(text, image_url=None):
    token = need("THREADS_ACCESS_TOKEN", "long-lived Threads token")
    user_id = need("THREADS_USER_ID", "your Threads user id")

    base = "https://graph.threads.net/v1.0/%s" % user_id
    form = {"access_token": token, "text": text}
    if image_url:
        form["media_type"] = "IMAGE"
        form["image_url"] = image_url
    else:
        form["media_type"] = "TEXT"

    container, _ = http(base + "/threads", method="POST", form=form)
    cid = container.get("id")
    if not cid:
        sys.exit("No container id: %s" % json.dumps(container)[:300])

    time.sleep(30)  # Meta documents a wait before publishing

    published, _ = http(base + "/threads_publish", method="POST",
                        form={"creation_id": cid, "access_token": token})
    return published


# ----------------------------------------------------------------------- X

def post_x(text, image_url=None, confirmed=False):
    if not confirmed:
        sys.exit(
            "X is pay-per-use since February 2026: roughly $0.01 per post, and "
            "about $0.20 if the post contains a URL. There is no free tier for "
            "new developers. Re-run with --confirm-paid if you accept the charge."
        )
    token = need("X_ACCESS_TOKEN", "OAuth 2.0 user token with tweet.write")

    if image_url:
        print("Note: image upload needs the chunked v2 media flow "
              "(initialize/append/finalize). Posting text only.", file=sys.stderr)

    res, _ = http("https://api.x.com/2/tweets", method="POST",
                  headers={"Authorization": "Bearer " + token},
                  data={"text": text})
    return res


# ------------------------------------------------------------------ TikTok

def post_tiktok(text, video_url=None):
    token = need("TIKTOK_ACCESS_TOKEN", "24-hour token with video.publish")
    if not video_url:
        sys.exit("TikTok needs a video. Pass --video-url (on a domain you have "
                 "verified in the TikTok developer dashboard).")

    info, _ = http("https://open.tiktokapis.com/v2/post/publish/creator_info/query/",
                   method="POST",
                   headers={"Authorization": "Bearer " + token,
                            "Content-Type": "application/json; charset=UTF-8"},
                   data={})
    privacy_options = (info.get("data", {}) or {}).get("privacy_level_options", [])
    privacy = ("PUBLIC_TO_EVERYONE" if "PUBLIC_TO_EVERYONE" in privacy_options
               else "SELF_ONLY")
    if privacy == "SELF_ONLY":
        print("App is unaudited: TikTok will only accept a private (SELF_ONLY) "
              "post. Pass TikTok's audit to post publicly.", file=sys.stderr)

    res, _ = http("https://open.tiktokapis.com/v2/post/publish/video/init/",
                  method="POST",
                  headers={"Authorization": "Bearer " + token,
                           "Content-Type": "application/json; charset=UTF-8"},
                  data={
                      "post_info": {
                          "title": text[:2200],
                          "privacy_level": privacy,
                          "disable_duet": False,
                          "disable_comment": False,
                          "disable_stitch": False,
                      },
                      "source_info": {
                          "source": "PULL_FROM_URL",
                          "video_url": video_url,
                      },
                  })
    return res


HANDLERS = {
    "linkedin": post_linkedin,
    "instagram": post_instagram,
    "threads": post_threads,
    "x": post_x,
    "tiktok": post_tiktok,
}


def main():
    ap = argparse.ArgumentParser(description="Publish directly via native APIs.")
    ap.add_argument("--platform", required=True, choices=sorted(HANDLERS))
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--text")
    src.add_argument("--pack")
    ap.add_argument("--image-url", help="public HTTPS URL; JPEG for Instagram")
    ap.add_argument("--video-url", help="TikTok, on a verified domain")
    ap.add_argument("--confirm-paid", action="store_true",
                    help="acknowledge X's per-post charge")
    args = ap.parse_args()

    if args.pack:
        pack = json.load(open(args.pack, encoding="utf-8"))
        entry = pack.get("posts", pack).get(args.platform)
        if not entry:
            sys.exit("Pack has no entry for %s" % args.platform)
        text = entry.get("copy", "") if isinstance(entry, dict) else str(entry)
        image_url = args.image_url or (entry.get("image_url")
                                       if isinstance(entry, dict) else None)
    else:
        text, image_url = args.text, args.image_url

    if args.platform == "x":
        result = post_x(text, image_url, confirmed=args.confirm_paid)
    elif args.platform == "tiktok":
        result = post_tiktok(text, args.video_url)
    else:
        result = HANDLERS[args.platform](text, image_url)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
