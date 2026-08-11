#!/usr/bin/env python3
"""
humanize_check.py — mechanical detector for the humanizer catalogue.

Flags the patterns from references/humanizer.md that can be found without
judgement. Ported from blader/humanizer (MIT) via Wikipedia's WikiProject
AI Cleanup "Signs of AI writing".

This finds candidates. It does not rewrite, and a hit is not automatically a
defect: watched phrases inside quotations are legitimate, and a single
isolated hit means nothing. Clusters are what matter.

Usage:
    python3 humanize_check.py --file draft.txt
    python3 humanize_check.py --text "some copy"
    python3 humanize_check.py --file draft.txt --json
    python3 humanize_check.py --file draft.txt --allow-em-dash   # voice sample uses them
"""

import argparse
import json
import re
import sys
import unicodedata

# --- Pattern 14: dashes -------------------------------------------------

DASHES = {
    "—": "em dash",
    "–": "en dash",
}

# --- Invisible characters ----------------------------------------------

INVISIBLES = {
    "​": "zero-width space",
    "﻿": "byte order mark",
    "­": "soft hyphen",
    " ": "narrow no-break space",
    "…": "unicode ellipsis",
    "‎": "left-to-right mark",
    "‏": "right-to-left mark",
}

# --- Pattern 7: AI vocabulary cluster -----------------------------------

AI_VOCAB = {
    "delve": "look at, dig into",
    "leverage": "use",
    "foster": "build, encourage",
    "fostering": "building",
    "ignite": "start",
    "empower": "let, help",
    "unleash": "release, start",
    "underscore": "show",
    "underscores": "shows",
    "streamline": "simplify",
    "elevate": "improve, raise",
    "harness": "use",
    "bolster": "strengthen",
    "spearhead": "lead",
    "garner": "get",
    "showcase": "show",
    "showcasing": "showing",
    "cutting-edge": "new",
    "seamless": "smooth",
    "seamlessly": "(delete)",
    "robust": "reliable",
    "multifaceted": "complex",
    "pivotal": "key",
    "transformative": "(say what changed)",
    "revolutionary": "(say what changed)",
    "game-changing": "(say what changed)",
    "game-changer": "(say what changed)",
    "unwavering": "steady",
    "comprehensive": "full",
    "holistic": "whole",
    "intricate": "complex",
    "intricacies": "details",
    "interplay": "relationship",
    "tapestry": "mix",
    "beacon": "example",
    "symphony": "mix",
    "testament": "proof",
    "cornerstone": "base",
    "treasure trove": "collection",
    "paradigm shift": "(say what changed)",
    "synergy": "(cut)",
    "vibrant": "(cut or be specific)",
    "crucial": "important",
    "seamless integration": "(cut)",
    "align with": "match",
    "enhance": "improve",
    "enduring": "lasting",
}

# --- Pattern 4: promotional -------------------------------------------

PROMOTIONAL = [
    "boasts a", "nestled", "in the heart of", "groundbreaking", "renowned",
    "breathtaking", "must-visit", "stunning", "exemplifies", "commitment to",
    "natural beauty", "rich history", "rich tradition",
]

# --- Pattern 3: -ing pseudo-analysis (trailing participle clause) -------

ING_ANALYSIS = [
    "highlighting", "underscoring", "emphasizing", "ensuring", "reflecting",
    "symbolizing", "contributing to", "cultivating", "encompassing",
    "solidifying", "cementing",
]

# --- Pattern 9: negative parallelism -----------------------------------

NEG_PARALLEL = [
    r"\bnot only\b[^.!?]{0,80}\bbut\b",
    r"\bit'?s not just\b",
    r"\bthis isn'?t just\b",
    r"\bisn'?t just about\b",
    r"\bnot merely\b",
    r"\bmore than just\b",
]

# --- Pattern 23: filler ------------------------------------------------

FILLER = {
    "in order to": "to",
    "due to the fact that": "because",
    "at this point in time": "now",
    "in the event that": "if",
    "has the ability to": "can",
    "have the ability to": "can",
    "it is important to note that": "(delete)",
    "it's important to note that": "(delete)",
    "it is worth noting that": "(delete)",
    "it's worth noting that": "(delete)",
    "needless to say": "(delete)",
    "for all intents and purposes": "(delete)",
    "in the world of": "in",
    "when it comes to": "(restructure)",
}

# --- Pattern 28: signposting -------------------------------------------

SIGNPOSTING = [
    "let's dive in", "let's explore", "let's break this down", "let's unpack",
    "here's what you need to know", "without further ado", "buckle up",
    "let me explain", "stay tuned",
]

# --- Pattern 33 / fake directness --------------------------------------

FAKE_DIRECTNESS = [
    "here's the thing", "here's the truth", "real talk", "let's be honest",
    "here's the kicker", "here's the part most people miss", "let that sink in",
    "plot twist", "the harsh truth", "honestly?", "look,",
]

# --- Pattern 27: authority tropes --------------------------------------

AUTHORITY_TROPES = [
    "the real question is", "at its core", "in reality", "what really matters",
    "the deeper issue", "the heart of the matter", "make no mistake",
]

# --- Pattern 32: aphorism formulas -------------------------------------

APHORISM = [
    r"\bis the new\b",
    r"\bthe currency of\b",
    r"\bthe language of\b",
    r"\bthe architecture of\b",
    r"\bis the [a-z]+ of [a-z]+\b",
]

# --- Pattern 25: generic positive conclusions --------------------------

GENERIC_CLOSERS = [
    "the future looks bright", "exciting times ahead", "the possibilities are endless",
    "in conclusion", "at the end of the day", "in essence", "ultimately,",
    "only time will tell", "the future is",
]

# --- Pattern 20/22: collaborative artifacts and sycophancy -------------

CHAT_ARTIFACTS = [
    "i hope this helps", "of course!", "certainly!", "you're absolutely right",
    "would you like me to", "want me to", "let me know if", "here is a",
    "great question", "excellent point", "i'd be happy to",
]

# --- Pattern 21: cutoff disclaimers / speculation ----------------------

SPECULATION = [
    "as of my last", "based on available information", "while specific details are limited",
    "it is believed that", "maintains a low profile", "not publicly available",
    "studies show", "experts say", "experts argue", "research suggests",
    "industry reports", "observers have noted", "some critics argue",
]

# --- Pattern 24: hedge stacking ----------------------------------------

HEDGES = ["could", "might", "may", "potentially", "possibly", "perhaps",
          "arguably", "somewhat", "relatively", "fairly", "quite", "generally"]

# --- Pattern 26: hyphenated pairs --------------------------------------

HYPHEN_PAIRS = [
    "third-party", "cross-functional", "client-facing", "data-driven",
    "decision-making", "well-known", "high-quality", "real-time",
    "long-term", "end-to-end", "world-class", "best-in-class",
]

# --- Pattern 16: inline-header lists -----------------------------------

INLINE_HEADER = re.compile(
    r"^\s*[-*•]\s*\*\*[^*]+\*\*\s*[:\-–—]?\s*\S", re.MULTILINE
)


def find_phrases(text, phrases, pattern_no, label, fixes=None):
    """Locate literal phrases, case-insensitively, with line numbers."""
    out = []
    lowered = text.lower()
    for phrase in phrases:
        start = 0
        while True:
            idx = lowered.find(phrase.lower(), start)
            if idx == -1:
                break
            line_no = text.count("\n", 0, idx) + 1
            item = {
                "pattern": pattern_no,
                "label": label,
                "line": line_no,
                "found": text[idx:idx + len(phrase)],
            }
            if fixes and phrase in fixes:
                item["suggest"] = fixes[phrase]
            out.append(item)
            start = idx + len(phrase)
    return out


def find_words(text, vocab, pattern_no, label):
    """Whole-word matches for a vocabulary dict of {word: suggestion}."""
    out = []
    for word, suggestion in vocab.items():
        for m in re.finditer(r"\b" + re.escape(word) + r"\b", text, re.IGNORECASE):
            out.append({
                "pattern": pattern_no,
                "label": label,
                "line": text.count("\n", 0, m.start()) + 1,
                "found": m.group(0),
                "suggest": suggestion,
            })
    return out


def find_regex(text, patterns, pattern_no, label):
    out = []
    for pat in patterns:
        for m in re.finditer(pat, text, re.IGNORECASE):
            out.append({
                "pattern": pattern_no,
                "label": label,
                "line": text.count("\n", 0, m.start()) + 1,
                "found": m.group(0).strip(),
            })
    return out


def sentences(text):
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def check_rule_of_three(text):
    """Pattern 10: 'a, b, and c' triads. Flags runs, not single instances."""
    hits = []
    pat = r"\b[\w'-]+(?:\s[\w'-]+){0,2},\s[\w'-]+(?:\s[\w'-]+){0,2},\s+and\s+[\w'-]+"
    for m in re.finditer(pat, text, re.IGNORECASE):
        hits.append({
            "pattern": 10,
            "label": "rule of three",
            "line": text.count("\n", 0, m.start()) + 1,
            "found": m.group(0),
        })
    return hits


def check_sentence_uniformity(text):
    """Layer 2 structural tell: every sentence landing at 18-24 words."""
    lens = [len(s.split()) for s in sentences(text)]
    if len(lens) < 4:
        return None
    mean = sum(lens) / len(lens)
    variance = sum((x - mean) ** 2 for x in lens) / len(lens)
    stdev = variance ** 0.5
    verdict = {
        "sentence_count": len(lens),
        "mean_words": round(mean, 1),
        "stdev_words": round(stdev, 1),
        "lengths": lens,
    }
    if stdev < 4.0:
        verdict["flag"] = (
            "Sentence lengths are uniform (stdev %.1f). This is the loudest "
            "structural tell. Break it up: add a fragment, let one sentence run long."
            % stdev
        )
    if 16 <= mean <= 26 and stdev < 5.0:
        verdict["flag"] = (
            "Mean %.1f words with low variation is the classic LLM cadence. "
            "Vary it deliberately." % mean
        )
    return verdict


def check_staccato(text):
    """Pattern 31: runs of very short sentences used for drama."""
    lens = [len(s.split()) for s in sentences(text)]
    run, runs = 0, []
    for n in lens:
        if n <= 5:
            run += 1
        else:
            if run >= 3:
                runs.append(run)
            run = 0
    if run >= 3:
        runs.append(run)
    if runs:
        return {
            "pattern": 31,
            "label": "staccato drama",
            "note": "Run of %d consecutive very short sentences. One is fine; "
                    "a run sounds engineered." % max(runs),
        }
    return None


def check_hedge_stacks(text):
    """Pattern 24: two or more hedges within a short window."""
    hits = []
    for sent in sentences(text):
        found = [h for h in HEDGES if re.search(r"\b" + h + r"\b", sent, re.IGNORECASE)]
        if len(found) >= 2:
            hits.append({
                "pattern": 24,
                "label": "hedge stacking",
                "found": ", ".join(found),
                "context": sent[:90],
            })
    return hits


def check_dashes(text, allow_em_dash=False):
    hits = []
    for ch, name in DASHES.items():
        if allow_em_dash and ch == "—":
            continue
        for m in re.finditer(re.escape(ch), text):
            hits.append({
                "pattern": 14,
                "label": name,
                "line": text.count("\n", 0, m.start()) + 1,
                "found": text[max(0, m.start() - 30):m.start() + 30].replace("\n", " "),
                "suggest": "Restructure: period, comma, colon, parentheses. "
                           "Swapping in a hyphen leaves the tell intact.",
            })
    for m in re.finditer(r"\s--\s", text):
        hits.append({
            "pattern": 14,
            "label": "double hyphen",
            "line": text.count("\n", 0, m.start()) + 1,
            "found": m.group(0),
        })
    return hits


def check_invisibles(text):
    hits = []
    for ch, name in INVISIBLES.items():
        count = text.count(ch)
        if count:
            hits.append({
                "pattern": "invisible",
                "label": name,
                "count": count,
                "codepoint": "U+%04X" % ord(ch),
                "suggest": "Strip.",
            })
    for ch in text:
        if unicodedata.category(ch) == "Cf" and ch not in INVISIBLES:
            hits.append({
                "pattern": "invisible",
                "label": "format character %s" % unicodedata.name(ch, "unknown"),
                "codepoint": "U+%04X" % ord(ch),
                "suggest": "Strip.",
            })
            break
    return hits


def analyse(text, allow_em_dash=False):
    findings = []
    findings += check_dashes(text, allow_em_dash)
    findings += check_invisibles(text)
    findings += find_words(text, AI_VOCAB, 7, "AI vocabulary")
    findings += find_phrases(text, PROMOTIONAL, 4, "promotional language")
    findings += find_words(text, {w: "cut the participle clause" for w in ING_ANALYSIS},
                           3, "-ing pseudo-analysis")
    findings += find_regex(text, NEG_PARALLEL, 9, "negative parallelism")
    findings += find_phrases(text, list(FILLER.keys()), 23, "filler", FILLER)
    findings += find_phrases(text, SIGNPOSTING, 28, "signposting")
    findings += find_phrases(text, FAKE_DIRECTNESS, 33, "fake directness")
    findings += find_phrases(text, AUTHORITY_TROPES, 27, "authority trope")
    findings += find_regex(text, APHORISM, 32, "aphorism formula")
    findings += find_phrases(text, GENERIC_CLOSERS, 25, "generic conclusion")
    findings += find_phrases(text, CHAT_ARTIFACTS, 20, "chat artifact")
    findings += find_phrases(text, SPECULATION, 21, "vague attribution / speculation")
    findings += find_phrases(text, HYPHEN_PAIRS, 26, "hyphenated pair")
    findings += check_rule_of_three(text)
    findings += check_hedge_stacks(text)

    for m in INLINE_HEADER.finditer(text):
        findings.append({
            "pattern": 16,
            "label": "inline-header list",
            "line": text.count("\n", 0, m.start()) + 1,
            "found": m.group(0).strip(),
            "suggest": "Convert to prose. This is the most recognisable "
                       "'AI wrote my post' shape.",
        })

    staccato = check_staccato(text)
    if staccato:
        findings.append(staccato)

    uniformity = check_sentence_uniformity(text)

    # Cluster score: distinct pattern families hit, which matters more than
    # raw count. One em dash is nothing; five families is a confession.
    families = {f.get("pattern") for f in findings}
    cluster = len(families)

    if cluster == 0:
        verdict = "clean"
    elif cluster <= 2:
        verdict = "probably fine — isolated hits, check for false positives"
    elif cluster <= 4:
        verdict = "needs a pass"
    else:
        verdict = "reads as machine-written — rewrite"

    return {
        "verdict": verdict,
        "cluster_score": cluster,
        "total_findings": len(findings),
        "sentence_uniformity": uniformity,
        "findings": findings,
    }


def main():
    ap = argparse.ArgumentParser(description="Detect AI writing tells.")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--file")
    src.add_argument("--text")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--allow-em-dash", action="store_true",
                    help="voice sample uses em dashes, so do not flag them")
    args = ap.parse_args()

    text = args.text if args.text else open(args.file, encoding="utf-8").read()
    report = analyse(text, allow_em_dash=args.allow_em_dash)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    print("verdict: %s" % report["verdict"])
    print("pattern families hit: %d   total findings: %d"
          % (report["cluster_score"], report["total_findings"]))

    u = report["sentence_uniformity"]
    if u:
        print("\nsentence rhythm: %d sentences, mean %.1f words, stdev %.1f"
              % (u["sentence_count"], u["mean_words"], u["stdev_words"]))
        if "flag" in u:
            print("  ! %s" % u["flag"])

    if report["findings"]:
        print("\nfindings:")
        by_label = {}
        for f in report["findings"]:
            by_label.setdefault(f["label"], []).append(f)
        for label, items in sorted(by_label.items(), key=lambda kv: -len(kv[1])):
            head = items[0]
            loc = " (line %s)" % head["line"] if "line" in head else ""
            print("  [%s] %s x%d%s" % (head.get("pattern"), label, len(items), loc))
            seen_suggestions = set()
            for it in items[:3]:
                shown = it.get("found") or it.get("context") or it.get("note", "")
                if shown:
                    print("      %s" % str(shown)[:100])
                sug = it.get("suggest")
                # One vocabulary hit has its own replacement; a structural
                # pattern repeats the same advice, so say it once.
                if sug and sug not in seen_suggestions:
                    print("      -> %s" % sug)
                    seen_suggestions.add(sug)
            if len(items) > 3:
                print("      ... %d more" % (len(items) - 3))

    print("\nNote: hits inside quotations are legitimate. Look for clusters, "
          "not isolated instances. Rewrite sentences, not characters.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
