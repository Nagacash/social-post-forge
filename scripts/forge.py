#!/usr/bin/env python3
"""
forge.py — CLI wrapper running the full pipeline outside an agent harness.

Inside an agent harness, read SKILL.md and drive the stages with the agent's
own tools; the critique and benchmark stages are materially better with real
reasoning behind them. This CLI exists so the repo is useful to everyone else.

Pipeline: ingest -> draft -> critique -> humanize -> (benchmark) -> pack

Works with Anthropic by default, or any OpenAI-compatible endpoint via
FORGE_BASE_URL (OpenRouter, Nous, Together, Groq, vLLM, Ollama, LM Studio).
Trend benchmarking needs a browsing agent and is not implemented here.

Usage:
    python3 forge.py --source episode.txt --voice voice-profiles/naga.yaml
    python3 forge.py --source notes.md --platforms linkedin,x --out pack.json
    python3 forge.py --source article.txt --no-humanize --json
"""

import argparse
import json
import os
import re
import socket
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

# Provider config. Defaults to Anthropic, but any OpenAI-compatible endpoint
# works by setting FORGE_BASE_URL — OpenRouter, Nous, Together, Groq, vLLM,
# Ollama, LM Studio. The repo should not assume everyone has Anthropic billing.
BASE_URL = os.environ.get("FORGE_BASE_URL", "").rstrip("/")
DEFAULT_MODEL = "claude-sonnet-4-5-20250929" if not BASE_URL else "gpt-4o-mini"
MODEL = os.environ.get("FORGE_MODEL", DEFAULT_MODEL)
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

# A hosted frontier model answers in seconds. A quantized model on CPU streams
# thousands of tokens at a few per second, so the same call can take many
# minutes — and this pipeline makes five to seven of them in sequence. Default
# generously when pointed at a local endpoint rather than failing a run that
# was only ever going to be slow.
_DEFAULT_TIMEOUT = 900 if BASE_URL else 180
TIMEOUT = int(os.environ.get("FORGE_TIMEOUT", _DEFAULT_TIMEOUT))

ALL_PLATFORMS = ["linkedin", "instagram", "x", "tiktok"]


# Pattern numbers -> the criteria they bear on, so a rewrite only carries the
# rubric rows it actually needs.
_ALWAYS_HUMANIZER = (
    "## The four rules of the rewrite",
    "## Voice calibration beats every rule below",
    "## Do not flag these (false positives)",
    "## Preserve these (signs of human writing)",
    "## Social-specific application layer",
)


def _split_sections(text, marker):
    """Split markdown on a heading marker, keeping the heading with its body."""
    out, cur, name = {}, [], None
    for line in text.split("\n"):
        if line.startswith(marker):
            if name is not None:
                out[name] = "\n".join(cur).rstrip()
            name, cur = line, [line]
        elif name is not None:
            cur.append(line)
    if name is not None:
        out[name] = "\n".join(cur).rstrip()
    return out


def humanizer_excerpt(reports):
    """Only the catalogue entries that actually fired, plus the judgement guards.

    Sending all 33 patterns every time was over half the rewrite prompt. The
    detector already knows which ones hit, so carry those and drop the rest.
    The guard sections always travel: without the false-positive list and the
    preserve list, a rewrite sands the post into competent nothing.
    """
    full = read_ref("humanizer.md")
    if not full:
        return ""
    fired = set()
    for rep in reports.values():
        for f in rep.get("tells", {}).get("findings", []):
            pat = f.get("pattern")
            if isinstance(pat, int):
                fired.add(pat)
    if not fired:
        fired = {14}  # dashes: the one worth restating even on a clean report

    body = _split_sections(full, "**")
    keep = [v for k, v in body.items()
            if any(k.startswith("**%d." % n) for n in fired)]
    guards = _split_sections(full, "## ")
    keep += [v for k, v in guards.items() if k.strip() in _ALWAYS_HUMANIZER]

    header = ("Relevant entries from the 33-pattern catalogue "
              "(references/humanizer.md). Patterns that did not fire are "
              "omitted; do not introduce them either.\n\n")
    return header + "\n\n".join(keep)


def rubric_excerpt(reports):
    """Only the criteria that are failing, plus the threshold rule."""
    full = read_ref("rubric.md")
    if not full:
        return ""
    failing = set()
    for rep in reports.values():
        for c in rep.get("mechanical", {}).get("failing_criteria", []):
            failing.add(c)
    sections = _split_sections(full, "## ")
    wanted = {"hook": "1.", "specificity": "2.", "voice": "3.",
              "formatting": "4.", "cta": "5."}
    prefixes = [wanted[c] for c in failing if c in wanted]
    prefixes += ["8."]  # anti-fabrication always travels
    keep = [v for k, v in sections.items()
            if any(k.startswith("## " + pre) for pre in prefixes)]
    head = ("Failing rubric criteria. Pass threshold is 4 on every criterion "
            "and 5 on anti-fabrication.\n\n")
    return head + "\n\n".join(keep)


def read_ref(name):
    path = os.path.join(ROOT, "references", name)
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def llm(prompt, system=None, max_tokens=4000, json_mode=True):
    """Call the configured provider. OpenAI-compatible when FORGE_BASE_URL is set."""
    if BASE_URL:
        key = (os.environ.get("FORGE_API_KEY")
               or os.environ.get("OPENAI_API_KEY") or "")
        if not key:
            sys.exit("FORGE_BASE_URL is set but FORGE_API_KEY is not. "
                     "Use a dummy value for local servers that ignore auth "
                     "(Ollama, LM Studio, vLLM). See .env.example.")
        url = BASE_URL + "/chat/completions"
        messages = ([{"role": "system", "content": system}] if system else [])
        messages.append({"role": "user", "content": prompt})
        payload = {"model": MODEL, "max_tokens": max_tokens, "messages": messages}
        if json_mode:
            # Small local models drift out of JSON without this. Servers that
            # do not implement it ignore the field rather than erroring.
            payload["response_format"] = {"type": "json_object"}
        # Reasoning models (qwen3 and friends) can spend the whole token budget
        # thinking and return empty content. Ollama accepts this switch; other
        # servers ignore an unknown field.
        if os.environ.get("FORGE_NO_THINK", "1") == "1":
            payload["think"] = False
        if os.environ.get("FORGE_KEEP_ALIVE"):
            # Ollama-specific: stop the model being evicted between the
            # pipeline's sequential calls, which is what makes run two cold.
            payload["keep_alive"] = os.environ["FORGE_KEEP_ALIVE"]
        headers = {"Authorization": "Bearer " + key,
                   "content-type": "application/json"}
    else:
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            sys.exit("No provider configured. Set ANTHROPIC_API_KEY, or set "
                     "FORGE_BASE_URL + FORGE_API_KEY for any OpenAI-compatible "
                     "endpoint. See .env.example.")
        url = ANTHROPIC_URL
        payload = {"model": MODEL, "max_tokens": max_tokens,
                   "messages": [{"role": "user", "content": prompt}]}
        if system:
            payload["system"] = system
        headers = {"x-api-key": key, "anthropic-version": "2023-06-01",
                   "content-type": "application/json"}

    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit("%s %d: %s" % (url, e.code,
                                e.read().decode("utf-8", "replace")[:400]))
    except (socket.timeout, TimeoutError):
        sys.exit(
            "Timed out after %ds waiting on %s.\n"
            "On CPU-only inference this is normal for a cold model: the first "
            "call pays for loading it from disk. Warm it once with\n"
            "  ollama run %s \"hi\"\n"
            "keep it resident with OLLAMA_KEEP_ALIVE=30m, and raise the ceiling "
            "with FORGE_TIMEOUT=3600." % (TIMEOUT, MODEL, MODEL))
    except urllib.error.URLError as e:
        reason = getattr(e, "reason", e)
        if isinstance(reason, (socket.timeout, TimeoutError)):
            sys.exit(
                "Timed out after %ds waiting on %s. Warm the model first "
                "(ollama run %s \"hi\"), keep it resident with "
                "OLLAMA_KEEP_ALIVE=30m, and raise FORGE_TIMEOUT."
                % (TIMEOUT, MODEL, MODEL))
        sys.exit("Cannot reach %s (%s)" % (url, reason))

    if BASE_URL:
        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            sys.exit("Unexpected response shape from %s:\n%s"
                     % (url, json.dumps(body)[:400]))
        if not (content or "").strip():
            sys.exit(
                "%s returned empty content. If this is a reasoning model it "
                "likely spent the budget thinking: raise max_tokens, or pick a "
                "non-reasoning model with FORGE_MODEL." % MODEL)
        return content
    return "".join(b.get("text", "") for b in body.get("content", []))


def _repair_newlines(chunk):
    """Escape raw newlines that appear inside JSON string literals.

    Social copy is full of line breaks and smaller models emit them literally
    inside the string rather than as \\n, which is invalid JSON. Rather than
    crash on an otherwise good generation, repair it.
    """
    out, in_str, esc = [], False, False
    for ch in chunk:
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            elif ch == "\n":
                out.append("\\n"); continue
            elif ch == "\r":
                continue
            elif ch == "\t":
                out.append("\\t"); continue
        elif ch == '"':
            in_str = True
        out.append(ch)
    return "".join(out)


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
                chunk = text[start:i + 1]
                try:
                    return json.loads(chunk)
                except json.JSONDecodeError:
                    try:
                        return json.loads(_repair_newlines(chunk))
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


def stage_critique(posts, allow_em_dash=False):
    reports = {}
    for platform, entry in posts.items():
        copy = entry.get("copy", "")
        if not copy:
            continue
        tmp = "/tmp/forge_%s.txt" % platform
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(copy)
        mech = run_script("critique.py", ["--file", tmp, "--platform", platform, "--json"])
        tell_args = ["--file", tmp, "--json"]
        if allow_em_dash:
            tell_args.append("--allow-em-dash")
        tells = run_script("humanize_check.py", tell_args)
        try:
            reports[platform] = {
                "mechanical": json.loads(mech) if mech.strip() else {},
                "tells": json.loads(tells) if tells.strip() else {},
            }
        except json.JSONDecodeError:
            reports[platform] = {"raw_mechanical": mech, "raw_tells": tells}
    return reports


def _slim_reports(reports):
    """Drop the parts of the checker output a rewrite cannot act on.

    The raw reports carry every finding with context strings and duplicated
    suggestions. The rewriter needs the verdict, what failed, and one example
    per pattern — not the full dump.
    """
    slim = {}
    for platform, rep in reports.items():
        mech = rep.get("mechanical", {})
        tells = rep.get("tells", {})
        seen, examples = set(), []
        for f in tells.get("findings", []):
            key = f.get("label")
            if key in seen:
                continue
            seen.add(key)
            examples.append({"pattern": f.get("pattern"), "label": key,
                             "found": str(f.get("found", ""))[:60]})
        slim[platform] = {
            "verdict": mech.get("verdict"),
            "failing_criteria": mech.get("failing_criteria", []),
            "issues": mech.get("platform_check", {}).get("issues", []),
            "warnings": mech.get("platform_check", {}).get("warnings", [])[:4],
            "hard_failures": tells.get("hard_failures", []),
            "tell_examples": examples[:12],
        }
    return slim


def stage_rewrite(posts, reports, brief, voice_text, humanize=True):
    rubric = rubric_excerpt(reports)
    humanizer = humanizer_excerpt(reports) if humanize else ""

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
       json.dumps(_slim_reports(reports), indent=2, ensure_ascii=False)[:6000],
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


def stage_repair(posts, reports, brief):
    """Second-chance rewrite aimed only at surviving hard-rule failures.

    The main rewrite asks the model to apply the whole catalogue, and smaller
    models reliably drop one or two items. Rather than ship a banned pattern
    with a soft verdict, hand back the exact residue and ask for a surgical fix.
    """
    residue = {p: r["tells"].get("hard_failures", [])
               for p, r in reports.items()
               if r.get("tells", {}).get("hard_fail")}
    if not residue:
        return posts, []

    prompt = """These posts still contain banned patterns after the humanize pass.

Fix ONLY these. Change nothing else: not the hook, not the facts, not the voice,
not the length. This is a surgical edit, not a rewrite.

SURVIVING FAILURES BY PLATFORM:
%s

RULES
- Em dashes and en dashes must not appear in the final text. Restructure the
  sentence: a period, a comma, a colon or parentheses. Do NOT swap in a hyphen,
  because the construction is the tell, not the glyph.
- Strip any invisible unicode.
- Invent no new facts. Every number and name must already be in the posts.

POSTS:
%s

Return the same JSON structure with only those fixes applied.
""" % (json.dumps(residue, indent=2, ensure_ascii=False),
       json.dumps(posts, indent=2, ensure_ascii=False))

    return extract_json(llm(prompt, max_tokens=8000)), sorted(residue)


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
        hard = tells.get("hard_fail")
        clean = families <= 2 and not hard
        sys.stderr.write("      %s %s  %s  %s\n" % (
            ui.c(platform.ljust(10), ui.INK),
            ui.c(("✓ " if passed else "✗ ") + mv,
                 ui.GOOD if passed else ui.WARN),
            ui.c("·", ui.FAINT),
            ui.c("%d tell famil%s%s" % (
                families, "y" if families == 1 else "ies",
                "  HARD: " + ", ".join(tells.get("hard_failures", [])) if hard else ""),
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
    # The catalogue says a real writing sample outranks the dash ban, so honour
    # the voice profile rather than flagging an author's own habit.
    allow_em_dash = bool(re.search(r"author_uses_em_dashes:\s*true", voice, re.I))
    if allow_em_dash:
        say(0, "VOICE", "author uses em dashes, dash rule relaxed", "ok")

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
    reports = stage_critique(posts, allow_em_dash=allow_em_dash)
    show_reports(reports)

    if not args.no_rewrite:
        label = "rewriting" if args.no_humanize else "rewriting + 33-pattern pass"
        say(4, "HUMANIZE", label)
        posts = stage_rewrite(posts, reports, brief, voice, humanize=not args.no_humanize)
        reports = stage_critique(
            {k: v for k, v in posts.items() if isinstance(v, dict)},
            allow_em_dash=allow_em_dash)
        say(4, "HUMANIZE", "after rewrite", "ok")
        show_reports(reports)

        # Enforcement: a surviving hard rule is a failure, not a warning.
        for attempt in (1, 2):
            failing = [p for p, r in reports.items()
                       if r.get("tells", {}).get("hard_fail")]
            if not failing:
                break
            say(4, "ENFORCE", "banned patterns survived in %s (pass %d)"
                % (", ".join(failing), attempt), "warn")
            posts, fixed = stage_repair(posts, reports, brief)
            reports = stage_critique(
                {k: v for k, v in posts.items() if isinstance(v, dict)},
                allow_em_dash=allow_em_dash)
            show_reports(reports)

        still = [p for p, r in reports.items()
                 if r.get("tells", {}).get("hard_fail")]
        if still:
            say(4, "ENFORCE", "STILL FAILING in %s — shipping flagged, do not "
                "post without an edit" % ", ".join(still), "fail")
        else:
            say(4, "ENFORCE", "no banned patterns remain", "ok")

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
