# Post Quality Rubric

Eight criteria, scored 1–5. **Pass threshold: every criterion ≥ 4, and criterion 8 = 5.**

Score the draft as a reviewer, not as its author. If possible run this as a separate subagent that receives the draft and the rubric but not the drafting conversation — self-review after writing is reliably generous.

Below-threshold criteria get a rewrite and a rescore. Cap at three rounds; if it still fails, the source brief is too thin. Go back to the user for specifics instead of polishing.

---

## 1. Hook Strength

Do the first one or two lines earn continued reading? On LinkedIn only ~140 characters show before "see more"; on TikTok you have about 3 seconds. The hook is not an introduction to the post, it is the reason the post gets read at all.

| Score | What it looks like |
|---|---|
| 1 | Generic opener ("In today's world…", "I wanted to share…", "Here are 5 tips…"). Could head any post by anyone. |
| 2 | States the topic but gives no reason to continue. Describes what the post is about. |
| 3 | Clear topic plus one weak trigger — a benefit or pain is mentioned but not sharpened. Might earn the click. |
| 4 | Strong lean-in with a curiosity loop left open. Reader has a concrete reason to keep going. |
| 5 | Lean-in → scroll-stop → snapback, fully executed, with a wide gap between setup and turn. Contains at least one of: a specific number, a contrarian claim, or personal stake. |

The three-step hook (from `kvsdileep/linkedin-writer`): **context lean-in** (topic + a trigger — benefit, pain, metaphor, or a stunning fact, said in as few words as possible), **scroll-stop interjection** ("But." "Except." One line, whose only job is to freeze the reader), **contrarian snapback** (snap opposite to the lean-in; the bigger the gap, the stronger the hook).

---

## 2. Specificity / Anti-Slop

Is the post populated with concrete, verifiable detail, or with AI-era filler vocabulary?

| Score | What it looks like |
|---|---|
| 1 | Several blacklist words. Zero numbers, names or dates. Could be about any company in any industry. |
| 2 | One or two blacklist phrases. Facts are vague — "many companies", "significant growth". |
| 3 | No obvious tells, but still generic. Fewer than three specific details. |
| 4 | Two or three specific, verifiable details. Reads like someone with direct experience wrote it. |
| 5 | Dense with specifics — exact figures, timeframes, named people, products, outcomes. Could not be written by someone who had not done the work. Zero blacklist vocabulary. |

Minimum bar for a 4: **three specific details** (numbers, names, or dates). This threshold is borrowed from `william.ai` and it is the single most reliable predictor of whether a post reads as human.

---

## 3. Voice Authenticity

Does this read as written by a specific person, or by a competent generic model?

| Score | What it looks like |
|---|---|
| 1 | Every sentence 18–24 words. All subject-verb-object. No fragments. Rule-of-three cascades. Could be any model on any topic. |
| 2 | Some variation, still mechanical. Uses fake-directness phrases ("Here's the truth:", "Real talk:"). Explains its own moral at the end. |
| 3 | Varied rhythm, no overt tells, but reads as competent editorial rather than a particular person. |
| 4 | Individual: sentence length genuinely varies, some fragments, first-person grounded in real experience, no explained moral. |
| 5 | Sits naturally beside the author's three reference posts. Contains at least one of: a real complaint, a named tool or product, an unhedged position, or a specific remembered moment. |

Uniform sentence length is the biggest structural tell there is. Models also explain their meaning explicitly about 77% of the time versus roughly 52% for human writers — so if the post ends by telling the reader what it meant, cut that ending.

---

## 4. Platform Formatting Compliance

| Score | What it looks like |
|---|---|
| 1 | Breaks hard limits (over 3,000 chars on LinkedIn, over 280 on X). Dense unbroken text. Hashtags mid-sentence. |
| 2 | Within limits but badly formatted — five-sentence paragraphs, generic or miscounted hashtags. |
| 3 | Length fine, paragraphs 2–3 sentences, hashtag count roughly right. Em-dashes or invisible characters still present. |
| 4 | Optimal length band, 1–3 sentence paragraphs, correct hashtag count, no em-dashes, export-ready plain text. |
| 5 | Everything in 4, plus correct CTA position and emoji placement for the platform, and length inside the evidenced sweet spot rather than merely legal. |

`scripts/critique.py` checks all of this mechanically. Run it before scoring by hand.

**Dashes and invisible unicode are hard rules, not weighted ones.** A post cannot score above 3 here while a single em or en dash survives, no matter how clean everything else is. `humanize_check.py` reports these as `hard_fail` and exits non-zero, and `forge.py` re-runs a targeted repair rather than shipping them. The only override is a voice profile whose reference posts genuinely use dashes.

---

## 5. CTA Clarity and Placement

| Score | What it looks like |
|---|---|
| 1 | No CTA, or a buried "let me know what you think". |
| 2 | Generic end-CTA not tied to the content — "Agree? Comment below." |
| 3 | Relevant closing question, vaguely phrased. On Instagram, CTA only at the end. |
| 4 | Specific low-friction CTA tied to the post's actual content. On Instagram, echoed near the top. |
| 5 | Asks for one concrete behaviour, integrated naturally, positioned correctly per platform — near the hook on Instagram, at the end on LinkedIn and X. On X, phrased to invite a reply the author can reply back to, which the ranking model rewards. |

---

## 6. Shareability / Value Density

Would someone forward this to a colleague?

| Score | What it looks like |
|---|---|
| 1 | Self-promotional or narrative with nothing extractable. |
| 2 | One vague takeaway, not framed as anything reusable. |
| 3 | A takeaway exists but as opinion rather than a transferable model. Saveable, not shareable. |
| 4 | Contains a named framework, checklist or mental model someone could use today. |
| 5 | Framework is named and memorable, 3–5 items, each with a label and a brief explanation. Or the narrative is so specific that people share it as "this is exactly what I went through". |

The test, stated plainly: would someone repost this to their team?

---

## 7. Angle Discipline

| Score | What it looks like |
|---|---|
| 1 | No identifiable angle, or several competing ones. |
| 2 | Has a topic, no position. Informational rather than argued. |
| 3 | Clear pillar, but execution does not match it — a "thought leadership" post that is really a how-to. |
| 4 | Single angle carried consistently: how-to, contrarian take, personal story, or industry read. Tone matches the angle. |
| 5 | Matches a declared content pillar and a declared angle type, and is distinct from the other posts generated in the same batch. |

When generating a batch, force one **story**, one **framework**, one **opinion**. Three posts on the same angle is the most common repetition failure.

---

## 8. Anti-Fabrication (must score 5)

| Score | What it looks like |
|---|---|
| 1 | Invented statistics or attributed quotes with no source. |
| 2 | Unfalsifiable claims implying specificity — "studies show", "experts say". |
| 3 | Directionally accurate but carries unsourced numbers. |
| 4 | All claims grounded in the source material; no fabrication beyond rounding. |
| 5 | Every specific claim traces to `source_brief.hard_facts` or `quotable_moments`. Quotes are verbatim and correctly attributed. |

This is the one criterion with no tolerance. A post with an invented statistic is a liability, not a draft. If a number surfaced during writing and is not in the brief, the model produced it — cut it or ask the user to confirm it.

---

## Report format

```json
{
  "platform": "linkedin",
  "scores": {
    "hook": 4, "specificity": 5, "voice": 4, "formatting": 5,
    "cta": 4, "shareability": 4, "angle": 5, "fabrication": 5
  },
  "verdict": "pass",
  "findings": [
    { "criterion": "hook", "issue": "…", "fix": "…" }
  ],
  "rewrite_round": 1
}
```
