# House style for anything a person outside the company will read

Emails, Slack and WhatsApp messages, documents, proposals, pull request descriptions
people outside the team read. Not code comments, not internal notes to Roald.

This file governs wording, rhythm and punctuation. Facts come from the brief. Shape comes
from the format. Claims we cannot stand behind are a separate matter and live with the
project that owns them.

Two sources built this. The AIC house style in
`ai-infrastructure-capital/docs/pitch-materials/style/STYLE.md`, which was derived from
Roald's own edits to investor copy. And a corpus of 1,707 typed prompts, 42 Slack
messages, 14 emails and nine labelled before-and-after pairs, measured in
`.docs/plans/2026.09.06-agent-operating-framework/05-roald-writing-profile.md`.

Where the two disagree, the corpus wins, because it is what he actually sends.

Line cap: 200. Adding a rule means cutting one that has stopped earning its place.

## 1. The nine pairs

These are the mechanism. The rules below are the backstop. Read the pairs first, and when
a rule and a pair conflict, follow the pair.

Full set in
`.docs/plans/2026.09.06-agent-operating-framework/research/05-roald-writing-corpus.md`
section A. The four that recur most:

> ✗ Hi Joseph — good speaking. Short rundown you can forward to Samson.
>
> ✓ Hi Joseph, was good meeting you. Here's a quick rundown:

Three edits in one line. The em dash became a comma. The subject was dropped, giving
"was good meeting you". And the instruction to the reader was deleted outright.

> ✗ US neoclouds, USD 1bn+ scale, who resell into the AI labs
>
> ✓ Tier 1 and 2 (US) neoclouds

He cut the explanation and kept the fact, and he used the label the reader's industry
already uses instead of the descriptor we invented.

> ✗ Low USD 4 per GPU-hour, fixed for the term
>
> ✓ Around USD 4 per GPU-hour

A committing word became an open one. He does this whenever a figure is not yet settled.

> ✗ …and there it is. Happy to go deeper once the NDA is signed.
>
> ✓ *(deleted, along with his own signature)*

He deletes the close. In seven separate cases he deleted a closing line and added nothing
in its place.

## 2. What he consistently changes about agent drafts

Ranked by how often the same edit recurs across the labelled pairs.

**He cuts the explanation of a fact and keeps the fact.** His own instruction, typed to an
agent: "Give away the minimum amount of information only and just a clear short reason."
Where a fact is specific enough — a named institution, a figure, a date — it is its own
justification and the sentence explaining why it is impressive gets deleted.

**He deletes the close.** No summarising line, no "this is what it means for you". Where
something does end a message it is an offer or a question. "Worth to do another call?"
"Anything else needed?" "Bel me gerust, of laat weten indien er nog verdere vragen zijn."

**He replaces a committing word with an open one.** "Around" rather than "fixed for the
term". He marks the specific thing he is unsure about rather than softening the whole
message.

**He breaks one long sentence into labelled lines.** A company-name-as-subject sentence
becomes a bare header, then a capability line, then a footprint line.

**He removes instructions to the reader.** Not "forward this to your colleague", not "ask
for the signed contracts". Offer instead, and vary the offer between documents.

**Where compression has removed an argument he restores it, with an operational fact
rather than a flourish.** This is the one direction in which his edit makes text longer.

## 3. Sentences

Target 12 to 16 words on average. Never over 40. His measured mean is 14.6 and his median
is 12.

Vary the length on purpose. About a quarter of his sentences run under eight words and
about a fifth run over twenty. Uniform sentence length is the single structural marker
that every source on machine-written text agrees on.

**Join clauses with a comma and a conjunction.** This is the most consistent surface
marker in his writing and an agent should reproduce it rather than correct it. "If they
are in Reykjavik, sure, it's always good to know lawyers and they seemed highly placed and
well connected." Do not convert these into separate sentences.

Drop the subject where he would. "Was nice to meet you today." "Read your background and
looking to learn." "Had inquired with Alta for my nodes as well but were lowballing it."

Active voice, present tense, "we" as the subject. Never "AIC is positioned to", never "the
vehicle seeks to", never "please find attached", never "kindly".

Contractions always. "We're", "didn't", "it'd", "don't", including in email to
counterparties.

Open on the concrete thing. Address the reader as "you" where risk or benefit is at stake.
Define jargon inline on first use, in ordinary words.

## 4. Punctuation

**Em dash inside a sentence: budget one per thousand words, and prefer zero.** His measured
rate is 1.01 per thousand, against a published human baseline of 3.23. Use a comma, or a
full stop, or a comma with "and", "so" or "but". Em dashes are fine in a label or an
eyebrow, which is where his own use of them sits: "Andy Chen, VP Global Business, Taipei —
the senior commercial one".

**Semicolons: none.** His measured rate is 0.39 per thousand words, which is close enough
to never. Split the sentence, or use a comma and a conjunction.

**Parentheses: sparingly, and they are allowed.** His measured rate is 5.61 per thousand.
The AIC guide bans them and the corpus does not support the ban. This is deliberate rather
than an oversight: banning the em dash, the semicolon and the parenthesis together leaves
only commas and full stops, which produces the long undifferentiated "and"-joined sentence
that is the current marker of machine-written English.

No exclamation marks in cold outreach or in anything an investor reads. In a warm channel
he doubles them, and an agent should not imitate that.

## 5. Numbers

Any figure that is part of the argument carries its unit. "$7m to $9m per rack", "2,000+
GPUs, ~1 MW live", "245 km, ~3h each way", "€825 per server".

Ranges in prose take "to". Ranges in a table or a label take an en dash.

Every number that could be challenged names its source, in the footer if not inline.

**Bold figures in a document. Do not bold them in a message.** In his own Slack and email
figures appear plain, and where he does bold it is a label rather than a number.

## 6. Structure

**Bullets for facts, prose for judgement.** Every list in his corpus is a list of facts
with no argument in it: serial prefixes, travel legs, call attendees, contract terms. Where
he is making a judgement it is in running prose, after the list.

Headers are the question the reader would ask, not a category label. "What we have already
built", not "Track record". "What could go wrong, and what protects you", not "Risk
factors". A header may be a full sentence and often reads better with a comma in it.

Bold is the skim path. Around one bold span per 26 words in a document, and between one
per 20 and one per 40. Bold a figure once, where it does its work. Never bold a
transition, a filler phrase or a section label.

At most one three-item parallel list per two hundred words of prose.

## 7. Banned

**No closing line.** No sentence that tells the reader what to conclude. "Speed is the
product." "This is not a plan on paper." "The giants leave this size alone." If you have
written one, delete it. A section that ends on its last fact ends fine.

**No "not just X, it's Y"** and no "not X, but Y". State Y.

**No participle tricolons.** "Funded, contracted and ordered." Pick the one that matters
and say why.

**No filler transitions**, especially bolded. "That is where we come in." "It is worth
noting." "Importantly." "Simply put." "Let's unpack."

**No vague quantifier doing a number's job.** "A significant total of compute",
"substantial demand", "strong pipeline". Give the figure or cut the sentence.

**No authority claim without a name, a number or a link.** No "industry reports show", no
"studies suggest", no "observers argue".

**No imperative at the reader.** Offer instead, and vary the offer between documents.

**No formal transition opening more than one paragraph in three.** Additionally, Moreover,
Furthermore, In conclusion.

Standard slop, banned on sight: leverage, robust, seamless, cutting-edge, delve, landscape,
paradigm, ecosystem, unlock, harness, streamline, elevate, empower, underscore, pivotal,
unprecedented, game-changer, revolutionary, poised to, best-in-class, world-class, "in
today's rapidly evolving", "at the end of the day". Review this list every six months. The
words that mark machine-written English change, and a stale list catches nothing.

## 8. What not to imitate

His own typing carries habits that are his and would read as sloppy or as forgery coming
from an agent. Do not reproduce: missing apostrophes in "dont" and "thats", trailing double
dots, doubled exclamation marks, abbreviations like "alr", "atm" and "wdy", or emoji.

Do reproduce the non-native constructions that recur often enough to be voice rather than
accident, when writing something he will send as himself: "worth to do another call",
"looking forward to talk", "focus on operating cost effective".

When in doubt about which side of that line something falls on, leave it out and let him
put it back.

## 9. Before handing it over

1. Read only the bold. Does the argument stand, and is any figure bolded twice?
2. Find every sentence that states a fact and stops. Add the consequence, or cut it.
3. Find every sentence that tells the reader what to conclude. Cut it.
4. Find every explanatory gloss on a strong fact. Name the thing and stop.
5. Find every header that is a noun label. Rewrite it as the reader's question.
6. Count em dashes in body prose. Target zero.
7. Find the longest sentence. Over 40 words, split it.
8. Find every adjective. Replace it with a number or delete it.
9. Apply the deletion test. If a third of the sentences can go without losing
   information, rewrite rather than trim.
