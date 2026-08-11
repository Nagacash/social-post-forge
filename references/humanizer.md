# Humanizer — the full catalogue

Ported from [blader/humanizer](https://github.com/blader/humanizer) (MIT), which is built on [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), maintained by WikiProject AI Cleanup from observations across thousands of instances of machine-generated text. Adapted here for social posts.

The insight underneath all 33 patterns, in Wikipedia's words:

> LLMs use statistical algorithms to guess what should come next. The result tends toward the most statistically likely result that applies to the widest variety of cases.

That averageness is the tell. Not errors — the absence of them. A post that could have been written about any company by any person is the failure state, and on social platforms it is fatal, because the feed is a competition for attention against people writing from actual experience.

This runs as **stage 3b**, after the rubric scoring and before the trend benchmark. It is not optional.

---

## The four rules of the rewrite

1. **Identify every instance** before rewriting anything.
2. **Preserve the information, not the shape.** Every claim survives. Depth need not be uniform — compress the dull parts, dwell where a human would, merge or split paragraphs freely. When keeping information and mirroring structure conflict, information wins.
3. **Never invent facts.** No name, number, date, quote or citation that is not in the source brief. Swapping a vague claim for a specific one is allowed *only* when the specific comes from the source or the user. If a sentence needs real detail to work, ask for it or write the plain version. Opinions and stance are voice, not facts.
4. **Match the voice.** Add personality only where the content calls for it.

Rule 3 is the one that interacts with the rubric: a humanizing rewrite that invents a statistic to sound more concrete has made the post worse, not better, and drops criterion 8 to a 1.

---

## Voice calibration beats every rule below

If the voice profile has `reference_posts`, analyse them before rewriting: sentence lengths, vocabulary, paragraph openings, punctuation habits, recurring phrases. Match those habits rather than producing generically clean output. Do not upgrade casual words or regularise deliberate quirks.

**A writing sample outranks every style rule in this file, including the em dash ban.** If the author uses em dashes, keep them at the sample's frequency. Matching the author beats scrubbing the tell — a post that sounds like the author with three em dashes in it beats a spotless post that sounds like nobody.

---

## Personality and soul

Avoiding AI patterns is half the job. Voiceless writing is as obvious as slop, and on social it performs worse, because there is nothing to follow.

Apply voice where the content calls for it — opinion posts, personal stories, founder writing, anything with a human name attached. For a compliance notice or a product spec, neutral and plain *is* the correct human register.

Where voice belongs: avoid uniform sentence structures, bloodless neutrality and perfect organisation. Let the writer have opinions, uncertainty, mixed feelings, humour, asides, uneven rhythm. Never add factual claims to manufacture personality.

---

## Content patterns

**1. Undue emphasis on significance, legacy, broader trends.**
Watch: stands/serves as, is a testament, a vital/crucial/pivotal/key role, underscores its importance, reflects broader, symbolizing its enduring, contributing to the, setting the stage for, marks a shift, key turning point, evolving landscape, indelible mark, deeply rooted.
> Before: Established in 1989, marking a pivotal moment in the evolution of regional statistics.
> After: Established in 1989, part of a wider decentralization of administrative functions.

**2. Undue emphasis on notability and coverage.** Watch: independent coverage, national media outlets, written by a leading expert, active social media presence. Keep the one real citation with context; drop the list.

**3. Superficial analysis with -ing endings.** Watch: highlighting, underscoring, emphasizing, ensuring, reflecting, symbolizing, contributing to, cultivating, fostering, encompassing, showcasing. Participles tacked on to fake depth.
> Before: Colors resonate with the region's natural beauty, symbolizing bluebonnets, reflecting the community's deep connection to the land.
> After: Painted blue, green and gold, colors meant to evoke Texas bluebonnets.

**4. Promotional language.** Watch: boasts a, vibrant, rich (figurative), profound, enhancing its, showcasing, exemplifies, commitment to, natural beauty, nestled, in the heart of, groundbreaking, renowned, breathtaking, must-visit, stunning. Endemic in brand social copy, which is exactly why it reads as advertising and gets scrolled past.

**5. Vague attribution and weasel words.** Watch: industry reports, observers have cited, experts argue, some critics argue, several sources. Name the real source or cut the claim. Never invent one to make a sentence sound sourced.

**6. Outline-like "challenges and future prospects" structure.** Watch: Despite its… faces several challenges, Despite these challenges, Challenges and Legacy, Future Outlook. On social this shows up as the obligatory "of course, there are challenges" paragraph before a hopeful close.

---

## Language and grammar

**7. AI vocabulary.** actually, additionally, align with, crucial, delve, emphasizing, enduring, enhance, fostering, garner, highlight (verb), interplay, intricate, key (adj), landscape (abstract), pivotal, showcase, tapestry, testament, underscore, valuable, vibrant. They co-occur — a cluster is the confession, a single instance is nothing.

**8. Copula avoidance.** Watch: serves as, stands as, marks, represents, boasts, features, offers. Use *is* and *has*.
> Before: Gallery 825 serves as the exhibition space and boasts over 3,000 square feet.
> After: Gallery 825 is the exhibition space. It has four rooms totaling 3,000 square feet.

**9. Negative parallelism and tailing negations.** "Not only X but Y", "It's not just X, it's Y", plus clipped fragments bolted on the end ("no guessing", "no wasted motion"). Epidemic in LinkedIn copy.
> Before: The options come from the selected item, no guessing.
> After: The options come from the selected item without forcing the user to guess.

**10. Rule of three overuse.** Ideas forced into triads to look comprehensive. Break it: use two items, or four, or a sentence.

**11. Elegant variation.** Synonym cycling driven by repetition penalties — protagonist, main character, central figure, hero. Reuse the plain noun.

**12. False ranges.** "From X to Y" where X and Y are not on a scale.

**13. Passive voice and subjectless fragments.** "No configuration file needed." "The results are preserved automatically." Name the actor.

---

## Style

**14. Em dashes and en dashes — cut them.** The final text contains no — and no –. The most reliable single tell, so treat it as a hard constraint rather than a preference. Replace in this order: period, comma, colon, parentheses, or restructure the sentence. Catch spaced ` — ` and double hyphens ` -- ` too. Scan the finished draft for both characters; any hit means it is not done. Only a writing sample that uses them overrides this.

**15. Boldface overuse.** Mechanical emphasis of key terms. Most platforms do not even render it, so it arrives as literal asterisks.

**16. Inline-header vertical lists.** Bulleted `**Term:** sentence` blocks. Convert to prose. This is the single most recognisable "AI wrote my LinkedIn post" shape.

**17. Title case in headings.** Use sentence case.

**18. Emojis decorating headings or bullets.** Distinct from platform-native emoji use — a pointing-down emoji before a closing question is idiomatic on LinkedIn; a decorative sparkle in front of every bullet is a machine signature.

**19. Curly quotation marks.** Use straight quotes. Alone this proves nothing; editors auto-curl.

---

## Communication

**20. Collaborative artifacts.** I hope this helps, Of course!, Certainly!, You're absolutely right, Would you like, Want me to, let me know, here is a. These leak from chat into the post itself.

**21. Knowledge-cutoff disclaimers and speculative gap-filling.** as of [date], while specific details are limited, based on available information, not publicly available, maintains a low profile, likely grew up, it is believed that. Say what is not known, or cut the sentence. Never dress a guess as fact.

**22. Sycophantic tone.** Great question, excellent point, you're absolutely right.

---

## Filler and hedging

**23. Filler phrases.** "In order to achieve this goal" → "To achieve this". "Due to the fact that" → "Because". "At this point in time" → "Now". "In the event that" → "If". "Has the ability to" → "can". "It is important to note that the data shows" → "The data shows". On a 280-character post, filler is not just a tell, it is theft of the only space you have.

**24. Excessive hedging.** Stacked qualifiers: could potentially possibly might.

**25. Generic positive conclusions.** "The future looks bright." "Exciting times ahead." Cut the paragraph. End on the last concrete fact, not a send-off.

**26. Hyphenated pair overuse.** third-party, cross-functional, client-facing, data-driven, decision-making, well-known, high-quality, real-time, long-term, end-to-end. Keep the hyphen attributively ("a high-quality report"), drop it in predicate position ("the report is high quality").

**27. Persuasive authority tropes.** The real question is, at its core, in reality, what really matters, fundamentally, the deeper issue, the heart of the matter. Ceremony around an ordinary point.

**28. Signposting.** Let's dive in, let's explore, let's break this down, here's what you need to know, without further ado. Do the thing instead of announcing it.

**29. Fragmented headers.** A heading followed by a one-line restatement of the heading.

**30. Diff-anchored writing.** Describing something by narrating what changed, outside an actual changelog.

**31. Manufactured punchlines and staccato drama.** Every sentence landing like a closer, then stacked fragments for effect. One short sentence is fine. A run of them sounds engineered — and this is the default register of bad LinkedIn writing, so it is the one to watch hardest here.

**32. Aphorism formulas.** X is the Y of Z, X becomes a trap, the language of, the currency of, the architecture of. Replace with the concrete claim it gestures at.

**33. Conversational rhetorical openers.** Honestly?, Look, Here's the thing, The thing is, Let's be honest, Real talk — used as fake-candid hooks. A person being honest usually just says the thing.

---

## Do not flag these (false positives)

Perfect grammar. Mixed casual and formal register. Bland prose with no specific tells. Formal vocabulary generally. Salutations and sign-offs. A single *however* or *additionally*. Curly quotes alone. Em dashes alone. One short emphatic sentence. Mid-sentence "honestly" or "look". Unsourced claims. Clean formatting. Any watched phrase appearing inside a quotation, a title, or an example where the phrase is being discussed rather than used.

**Look for clusters, not isolated hits.** One em dash means nothing. Em dashes plus rule-of-three plus "vibrant tapestry" plus a tidy conclusion is a confession.

This matters especially for quoted material. A podcast guest who actually said "it's not just a tool, it's a mindset" gets quoted verbatim. Pattern 9 applies to your prose, not to their words.

---

## Preserve these (signs of human writing)

Specific, hard-to-fabricate detail. Mixed feelings and unresolved tension. Dated, era-bound references. First-person choices the writer can defend. Variety in sentence length. Genuine asides and self-corrections.

Over-editing these destroys the thing that made the post worth reading. A humanizing pass that sands a post down to smooth competence has failed, even if it removed every flagged pattern.

---

## Process

1. Run `scripts/humanize_check.py` to find the mechanically detectable patterns.
2. Identify the remaining instances by reading.
3. Rewrite. Check it reads naturally aloud, varies sentence length, prefers specific detail and simple constructions.
4. Ask two questions and answer both briefly:
   - *What makes this obviously AI generated?*
   - *Does the rewrite state any fact, name, number, date or citation that is not in the source brief?*
   A fabrication is a defect even when it sounds more human.
5. Produce the final version, containing no em or en dashes.

Step 4 is the audit pass. The upstream project found that a second look after the first rewrite catches what the first pass introduced while fixing something else — so do not skip it on the grounds that you already checked.

---

## Social-specific application layer

The catalogue is necessary but not sufficient for posts. Additional rules for content a stranger judges in under two seconds:

- **No structure theatre.** Bullets, headers and bold inside a 200-word post are a machine signature. A person typing a thought does not format it like documentation.
- **One idea per post.** Not three. The urge to be comprehensive is a model instinct, not a human one.
- **The first line cannot be throat-clearing.** No "I've been thinking a lot about…", no "In today's landscape…". Open on the thing itself.
- **Specifics are the whole game.** Real numbers, real tool names, real outcomes. Verify each against the source brief before publishing.
- **Uneven rhythm.** Vary paragraph length. Let one sentence be deliberately blunt. Avoid the symmetrical three-beat body.
- **Admit a limit.** "This might not work for you" and "I got this wrong for two years" read unmistakably human and outperform manufactured certainty.
- **End on the ask or the last concrete fact.** No summary line, no "what do you think?" bolted onto an unrelated post.
- **Match the register of the platform, not of the brand deck.** The same claim is phrased differently on LinkedIn and TikTok, and the brand-deck phrasing is wrong on both.
