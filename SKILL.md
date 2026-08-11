---
name: social-post-forge
description: Turn any source (podcast audio, business description, article, URL, notes) into platform-native social posts for LinkedIn, Instagram, X/Threads and TikTok. Drafts natively per platform, scores against an 8-criterion rubric, runs a 33-pattern humanizer pass to strip AI writing tells, rewrites against the structure of currently-trending posts, produces image prompts, then publishes via copy-paste pack, self-hosted Postiz, or native platform APIs. Use for content repurposing, or standalone to audit and humanize an existing draft.
version: 1.0.0
author: Maurice Holda (Naga Codex)
license: MIT
metadata:
  hermes:
    tags: [content, social-media, copywriting, marketing, humanizer, anti-slop, repurposing, linkedin, instagram, tiktok, publishing]
    homepage: https://github.com/Nagacash/social-post-forge
    author_url: https://nagacodex.cloud
    related_skills: [humanizer, ghostwriter]
---

# social-post-forge

Turn any source — a business description, a podcast episode, a text file, a URL, a pile of notes — into platform-native social posts for LinkedIn, Instagram, X/Threads and TikTok/Reels. Every draft is scored against a rubric, rewritten against the structure of what is currently working in the niche, paired with an image prompt, and then either handed over as a copy-paste pack or published automatically.

The pipeline exists because the usual failure mode is not "the AI can't write" — it is that one generic post gets reflowed four ways, nobody checks it, and it reads like every other AI post in the feed. Each stage below is a defence against a specific failure.

---

## When to use this

Use when the user wants social content produced from source material: "make posts from this podcast", "write this week's LinkedIn", "turn our about page into a launch campaign", "repurpose this article". Also use when they want an existing draft critiqued or rewritten against current trends.

Do not use for one-off single-sentence tweets where the whole pipeline is overhead, or for paid ad copy (different discipline, different rubric).

---

## Running this on any harness

This skill is plain Markdown plus standard-library Python, so it runs anywhere that supports skill-style instructions: Hermes Agent, Claude Code, Codex, Cursor, OpenClaw, or a bare shell.

The scripts have **no dependencies** beyond the Python 3.8+ standard library and no API keys, so `humanize_check.py`, `critique.py` and both publishers work identically everywhere. Only the generative stages depend on the host's tools.

Named tools below use Hyperagent's names because that is where this was built. **Substitute your harness's equivalent** — the capability is what matters, not the name.

| Stage needs | Hyperagent | Hermes Agent | Claude Code / Codex | If unavailable |
|---|---|---|---|---|
| Transcribe audio | `TranscribeAudio` | `transcribe` tool, or `whisper` via shell | `whisper` / `ffmpeg` via Bash | Ask the user to paste a transcript. Do not guess at audio content. |
| Read a URL | `ExaContents` | `web_fetch` / `web_search` | `WebFetch` | Ask the user to paste the text. |
| Read a local file | `Read` | `read_file` | `Read` | — (universally available) |
| Trend research | `ExaSearch` (category `tweet`/`linkedin`, date-filtered) | `web_search` | `WebSearch` | **Skip stage 4** and say so. A guessed trend report is worse than none. |
| Generate an image | `GenerateImage` | image toolset if enabled | none by default | Hand over the image prompt. It is useful on its own. |
| Find reference photos | `SearchImages` | `web_search` images | none | Skip; describe the shot in the prompt instead. |
| Public image URL (Instagram) | `PublishFilePublicly` | any static host | any static host | Instagram cannot post without one. Use Postiz, or fall back to copy-paste. |
| Persist the voice profile | `CreateMemory` | Hermes memory / `~/.hermes/` | a file in the repo | Save `voice-profiles/{business}.yaml` next to the skill. |
| Separate reviewer for stage 3a | subagent via `Agent` | `delegate_task` | `Task` tool | Do the critique pass in a fresh turn, and read as a reviewer rather than the author. |

Two rules when a capability is missing:

1. **Degrade loudly.** Tell the user which stage you skipped and why. Silently dropping the trend benchmark and presenting the output as fully processed is the worst possible failure, because the post looks finished.
2. **Never simulate a tool.** No invented transcript, no imagined trending posts, no fabricated engagement numbers. That breaks the anti-fabrication rule the whole pipeline is built around.

### Install

Hermes Agent — use the installer, which resolves the correct directory:

```bash
hermes skills install https://raw.githubusercontent.com/Nagacash/social-post-forge/main/SKILL.md
```

The skills directory differs between Hermes deployments (`~/.hermes/skills/` on some local installs, `/opt/data/skills/` on server and container builds). Copying the folder into the wrong one leaves it invisible to `skills_list` with no error, so run `hermes skills list` to confirm the live path before cloning the full repo there.

Claude Code, Cursor, or any harness with a skills directory:

```bash
git clone https://github.com/Nagacash/social-post-forge \
  ~/.claude/skills/social-post-forge
```

Cross-agent skills CLI:

```bash
npx skills add Nagacash/social-post-forge
```

Clone the whole repo rather than just `SKILL.md` where you can. `SKILL.md` alone still works — it carries the full pipeline — but the references hold the 33-pattern catalogue and the rubric, and the scripts do the mechanical checking. Without them the humanize pass is judgement-only.

---

## The pipeline

```
1. INGEST      source material  →  source brief + voice profile
2. DRAFT       source brief     →  native draft per platform
3a. CRITIQUE   draft            →  rubric score → rewrite until it passes
3b. HUMANIZE   passing draft    →  33-pattern pass → rewrite → audit pass
4. BENCHMARK   humanized draft  →  structural patterns from current top posts → rewrite
5. VISUAL      final copy       →  image prompt (+ optional generated image)
6. PUBLISH     final pack       →  copy-paste / Postiz / native API
```

Never skip stage 3. A draft that has not been scored is not finished, it is just written. And a draft that has not been through the humanizer reads like every other post in the feed, which is the same as not being read.

---

## Stage 1 — Ingest

Goal: one **source brief** that everything downstream reads from. Never write posts straight off raw source.

### Getting the material in

| Source | How |
|---|---|
| Podcast / audio | `TranscribeAudio` with `speakerDiarization: true`, then mine the transcript |
| Video | Transcribe the audio track the same way |
| URL / article | `ExaContents` with `text: true` |
| Text / markdown / PDF file | Read it directly; `FetchStoredFile` first if it is an uploaded attachment |
| Business description | Ask the user, or read their site with `ExaContents` |
| Loose notes | Take as-is |

For podcasts specifically: do not summarise the episode. Summaries make dull posts. Hunt for **the 3–5 most quotable moments** — a claim someone would argue with, a number that surprises, a story with a turn in it, a strong opinion stated plainly. Quote them near-verbatim in the brief with speaker attribution, because the actual phrasing is the raw material.

### The source brief

Produce this before drafting anything:

```yaml
source_brief:
  what_this_is: "Episode 12 of the Naga Codex podcast, 48 minutes, two speakers"
  core_thesis: "One sentence. The single argument worth making."
  key_points:
    - "3-5 supporting points, each concrete"
  quotable_moments:
    - speaker: "Maurice"
      quote: "Near-verbatim. The actual words."
      why: "Contrarian — most people believe the opposite"
  hard_facts:
    - "Numbers, dates, names, prices, outcomes. These are gold — posts live or die on them."
  audience: "Who this is for, specifically"
  what_most_people_get_wrong: "The contrarian angle. Required, not optional."
```

If `hard_facts` comes back empty, stop and ask the user for specifics. A post with no numbers, names or dates cannot score above a 3 on Specificity and will read like every other post in the feed.

### The voice profile

Captured **once per business**, reused every run. Save it as a memory (`CreateMemory`, category `project_context`) or as `voice-profiles/{business}.yaml` in the repo so the second run is cheaper than the first.

See `examples/voice-profile.example.yaml` for the full schema. The parts that matter most:

- `reference_posts` — 3 real posts by this author that performed well. These anchor the voice far better than adjectives do. "Professional but warm" means nothing; three real posts mean everything.
- `banned` — words and claims this business will not say.
- `pillars` — the 3–5 recurring themes, so content stays on-territory.
- `cta_default` — what a reader should actually do.

If no voice profile exists and the user cannot supply reference posts, say so plainly and write in a neutral register rather than inventing a personality for them.

---

## Stage 2 — Draft

Write each platform **from the source brief**, natively. Do not write one post and reflow it — that is the single most visible tell of automated content, because LinkedIn structure in an Instagram caption reads wrong to anyone who uses both.

Full conventions with evidence are in `references/platform-conventions.md`. The short version:

**LinkedIn** — 1,800–2,800 characters. Structure: Hook → Problem → Named Framework → Action → Engagement question. Paragraphs of 1–3 sentences with blank lines between. 1–3 specific hashtags at the end. No em-dashes. The first ~140 characters are all that shows before "see more", so the hook carries the whole post.

**Instagram** — caption under ~30 words outperforms on engagement for most accounts; go longer only when the story earns it. First line self-contained and curiosity-led. High-priority CTA near the top, not only at the bottom. 3–5 tight hashtags. Also produce **carousel slide copy** (6–8 slides, one idea per slide, slide 1 is the hook, last slide is the CTA) since carousels outperform single images for saves.

**X / Threads** — 100–200 characters is the engagement sweet spot for a single post. One idea. If the material needs more, write a thread: post 1 is a standalone hook with the outcome stated, each following post carries exactly one idea, the last is the takeaway. Hashtags are not needed on X. Threads (Meta) allows 500 characters and reads more conversationally.

**TikTok / Reels** — a script, not a caption. The first 3 seconds decide everything. Format:

```
0-1s   [visual]  movement or a striking result on screen
1-3s   [spoken]  the promise or the problem, said plainly
       [on-screen text]  the same claim, written
3-20s  [beats]   rapid proof, one point per beat
end    [payoff + specific comment prompt]
```

Write the on-screen text separately from the spoken line — they do different jobs and TikTok is a search engine, so the caption and on-screen text should carry the words someone would actually search.

### Angle discipline

When producing several posts from one source, force **different angles** rather than three flavours of the same post. Use the three-angle rule: one **story** post, one **framework** post, one **opinion** post. This is borrowed from PAUL (`pauxiel/linkedin-ghost-writer`) and it is the cheapest possible defence against repetitive output.

---

## Stage 3a — Critique

This is the stage that makes the difference, so do not treat it as a formality. Run it as a genuinely separate reviewing pass — ideally a subagent with the rubric and the draft but **not** the enthusiasm of having just written it.

Run the mechanical checker first, since it is free and catches the dumb stuff:

```bash
python3 scripts/critique.py --file draft.json --platform linkedin
```

It checks character limits, paragraph density, em-dashes and invisible unicode, banned vocabulary, hashtag counts, specificity markers (numbers/names/dates), sentence-length uniformity, and CTA presence. It returns a JSON report with a mechanical score and specific line-level findings.

Then score the draft against the eight criteria in `references/rubric.md`:

1. Hook Strength
2. Specificity / Anti-Slop
3. Voice Authenticity
4. Platform Formatting Compliance
5. CTA Clarity and Placement
6. Shareability / Value Density
7. Angle Discipline
8. Anti-Fabrication

**Pass threshold: every criterion ≥ 4, and Anti-Fabrication = 5.** Anything below that gets rewritten and rescored, not shipped with a caveat. Cap at three rewrite rounds; if it still fails after three, the source brief is too thin — go back and ask the user for more specifics rather than polishing an empty post.

Anti-Fabrication deserves special attention: every number, name, quote and claim in the post must trace back to `source_brief.hard_facts` or `quotable_moments`. If a statistic appeared during drafting but is not in the brief, the model invented it. Cut it.

---

## Stage 3b — Humanize

The rubric catches whether a post is *good*. This stage catches whether it reads as though a machine wrote it, which is a different failure and a more common one. A post can score 4s across the board and still be unmistakably synthetic.

Work through **`references/humanizer.md`** — the full 33-pattern catalogue, ported from [blader/humanizer](https://github.com/blader/humanizer) (MIT) and Wikipedia's WikiProject AI Cleanup guide. It is embedded in this repo rather than referenced externally, so the skill is self-contained. `references/ai-tells.md` is the condensed three-layer card for quick inline checking; `humanizer.md` is the authority.

Run the detector first:

```bash
python3 scripts/humanize_check.py --file draft.txt
```

It flags em and en dashes, invisible unicode, the AI vocabulary cluster, negative parallelism, rule-of-three runs, filler phrases, signposting, aphorism formulas, inline-header lists, sycophancy, hedge stacks and staccato runs — with line numbers and suggested replacements.

Then the four rules that govern the rewrite:

1. Identify every instance before changing anything.
2. Preserve the information, not the shape. When keeping information and mirroring structure conflict, information wins.
3. **Never invent facts.** Specificity has to come from the source brief or the user, never from the rewrite. A humanizing pass that invents a statistic to sound concrete has made the post worse and drops Anti-Fabrication to a 1.
4. Match the voice.

Two things that override the defaults:

- **A writing sample outranks every style rule, including the em dash ban.** If `voice_profile.reference_posts` shows the author uses em dashes, keep them at their frequency. Sounding like the author beats scrubbing the tell.
- **Look for clusters, not isolated hits — except the hard rules.** For judgement patterns a single hit means nothing; they only convict in combination. This matters most for quoted material: if a podcast guest actually said "it's not just a tool, it's a mindset", that gets quoted verbatim, because the patterns apply to your prose and not to their words. **Dashes and invisible unicode are the exception and fail at any count.** The detector reports them as `hard_fail` with a non-zero exit, and a cluster score of 1 must not be allowed to launder a surviving banned character.

**Enforce, do not report.** After the rewrite, re-run the detector. If a hard rule survived, do a surgical repair pass that fixes only the residue and touches nothing else, then re-check. `forge.py` does this automatically for up to two rounds and flags the pack loudly if anything still fails. Reporting "1 tell family, probably fine" while shipping a banned pattern is the failure mode this stage exists to prevent.

Finish with the **audit pass**, which is the step people skip. After rewriting, ask and briefly answer:

- *What makes this obviously AI generated?*
- *Does the rewrite state any fact, name, number, date or citation that is not in the source brief?*

Then produce a final version. The upstream project added this second look precisely because the first rewrite tends to introduce new tells while fixing old ones.

One caution: do not sand the post into smooth competence. Specific hard-to-fabricate detail, mixed feelings, genuine asides, uneven sentence length and defensible first-person opinions are what make it read human. Removing every flagged pattern while also removing those leaves a clean post that nobody wants to read, and that is a failed pass, not a strict one.

Rescore the affected rubric criteria afterwards — Hook, Voice and Specificity all move during this stage.

---

## Stage 4 — Trend benchmark

Rewrite the passing draft against the **structure** of what is currently working in the niche. Structure only — never wording.

Dispatch a subagent:

```
ExaSearch, category "tweet" or "linkedin", startPublishedDate = last 14 days,
query = the niche + topic
```

Have it return a **structural pattern report**, not post text:

```yaml
pattern:
  dominant_hook_type: "number-led | contrarian claim | personal stake | question"
  typical_length: "chars or words"
  formatting: "single para | short-line stack | numbered list | thread"
  angle_distribution: "what positions are being taken"
  what_is_absent: "the gap nobody is filling — often the best angle available"
```

Then rewrite the draft to match the winning structure while keeping your own thesis, facts and voice.

The discipline that keeps this from producing derivative slop: **extract the shape, discard the text.** Do not paste trending posts into the drafting context. The subagent reads them; the writer only ever sees the pattern report. This is how PAUL, AutoPost AI and SocialFlow all handle it, and it is the difference between "informed by what works" and "wrote a slightly worse version of someone else's post".

Pay attention to `what_is_absent`. If everyone in the niche is posting optimistic takes, the contrarian one is the one that gets seen.

Rescore after rewriting. A trend rewrite can quietly break the hook or drop a hard fact.

---

## Stage 5 — Visual

**Always** produce an image prompt per post, whether or not the user wants it generated. The prompt is useful on its own.

Write prompts with specific visual nouns, not concepts. "AI automation" is not an image. From AutoPost AI's writer prompt, the rule is 5–12 descriptive keywords covering subject + action + context + light/mood + visual detail:

- Weak: `business growth, AI, success`
- Strong: `young founder at a standing desk reviewing a printed dashboard, early morning window light, muted greys and one accent colour, shallow depth of field`

Match format to platform: 4:5 for Instagram feed, 9:16 for Reels/TikTok covers and Stories, 1.91:1 for LinkedIn link posts, 16:9 for X.

Then **ask the user**: generate the image now, or keep the prompt? Only make the offer if your harness actually has image generation (see the capability table above) — on Hyperagent it does, on a stock Claude Code install it does not. Where it is unavailable, hand over the prompt and say so rather than promising an image you cannot produce. If it is available:

```
GenerateImage({ prompt, aspectRatio: "4:5", title: "IG post — <topic>" })
```

For anything grounded in a real place, product or person, use `SearchImages` first and pass the result as `inputImages` — editing a real photo beats imagining one. Never generate a fake photo of a real person or a real venue and present it as documentation.

---

## Stage 6 — Publish

Three modes. Default to the first unless the user has set the others up.

### Mode A — Copy-paste pack (default, zero setup)

Emit a clean per-platform block: final copy, hashtags, image prompt or generated image, and suggested posting time. This is what most users actually want, and it keeps a human in the loop before anything goes public.

### Mode B — Postiz (self-hosted, open source, free)

Postiz (AGPL-3.0) is the best free bridge: one local API, ~30 platforms, no feature gating on self-hosted, and no per-post fee. Setup is in `references/publishing-setup.md`.

```bash
python3 scripts/publish_postiz.py --pack pack.json --when now
python3 scripts/publish_postiz.py --pack pack.json --when 2026-09-01T10:00:00Z
python3 scripts/publish_postiz.py --list-channels
```

Requires `POSTIZ_URL` and `POSTIZ_API_KEY`. Note that Postiz auth uses a raw `Authorization: <key>` header, not `Bearer`. You still create your own developer app per network — Postiz brokers the posting, not the credentials.

Mixpost is the alternative, but its free Lite tier only covers X, Facebook Pages and Mastodon; LinkedIn, Instagram, TikTok and Threads all sit behind the paid Pro licence. For this project's platform set, Postiz is the one that is genuinely free.

### Mode C — Native APIs (no middleman)

`scripts/publish_native.py` posts directly. Per-platform reality, verified August 2026:

| Platform | Cost | Review needed for your own account? | Main friction |
|---|---|---|---|
| Threads | Free | No — add yourself as app Tester | Easiest of the four |
| LinkedIn | Free | No — `w_member_social` works immediately | 60-day token, no refresh token without partner status, so re-auth every 60 days |
| Instagram | Free | No | Business/Creator account linked to a Facebook Page; image must be a public HTTPS JPEG URL; two-step container then publish |
| X | **Paid** | No | Pay-per-use since Feb 2026, ~$0.01/post and ~$0.20 if the post contains a URL; no free tier for new developers |
| TikTok | Free | **Yes** | Unaudited apps can only post `SELF_ONLY` (private). Public posting needs a TikTok audit, and their policy language explicitly disfavours personal automation tools |

Two things to tell the user up front rather than after they have spent an afternoon on it: **X now costs money per post**, and **TikTok will not let you post publicly until your app passes an audit**. For those two, the copy-paste pack is usually the honest answer.

Instagram needs the image at a public HTTPS URL. `PublishFilePublicly` on a generated image supplies exactly that.

---

## Running the whole thing

Inside an agent harness, work through the stages using the host's tools directly — that is the intended path and gives the best results, because critique and trend benchmarking are reasoning tasks rather than API calls.

The repo also ships a CLI for use outside a harness:

```bash
python3 scripts/forge.py --source episode.txt --voice voice-profiles/naga.yaml --platforms linkedin,instagram,x,tiktok
```

The CLI orchestrates ingest, mechanical critique and publishing, and calls an LLM API for the generative stages. It needs `ANTHROPIC_API_KEY`. It is deliberately the thinner experience — it has no trend benchmarking, because that needs a browsing agent, and its critique stage is mechanical only.

---

## Failure modes worth naming

- **The brief was thin and you wrote anyway.** No hard facts means no good post. Ask instead of padding.
- **You skipped the critique because the draft "read fine".** It always reads fine to the writer. Score it.
- **You ran the humanizer as a find-and-replace.** Swapping `—` for `-` or "leverage" for "use" leaves the construction intact. Rewrite the sentence.
- **You humanized the post into blandness.** Removing every tell *and* every opinion, aside and specific leaves competent nothing. The asides are the point.
- **Trending posts leaked into the drafting context.** Now you have a derivative post. Only the pattern report crosses that boundary.
- **You reflowed one post four ways.** Native drafting per platform, every time.
- **A statistic appeared out of nowhere.** Check it against the brief. If it is not there, it is invented.
- **You promised automated posting on X or TikTok without mentioning cost and audit gates.** Surface those before the user builds on the assumption.
