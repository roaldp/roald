# Research: agent writing style, status updates, and briefing intake

Compiled 2026-09-06 for the agent operating framework. Two problems in scope:

1. Agent-written external content (emails, docs, Slack) reads as machine-written and is slow to read.
2. Agent status updates to the supervisor are too long; target is an under-one-minute read with
   detail available on demand.

All source ratings and cross-verification notes are in the tables. Where a recommendation rests on
one source only, it is marked SINGLE-SOURCED.

---

## Sources

| Title | Author / org | Date | Rating | Reason |
|---|---|---|---|---|
| [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) | English Wikipedia editors | live page, read 2026-09-06 | STRONG | Continuously maintained catalogue built by editors who audit thousands of suspected AI edits; itemises collocations, not vibes; explicitly warns detectors have non-trivial error rates. |
| [How to spot AI writing (Off the Charts)](https://theeconomistoffthecharts.substack.com/p/how-to-spot-ai-writing) | The Economist data team | Jul–Aug 2026 | STRONG | Original corpus study: 55,940 sentences / 1.2M words, own articles vs four frontier models, plus NYT/WaPo and novels 1950–2022. Paywalled — figures below come from secondary reports. |
| [Forget em dashes: viral report on AI writing has surprising new clues](https://www.fastcompany.com/91584243/how-to-identify-ai-generated-writing-viral-report-has-surprising-new-clues-economist) | Fast Company | Aug 2026 | MODERATE | Reputable secondary reporting on the Economist study; returned HTTP 403 to direct fetch, so its figures reach us third-hand via search summaries. |
| [Em dash: AI writing's biggest giveaway has changed](https://dataconomy.com/2026/08/04/how-to-spot-ai-writing/) | Dataconomy | 2026-08-04 | MODERATE | Independent second report of the same Economist figures; also 403 on direct fetch. Used only to corroborate Fast Company. |
| [Signs of AI Writing: 12 Patterns With Reproducible Thresholds](https://slopdetector.org/blog/signs-of-ai-writing) | SlopDetector | 2026-07-31 | MODERATE | Only source found that gives numeric, testable thresholds, and it names its baselines (700k words human prose; 14.2M PubMed abstracts). But it is a vendor blog selling a detector, so thresholds are self-serving and unreviewed. |
| [Delving into LLM-assisted writing in biomedical publications through excess vocabulary](https://arxiv.org/abs/2406.07016) | Kobak, Márquez, Horvát, Lause | 2024 (OLDER) | STRONG (older) | Large-scale corpus method: 15M+ PubMed abstracts 2010–2024, excess-frequency methodology, finds ≥13.5% of 2024 abstracts LLM-processed (up to 40% in some subcorpora). Word lists are now dated. |
| [Testing of detection tools for AI-generated text](https://arxiv.org/pdf/2306.15666) | Weber-Wulff et al. | 2023 (OLDER) | STRONG (older) | Systematic detector evaluation; all tools below 80% accuracy. Foundational for the "do not trust detectors" position. |
| [Evaluating the accuracy and reliability of AI content detectors in academic contexts](https://link.springer.com/article/10.1007/s40979-026-00213-1) | Int. Journal for Educational Integrity | 2026 | STRONG | Peer-reviewed 2026 replication: leading tools at 69% and 61% accuracy, near-0% on hybrid human+AI text. |
| [Prompt engineering best practices](https://claude.com/blog/best-practices-for-prompt-engineering) | Anthropic | 2025-11-10 (OLDER) | STRONG | First-party Claude guidance; states positive framing beats negative constraints and gives a worked example. |
| [claude-code issue #26390: terminal markdown renderer](https://github.com/anthropics/claude-code/issues/26390) | community bug report on Anthropic repo | 2026-02-17 | STRONG | Feature-by-feature observed test of the shipped terminal renderer. Single reporter, so treat exact coverage as one measurement. |
| [claude-code issue #58983: tables in VS Code terminal mode](https://github.com/anthropics/claude-code/issues/58983) | community bug report | 2026 | MODERATE | Corroborates that rendering differs per surface (terminal mode vs native UI mode). |
| [Formatting message text](https://docs.slack.dev/messaging/formatting-message-text/) | Slack | current | STRONG | First-party platform docs; enumerates mrkdwn and confirms it is not markdown and has no HTML layer. |
| [Organizing information with collapsed sections](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/organizing-information-with-collapsed-sections) | GitHub | current | STRONG | First-party docs confirming `<details>`/`<summary>` support and the blank-line caveat. |
| [Ask or Assume? Uncertainty-Aware Clarification-Seeking in Coding Agents](https://arxiv.org/abs/2603.26233) | arXiv 2603.26233 | 2026-03-27 | STRONG | Controlled experiment on an underspecified SWE-bench Verified variant with resolve-rate numbers and query counts. Preprint, not yet peer reviewed. |
| [ReqElicitGym: Evaluation Environment for Interview Competence in Conversational Requirements Elicitation](https://arxiv.org/html/2602.18306) | arXiv 2602.18306 | 2026-02-20 | STRONG | Purpose-built benchmark for LLMs conducting elicitation interviews; reports turn counts and elicitation rates by requirement type. Preprint. |
| [Building LLM-Based Voice Agents for Requirements Elicitation](https://dl.acm.org/doi/10.1145/3786167.3788420) | Int. Workshop on Agentic Engineering (ACM) | 2026 | MODERATE | Peer-reviewed venue but an "experience report on early prototypes" with a small participant study (4–6 min rounds). |
| [From Prompt to Process: a Process Taxonomy and Comparative Assessment of Frameworks Supporting AI Software Development Agents](https://arxiv.org/pdf/2606.04967) | S. O. de Macedo, arXiv 2606.04967 | 2026-06-04 | MODERATE | Systematic comparison of eight agent frameworks (BMAD, SpecKit, OpenSpec, Spec-Flow, GSD, Spec-Kitty, ChatDev, SWE-Agent). Single-author preprint; findings are qualitative. |
| [Spec Kit Agents: Context-Grounded Agentic Workflows](https://arxiv.org/html/2604.05278v1) | arXiv 2604.05278 | 2026-04 | MODERATE | Describes the specify → plan → tasks → implement staging and its artefacts. Preprint. |
| [Persona drift in long-running agent sessions](https://tianpan.co/blog/2026-05-02-persona-drift-long-horizon-agent-sessions) | Tian Pan | 2026-05-02 | WEAK–MODERATE | Practitioner blog. Cites a >30% self-consistency degradation after 8–12 turns but the underlying measurement is not independently traceable from the post. Treat the number as indicative only. |
| [The Mom Test](https://mtlynch.io/book-reports/the-mom-test/) (book by Rob Fitzpatrick, 2013) | summarised by Michael Lynch | book 2013 (OLDER) | STRONG (older) | Foundational interview discipline; the three rules and the commitment test are stable and widely replicated in practice. |
| [US Army Regulation 25-50, Preparing and Managing Correspondence](https://armypubs.army.mil/epubs/DR_pubs/DR_a/ARN42124-AR_25-50-007-WEB-13.pdf) | US Army | current revision (doctrine dates to 1980s) | STRONG (older) | Primary doctrine for BLUF; gives hard numbers (≈15-word average sentence, paragraphs ≤10 lines, understood in a single rapid reading). |
| [Progressive Disclosure](https://www.nngroup.com/videos/progressive-disclosure/) | Nielsen Norman Group | pattern from 1995 (OLDER) | STRONG (older) | Foundational UX pattern and, importantly, its failure condition: if the first layer omits what users frequently need, you relocate complexity rather than reduce it. |
| Assorted SEO listicles on "AI slop", "BLUF for SEO", "acceptance criteria 2026" | various | 2026 | WEAK | High volume, no original data, mutually plagiarising. Used only to confirm that a claim is widely repeated, never as evidence. |

---

## Q1. What specifically makes text read as AI-written in 2026

### The headline change since 2025: the em dash is no longer the tell, but it still is for Claude

The Economist compared 55,940 sentences and 1.2M words of its own journalism against versions of
the same articles written by ChatGPT, Claude, Gemini and Grok, plus NYT/WaPo copy and novel
excerpts from 1950–2022. Its finding on the most famous marker: em dashes no longer separate AI
from human writing in general. ChatGPT now uses em dashes *less* often than any other model tested
and less often than human writers. Of the four models, **only Claude uses em dashes more often
than humans do**. (Economist, via Fast Company and Dataconomy — two independent secondary reports
of the same study; the primary is paywalled, so the direction of the finding is cross-verified but
the exact per-model rates are not.)

Practical consequence for this project: the generic 2025 advice "ban em dashes" is obsolete for AI
writing generally, and simultaneously it is the single most defensible ban *for a Claude-based
system specifically*. Both things are true at once.

SlopDetector gives the one numeric threshold available: an em-dash density above **20 per 1,000
words** in short modern prose, against a human baseline of **3.23 per 1,000** measured over 700,000+
words of published human prose. SINGLE-SOURCED and vendor-produced; use as a rough tripwire, not a
finding.

### Structural markers, with thresholds where they exist

| Marker | Description | Threshold offered | Sources |
|---|---|---|---|
| Low burstiness | Uniform sentence length; no long/short alternation | sentence-length std-dev ÷ mean below **0.4**; humans typically 0.6–1.2, AI 0.2–0.4 | SlopDetector (numbers, SINGLE-SOURCED); Economist and Wikipedia both independently report uniform sentence length / lack of human cadence |
| Rule of three | Everything arrives as triplets: "efficient, scalable, and reliable" | more than one polished triplet per 200 words | SlopDetector; Wikipedia; Economist coverage |
| Negative parallelism / antithesis | "not just X, but Y", "it's not X, it's Y" | same contrast frame 3+ times in one piece | Wikipedia (names it "negative parallelisms"); SlopDetector |
| Transition stacking | Formal connectives at fixed intervals ("Additionally", "Moreover", "Furthermore") | more than half of paragraphs opening with a formal transition | Wikipedia ("uniform, formulaic transitions at fixed intervals are atypical of expert human style"); SlopDetector |
| Copula avoidance | "is/are" replaced by "serves as a", "stands as", "marks the" | one study measured a **>10% drop in "is"/"are"** frequency in 2023 text | Wikipedia citing corpus work; independently noted in the researchleap linguistic-markers piece |
| Section-header reflex | Headers of the form "X and Y": "Challenges and Future Directions", "Awards and recognition" | none | Wikipedia (itemised list of header patterns) |
| Closing-summary reflex | Outline-like conclusions about "challenges and future prospects", "broader significance" | none | Wikipedia |
| Hedging density | "may potentially", "could arguably help" | none numeric; AI essays show measurably higher hedging-marker counts than human essays in corpus comparison | researchleap corpus comparison; Wikipedia |
| Fake authority | "industry reports show", "observers argue", "some critics" with no name, number or link | >50% of authority claims uncited | Wikipedia (vague sourcing); SlopDetector |
| Under-punctuation | LLMs skimp on commas, semicolons and parentheses and produce long undifferentiated sentences; "and" is the most overused word | none | Economist via both secondary reports |
| Deletion test | Sentences that can be removed with no information loss | more than one third of sentences survivable = fail | SlopDetector, SINGLE-SOURCED but operationally the most useful test in the list |

### Lexical markers

Wikipedia's list is the best-maintained and is versioned by era, which matters because the
vocabulary drifts as models change:

- 2023 – mid-2024: *additionally, boasts, bolstered, crucial, delve, emphasizing, enduring, garner,
  intricate, interplay, landscape, pivotal, underscore, tapestry, testament*
- mid-2024 – mid-2025: *align with, enhance, fostering, highlighting, showcasing*
- mid-2025 onward: *emphasizing, enhance, highlighting, showcasing*

Recurring collocations: "stands/serves as a", "is a testament to", "plays a crucial/pivotal/vital
role", "reflects broader trends", promotional adjectives ("vibrant", "nestled", "rich heritage").

Corpus backing: Kobak et al. tracked 15M+ PubMed abstracts 2010–2024 and found LLM style words
produced an abrupt frequency break, letting them infer that at least 13.5% of 2024 abstracts were
LLM-processed, up to 40% in some subcorpora — an effect larger than that of the Covid pandemic on
scientific vocabulary. SlopDetector reports "delves" at 25× its pre-ChatGPT frequency in the same
PubMed data.

Model-specific note: Grok over-uses superficially scientific words (*causal, empirical, correlate*)
and still over-uses *underscore* as of 2026 (Wikipedia, SINGLE-SOURCED).

### The convergence principle — the most important finding for a style rule set

Every serious source lands on the same point: no single marker convicts. SlopDetector: "three or
four signs failing at once in the same short passage is the fingerprint." Wikipedia: "reliable
manual detection requires cluster analysis across multiple signs." A 2026 defence piece
(robotsatemyhomework) argues, correctly, that em dashes, "not X but Y" and the rule of three are
all legitimate techniques a good human writer uses; what marks AI is their *stacking* at uniform
density.

This argues against a flat banned-list style guide and in favour of density budgets plus a
whole-draft check.

### Detectors, and the contradiction we have to hold

Detectors are unfit for our purpose:

- All tools tested scored under 80% accuracy (Weber-Wulff et al., 2023, OLDER).
- 2026 replication: leading tools at 69% and 61% overall, dropping to near 0% on hybrid human+AI
  text — which is exactly what our output will be.
- Detectors misclassify non-native English writing as AI, and are 28–38 percentage points less
  accurate on scientific text than on humanities text.

**Recorded disagreement.** Multiple studies find humans cannot distinguish AI from human text above
chance, and Wikipedia's own page cites this. Yet the user's stated problem is that agent output is
*instantly* identifiable. Both can be true: the detection studies use short, decontextualised,
single-paragraph samples from readers with no baseline for the author. The user is reading longer
pieces, in a channel where he knows what his own writing looks like, and where he already suspects
an agent wrote it. Prior + baseline + length is what makes it obvious. This means our target should
be **the user's perception on his own channels**, not any detector score and not a general-population
study. We should not adopt any metric that optimises for fooling a detector.

---

## Q2. What actually works to fix it in a system prompt or style guide

### Positive exemplars beat negative constraints — first-party evidence

Anthropic's own prompt-engineering guidance (2025-11-10, OLDER but first-party and current for
Claude 4.x/5) states the rule plainly: tell the model what to do instead of what not to do. Its
worked example is directly on point for our problem:

- Less effective: "Do not use markdown in your response"
- Better: "Your response should be composed of smoothly flowing prose paragraphs"

The same document is explicit that examples are the tool for tone and format: examples "shine when
explaining concepts or demonstrating specific formats", and that Claude 4.x-class models "pay very
close attention to details in examples" — so an exemplar must contain no pattern you do not want
copied. It also notes that the formatting style *of the prompt itself* influences the response
style, which means a style guide written in bulleted AI-slop prose will teach the agent to write
bulleted AI-slop prose.

Cross-verification: multiple 2026 practitioner guides repeat the combined recipe — 2–3 few-shot
samples of the target style, plus a short list of banned patterns as guardrails, plus an explicit
output schema. Those secondary guides are WEAK individually (SEO content farms), but they are
consistent with the first-party guidance rather than contradicting it, so the combined
recommendation is: **exemplars as the primary mechanism, a short negative list as a backstop for
the few failure modes that are predictable and mechanical (em dash, "not just X but Y").**

Nothing found gives a controlled A/B result on style transfer via few-shot vs instruction *for
Claude specifically*. That evaluation does not appear to exist publicly. Mark as UNPROVEN and
consider running it ourselves.

### Style guides degrade over long contexts

Persona drift — the progressive divergence of behaviour from the original system instruction — is
attributed to the U-shaped attention distribution over token position ("lost in the middle"): the
model attends most strongly to the start and end of context, and a style guide buried in the middle
of a long session loses force. The practitioner source reports self-consistency degrading by over
30% after 8–12 dialogue turns; that specific number is SINGLE-SOURCED and not independently
traceable, so treat it as directional. The general phenomenon is corroborated by Chroma's "context
rot" work, which finds degradation as input token count grows across every major model regardless of
window size.

Design implication, cross-verified in direction if not in magnitude: a style guide that is stated
once at session start will not hold for a long agent run. It has to be re-injected at the point of
writing — as a skill, a pre-write hook, or a dedicated writing subagent that receives the exemplars
in a fresh short context — rather than parked in CLAUDE.md and hoped for.

---

## Q3. Status update format for a human supervising parallel agent streams

### Verified surface support for collapsible sections

The user asked directly whether dropdowns are possible. Answer per surface:

| Surface | Does `<details>`/`<summary>` collapse render? | Evidence | Confidence |
|---|---|---|---|
| GitHub (issues, PRs, comments, READMEs) | **Yes.** Supports nested markdown, headers, images, code blocks inside; `<details open>` starts expanded; needs a blank line after `</summary>` before markdown content. | [GitHub docs](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/organizing-information-with-collapsed-sections) | High — first-party docs |
| Slack message | **No.** mrkdwn is not markdown and has no HTML layer. Supported: bold, italic, strike, inline code, code blocks, blockquote, links, mentions, date formatting. Not supported: headers, tables, HTML, collapsible sections. | [Slack docs](https://docs.slack.dev/messaging/formatting-message-text/) | High — first-party docs |
| Claude Code terminal | **No.** The renderer implements a subset of GFM. Supported: bold, italic, bold-italic, code spans, fenced code blocks with syntax highlighting, diff blocks, tables, bulleted/numbered lists, single-level blockquotes. Silently broken: h2–h6 (all render as identical bold, hierarchy lost), link labels (label discarded, raw URL shown), strikethrough (literal `~~`), task lists (checkbox state lost), nested blockquotes, HTML entities (rendered verbatim). No HTML tag support is documented or observed. | [claude-code #26390](https://github.com/anthropics/claude-code/issues/26390), 2026-02-17 | Medium-high for the feature list (SINGLE-SOURCED, one tester); `<details>` specifically was not tested, so its non-support is **inferred** from the absence of any HTML handling and the verbatim treatment of HTML entities |
| Claude Code in VS Code, terminal mode | Tables flatten to `header: value` lines; renders correctly only in native UI mode. | [claude-code #58983](https://github.com/anthropics/claude-code/issues/58983) | Medium — one report, but it establishes that rendering varies by surface within one product |
| Claude Desktop / claude.ai chat message body | **Not verified.** Chat renders markdown. No source found confirming or denying HTML element rendering in the message stream. | — | Low — treat as unsupported until tested |
| Claude Artifacts (desktop and web) | **Yes, in principle.** Artifacts accept `.html`/`.htm`/`.md` and render live HTML/CSS/JS in a side panel, so `<details>` would behave as a real disclosure widget. | Anthropic artifact format docs via secondary coverage | Low-medium — the artifact HTML capability is well attested; the specific `<details>` case is inferred, not tested |

**Net answer: dropdowns are available on exactly one of the surfaces we care about (GitHub), and
possibly inside a Claude artifact. They are not available in the Claude Code terminal or in Slack.**
Progressive disclosure therefore has to be implemented by *layering across artefacts*, not by a
widget.

Available substitutes for a collapse, per surface:

- **Slack:** post the summary as the parent message and the detail as a thread reply. This is the
  native progressive-disclosure mechanism. Secondary options: a code block (visually compact and
  scroll-contained), a canvas, or a link to a file. Note Slack also auto-collapses long messages
  behind "Show more" after a few thousand characters, but this is uncontrolled truncation that
  breaks formatting — do not rely on it as a feature. Slack's own guidance budget is 4,000
  characters per message; the hard limit is 40,000.
- **Claude Code terminal:** short summary in the response, detail written to a file, path given.
  Because h2–h6 all render identically and link labels are discarded, use at most one heading level
  and print bare URLs/paths rather than `[label](url)`.

### What the summary layer should contain

BLUF is the well-documented convention and comes with hard numbers from AR 25-50: main point first,
active voice, average sentence around 15 words, paragraphs no longer than 10 lines and each about a
single idea, and the standard that the reader understands it in a single rapid reading. That
standard is the closest doctrinal match to the user's "under one minute" requirement. (OLDER but
stable; the 2026 BLUF material found online is SEO-grade restatement and adds nothing — the
"50 words / 18 words per sentence / evidence at 51–150 words" layering scheme is WEAK-sourced and
should be treated as one plausible instantiation, not evidence.)

Nielsen's progressive disclosure supplies the constraint that matters most and is the one most
often violated: **the first layer must contain everything the reader frequently needs.** If it does
not, you have relocated complexity rather than reduced it, and the supervisor now pays a click plus
a re-read. For parallel agent supervision this means the summary must carry the decision and the
blocker, not just a topic label.

SBAR (Situation, Background, Assessment, Recommendation) was searched for but no 2026 material tying
it to agent status updates was found. It remains a defensible ordering from clinical handover
practice, but for this use case it is dominated by BLUF: SBAR puts the recommendation last, BLUF
puts it first, and the user's constraint is a one-minute read.

---

## Q4. Requirements elicitation from a non-specific brief

### Agents are measurably bad at knowing when to ask, and this is fixable by architecture

**Ask or Assume? (arXiv 2603.26233, 2026-03-27)** built an underspecified variant of SWE-bench
Verified (500 GitHub issues with details deliberately removed) and tested clarification-seeking
scaffolds. Results:

| Configuration | Resolve rate |
|---|---|
| Full spec baseline (nothing removed) | 70.80% |
| Interactive baseline | 70.40% |
| **Uncertainty-aware multi-agent (UA-Multi)** | **69.40%** |
| Uncertainty-aware single agent (UA-Single) | 61.20% |
| Hidden baseline (underspecified, no asking) | 54.80% |

The design that produced this: a separate **Intent Agent** watches the conversation while the Main
Agent does the work, and at each turn asks three questions of the state — *what is the intended
goal; what is missing, ambiguous or assumption-heavy; what must be clarified before proceeding.*
Decoupling detection from execution is what moved the number: the same uncertainty awareness inside
a single agent scored 8.2 points lower.

Two findings bear directly on "how many questions before it becomes annoying":

- UA-Multi asked **3.06 questions per task it chose to query**, vs 1.84 for the single-agent version
  — and the multi-agent version scored higher. More questions, better outcome, on tasks it decided
  were worth asking about.
- It **skipped asking entirely on 31.2% of tasks** and still hit a 76.92% resolve rate on those,
  matching the no-information baseline's 77.56% on the same subset. That is the calibration signal:
  a good asker recognises when it can resolve the ambiguity itself.
- Timing: questions were spread across early (41.8%) and mid (43.4%) trajectory, not front-loaded.
  Some ambiguity is only visible after you have read the code.
- Cost: $3.50/task vs $1.63 for the fully-specified baseline. The scaffold is roughly 2× the token
  cost.

Design implication, SINGLE-SOURCED but with a clean experimental design: run intake as a **separate
intent-checking pass**, not as instructions bolted onto the working agent; budget around **3
questions per genuinely ambiguous area**; and require the agent to first attempt resolution from the
repository, because roughly a third of apparent ambiguity is self-resolvable.

### Agents ask the wrong kind of question, and cannot elicit style preferences at all

**ReqElicitGym (arXiv 2602.18306, 2026-02-20)** benchmarks LLMs conducting elicitation interviews:

- All models tested "strongly favour probing over clarification", and clarification is consistently
  the *less* effective of the two — LLMs "struggle to ask precise clarification questions."
- Best model achieved an elicitation rate of **0.32**: about 68% of implicit requirements were never
  surfaced.
- Interview length without chain-of-thought varied wildly, **3.86 to 19.98 turns**. Chain-of-thought
  prompting cut turn counts substantially while improving question quality — i.e. making the agent
  reason before asking makes it ask less and better.
- Performance by requirement type: worst on **style-related requirements, with elicitation rates
  near zero** for aesthetic preferences. Interaction and content requirements fared modestly better.

That last finding is the single most consequential result in this document for the project as a
whole. **An agent will not successfully interview the user about how he wants things to look or
sound.** Style must be supplied as exemplars and captured from artefacts he has already approved;
it must not be gathered by asking him questions about it.

The ACM workshop experience report on voice agents for elicitation (2026) is consistent — agents
that offered clarifying questions, summarised key points, and suggested additions performed better —
but the study is small (4–6 minute rounds per participant) and is MODERATE evidence at best.

### Converting a rambling spoken brief into criteria

Foundational, all OLDER, all stable, none contradicted by 2026 material:

- **The Mom Test** (Fitzpatrick, 2013): talk about their life not your idea; ask about specifics in
  the past, not hypotheticals about the future; listen more than you talk. Compliments and opinions
  are noise; the signal is commitment. Applied to a work brief, the transferable move is to convert
  "I want it to feel snappy" into "show me the last time this annoyed you and what you did about
  it" — past specifics rather than stated preferences. This directly compensates for the
  ReqElicitGym finding that stated style preferences cannot be elicited.
- **Given/When/Then**: given an initial context, when an action occurs, then this outcome. The
  format's value is that it forces an observable trigger and an observable result.
- **INVEST** (Independent, Negotiable, Valuable, Estimable, Small, Testable) and **SMART** as
  filters on each derived item.
- **EARS** (Easy Approach to Requirements Syntax) appears in AWS Kiro's `requirements.md` as the
  acceptance-criteria format of choice in 2026 agent tooling — worth noting as the format the
  tooling ecosystem converged on.

No 2026 source was found that measures any of these formats against each other for agent
consumption. Their use here is convention, not evidence.

---

## Q5. Discovery → ideation → design requirements → MVP staging

The 2026 convergence is **spec-driven development (SDD)**, and by 2026 every major agent tool ships
a flavour of it: GitHub Spec Kit, AWS Kiro, Claude Code, Cursor, OpenSpec, BMAD, Tessl, Google
Antigravity.

Stage/artefact mapping, cross-verified across the Spec Kit Agents paper, the process-taxonomy
preprint, and the tooling docs described therein:

| Stage | Artefact | Contains |
|---|---|---|
| Specify | `spec.md` / `requirements.md` | business context, success criteria, acceptance criteria (EARS in Kiro) |
| Plan / design | `plan.md` / `design.md` | architectural decisions, chosen approach, rejected alternatives |
| Decompose | `tasks.md` | testable units, checklist form |
| Implement | code + tests | traced back to spec items |
| Standing context | `CLAUDE.md` / `AGENTS.md` | the persistent project voice that rides along in every session |

The core claim, stated most clearly in the Spec Kit Agents paper: SDD's value is **externalising the
intermediate artefacts** so intent is explicit and there is a structured audit trail — not the
specific file names.

The comparative assessment of eight frameworks (BMAD, SpecKit, OpenSpec, Spec-Flow, GSD, Spec-Kitty,
ChatDev, SWE-Agent) reports that maturity varies widely and identifies consistent gaps: no unified
process model, weak bidirectional traceability from spec to code, limited standardisation in how
agents document their reasoning, and underdeveloped validation of agent output against the spec.
Single-author preprint with qualitative findings — MODERATE.

Notably absent from all of this: a **discovery or ideation stage**. Every framework found starts at
"specify", i.e. it assumes a decided intent. The gap the user is describing — a rambling voice brief
that precedes any spec — is upstream of where the 2026 SDD ecosystem begins. No credible source was
found covering a discovery-to-spec agent stage. This is a genuine unmet need, not something to
adopt from elsewhere.

---

## Concrete rules we could adopt

Numbered, testable. Confidence reflects source strength and cross-verification.

**Style rules for external content**

1. **No em dashes in agent-written external content; use a comma, a colon, a full stop, or restructure.** Confidence: HIGH for a Claude-based system, and only for a Claude-based system. Claude is the one model among four tested that still exceeds the human em-dash rate, even though the marker has stopped working for AI writing generally. Sources: Economist study via two independent secondary reports; SlopDetector threshold (20/1,000 words vs 3.23 human baseline).
2. **Ban the "not just X, it's Y" / "not X, but Y" antithesis outright in short-form writing.** Replacement: state Y directly. Confidence: HIGH. Sources: Wikipedia (names it), SlopDetector (threshold), Economist coverage.
3. **At most one three-item parallel list per 200 words of prose; the second one must be broken to two or four items.** Confidence: MEDIUM — the pattern is triple-sourced, the numeric threshold is single-sourced and vendor-produced.
4. **Vary sentence length deliberately: every paragraph must contain at least one sentence under 8 words and one over 20.** This is the positive-framing version of the burstiness rule (target std-dev/mean above 0.6). Confidence: MEDIUM — burstiness is consistently reported, but the 0.4/0.6 cut-points are single-sourced.
5. **Use commas, semicolons and parentheses; do not run two ideas into one long unpunctuated sentence joined by "and".** Confidence: MEDIUM-HIGH. Sources: Economist study (under-punctuation and "and" over-use are its named replacement markers for the em dash), cross-reported by two outlets.
6. **Banned vocabulary in external content, with replacements:** delve→look at; leverage→use; utilize→use; underscore/highlight/showcase→show; foster→build; pivotal/crucial→important, or delete; landscape/realm/tapestry→delete; robust→specific property; a testament to→delete; serves as / stands as→is; plays a crucial role in→delete and state the effect. Confidence: HIGH for the pattern, MEDIUM for any individual word, because these lists drift every 6–12 months. The rule should carry a review date. Sources: Wikipedia (era-versioned list), Kobak et al. (corpus method), SlopDetector.
7. **No formal transition word at the start of more than one paragraph in three** (Additionally, Moreover, Furthermore, In conclusion). Confidence: MEDIUM-HIGH; the pattern is cross-verified, the exact ratio is single-sourced.
8. **Every authority claim carries a name, number, link, or is deleted.** No "industry reports show", "observers argue", "studies suggest". Confidence: HIGH; cross-verified in Wikipedia and SlopDetector, and it is a substance rule, not just a style rule.
9. **Deletion test before sending: if more than a third of sentences can be cut without losing information, rewrite.** Confidence: MEDIUM (single-sourced threshold) but HIGH value — this is the only rule in the list that attacks the "inefficient to read" half of the user's complaint rather than the "sounds like AI" half.
10. **No closing summary paragraph in short-form external writing; no "challenges and future directions" section; no header of the form "X and Y".** Confidence: MEDIUM-HIGH. Source: Wikipedia's itemised structural list; corroborated by the Economist's uniformity findings only in spirit.
11. **Prose stays prose. Bullets only for genuinely enumerable, parallel, unordered items.** Confidence: MEDIUM-HIGH; supported by Anthropic's own worked example of positive framing ("smoothly flowing prose paragraphs"), and by the general uniformity findings. Note this contradicts nothing in the sources but is not directly measured anywhere.
12. **No sycophantic opener** ("Great question", "You're absolutely right", "Happy to help"). Confidence: MEDIUM — widely repeated in 2026 practitioner material, no corpus study found that quantifies it. Treat as user preference backed by weak evidence.

**Mechanism rules — how to enforce the above**

13. **Carry 2–3 exemplars of the user's own approved writing per genre (email, Slack, doc, PR description) and put them in the prompt at the point of writing.** Exemplars are the primary mechanism; rules 1–12 are the backstop. Confidence: HIGH. Source: Anthropic first-party guidance that examples are the tool for tone and format and that Claude 4.x-class models attend closely to example details.
14. **Write every rule positively where a positive form exists.** "Do not use markdown" is Anthropic's own example of the weaker form; "compose smoothly flowing prose paragraphs" is the stronger. Confidence: HIGH, first-party.
15. **Scrub the exemplars and the style guide itself of every pattern in rules 1–12,** because the model copies example details and prompt formatting influences output formatting. Confidence: HIGH, first-party.
16. **Re-inject the style guide at write time, not once at session start.** Long sessions drift; attention is U-shaped over position. Implement as a writing skill or subagent with a fresh short context. Confidence: MEDIUM-HIGH for the direction, LOW for any specific turn count.
17. **Never use an AI detector score as an acceptance test.** Confidence: HIGH. Detectors run at 61–69% accuracy and near 0% on hybrid human+AI text, which is precisely what we produce. The acceptance test is the user's own read.

**Status update rules**

18. **BLUF, one screen, and the first layer must contain the decision and the blocker — not a topic label.** Concrete shape: one line of outcome, then what needs a decision, then what changed that would alter the plan, then where the detail lives. Confidence: HIGH; BLUF from AR 25-50 doctrine, and the "first layer must be sufficient" constraint from Nielsen's progressive disclosure, which names under-filled first layers as the pattern's main failure mode.
19. **Target AR 25-50's numbers: ~15-word average sentence, paragraphs under 10 lines, one idea per paragraph, understood in a single rapid reading.** Confidence: MEDIUM-HIGH — stable doctrine, though written for memoranda not agent updates.
20. **Detail goes in a file; the update carries the path.** Do not attempt collapsible sections in the Claude Code terminal or in Slack. Confidence: HIGH — see the surface table.
21. **In Slack, summary in the parent message, detail in the thread; keep the parent under 4,000 characters.** Confidence: HIGH; first-party Slack docs for both the formatting limits and the absence of HTML.
22. **In the Claude Code terminal, use at most one heading level and print bare paths/URLs rather than markdown links.** h2–h6 render identically so hierarchy is invisible, and link labels are discarded leaving broken grammar. Confidence: MEDIUM-HIGH — observed behaviour, single reporter.
23. **In GitHub PR descriptions, use `<details>` for logs, diffs, and test output,** with a blank line after `</summary>`. Confidence: HIGH, first-party docs.

**Intake rules**

24. **Run intake as a separate pass from execution.** A dedicated intent-checking step scored 69.40% vs 61.20% for the same uncertainty-awareness folded into the working agent, against a 54.80% no-asking floor. Confidence: MEDIUM-HIGH — one preprint, but a clean controlled comparison.
25. **The intent check asks three questions of the brief: what is the intended goal; what is missing, ambiguous or assumption-heavy; what must be clarified before proceeding.** Confidence: MEDIUM, single-sourced but it is the exact mechanism that produced the result in rule 24.
26. **Budget ~3 questions per genuinely ambiguous area, and require an attempt to resolve from the repo first.** The reference system asked 3.06 questions per queried task and chose not to ask at all on 31.2% of tasks without losing accuracy on those. Confidence: MEDIUM, single-sourced.
27. **Allow questions mid-task, not only up front.** In the reference system 43.4% of questions arose mid-trajectory, after the agent had read the code. Confidence: MEDIUM, single-sourced.
28. **Make the agent reason before it asks.** Chain-of-thought cut interview length substantially while improving question quality; without it, interview length varied from 3.86 to 19.98 turns. Confidence: MEDIUM, single-sourced.
29. **Do not interview the user about style or aesthetic preferences — collect exemplars instead.** LLM elicitation rates for style requirements are near zero. Confidence: MEDIUM-HIGH; single-sourced measurement, but it converges with the Mom Test's rule that stated preferences are noise and past specifics are signal.
30. **Convert every brief item into Given/When/Then with an observable trigger and observable outcome; filter with INVEST.** Confidence: LOW-MEDIUM as *evidence* — this is settled convention, not measured. Adopt for lack of a better-evidenced alternative.

---

## Explicitly rejected / unproven

- **"Ban em dashes because AI uses them" as a general claim.** Rejected. The Economist's 2026 corpus
  shows ChatGPT now uses fewer em dashes than humans. We keep the ban for a different, narrower
  reason: Claude specifically still exceeds the human rate.
- **Any detector-score acceptance gate.** Rejected on evidence: 61–69% accuracy, near 0% on hybrid
  text, biased against non-native English.
- **"Humans can't tell AI writing apart" as a reason to stop worrying.** Rejected as inapplicable —
  those studies test short decontextualised samples read by strangers, not longer pieces read by
  someone who knows the author's baseline and already suspects an agent wrote it.
- **Collapsible dropdowns as the status-update mechanism.** Rejected for Claude Code terminal and
  Slack: no HTML layer in either. Retained for GitHub only.
- **SBAR for agent status updates.** Not adopted: no 2026 evidence for this use, and it puts the
  recommendation last, which conflicts with the one-minute-read requirement.
- **Few-shot vs instruction for style transfer, measured on Claude.** UNPROVEN. Anthropic's
  first-party guidance says examples work for tone and that positive framing beats negative, but no
  public controlled comparison for style transfer specifically was found. Candidate for our own
  evaluation.
- **All numeric thresholds from SlopDetector** (em dashes/1,000 words, burstiness 0.4, one triplet
  per 200 words, transition ratio, deletion test at one third). SINGLE-SOURCED and vendor-produced.
  Usable as tripwires, not as evidence.
- **The "50 words / 18 words per sentence / evidence at 51–150 words" BLUF layering scheme.** Found
  only in SEO content. Not adopted as evidence; AR 25-50's numbers are used instead.
- **The ">30% persona self-consistency degradation after 8–12 turns" figure.** Direction is
  corroborated by context-rot work; the specific number is not independently traceable.
- **A discovery or ideation stage in any 2026 agent framework.** None found. Every SDD framework
  surveyed begins at "specify" and assumes intent is already decided.

## Open questions

1. Does Claude Desktop / claude.ai render HTML in the chat message body, or only inside artifacts?
   Not answered by any source. Needs a 2-minute manual test.
2. Does the Claude Code terminal renderer pass `<details>` through as literal text, strip it, or
   render its contents flat? Inferred non-support only; issue #26390 did not test HTML tags.
3. What is the user's actual em-dash and sentence-length profile in his own writing? Rules 1 and 4
   should be calibrated against his corpus, not against a published human baseline.
4. Does a few-shot exemplar set outperform an explicit rule list for Claude on this specific style
   transfer, and by how much? No public evidence. Cheap to test with the user's own emails as the
   target.
5. How many exemplars, and how stale can they be, before the effect degrades? Unaddressed anywhere.
6. What is the right re-injection point for the style guide in a long Conductor session — every
   write, every N turns, or on entry to a writing subagent?
7. Is there a measurable annoyance ceiling for intake questions with a human in the loop? The
   3.06-questions figure comes from an agent-agent simulation, not from human subjects.
8. Where does the discovery-to-spec stage's artefact live, and what is its format, given that no
   existing framework defines one?
