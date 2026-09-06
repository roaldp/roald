# What the work on this machine actually is

Measured 2026-09-06 from 1,741 unique prompts Roald typed, filtered to remove pasted agent
output. This exists because the first version of the scoping screen asked generic
product-management questions that fit almost none of this.

## Most of what he types is not a job

| Prompt length | Share |
|---|---|
| Median | 21 words |
| 40 words or more | 22.8% |
| 60 words or more | 11.1% |
| 100 words or more | 1.2% |

Longest prompt in the corpus is 111 words. An explicit second goal, "and also" or "then
also", appears in 1.8 per cent.

**So a scoping screen that fires on every request would fire wrongly about nine times out
of ten.** Most turns are not projects. They are moves inside a piece of business already in
flight: "ask for Yonten's confirmation of this timeline", "planning on sending this to
Yonten, add that the overview is attached", "let me know whether I can already review the
short version".

The screen needs an exit at the top for those, or it becomes the thing it was built to
prevent.

## The job families

First match wins, so a prompt is counted once.

| Family | Share | What it looks like |
|---|---|---|
| Legal and contract | 12.2% | "draft such deed that would survive an insolvency", "Rep 6.1(m) dangling Schedule 1 reference", "what is the contract coverage" |
| Build and code | 9.0% | the portal, the websites, the game, the pulse companion |
| State lookup | 8.4% | "check the latest local version regarding the hardware procurement timeline", "any open pending items on the security side" |
| Numbers and model | 7.2% | "what is the MOIC on a 30% IRR over five years", "are these IRR numbers including the 5% operator fee" |
| Correcting a draft | 5.9% | "bro this is unclear, tell me the full section to edit", "very long answer, could be more factually focussed" |
| Record keeping | 5.3% | CRM entries, serial registers, dataroom backfill, call notes |
| Outbound copy | 3.3% | emails, WhatsApp rundowns, one-pagers, investor updates |
| Research and decision | 3.3% | "should we", "is it worth", "compare these" |
| Ops and monitoring | 1.3% | weekly node checks, coverage, rewards |
| Unclassified | 44.1% | short conversational turns inside work in flight |

Two things this says that the earlier design got wrong.

**This is a fund and infrastructure operator's inbox, not a product backlog.** The single
largest named family is legal and contract work. Software is 9 per cent. A screen built
around "what number moves" fits the 9 per cent and misfits the rest.

**Almost everything has a decision or an obligation behind it**, usually with a
counterparty and a date. Can we sign. What do we quote. Is the wire due. Can I send this.
Is this figure the one to put in front of an investor. That is the axis the screen should
turn on, not a metric.

## The risk that actually costs him

He acts on agent output where money and legal exposure sit behind it. The failures that
matter in this corpus are not "we built the wrong feature". They are:

- Working from a superseded document. The AIC repo keeps a "known stale files, do not trust
  these" section precisely because of this.
- Quoting a figure that has three versions in circulation. That repo names three different
  order totals still appearing in historical files, only one of which is current.
- Treating an unmerged record as real. Its own hygiene note records that roughly four in
  ten counterparty records never reach `main`, and the CRM only counts what is committed.
- Sending a claim the company cannot stand behind. That is what `CLAIMS.md` exists for.

So the second screen question should not be "what number says it worked". It should be
"what has to be true for this to be safe to act on".

## What the screen became

Three questions, tailored:

1. **What decision or obligation is waiting on this, whose, and by when?** Fits every
   family. Nothing waiting means it is a nice-to-have.
2. **What has to be true for the answer to be safe to act on?** Family-specific, listed in
   the skill.
3. **What is the smallest thing that gets that decision made?**

Plus an exit above them: if this is a turn inside work already in flight, and most turns
are, do it and skip the screen.
