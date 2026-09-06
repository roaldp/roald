# Roald's measured writing profile

Measured 2026-09-06 from his own typed prompts in `~/.claude/projects/**/*.jsonl`. This
answers verification item 7: calibrate the style rules against his corpus rather than
against a published human baseline.

## What was measured, and what it is not

Every message in every Claude Code session log where `type` is `user` and `isMeta` is
false. Filtered to remove anything that is not him typing:

- Shorter than 40 characters, or longer than 600.
- Containing a code fence, a bullet list, a markdown header, a table, or bold markup.
  These are pasted documents and pasted agent output, not his writing.
- More than six newlines.
- Starting with `/`, `{`, or `[Request interrupted`.
- Duplicates, keyed on the first 120 characters lowercased. This removes the pulse
  companion's automated prompts, which repeat verbatim thousands of times and would
  otherwise dominate the sample.

What survives: **1,707 unique prompts, 48,664 words.**

**This is his instructing-an-agent register, not his external-email register.** He types
these fast, in lowercase, with typos, to a machine. Forty-eight per cent of sentences
start with a lowercase letter. Nothing here should be copied into a rule about how to
write to an investor. What it is good for is two things: calibrating the mechanical
thresholds that are register-independent, such as em-dash rate, and setting the target
for how an agent should write *to him*.

The register-specific corpus — what he actually sends to people — is in
`research/05-roald-writing-corpus.md`: nine labelled before-and-after pairs, 42 Slack
messages, 14 emails, 12 commit messages.

## Punctuation, per 1,000 words

| Mark | Roald | Published baselines |
|---|---|---|
| Em dash | **1.01** | Human ~3.23. The threshold used to flag AI text is 20. |
| Semicolon | 0.39 | — |
| Open parenthesis | 5.61 | — |
| Colon | 9.64 | — |
| Comma | 37.19 | — |

**The em-dash rule is well calibrated to him and then some.** At 1.01 per thousand words
he uses em dashes at under a third of the published human rate, and at one twentieth of
the rate that flags text as machine-written. An agent writing at even the human baseline
is writing three times more em dashes than he does. The ban stays, and the target is zero
rather than "human-like".

Semicolons at 0.39 per thousand mean he effectively does not use them. The existing AIC
rule "no semicolons in body copy, split the sentence" matches his own practice.

Commas at 37 per thousand against a very low semicolon and em-dash rate is the mechanical
signature of the habit the corpus agent identified independently: **he chains clauses with
commas.** `Read your background and looking to learn.` `we are working to get the equity
released, assume its still in chf and todays fx is 1.00 CHF = 1.22964931 USD, what if we
dont get it released before …`

That has a direct consequence for the style guide. A rule that says "short sentences" or
"one idea per sentence" will produce clean full stops, and clean full stops are not what
he writes. The rule that fits his corpus is: **join clauses with a comma and a conjunction,
never with a dash or a semicolon.**

## Sentences

| Measure | Roald |
|---|---|
| Count | 3,334 |
| Mean length | 14.6 words |
| Median length | 12 words |
| Burstiness, standard deviation over mean | 0.71 |
| Under 8 words | 24% |
| Over 20 words | 21% |
| Over 40 words | 3% |

Mean 14.6 words is close to AR 25-50's roughly-fifteen-word doctrine for a
bottom-line-up-front memorandum, which is a convenient coincidence rather than evidence of
anything.

Burstiness at 0.71 clears the 0.6 threshold that is used as the marker for human-varied
sentence length. The mean sitting above the median by 2.6 words is the shape you get from
a mass of short sentences with a long one thrown in, which is exactly what the "one
sentence under eight words and one over twenty per paragraph" rule is trying to reproduce.

**The mechanical targets for generated prose, taken from his own numbers rather than from
a published baseline:**

- Em dashes: zero. Anything above about one per thousand words is already above him.
- Semicolons: zero.
- Mean sentence length: 12 to 16 words.
- Burstiness: at or above 0.7.
- Roughly a quarter of sentences under eight words, roughly a fifth over twenty, almost
  none over forty.

## Constructions he does not use

Measured across the same corpus, per 1,000 words:

| Construction | Rate |
|---|---|
| "not just X, it's Y" | 0.00 |
| Additionally, Moreover, Furthermore, In conclusion | 0.01 |
| leverage, robust, seamless, delve, streamline, holistic, synergy | 0.08 |

Zero, and near-zero. Every one of these is on the banned list already, and his own corpus
confirms he does not write them. That is the useful direction of evidence: the rules are
not asking an agent to write unlike Roald in order to sound less like an AI. They are
asking it to write like Roald.

## Two habits from the labelled corpus that the numbers do not show

From `research/05-roald-writing-corpus.md`:

**He drops subjects and auxiliaries.** `Was nice to meet you today.` `Read your background
and looking to learn.` This is a non-native-speaker construction and it is a large part of
why his writing does not read as generated. It cannot be produced by a rule that says
"write short sentences"; it has to come from exemplars.

**He never writes a closing line.** He ends on a question or an offer: `Worth to do
another call?`, `Anything else needed?`. In one of the labelled pairs he deleted the
drafted closing outright. This independently confirms section 3 of the existing AIC
`STYLE.md`, which bans closing lines and was derived from a different set of edits.

## Gap in the corpus

No English long-form prose that he wrote unaided. His longest unaided writing is in Dutch.
So for a long English document the exemplar set is thin, and the style guide is
extrapolating from short-form. Worth saying out loud rather than pretending the corpus
covers it.

## Reproducing this

The measurement script is inline in the session transcript for this run rather than
committed, because it is a one-off. If it becomes a recurring check it belongs in
`scripts/` next to `agent_inventory.py`, and the natural form is a `--profile` flag on the
style linter that reports these numbers for any text file.
