# AI Tells — Quick Reference

The fast card, structured in three layers after `starside-io/ghostwriter` (MIT). Use it for inline checking while drafting.

**For the actual humanize pass (stage 3b), use `humanizer.md`** — the full 33-pattern catalogue with rewrite rules, false-positive guards and the audit pass. This file is the condensed subset; that one is the authority.

`scripts/humanize_check.py` detects Layer 1 and most of Layer 2 mechanically. Layer 3 needs judgement.

---

## Layer 1 — Characters

Mechanically detectable, no excuses for shipping these.

| Character | Codepoint | Action |
|---|---|---|
| em-dash | U+2014 | Rewrite the sentence. Do not swap in a hyphen — the sentence *construction* is the tell, not the glyph. |
| en-dash | U+2013 | Only legitimate in numeric ranges. |
| zero-width space | U+200B | Strip. |
| BOM | U+FEFF | Strip. |
| soft hyphen | U+00AD | Strip. |
| narrow no-break space | U+202F | Strip. |
| unicode ellipsis | U+2026 | Replace with three periods, or cut. |
| curly quotes | U+2018-201D | Fine in prose; strip when the platform mangles them. |

The em-dash point is worth repeating because it is the most common wrong fix: replacing `—` with `-` leaves the same tell. The giveaway is the *appositive interruption habit*, so restructure into two sentences or use a comma.

---

## Layer 2 — Style

**Vocabulary blacklist.**

| Category | Flagged | Use instead |
|---|---|---|
| Verbs | delve, leverage, foster, ignite, empower, unleash, underscore, streamline, elevate, navigate (metaphorical), harness, bolster, spearhead | look at, use, help, start, show, cut, speed up, improve, lead |
| Adjectives | cutting-edge, seamless, robust, multifaceted, pivotal, transformative, revolutionary, game-changing, unwavering, comprehensive, holistic | new, reliable, strong, key, full, useful — or a concrete fact instead |
| Nouns | tapestry, landscape, realm, beacon, symphony, journey, roadmap, testament, cornerstone, treasure trove, paradigm shift, synergy, ecosystem (metaphorical) | mix, situation, field, guide, plan, proof, base |
| Openers | "In today's fast-paced world", "In today's digital landscape", "Imagine a world where" | start with the actual point |
| Closers | "In conclusion", "Ultimately", "At the end of the day", "In essence" | end on a consequence, or just stop |
| Fake directness | "Here's the thing:", "Here's the truth:", "Real talk:", "But here's the kicker:", "Here's the part most people miss:", "Let that sink in." | deliver the insight without the drumroll |
| Intensifiers | deeply, truly, fundamentally, inherently, seamlessly, incredibly | delete — they almost always weaken the sentence |

**Structural tells.**

- **Uniform sentence length.** Every sentence landing at 18–24 words is the single loudest signal. Human writing varies wildly. Break it up with fragments and the occasional long winding sentence.
- **All SVO, all the time.** No fragments, no inversions, no sentences opening with But or And.
- **Rule of three everywhere.** "Faster, cheaper, and more reliable." Occasionally fine, as a reflex it is a tell.
- **Negative parallelism.** "It's not just X, it's Y." Extremely common, instantly recognisable.
- **Hedging stacks.** "It's worth noting that it may potentially be somewhat useful."
- **Sycophancy.** "Great question!" "That's a fascinating point." Nobody writes like this in a post.

---

## Layer 3 — Structure

Judgement calls, and the ones that separate a 4 from a 5 on Voice Authenticity.

**Explaining the meaning.** Models spell out the moral roughly 77% of the time versus about 52% for humans. If the post ends by telling the reader what it meant, delete that ending. Trust the reader.

**Naming vague things.** Models say "a leading tool", "a major client", "significant improvements". Humans say "Figma", "the Hamburg account", "cut it from 40 minutes to 6". Humans name real things at about twice the rate.

**Embodied emotion.** Models reach for physical descriptions of feeling — tight chest, cold sweat, heart racing — about 81% of the time versus 29% for humans. Real writers usually just say what happened and let it land.

**Symmetry.** Model output tends toward suspiciously balanced structures: equal-length sections, matched pairs, tidy resolutions. Real writing is lopsided, because some parts matter more.

---

## Signs of human writing — preserve these

When editing, do not sand these off. They are why the post works.

- A specific unhedged opinion, including one some readers will dislike
- Named tools, companies, prices, dates
- A genuine complaint or frustration
- An aside that does not serve the main argument
- Uneven emphasis — one section much longer because it matters more
- An ending that stops rather than concludes
- Mild informality and contractions

---

## Checking procedure

1. Run `scripts/critique.py` — catches Layer 1 and most of Layer 2.
2. Read for Layer 3 by hand, or hand it to a reviewer subagent.
3. Run the `humanizer` skill for the full 33-pattern pass.
4. Rewrite flagged **sentences**, not flagged characters. A find-and-replace on vocabulary leaves the underlying construction intact and reads worse than the original.
