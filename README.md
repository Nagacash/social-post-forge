<img src="assets/hero.svg" alt="social-post-forge" width="100%">

# social-post-forge

An agent skill that turns any source — a podcast episode, a business description, an article, a pile of notes — into platform-native social posts for LinkedIn, Instagram, X/Threads and TikTok. Every draft gets scored against a rubric, stripped of AI writing tells, rewritten against what is currently working in the niche, paired with an image prompt, and then either handed over as a copy-paste pack or published automatically.

Plain Markdown plus Python. No workflow builder, no monthly SaaS, no webhook plumbing.

<img src="assets/pipeline.svg" alt="The six-stage pipeline" width="100%">

```
1. INGEST      source material  →  source brief + voice profile
2. DRAFT       source brief     →  native draft per platform
3a. CRITIQUE   draft            →  rubric score → rewrite until it passes
3b. HUMANIZE   passing draft    →  33-pattern pass → rewrite → audit pass
4. BENCHMARK   humanized draft  →  structural patterns from top posts → rewrite
5. VISUAL      final copy       →  image prompt (+ optional generated image)
6. PUBLISH     final pack       →  copy-paste / Postiz / native API
```

## Why the extra stages

The usual failure is not that models cannot write. It is that one generic post gets reflowed four ways, nobody checks it, and it reads like every other AI post in the feed. Each stage is a defence against a specific failure:

- **Native drafting** — a LinkedIn structure inside an Instagram caption reads wrong to anyone who uses both.
- **Rubric scoring** — a draft that has not been scored is not finished, it is just written. Eight criteria, threshold of 4, anti-fabrication must be 5.
- **The humanize pass** — a post can score well on every rubric criterion and still be unmistakably synthetic. Different failure, different fix.
- **Structure-only trend benchmarking** — trending posts never enter the drafting context. Only a pattern report crosses that boundary, which is the difference between informed by what works and a worse version of someone else's post.

## Install

### As an agent skill

The runtime artifact is `SKILL.md` with agentskills.io-compatible YAML frontmatter, so any harness that supports skill-style instructions can discover and load it — Hermes Agent, Claude Code, Codex, Cursor, OpenClaw.

**Hermes Agent** (Nous Research):

```bash
hermes skills install https://raw.githubusercontent.com/Nagacash/social-post-forge/main/SKILL.md
# or clone the full directory to get references and scripts
git clone https://github.com/Nagacash/social-post-forge ~/.hermes/skills/social-post-forge
```

**Claude Code / Cursor / any skills directory:**

```bash
git clone https://github.com/Nagacash/social-post-forge ~/.claude/skills/social-post-forge
```

**Cross-agent skills CLI:**

```bash
npx skills add Nagacash/social-post-forge
```

Clone the whole repo rather than just `SKILL.md` where you can. `SKILL.md` alone carries the full pipeline, but the references hold the 33-pattern catalogue and the rubric, and the scripts do the mechanical checking.

The skill names Hyperagent tools (`TranscribeAudio`, `ExaSearch`, `GenerateImage`) because that is where it was built. `SKILL.md` includes a capability-mapping table so an agent on another harness substitutes its own equivalents, and states what to skip — loudly — when a capability is missing. The scripts need no host tools at all.

### As a CLI

```bash
git clone https://github.com/Nagacash/social-post-forge
cd social-post-forge
cp .env.example .env    # add ANTHROPIC_API_KEY
python3 scripts/forge.py --source episode.txt --voice voice-profiles/mine.yaml
```

No dependencies beyond the Python 3.8+ standard library.

The CLI is deliberately the thinner experience. Critique and trend benchmarking are much stronger with a real agent behind them, because they are reasoning tasks rather than API calls.

## Usage

```bash
# Full pipeline, all four platforms
python3 scripts/forge.py --source episode.txt --voice voice-profiles/mine.yaml

# Two platforms, save the pack
python3 scripts/forge.py --source notes.md --platforms linkedin,x --out pack.json

# Check an existing draft without generating anything
python3 scripts/critique.py --file draft.txt --platform linkedin
python3 scripts/humanize_check.py --file draft.txt

# Publish
python3 scripts/publish_postiz.py --pack pack.json --when now
python3 scripts/publish_native.py --platform linkedin --pack pack.json
```

## The humanize pass

`references/humanizer.md` carries the full 33-pattern catalogue, ported from [blader/humanizer](https://github.com/blader/humanizer) (MIT) and Wikipedia's [Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) guide, maintained by WikiProject AI Cleanup. It is embedded here rather than referenced as an external dependency, so the skill is self-contained.

The insight underneath all 33 patterns, in Wikipedia's words:

> LLMs use statistical algorithms to guess what should come next. The result tends toward the most statistically likely result that applies to the widest variety of cases.

`scripts/humanize_check.py` detects the mechanically findable subset — dashes, invisible unicode, the AI vocabulary cluster, negative parallelism, rule-of-three runs, filler, signposting, aphorism formulas, inline-header lists, hedge stacks, staccato runs and sentence-length uniformity. It scores by **pattern families hit**, not raw count, because clusters are what matter and a single em dash is nothing.

<img src="assets/detector.svg" alt="humanize_check.py output" width="100%">

Three rules keep the pass honest:

1. **Never invent facts.** Specificity has to come from the source or the author, never from the rewrite. A rewrite that adds a plausible statistic to sound concrete has made the post worse.
2. **A writing sample outranks every style rule**, including the em dash ban. If the author uses them, keep them at their frequency. Sounding like the author beats scrubbing the tell.
3. **Do not sand the post into blandness.** Removing every flagged pattern *and* every opinion, aside and specific leaves competent nothing. That is a failed pass, not a strict one.

## The CLI

`forge.py` runs the whole pipeline outside an agent harness. Colour is truecolor where the terminal supports it, degrades through 256 and 16 colour, and strips to plain ASCII when piped or when `NO_COLOR` is set — so output stays greppable and safe to redirect into a log.

<img src="assets/cli.svg" alt="forge CLI output" width="100%">

Progress goes to stderr and the pack goes to stdout, so `forge.py --source x.txt --json > pack.json` works without the banner landing in your JSON.

## Publishing

| Mode | Setup | Cost | Use when |
|---|---|---|---|
| Copy-paste pack | none | free | Default. Posting a few times a week. |
| [Postiz](https://github.com/gitroomhq/postiz-app) self-hosted | Docker stack | free | Posting daily across several platforms. |
| Native APIs | one OAuth app per platform | mostly free | You only care about one platform. |

Two things worth knowing before you invest an afternoon, both verified August 2026:

- **X is pay-per-use** since February 2026. Roughly $0.01 per post, about **$0.20 if the post contains a URL**. No free tier for new developers.
- **TikTok requires an audit.** Unaudited apps can only post privately (`SELF_ONLY`), and TikTok's content-sharing guidelines explicitly name "a utility tool to help upload contents to the account(s) you or your team manages" as not acceptable.

For those two, the copy-paste pack is usually the honest answer. Full setup instructions, endpoints, scopes, token lifetimes and gotchas are in `references/publishing-setup.md`.

Postiz is the recommended bridge because its self-hosted build has no feature gating and covers all four platforms. Mixpost Lite is free but only covers X, Facebook Pages and Mastodon; LinkedIn, Instagram, TikTok and Threads sit behind its paid tier.

## Layout

```
SKILL.md                              the pipeline — the runtime artifact
references/
  humanizer.md                        33-pattern catalogue + rewrite rules
  ai-tells.md                         condensed three-layer quick card
  rubric.md                           8 scoring criteria, 1-5 each
  platform-conventions.md             per-platform rules, evidenced vs practice
  publishing-setup.md                 Postiz + native API setup
scripts/
  forge.py                            CLI: full pipeline
  ui.py                               terminal styling, stdlib only
  critique.py                         mechanical rubric checks
  humanize_check.py                   AI-tell detector
  publish_postiz.py                   self-hosted Postiz publishing
  publish_native.py                   direct platform APIs
examples/
  voice-profile.example.yaml          the schema, filled in
assets/                               README imagery
```

## The voice profile

Captured once per business, reused every run. The field that matters is `reference_posts` — three real posts that performed well, pasted verbatim including the things that look like mistakes. Those are the voice. Adjectives like "professional but warm" teach a model nothing.

See `examples/voice-profile.example.yaml`.

## Credits

- [blader/humanizer](https://github.com/blader/humanizer) (MIT) — the 33-pattern catalogue
- [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) — WikiProject AI Cleanup, the source underneath it
- [starside-io/ghostwriter](https://github.com/starside-io/ghostwriter) (MIT) — the three-layer tell framework
- [kvsdileep/linkedin-writer](https://github.com/kvsdileep/linkedin-writer) (MIT) — the three-step hook formula
- [Postiz](https://github.com/gitroomhq/postiz-app) (AGPL-3.0) — the self-hosted publishing bridge
- Pipeline ideas from `alankritxghosh/william.ai`, `pauxiel/linkedin-ghost-writer`, `rayane-rhsn/autopost-ai` and Akamai's multi-agent social transform example

## License

MIT. See [LICENSE](LICENSE).
