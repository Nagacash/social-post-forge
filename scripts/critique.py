#!/usr/bin/env python3
"""
critique.py — mechanical rubric checks for a draft social post.

Covers the parts of references/rubric.md that can be measured: platform
formatting compliance, specificity markers, hook shape, CTA presence and
sentence rhythm. The semantic criteria (voice authenticity, shareability,
anti-fabrication) need a reader, and are scored by the agent.

Usage:
    python3 critique.py --file draft.txt --platform linkedin
    python3 critique.py --text "..." --platform x --json
    python3 critique.py --pack pack.json          # every platform in one pack
"""

import argparse
import json
import re
import sys

PLATFORMS = {
    "linkedin": {
        "hard_limit": 3000,
        "target": (1800, 2800),
        "hashtags": (1, 3),
        "max_sentences_per_para": 3,
        "fold": 140,
        "cta_position": "end",
    },
    "instagram": {
        "hard_limit": 2200,
        "target": (80, 600),
        "hashtags": (3, 5),
        "max_sentences_per_para": 3,
        "fold": 125,
        "cta_position": "top+end",
    },
    "x": {
        "hard_limit": 280,
        "target": (100, 200),
        "hashtags": (0, 1),
        "max_sentences_per_para": 4,
        "fold": 280,
        "cta_position": "end",
    },
    "threads": {
        "hard_limit": 500,
        "target": (100, 350),
        "hashtags": (0, 2),
        "max_sentences_per_para": 4,
        "fold": 500,
        "cta_position": "end",
    },
    "tiktok": {
        "hard_limit": 2200,
        "target": (50, 300),
        "hashtags": (1, 5),
        "max_sentences_per_para": 4,
        "fold": 100,
        "cta_position": "end",
    },
}

WEAK_OPENERS = [
    "in today's", "in the world of", "i wanted to share", "i've been thinking",
    "here are 5", "here are 3", "as we all know", "have you ever wondered",
    "imagine a world", "in this post", "excited to announce", "thrilled to share",
    "happy to share", "i'm pleased to",
]

CTA_MARKERS = [
    "?", "comment", "share", "save this", "tag ", "drop a", "let me know",
    "what's your", "what is your", "dm ", "link in bio", "follow for",
    "try it", "tell me", "reply", "agree", "curious",
]

MONTHS = ("january february march april may june july august september "
          "october november december").split()


def sentences(text):
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def paragraphs(text):
    return [p.strip() for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]


def count_specificity(text):
    """Numbers, proper nouns, dates. The rubric wants >= 3 for a score of 4."""
    numbers = re.findall(r"\b\d[\d,.]*\s?(?:%|percent|k|m|bn|x|€|\$|£)?", text)
    money = re.findall(r"[€$£]\s?\d[\d,.]*", text)
    # Proper nouns not at sentence start, a rough but workable proxy.
    propers = []
    for sent in sentences(text):
        words = sent.split()
        for w in words[1:]:
            clean = w.strip(".,!?:;\"'()")
            if "'" in clean or "’" in clean:
                continue  # contractions like "Let's" are not proper nouns
            if len(clean) > 2 and clean[0].isupper() and not clean.isupper():
                propers.append(clean)
    dates = [w for w in text.lower().split() if w.strip(".,") in MONTHS]
    years = re.findall(r"\b(?:19|20)\d{2}\b", text)
    return {
        "numbers": len(numbers),
        "money": len(money),
        "proper_nouns": len(set(propers)),
        "dates": len(dates) + len(years),
        "total": len(numbers) + len(set(propers)) + len(dates) + len(years),
        "examples": sorted(set(propers))[:6],
    }


def check_hook(text, cfg):
    first_line = text.strip().split("\n")[0]
    hook = first_line[:cfg["fold"]]
    issues = []
    low = hook.lower()

    for opener in WEAK_OPENERS:
        if low.startswith(opener) or opener in low[:60]:
            issues.append("Weak opener: '%s'. Open on the thing itself." % opener)
            break

    has_number = bool(re.search(r"\d", hook))
    has_contrarian = any(w in low for w in [
        "wrong", "myth", "nobody", "everyone", "stop ", "don't", "actually",
        "unpopular", "mistake", "worst", "never", "overrated", "lie",
    ])
    has_stake = any(w in low for w in ["i ", "we ", "my ", "our "])

    if not (has_number or has_contrarian or has_stake):
        issues.append(
            "Hook has no number, no contrarian claim and no personal stake. "
            "The rubric needs at least one of the three for a 4."
        )
    if len(first_line) > cfg["fold"]:
        issues.append(
            "First line is %d chars; only ~%d show before the fold. "
            "Front-load the claim." % (len(first_line), cfg["fold"])
        )
    return {
        "first_line": first_line[:120],
        "has_number": has_number,
        "has_contrarian": has_contrarian,
        "has_personal_stake": has_stake,
        "issues": issues,
    }


def check_platform(text, platform):
    cfg = PLATFORMS[platform]
    issues = []
    warnings = []

    body = re.sub(r"#\w+", "", text).strip()
    chars = len(text)
    words = len(text.split())

    if chars > cfg["hard_limit"]:
        issues.append("Over the hard limit: %d / %d chars." % (chars, cfg["hard_limit"]))

    lo, hi = cfg["target"]
    if platform == "instagram":
        if words > 60:
            warnings.append(
                "Caption is %d words. Under ~30 generally engages better on "
                "Instagram; go long only if the story earns it." % words
            )
    elif chars < lo:
        warnings.append("Short for %s: %d chars (target %d-%d)." % (platform, chars, lo, hi))
    elif chars > hi:
        warnings.append("Long for %s: %d chars (target %d-%d)." % (platform, chars, lo, hi))

    tags = re.findall(r"#\w+", text)
    tlo, thi = cfg["hashtags"]
    if len(tags) > thi:
        issues.append("%d hashtags; %s wants %d-%d." % (len(tags), platform, tlo, thi))
    elif len(tags) < tlo:
        warnings.append("%d hashtags; %s wants %d-%d." % (len(tags), platform, tlo, thi))

    generic = [t for t in tags if t.lower() in (
        "#marketing", "#business", "#success", "#motivation", "#ai",
        "#fyp", "#foryou", "#viral", "#love", "#instagood")]
    if generic:
        warnings.append("Generic hashtags: %s. Be specific." % ", ".join(generic))

    for i, para in enumerate(paragraphs(body), 1):
        n = len(sentences(para))
        if n > cfg["max_sentences_per_para"]:
            warnings.append(
                "Paragraph %d has %d sentences; keep to %d or fewer."
                % (i, n, cfg["max_sentences_per_para"])
            )

    if platform == "linkedin" and "\n\n" not in text.strip():
        issues.append("No blank lines. LinkedIn needs whitespace between paragraphs.")

    if re.search(r"\*\*[^*]+\*\*|^#{1,6}\s", text, re.MULTILINE):
        issues.append("Markdown present. No platform renders it; it posts as literal characters.")

    low = text.lower()
    has_cta = any(m in low for m in CTA_MARKERS)
    if not has_cta:
        issues.append("No detectable CTA.")
    elif cfg["cta_position"] == "top+end":
        head = low[:200]
        if not any(m in head for m in CTA_MARKERS):
            warnings.append(
                "Instagram: high-priority CTA should also appear near the top. "
                "Most readers never expand the caption."
            )

    return {
        "chars": chars,
        "words": words,
        "hashtags": tags,
        "paragraphs": len(paragraphs(body)),
        "has_cta": has_cta,
        "issues": issues,
        "warnings": warnings,
    }


def score(text, platform):
    cfg = PLATFORMS[platform]
    plat = check_platform(text, platform)
    hook = check_hook(text, cfg)
    spec = count_specificity(text)

    hook_score = 5 - min(4, len(hook["issues"]) * 2)
    signals = sum([hook["has_number"], hook["has_contrarian"], hook["has_personal_stake"]])
    if signals == 0:
        hook_score = min(hook_score, 2)

    if spec["total"] >= 6:
        spec_score = 5
    elif spec["total"] >= 3:
        spec_score = 4
    elif spec["total"] >= 1:
        spec_score = 3
    else:
        spec_score = 1

    fmt_score = 5 - min(4, len(plat["issues"]) * 2 + len(plat["warnings"]))
    cta_score = 4 if plat["has_cta"] else 1

    mech = {
        "hook": max(1, hook_score),
        "specificity": spec_score,
        "formatting": max(1, fmt_score),
        "cta": cta_score,
    }
    failing = [k for k, v in mech.items() if v < 4]

    return {
        "platform": platform,
        "mechanical_scores": mech,
        "failing_criteria": failing,
        "verdict": "pass (mechanical)" if not failing else "rewrite needed",
        "platform_check": plat,
        "hook_check": hook,
        "specificity": spec,
        "needs_human_scoring": [
            "voice_authenticity", "shareability", "angle_discipline", "anti_fabrication",
        ],
        "reminder": "Run humanize_check.py, then score the semantic criteria against "
                    "references/rubric.md. Anti-fabrication must be 5.",
    }


def report(res):
    print("=" * 60)
    print("%s — %s" % (res["platform"].upper(), res["verdict"]))
    print("=" * 60)
    p = res["platform_check"]
    print("%d chars, %d words, %d paragraphs, %d hashtags"
          % (p["chars"], p["words"], p["paragraphs"], len(p["hashtags"])))

    print("\nmechanical scores:")
    for k, v in res["mechanical_scores"].items():
        print("  %-14s %d/5 %s" % (k, v, "" if v >= 4 else "  <-- below threshold"))

    s = res["specificity"]
    print("\nspecificity: %d markers (%d numbers, %d proper nouns, %d dates)"
          % (s["total"], s["numbers"], s["proper_nouns"], s["dates"]))
    if s["examples"]:
        print("  named: %s" % ", ".join(s["examples"]))
    if s["total"] < 3:
        print("  ! Under 3 specific details. Cannot score above 3 on Specificity.")

    h = res["hook_check"]
    print("\nhook: %s" % h["first_line"])
    print("  number:%s contrarian:%s stake:%s"
          % (h["has_number"], h["has_contrarian"], h["has_personal_stake"]))
    for i in h["issues"]:
        print("  ! %s" % i)

    if p["issues"]:
        print("\nissues:")
        for i in p["issues"]:
            print("  ! %s" % i)
    if p["warnings"]:
        print("\nwarnings:")
        for w in p["warnings"]:
            print("  - %s" % w)

    print("\nstill needs a reader: %s" % ", ".join(res["needs_human_scoring"]))


def main():
    ap = argparse.ArgumentParser(description="Mechanical rubric checks.")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--file")
    src.add_argument("--text")
    src.add_argument("--pack", help="pack.json with {platform: {copy: ...}}")
    ap.add_argument("--platform", choices=sorted(PLATFORMS))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.pack:
        pack = json.load(open(args.pack, encoding="utf-8"))
        posts = pack.get("posts", pack)
        results = []
        for platform, entry in posts.items():
            if platform not in PLATFORMS:
                continue
            copy = entry.get("copy", "") if isinstance(entry, dict) else str(entry)
            results.append(score(copy, platform))
        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            for r in results:
                report(r)
                print()
        return 0 if all(not r["failing_criteria"] for r in results) else 1

    if not args.platform:
        ap.error("--platform is required with --file/--text")

    text = args.text if args.text else open(args.file, encoding="utf-8").read()
    res = score(text, args.platform)
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        report(res)
    return 0 if not res["failing_criteria"] else 1


if __name__ == "__main__":
    sys.exit(main())
