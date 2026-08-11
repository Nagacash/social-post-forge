#!/usr/bin/env python3
"""
forge.py — CLI wrapper running the full pipeline outside an agent harness.

Inside an agent harness, read SKILL.md and drive the stages with the agent's
own tools; the critique and benchmark stages are materially better with real
reasoning behind them. This CLI exists so the repo is useful to everyone else.

Pipeline: ingest -> draft -> critique -> humanize -> (benchmark) -> pack

Requires ANTHROPIC_API_KEY. Trend benchmarking needs a web search key and is
skipped with a warning when absent.

Usage:
    python3 forge.py --source episode.txt --voice voice-profiles/naga.yaml
    python3 forge.py --source notes.md --platforms linkedin,x --out pack.json
    python3 forge.py --source article.txt --no-humanize --json
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import ui
except ImportError:  # ui.py is optional; fall back to plain text
    ui = None

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

MODEL = os.environ.get("FORGE_MODEL", "claude-sonnet-4-5-20250929")
API_URL = "https://api.anthropic.com/v1/messages"

ALL_PLATFORMS = ["linkedin", "instagram", "x", "tiktok"]


def read_ref(name):
    path = os.path.join(ROOT, "references", name)
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def llm(prompt, system=None, max_tokens=4000):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        sys.exit("ANTHROPIC_API_KEY is not set. See .env.example.")

    payload = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        payload["system"] = system

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode(),
        headers={
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            body = json.loads(r.read().decode())
        return "".join(b.get("text", "") for b in body.get("content", []))
    except urllib.error.HTTPError as e:
        sys.exit("Anthropic API %d: %s" % (e.code, e.read().decode("utf-8", "replace")[:400]))


def extract_json(text):
    """Models like to wrap JSON in prose or fences. Dig it out."""
    fenced = re.search(r"```(?:json)?\s*(.+?)```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    start = min([i for i in (text.find("{"), text.find("[")) if i != -1] or [0])
    depth, in_str, esc = 0, False, False
    for i, ch in enumerate(text[start:], start):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch in "{[":
            depth += 1
        elif ch in "}]":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except json.JSONDecodeError:
                    break
    sys.exit("Could not parse JSON from model output:\n%s" % text[:600])


# ------------------------------------------------------------------ stages

def stage_ingest(source_text, voice_text):
    prompt = """Read the source material and produce a source brief as JSON.

Do NOT summarise. Hunt for the material that makes a post worth reading: a claim
someone would argue with, a number that surprises, a story with a turn in it, a
strong opinion stated plainly.

Return exactly this shape:
{
  "what_this_is": "one line",
  "core_thesis": "one sentence - the single argument worth making",
  "key_points": ["3-5 concrete supporting points"],
  "quotable_moments": [{"speaker": "", "quote": "near-verbatim", "why": ""}],
  "hard_facts": ["numbers, dates, names, prices, outcomes"],
  "audience": "who specifically",
  "what_most_people_get_wrong": "the contrarian angle - required"
}

hard_facts is the most important field. If the source genuinely contains no
numbers, names or dates, return an empty array rather than inventing any.

SOURCE MATERIAL:
""" + source_text[:60000]

    if voice_text:
        prompt += "\n\nVOICE PROFILE (for context only, do not copy into the brief):\n" + voice_text

    return extract_json(llm(prompt, max_tokens=3000))


def stage_draft(brief, voice_text, platforms):
    conventions = read_ref("platform-conventions.md")
    system = ("You write social copy that sounds like a specific person with direct "
              "experience, not like a brand account. You never invent facts.")

    prompt = """Write one native post per platform from this source brief.

Write each platform natively. Do NOT write one post and reflow it - that is the
most visible tell of automated content.

Force different angles across the batch: one story, one framework, one opinion.

Every specific claim must trace back to hard_facts or quotable_moments in the
brief. Invent nothing.

SOURCE BRIEF:
%s

PLATFORM CONVENTIONS:
%s
""" % (json.dumps(brief, indent=2, ensure_ascii=False), conventions)

    if voice_text:
        prompt += "\n\nVOICE PROFILE - match this voice, especially the reference posts:\n" + voice_text

    prompt += """

Return JSON only:
{
  "linkedin":  {"copy": "...", "angle": "story|framework|opinion", "image_prompt": "..."},
  "instagram": {"copy": "...", "carousel": ["slide 1", "..."], "angle": "...", "image_prompt": "..."},
  "x":         {"copy": "...", "thread": ["..."], "angle": "...", "image_prompt": "..."},
  "tiktok":    {"copy": "...", "script": "0-1s [visual] ...", "angle": "...", "image_prompt": "..."}
}

Include only these platforms: %s

image_prompt must use 5-12 concrete visual keywords covering subject, action,
context, light and mood. "AI automation" is not an image.
""" % ", ".join(platforms)

    return extract_json(llm(prompt, system=system, max_tokens=8000))


def run_script(name, args):
    try:
        out = subprocess.run(
            [sys.executable, os.path.join(HERE, name)] + args,
            capture_output=True, text=True, timeout=120,
        )
        return out.stdout
    except Exception as e:  # noqa: BLE001
        return "could not run %s: %s" % (name, e)


def stage_critique(posts):
    reports = {}
    for platform, entry in posts.items():
        copy = entry.get("copy", "")
        if not copy:
            continue
        tmp = "/tmp/forge_%s.txt" % platform
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(copy)
        mech = run_script("critique.py", ["--file", tmp, "--platform", platform, "--json"])
        tells = run_script("humanize_check.py", ["--file", tmp, "--json"])
        try:
            reports[platform] = {
                "mechanical": json.loads(mech) if mech.strip() else {},
                "tells": json.loads(tells) if tells.strip() else {},
            }
        except json.JSONDecodeError:
            reports[platform] = {"raw_mechanical": mech, "raw_tells": tells}
    return reports


def stage_rewrite(posts, reports, brief, voice_text, humanize=True):
    rubric = read_ref("rubric.md")
    humanizer = read_ref("humanizer.md") if humanize else ""

    prompt = """Rewrite these posts to fix what the checkers found.

Rules that override everything else:
1. Never invent a fact. Specificity comes from the source brief or not at all.
   A rewrite that adds a plausible statistic has made the post worse.
2. Preserve the information, not the shape.
3. Do not sand the posts into smooth competence. Specific detail, genuine
   asides, uneven sentence length and defensible opinions are what make copy
   read human. Removing every flagged pattern AND every trace of personality
   is a failed pass, not a strict one.
4. Look for clusters, not isolated hits. A watched phrase inside a quotation
   from the source is legitimate and stays.

CURRENT POSTS:
%s

CHECKER REPORTS:
%s

SOURCE BRIEF (the only permitted source of facts):
%s

RUBRIC:
%s
""" % (json.dumps(posts, indent=2, ensure_ascii=False),
       json.dumps(reports, indent=2, ensure_ascii=False)[:12000],
       json.dumps(brief, indent=2, ensure_ascii=False),
       rubric)

    if humanizer:
        prompt += "\n\nHUMANIZER CATALOGUE - apply the full pass:\n" + humanizer

    if voice_text:
        prompt += "\n\nVOICE PROFILE:\n" + voice_text
        prompt += ("\n\nIf the reference posts use em dashes, keep them at that "
                   "frequency. Matching the author beats scrubbing the tell.")

    prompt += """

Then run the audit pass on your own rewrite and answer both briefly:
- What still makes this look AI generated?
- Does the rewrite state any fact, name, number or date not in the source brief?

Return the same JSON structure as the input posts, plus an "audit" key holding
your two answers.
"""
    return extract_json(llm(prompt, max_tokens=8000))


def say(n, title, detail="", state="run"):
    """One progress line per stage, on stderr so stdout stays pipeable."""
    if ui is None:
        sys.stderr.write("[%d/5] %s %s\n" % (n, title.lower(), detail))
    else:
        sys.stderr.write(ui.step(n, 5, title, state, detail) + "\n")
    sys.stderr.flush()


def show_reports(reports):
    for platform, rep in reports.items():
        mech = rep.get("mechanical", {})
        tells = rep.get("tells", {})
        mv = mech.get("verdict", "?")
        tv = tells.get("verdict", "?")
        if ui is None:
            sys.stderr.write("    %-10s %-18s tells: %s\n" % (platform, mv, tv))
            continue
        passed = not mech.get("failing_criteria")
        families = tells.get("cluster_score", 0)
        clean = families <= 2
        sys.stderr.write("      %s %s  %s  %s\n" % (
            ui.c(platform.ljust(10), ui.INK),
            ui.c(("✓ " if passed else "✗ ") + mv,
                 ui.GOOD if passed else ui.WARN),
            ui.c("·", ui.FAINT),
            ui.c("%d tell famil%s" % (families, "y" if families == 1 else "ies"),
                 ui.GOOD if clean else ui.BAD)))
    sys.stderr.flush()


def main():
    ap = argparse.ArgumentParser(description="social-post-forge CLI")
    ap.add_argument("--source", required=True, help="text/markdown file, or '-' for stdin")
    ap.add_argument("--voice", help="voice profile yaml")
    ap.add_argument("--platforms", default=",".join(ALL_PLATFORMS))
    ap.add_argument("--out", default="pack.json")
    ap.add_argument("--no-humanize", action="store_true")
    ap.add_argument("--no-rewrite", action="store_true", help="draft and report only")
    ap.add_argument("--json", action="store_true", help="print the pack to stdout")
    args = ap.parse_args()

    platforms = [p.strip() for p in args.platforms.split(",") if p.strip() in ALL_PLATFORMS]
    if not platforms:
        sys.exit("No valid platforms. Choose from: %s" % ", ".join(ALL_PLATFORMS))

    source = sys.stdin.read() if args.source == "-" else open(
        args.source, encoding="utf-8").read()
    voice = open(args.voice, encoding="utf-8").read() if args.voice else ""

    if ui is not None:
        sys.stderr.write(ui.banner() + "\n")

    say(1, "INGEST", "reading the source")
    brief = stage_ingest(source, voice)
    facts = len(brief.get("hard_facts") or [])
    quotes = len(brief.get("quotable_moments") or [])
    if facts:
        say(1, "INGEST", "%d hard facts · %d quotable moments" % (facts, quotes), "ok")
    else:
        say(1, "INGEST", "no hard facts in the source, posts will be generic", "warn")

    say(2, "DRAFT", "writing natively per platform")
    posts = stage_draft(brief, voice, platforms)
    say(2, "DRAFT", " · ".join(platforms), "ok")

    say(3, "CRITIQUE", "rubric + tell detection")
    reports = stage_critique(posts)
    show_reports(reports)

    if not args.no_rewrite:
        label = "rewriting" if args.no_humanize else "rewriting + 33-pattern pass"
        say(4, "HUMANIZE", label)
        posts = stage_rewrite(posts, reports, brief, voice, humanize=not args.no_humanize)
        reports = stage_critique({k: v for k, v in posts.items() if isinstance(v, dict)})
        say(4, "HUMANIZE", "after rewrite", "ok")
        show_reports(reports)

    audit = posts.pop("audit", None)
    pack = {
        "source_brief": brief,
        "posts": {k: v for k, v in posts.items() if k in platforms},
        "reports": reports,
        "audit": audit,
    }

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(pack, f, indent=2, ensure_ascii=False)
    say(5, "PACK", args.out, "ok")

    if args.json:
        print(json.dumps(pack, indent=2, ensure_ascii=False))
    else:
        for platform in platforms:
            entry = pack["posts"].get(platform)
            if not entry:
                continue
            print()
            print(("=" * 60 + "\n" + platform.upper() + "\n" + "=" * 60)
                  if ui is None else ui.rule(platform.upper()))
            print(entry.get("copy", ""))
            if entry.get("script"):
                print("\n--- script ---\n" + entry["script"])
            if entry.get("carousel"):
                print("\n--- carousel ---")
                for i, slide in enumerate(entry["carousel"], 1):
                    print("  %d. %s" % (i, slide))
            if entry.get("thread"):
                print("\n--- thread ---")
                for i, t in enumerate(entry["thread"], 1):
                    print("  %d. %s" % (i, t))
            if entry.get("image_prompt"):
                print("\n--- image prompt ---\n" + entry["image_prompt"])

    if audit:
        print("\n--- audit ---\n%s" % json.dumps(audit, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    sys.exit(main())
