# Roald Parmentier — writing corpus

Assembled 2026-09-06. Purpose: give agents few-shot exemplars of Roald's actual writing instead of
rules about it. Everything below is verbatim. Typos, missing apostrophes, Dutch-English mixing and
inconsistent capitalisation are his and are left in on purpose.

## Sources used, and what was excluded

| Source | Status | Count kept |
|---|---|---|
| `docs/pitch-materials/style/MESSAGES.md` and `STYLE.md` (AIC repo) | Read | 9 labelled pairs |
| Slack, workspace `nodaoworkspace`, user `U0B9QJYNNGL` | Read via MCP, 4 pages of `from:` search | 42 messages |
| Gmail, `roald.parmentier@gmail.com` / `roald@allusion.be` | Read via MCP, `in:sent` | 14 emails |
| Claude Code session logs, `~/.claude/projects/**/*.jsonl` | Parsed locally | 3,384 typed prompts available; 75 quoted |
| Git commit messages across `~/conductor/repos/*` | Parsed locally | 12 that read as his |
| Fireflies-derived verbatim call transcript | Read from AIC repo | 1 long spoken sample |

**Excluded as not written by him**, though they appear under his name:

- The `NODAO invoice poll` and `Capex + Memory Scan` messages in Slack DM `D0B95GB7ZL7`. These are
  agent-generated reports posted through his account. They are the single largest block of text in
  his Slack history and would poison the corpus if treated as his voice.
- Most commit messages on `roaldp`-authored commits. The majority carry a `Co-Authored-By` trailer
  or the long bulleted agent shape. Only the short ones are kept.
- The right-hand side of the `STYLE.md` §1/§3/§9 pairs. Those are labelled "what shipped", not "what
  Roald wrote"; the shipped copy is a revised agent draft. They are kept in Section A but marked
  with lower confidence than the `MESSAGES.md` pairs, which are explicitly the version Roald sent.

---

# Section A — Labelled pairs

## A1. High confidence: the version Roald actually sent

Source: `~/conductor/workspaces/ai-infrastructure-capital/bozeman/docs/pitch-materials/style/MESSAGES.md`
§4. The file states the pairs come from one rundown drafted for Joseph Tan (RWA ODL) on 3 September
2026 and the version Roald actually sent. Left is the agent draft, right is what he sent.

**A1.1 — Describing off-takers**

> Agent: `Off-takers: US neoclouds, USD 1bn+ scale, who resell into the AI labs.`
>
> Roald: `Off-takers: Tier 1 and 2 (US) neoclouds`

**A1.2 — Pricing language**

> Agent: `Low USD 4 per GPU-hour, fixed for the term`
>
> Roald: `Around USD 4 per GPU-hour`

**A1.3 — The opener**

> Agent: `Hi Joseph — good speaking. Short rundown you can forward to Samson.`
>
> Roald: `Hi Joseph, was good meeting you. Here's a quick rundown:`

**A1.4 — The lead**

> Agent: `AI Infrastructure Capital — we finance, own and operate NVIDIA B300 GPU systems in the European Nordics (Iceland), 100% renewable, sub-1.2 PUE. We own the hardware outright; a contracted operator runs the site.`
>
> Roald: `About AI Infrastructure Capital` / `We finance, own and operate NVIDIA B300 GPU systems` / `Footprint in the European Nordics (Iceland), 100% renewable, sub-1.2 PUE.`

**A1.5 — The close**

> Agent: `Happy to go deeper once the NDA is signed.` / `Roald`
>
> Roald: *(nothing — the message ends on its last fact)*

**A1.6 — Corroboration of A1.2 from the same week.** The `intros/2026-09-03-roald-verbal-intro-rwa-odl.md`
register records that in speech he said *"low $4 per hour on the GPUs themselves"*, and that "the
version actually sent to this counterparty in writing afterwards said *'around USD 4 per
GPU-hour'*." So the softening in A1.2 is his own edit of his own spoken phrasing, not a
correction of the agent.

**A1.7 — The same rundown, as he actually sent it in email a few hours earlier.** Email to Alexander
Vladimirov, 3 September 2026, message `1a066dea965e3cc0`. This is the shipped shape of A1.4 in his
own hand, with an ask attached at the end:

> Hi Alexander,
>
> Was nice to meet you today. As discussed, here's a short note on what we do:
> *About AI Infrastructure Capital*
>
>    - We finance, own and operate NVIDIA B300 GPUs and lease them to Tier 1
>    and 2 neoclouds on long-term offtake agreements.
>    - Footprint in the European Nordics (Iceland), 100% renewable, sub-1.2
>    PUE.
>    - Batch size: 32 to 96 systems (8x B300 each), roughly USD 16M to 55M
>    per batch.
>    - Off-takers: Tier 1 and 2 (US) neoclouds
>
> *Contract terms for our customers:*
>
>    - Term 3 to 5 years
>    - 20-30% customer prepayment at signature, escrowed, released on
>    deployment
>
> For your 200MW project, specifically the initial 20MW, we could look into a
> leasing option but we would not own the datacenter or colocation contract
> ourselves, I think it makes the most sense to secure a neocloud as the
> first customer and have them contract the initial capacity with room to
> scale-up. If you have such a partner, we can discuss how to support their
> GPU buildout with leasing, so they don't increase their debt or give away
> equity to finance this project.
>
> Best,
> Roald

## A2. Lower confidence: agent draft versus shipped copy

Source: `docs/pitch-materials/style/STYLE.md` §1, §3 and §9. Left is stated to be agent-produced,
right is stated to be what shipped. Whether the right side is Roald's own wording or a revised
agent draft is not recorded, so treat these as house-voice exemplars rather than authorship
samples.

**A2.1 — Compression that deleted the argument**

> Agent: `Landing all three at once is the business.`
>
> Shipped: `Getting all three to land inside the same **6-month window** is the actual business. All our operations are optimized for frequent deployments of this size.`

**A2.2 — Explanatory gloss on a strong fact**

> Agent: `anchored by a **Swiss pension investment foundation** that underwrote us before anyone else. A pension foundation's diligence is the slowest kind, and it has already been passed once.`
>
> Shipped: `anchored by the **Swiss pension investment foundation "Anlagestiftung VALYOU"**`

**A2.3 — Closing lines**

> Agent, all deleted: `This is not a plan on paper.` `Speed is the product.` `The giants leave this size alone.` `Your money is never early.` `None of this is a projection.` `Every fear gets a mechanism, not a reassurance.` `The next contract is ours to close rather than a cold start.`
>
> Shipped, replacing the last of those: `All our operations are optimized for frequent deployments of this size. SPV 1 proves the financing model on top of our running operations, and the next contract is being negotiated.`

**A2.4 — Header as reader's question**

> Agent: `01 · Track record`
>
> Shipped: `What we have already built`

---

# Section B — Raw samples by channel

## B1. Slack, English

All from `nodaoworkspace.slack.com`, channels `#ac-main`, `#ac-admin`, and DMs. September 2026
unless noted.

**B1.1** (#ac-main, 2026-09-05, on a Reuters link)

> yes please, for your reference here is a short article about Nscale and Figure's partnership.
> I'm sure you can give it a spin to Sebastian.
> • It nicely fits our narrative of currently financing and operating GPUs and humanoids later, when mature enough.
> • Although we're very small now, with Valyou and Ragnarok we can reach pension fund and sovereign wealth funds soon, then act as catalyst for debt-free infra financing for Nscale and Figure
> • They'll use Vera Rubin racks and I'm starting to think we should invest in those as well,
> • cost is $7m - $9m per rack and only watercooled (more complex datacenter requirements)
> • but leading with token-output-per-watt

**B1.2** (#ac-main, 2026-09-05)

> Conference: would value your input on outreach messages, I'll put some examples in chat, feel free to roast and be creative :wink:

**B1.3** (#ac-main, 2026-09-05, an outreach message he wrote and pasted for review)

> Hi Theron,
> Read your background and looking to learn as we deploy <5MW projects at a time in Europe and Iceland. We own the GPU hardware and contract offtake to neoclouds.
>
> To run things lean and focus on operating cost effective, we use colocation and deliberately stop at bare metal and let our customers handle the orchestration.
> I'd value your perspective while we're scaling up towards larger projects.
>
> Best,
> Roald

**B1.4** (#ac-main, 2026-09-05, second outreach draft in the same thread)

> Hi Zhenyun,
>
> We're an operator and owner of GPU infrastructure in Europe. Would you be open for a conversation about your capacity roadmap, and the relevant architectures?
>
> Best,
> Roald

**B1.5** (#ac-main, 2026-09-05)

> You know Sebastian Becker of RedAlpine right? He's also investor in Nscale, neocloud who announced partnership with Figure (humanoids) for Vera Rubin racks, Im trying a couple ways in.

**B1.6** (#ac-main, 2026-09-04, status update)

> Update:
> • have all serials now, 1 photograph was cut short but we can infer the number (logical sequence) and will be confirmed in Iceland
> • all servers are being shipped now
> • I finalize the transaction finalization agreement this afternoon with the serial numbers so we have a document proof the first leg is complete (payment & identified goods)
> • after customer acceptance the ownership transfer is automatically complete

**B1.7** (#ac-main, 2026-09-04)

> The way it unfolds for us is having access to electricity, look credible and local connections help

**B1.8** (#ac-main, 2026-09-04)

> If they are in Reykjavik, sure, it's always good to know lawyers and they seemed highly placed and well connected (Blackrock intro...)
>
> Their actual office is all the way on the northeast side

**B1.9** (#ac-admin, 2026-09-04, agreeing to a booking)

> OK for me to rent until (including) thursday and from Keflavik airport, then Cédric and I can drive back there on Thursday

**B1.10** (#ac-admin, 2026-09-04)

> Hope it's manageable, thanks for the headsup!

**B1.11** (#ac-main, 2026-09-04)

> And hope you feel better already!

**B1.12** (#ac-admin, 2026-09-03, asking for a change without asking directly)

> Thanks for offering to rent it incl Friday, but how early could I return it? As I'll be at the airport around 6AM already, hotel has a shuttle service but didn't get back to me yet about price, can do a taxi so will figure it out.. it's not that far :slightly_smiling_face:

**B1.13** (#ac-main, 2026-09-03, a briefing with an open question at the end)

> Joseph Tan intro call (ex-YC founder, came in via email):
> • He offers an asset-backed loan up to $100M at 10% APY, 2-year term, 50–70% LTV, secured on the hardware plus a pledge of the customer contracts with step-in on default, underwritten on the off-taker's credit rather than the hardware;
> • his partner Samson (Hong Kong, finance role at an unnamed Taiwanese neocloud) covers Asia, and
> • is raising his own fund for datacenter, chips... but not sure about their edge there
>
> Worth to do another call? Their current offering is not a fit, but they may have some flexibility.

**B1.14** (#ac-main, 2026-09-03, framing an argument in his own words before quoting an agent brief)

> Yes, short note below:
> In short: Custom ASICS tie you to transformers as they exist today, which probably isn't the long-term architecture anyway. An ex-Google engineer I spoke to, who spent five years taking TPUs from research into the production fleet, is convinced we haven't landed on the right architecture yet: LLMs brute-force intelligence, and something will compete. Yann LeCun (ex-Meta, now building world models) argues the same.

**B1.15** (#ac-main, 2026-09-03, a correction to a draft)

> morning! One remark left on the investor update, PR #369
>
> 3rd year extension will be after server acceptance test, once servers are live, not next week:
> > "The third-year extension is not signed yet. We are still finalising it with the customer and are confident we agree on it by next week." --> "The third-year extension is not signed yet. We are still finalising it with the customer and are confident we agree on it after the server acceptance test in Iceland."

**B1.16** (#ac-main, 2026-09-03)

> Runpod is interested in our 8 additional servers if they're live in Oct. they have 3400 (GPUs i think) going live in December so less interest in our next batch.. for now at least.

**B1.17** (#ac-main, 2026-09-03)

> ah interesting, now its working for me again but had troubles for 30min

**B1.18** (#ac-main, 2026-09-03)

> hehe.. wonder if the "others" are congested because so many people moved upon Claude's downtime

**B1.19** (#ac-main, 2026-09-03)

> right! got carried away with some emails

**B1.20** (#ac-main, 2026-09-03, approving)

> @Cédric investor update is OK

**B1.21** (#ac-main, 2026-09-02, approving)

> @Cédric investor update looks good!

**B1.22** (#ac-main, 2026-09-02, deferring a review)

> processing it, content looks good, will make a suggestion on the wording and simplify it in places (like the pledge)

**B1.23** (#ac-main, 2026-09-02, softening his own edit)

> Investor update opening PR now. It's really just phrasing, and I was only there on 1st of September, in the warehouse.

**B1.24** (#ac-main, 2026-09-02, call prep he wrote himself)

> will be on time for GMI call, here's quick prep:
> • Alex Yeh (founder/CEO) made the intro and owns the relationship.
> • On the call: Andy Chen, VP Global Business & Product Development, Taipei — the senior commercial one, cc'd "for support", so he's the escalation not the day-to-day.
> • Lawrence Ngan, BD Manager, APAC — assigned as working owner, no public footprint at all, so he'll run the process but won't agree terms.
> • What to talk about:
>     a. whether they look for only GB300 or also B300 (ours)
>     b. Their ops concern: whether we can meet their SLA
>         i. our partner track record: 3 years, ~300 servers, 2,000+ GPUs, ~1 MW live, A100→H100→B300, a 64-node cluster for one contract customer, 99.9% SLA never missed.
>     c. Which option:
>         i. Host in Iceland
>         ii. Host in their DC: which site, what spec, what price. Site and MW.

**B1.25** (#ac-admin, 2026-09-02, travel logistics he wrote himself)

> Travel details Borealis Blönduós
>
> Flying - plan A
> • Depart and return Reykjavík Domestic Airport (RKV) — the in-city airport ~10 min from the hotel, not Keflavík. RFA is based on the field.
> • C172N booked 09:00–16:00. Cédric flying with RFA's safety pilot, ~1.5h each way.
> • Blönduós Airport → campus is 4.2 km / 6 min. Michiel or Jeff to collect us, otherwise a taxi.
> Driving - plan B
> If we drive:
> • Ring Road north (Maps), 245 km, ~3h each way via Borgarnes and over Holtavörðuheiði.
> • 07:00 start → at the DC ~10:30 → back in Reykjavík ~16:00.
> • There is an alternative gravel road for when the main one is closed, but that's unlikely: 278 km / 3h35
>
> Anything else needed?

**B1.26** (#ac-admin, 2026-09-02)

> Happy to book myself for Thursday 24 to Fri 25th near Keflavik, then I'll travel to Keflavik (near airport) with Cédric on Thursday, am planning for another datacenter visit on Thu afternoon in Keflavik.

**B1.27** (#ac-admin, 2026-09-02)

> Hi @Bianka, correct: my flight is Friday 25th (FI554) at 07:35 local time. I'll make a quick check if there's a hotel available in Keflavik, as that'd be a shorter trip (Reykjavik is 40mins)

**B1.28** (#ac-admin, 2026-09-02)

> thank you Bianka!

**B1.29** (#ac-admin, 2026-09-02)

> looks excellent

**B1.30** (#ac-admin, 2026-09-01)

> I'll come back on this!

**B1.31** (#ac-main, 2026-09-02, delegating an event)

> Event in Zurich with Nebius and NVIDIA on physical AI, could you try to attend? https://luma.com/lkh6du5z

**B1.32** (#ac-main, 2026-09-02)

> Check PR 363 for the update on our investor update :slightly_smiling_face:

**B1.33** (#ac-main, 2026-09-02)

> Ist fascinating the kind of equipment that is on our servers. I got an explanation yesterday by Jeff

**B1.34** (#ac-main, 2026-09-02, deflecting a compliment)

> Hah thanks always feel it can be better

**B1.35** (#ac-main, 2026-09-02)

> having lunch with a friend of mine to go through the model, very valuable feedback

**B1.36** (#ac-main, 2026-09-01, market observation with hedging)

> Just seen this on Lyceum's site, didn't have the impression they were deploying that many clusters of their own, probably rented from Verda. Didn't know either of them was active in Iceland... 36 B300 serves going live end of Sept.

**B1.37** (#ac-main, 2026-09-01, qualifying a relationship claim)

> not that well though, I talked to him once or twice, they were a partner at a startup conference we launched, years ago. Could be interesting to go via Emma, can imagine they get credible contracts

**B1.38** (#ac-main, 2026-09-01)

> in call with our insurer, slightly running over

**B1.39** (#ac-main, 2026-09-01)

> currently at Hashblock, have some calls starting soon

**B1.40** (#ac-main, 2026-08-31)

> Talked to Michiel, it'd be better if I see the machines tomorrow as they started unpacking the first one just now and it takes some time to do so carefully. They will send a picture report of the first ones and I'll video call them.

**B1.41** (#ac-main, 2026-08-31)

> We're funding the "machine age", a16z is taking a similar narrative
> https://a16z.com/the-machine-age-fund/

**B1.42** (#ac-main, 2026-08-31)

> Gm! hope you had a nice weekend. I'll go check the servers in a good hour :star-struck:

## B2. Slack, Dutch

He switches to Dutch with Belgian counterparties (Michiel, Jeff, Quint). Same terseness, more
diminutives and more exclamation marks.

**B2.1** (Group DM, 2026-09-04)

> @Jeff De Paepe heb je al labels op volgende machines geplaatst:
> ```GQL8N2312A0004
> GQL8N2312A0012```
>
> Ik vermoed dat deze eerder besteld zijn en best bij Wellguard passen, dan heeft AIC altijd de prefix GQI8N2312A (zo zijn er 30) en Wellguard 2x GQL8N2312A
>
> LMK :slightly_smiling_face:

**B2.2** (Group DM, 2026-09-04)

> Ik mis één server waar de serial no er niet opstaat. Volgens de rest van de serial's zou dit GQI8N2312A0008 moeten zijn, indien reeds verscheept dan noteer ik deze redenering en confirmen we later wel

**B2.3** (Group DM, 2026-09-04)

> Hi @Jeff De Paepe heb je nog foto's van de overige machines? Mis nog 9 serials van AIC en 2 van Wellguard. Alvast bedankt!!

**B2.4** (Group DM, 2026-09-04)

> weet je welke serienummers ik dan voor Wellguard hou vs. op het AIC document zet?

**B2.5** (Group DM, 2026-09-04)

> yes got it en no worries hoor

**B2.6** (Group DM, 2026-09-04)

> top, merci!

**B2.7** (Group DM, 2026-09-04)

> dan deel ik later deze NM de transactie finalization doc met de serials vernoemd

**B2.8** (Group DM, 2026-09-02)

> Keep me posted als jullie al shipments (plannen) te maken. Hopelijk loopt het vlotjes vandaag!

**B2.9** (Group DM, 2026-09-01)

> Welke hourly rental rate zien jullie atm voor b300's? Heb via Wellguard de vraag gekregen voor een nieuw voorstel, apart van de eerste 2 servers

**B2.10** (Group DM, 2026-09-01)

> Hi guys, ik plan om er rond 11u te zijn Ok?

**B2.11** (Group DM, 2026-08-31)

> Hallo, yes, morgen past ook. Maar kunnen jullie dan please al enkele fotootjes sturen?

**B2.12** (Group DM, 2026-08-31)

> ik kom rond 11u dan even langs, maar geen haast, de overige serienummers mogen jullie doorsturen

**B2.13** (Group DM, 2026-08-31)

> any picture guys? :sweat_smile: just one is fine, but teased Cédric too much

**B2.14** (Group DM, 2026-08-31)

> no worries super, merci!!

**B2.15** (Group DM, 2026-08-31)

> Top. Merci

**B2.16** (DM with Quint, 2026-08-31, floating an idea)

> wild idea maar waarom niet enkele WTN whales een consortium doen vormen, en met Enzo & Leo volledige overdracht proberen regelen en u technisch maintenance laten leiden?
> Maak me vooral nog zorgen om hun technische toegang en niemand die het project nog actief managed..

**B2.17** (DM with Quint, 2026-08-31)

> toevallig nog contact met David F. gehad?

**B2.18** (DM with Quint, 2026-08-31)

> tricky tricky

**B2.19** (DM with Quint, 2026-08-31)

> is er nog een andere exchange dan ICPswap waarop ik nicp kan handelen?

**B2.20** (DM with Quint, 2026-08-31)

> géén enkele DEX / CEX ?

## B3. Email, English

**B3.1** — To Alireza Masrour and Brittni Schimke (Plug and Play), 2026-09-04, cold-ish warm
reconnect. Message `1a06d8ef3922091e`.

> Hi Alireza and Brittni,
>
> End of next week, I'm flying over to attend an AI infrastructure conference
> in Santa Clara. Alireza, it would be a great time to catch up if you're
> available on Monday Sept. 14 or Tue 15?
>
> Also available over the weekend.
> Really looking forward to see the PNP team again!!
>
> Best,
> Roald

**B3.2** — Follow-up in the same thread, 2026-09-04, message `1a06daca86eb7aad` (snippet as stored):

> Thank you! @Brittni, would Tuesday still work for lunch? Just got a meeting request for Monday-lunch up in SF. Thank you :)

**B3.3** — To Lumen customer financial services, 2026-08-26, a change request to a vendor.
Message `1a03dbf126f49bb4`.

> Dear,
>
> Thank you for your email. Could you update the email to "roaldp@nodao.org" ?
> Rest looks good. Appreciate it.
>
> Best,
> Roald

**B3.4** — To Antoine Loiseau (Roundtable), 2026-08-28, message `1a047218a50ba25b`:

> Hi Antoine,
>
> Thank you and just booked for September 2, 2026 3:00 PM. Looking forward to our call!
>
> Best,
> Roald

**B3.5** — To Nick Aldewereld, 2026-08-24, message `1a03540188ebaf19`:

> Hi Nick, booked for Thursday! Thank you. Looking forward to it.
>
> Roald

**B3.6** — To Alexander Vladimirov, 2026-08-27, message `1a044f13b927366f`:

> Hi Alexander,
>
> Good to connect, shared an invite for Thursday:
>
> Intro: Alexander - Roald
> Donderdag 3 sep • 12:00–12:30
> Deelname-informatie van Google Meet
> Link voor videogesprek: https://meet.google.com/sgu-cxhb-wgj
>
> Looking forward to talk.
>
> Best,
> roald

**B3.7** — Reply to Alexander, 2026-08-28, message `1a0471e9f717e36d`, in full:

> Likewise!

**B3.8** — To Boardy (an AI intro agent), 2026-08-27, accepting an intro, message `1a044e1d9baf8289`, in full:

> Sure lets go

**B3.9** — To Louise Velayo (Aviate Labs), 2026-09-05, message `1a071554253cd47c` (snippet as stored):

> Great, thank you! Had inquired with Alta for my nodes as well but were lowballing it.

**B3.10** — The long-form English rundown is A1.7 above. It is the only substantial English email to
an external counterparty found in the last 180 days.

## B4. Email, Dutch

His Dutch business email is markedly longer and more structured than his English. These are the
best available proxy for how he writes at length when he is not being helped.

**B4.1** — To Paul Derweduwe (Wellguard), 2026-09-02, sending an investment model. Message
`1a063eda5c30ba00`.

> Dag Paul,
>
> Zoals beloofd, in bijlage het eenvoudige model voor 5 servers in on-demand
> rental. Ik laat ook weten zodra we richting een volgende contract-batch
> gaan waar je zou kunnen aansluiten.
>
> *Samenvatting*:
>
>    - *Investering*: $2.875.000 (5 servers × $575.000)
>    - *Maandelijkse uitkering: *$81.105/maand (bij 70% bezetting)
>    - *Terugverdiend*: ±36 maanden (na eeste uitbetaling)
>    - *IRR over 5 jaar:* 27,5%
>    - *Uurtarief en bezetting: *we rekenen met $6,00 per GPU per uur en 70%
>    bezetting
>       - Bij on-demand halen we vandaag $6,00–$6,25, en onze pool draait
>       tegen de 90% verhuurd. In het tabblad zie je elke bezetting van 50% tot
>       100% op $6,00.
>    - *Inbegrepen*: Hosting in IJsland en onze poolvergoeding na
>    hostingkosten zijn inbegrepen, dit dekt alle operaties, onderhoud,
>    networking equipment en RMA.
>    - *Belangrijk:* de rendementen zijn indicatief en vóór belasting bij de
>    investeerder.
>
> Een correctie op mijn mail van 25 augustus*: *voor September is de prijs
> verder gestegen naar $575.000 per server in plaats van $560.000. We kunnen
> deze pas vasthouden bij de eerste betaling en gaan uit van verdere stijging
> gezien de chip tekorten.
>
> Bij bestelling in september zijn de oplevering en eerste inkomsten verwacht
> voor januari 2027, mogelijks een maand vroeger.
>
> Bel me gerust, of laat weten indien er nog verdere vragen zijn.
> Heb ook een foto toegevoegd van de servers uit onze vorige batch die zopas
> zijn toegekomen :)
>
> Vriendelijke groeten,
> Roald
> +32471363226

**B4.2** — Same thread, 2026-09-02, holding message:

> Hi Paul,
>
> Berekening komt er deze namiddag aan, even druk in meetings.
> Groet!

**B4.3** — Same thread, 2026-09-01, asking for the parameter before doing the work:

> Dag Paul,
>
> Zeker. Voor hoeveel servers of welk investeringsbedrag had je dit graag
> gezien?
>
> Vriendelijke groeten,
> Roald

**B4.4** — Same thread, 2026-08-25, terms recap:

> Dag Paul,
>
> Zoals besproken:
>
> - Contracten in onderhandeling zijn 3 - 5 jaar looptijd, 15 - 20% voorafbetaling
> - Afhankelijk van de klant gaat de voorafbetaling ofwel naar de aankoop van servers, wat een korting geeft voor de investeerder, of zal na oplevering als cash worden uitgekeerd
> - Investeringsnood per contract: 32 tot 80 servers ($18m - $45m)
> - Net als bij onze eerdere samenwerking kan één investeerder deel uitmaken van een grotere batch.
> - Huidige prijs per server: $560k (5% variate afhankelijk van technische vereisten klant)
> - Opleverdatum: Januari 2027 (indien in September besteld)
> - Locatie: IJsland, Tier 3 datacenter (volledig redundant), 100% groene stroom & relatief goedkoop
>
> Het vorige contract waarond we contact hadden gaat om 32 servers op een 3 jaar afnamecontract dat in September live gaat.
>
> Vriendelijke groeten,
> Roald

**B4.5** — To Paul/Jef/Hendrik (Wellguard), 2026-06-09, delivering bad price news and an option.
This is his longest self-written prose sample.

> Dag Paul, Jef en Hendrik,
>
> In bijlage de updated-quote voor jullie 2 racks B300.
>
> Een kort woordje bij de prijs:
>
> - Deze ligt net iets hoger dan twee weken geleden, een verschil van ongeveer €825 per server, door de verder gestegen marktprijzen op componenten.
> - De huidige prijs kan de pool voor één week vasthouden (los van vermeldde vervaldatum).
> - Levertermijn is 4 tot 6 weken.
> - De quote komt van Hashblock, dit is een Belgische entiteit van de pool die toelaat zonder BTW te factureren en de machines ook meteen in te klaren in IJsland.
>
> Ook een update over de timing van het 24-maandencontract:
>
> - De pool kan het 24-maandencontract met de eindklant pas aangaan zodra de volledige bestelling voor die 16 B300's geplaatst is. We hebben momenteel een batch van B300's in closing met andere investeerders.
> - Samen met jullie 2x B300's komen we aan het nodige aantal, en die van jullie geef ik voorrang om in het contract deel te nemen. Aangezien een van die investeerders een Zwitsers pensioenfonds is, verwachten we hun fondsen pas tegen eind deze maand.
> - Een mogelijke meevaller: gezien deze grote order eraankomt hebben we zicht op een licht verlaagde kost van het datacenter, dit wordt normaal deze week getekend en zal in jullie maandelijkse overzicht zichtbaar zijn.
>
> *Wat we daarom kunnen voorstellen:* een mogelijkheid is om jullie bestelling nu al te plaatsen en de B300's in on-demand service te brengen zodra geleverd, tot de eerstvolgende batch op 24-maanden contractbasis wordt opgeleverd. Dit zou een maand extra inkomsten betekenen. Van zodra het 24-maandencontract ingaat, schuiven jullie racks daar gewoon in mee, hier zijn geen kosten aan verbonden.
>
> Uiteraard is de keuze aan jullie. Laat gerust weten of jullie meteen willen starten in on-demand, of liever wachten tot het 24-maandencontract rond is. De service agreement komt er ook aan.
>
> Bij vragen spring ik graag op een call, laat maar weten.
>
> Vriendelijke groeten,
> Roald

**B4.6** — To Paul (Wellguard), 2026-06-01, delivering a cost increase and apologising:

> Dag Paul,
>
> Zonet met de boekhouder gesproken, ook voor hem lijkt de Luxemburgse btw weerlegbaar, maar het is aan te raden dit langs jullie kant ook te checken. De geldstroom zou als volgt gaan:
> eindklant (afnemer – in US, in USD) → betaalt aan pool (operator – Belgische bv, ontvangt USD) → betaalt aan investor (Luxemburgse holding, in EUR)
>
> In verband met de projectie: mijn planning is wat vertraagd, dus kan ik je nog geen nieuwe forecast sturen. Wel is er een update in verband met de hosting costs. Doordat er vorige maand 300 kW toegevoegd is en één Zwitsers vehicle nu in closing is (ook 300 kW), is de huidige data room volzet en moeten we naar een naburige faciliteit. Deze is bij dezelfde provider (AtNorth), maar daar rekenen ze *€227/kW/month* aan, ook voor mij even slikken. In een van mijn projecties komt dit uit op een 1,5% lagere ROI.
>
> Deze info is vanochtend tot bij mij gekomen, mijn excuses dat we dit vrijdag niet zagen aankomen. We hebben reeds een optie op een nieuwe uitbreiding in onze huidige facility, maar deze zal pas eind dit jaar operationeel zijn en ook daar verwachten we een prijsverhoging. Helaas moeten deze kosten doorgerekend worden. Indien je in tussentijd nog vragen hebt, ontvang ik deze graag, ik ben ook steeds bereid op een call te springen.
>
> Vriendelijke groeten,
> Roald

**B4.7** — To Paul (Wellguard), 2026-05-29, answering diligence questions. Excerpt on residual value,
showing how he handles a question he cannot answer with certainty:

> Als eigenaar van de machines hebt u de vrijheid om deze machines zelf, op elk moment met 3 maanden notice, te verkopen. Omdat wij zelf regelmatig assets verkopen hebt u de optie dat wij dit voor u doen, dan bevragen we onze used reseller partners voor quotes op dat moment en u beslist. Uit eigen ervaring ligt de waarde van 3 en 5 jaar oude machines tussen de 50 en 30%, respectievelijk, maar dit varieert van type en trend-timing. Bij een andere investeerder hebben we bijvoorbeeld afgesproken om hierop een commissie te nemen, zodat er incentive is om de maximale prijs te bekomen en op het "juiste" moment te verkopen. We kunnen dit straks verder bespreken, zeker bereid om jullie hierover te ontzorgen.

And on warranty risk:

> Na 3 jaar worden vervangstukken wel aangerekend maar al het onderhouds-werk & RMA werk wordt niet aangerekend. Let wel: nooit met zekerheid te zeggen maar de meeste defecten komen de eerste 2 weken tijdens testen naar boven of de periode nadien. Deze machines zijn gedesigned om minstens 7 jaar te opereren.

**B4.8** — To his co-partners at Allusion, 2026-09-03, on a fee dispute with an introducer. Message
`1a0678a73cf4d2ef`. Note how he takes the other side's part and puts blame on himself.

> Hi Paul en Jules.
>
> Ik sprak vandaag nog met Thomas. Zoals in het doorgestuurde mailtje te
> lezen is, wil hij graag de case 4Mica en Qash afronden voordat hij op reis
> vertrekt. Ik heb hem destijds in mei gevraagd om zelf met een voorstel en
> terms te komen. Hoewel het mailtje streng klinkt en ik zijn frustratie wel
> begrijp, moet je er geen aanstoot aan nemen. Ik heb hem ook uitgelegd dat
> ik ook een vertragende factor hierin ben.
>
> Wij hebben het hier na de investering in 4Mica nog over gehad dat Allusion
> liefst niet aan een heleboel externen fees begint te betalen. Maar dat als
> ik dealflow via externen binnenkrijg, en die hierop een carry of
> introductie fee willen, dat dat van mijn potje afgaat, waarmee ik oké ben.
> Vandaar ook de structuur van Thomas, waar we alle drie een partij in zijn.
>
> Zoals op de laatste meeting besproken:
>
>    - Jules, heb jij al eens kunnen kijken wat er mogelijk is vanuit
>    Allusion en of we met Thomas zijn terms kunnen leven?
>    - Kunnen we dit proberen af te ronden, en zet ik een gezamenlijke
>    e-mailthread op?
>
> Om deze case vooruit te helpen, en zoals eerder aangegeven, zie ik dit het
> liefst los van onze afspraken. En vind ik ook dat Thomas zijn cut zeer
> zeker verdient, gezien het werk dat hij al in beide start-ups heeft
> gestoken. Zonder hem zouden we in geen enkele vorm bijde geïnvesteerd zijn.
>
> Bel me gerust op.
>
> Beste groeten,
> Roald

**B4.9** — To his mother, 2026-08-26, message `1a03f1a760e5f604`:

> Dag mama,
>
> Niets mee doen, is een standaard melding van algemene gebruikersvoorwaarden. Geen verkoopsovereenkomst of zo.
>
> Groetjes
> Roald

**B4.10** — To his father, 2026-08-24, message `1a0353be10d1071e` (snippet as stored):

> dag papa, het probleem ligt vooral bij de verschillende netwerken die een technieker ooit heeft opgezet, daardoor moet uw toestel hele tijd van netwerk veranderen, op twee uur heb ik dat wel aangepast.

**B4.11** — To Kristof Sanders, 2026-08-24, message `1a033dbc8ebbf9d6`:

> Dag Kristof,
>
> Dank om dit te delen!
>
> Gr,
> Roald

## B5. Typed instructions to agents

Extracted from `~/.claude/projects/**/*.jsonl`. 3,384 unique typed messages exist; a sample follows.
This is the largest and most reliable corpus of his unedited writing, because nothing intervenes
between his keyboard and the file.

### B5.1 Giving a task

> - work out a funding timeline from today aug 14
> - next week we should make the final payment, look into meetings with michiel yesterday and when the final payment should be made
> - and refresh how much will have to be paid and what our funding gap is
> - prepare this note so i can bring it up in an email to our board of whats on the planning, flag me if you dont see the meeting notes from michiel from last 2 days

> - content edit: do not show "fail" but "miss" on the live site, i thought the repo was updated alr
> - ensure the email signup form works, dont think it does anything now
> - add a minimal nodao header
> - then add the custom domain but halt if you get stuck somewhere, do not touch anything else than the nodao.org domain

> Okay perform another look into the repo in our progress and come up with the best next steps for me to get a quote for my ICP notes. If you use any sub-agents to search the web, keep them limited to just three. You yourself are an orchestrator and should use your reasoning. Capture the status of our progress, prepare anything to make it easy for me to immediately reach out to people in my own writing style, and advise me on the next step and prepare it for me please.

> everyone is battling cold outreach written by ai nowadays, nything generic like "saw your speaking at x, we doing Y" is cold outreach trigger, set up a system where you can draft and evaluate these kind of outreach messages for our case, for neoclouds. You can use 2 claude opus subagents for 10 runs, you orchestrate their role, one drafts, one receives as classifier and you act as observer and provide feedback to drafter agent.

> So next up I need to keep an overview of who all the potential end customers we are engaging with are. I want to challenge you and look for a way how you can make that visual for me whenever I am chatting in this thread and whenever we are editing the CRM and processing meeting transcripts

> for this V3 we want to keep it a onepger with minimal changes to the original so it can be distributed today. Make a list of feedback we should implement over V2.

> determine a minimum hourly rate and above 15% prepayment that we can land on with lyceum given we have these open market offers (note that they' still have an up to 10% commission applied on them)

> side-check: investigate whether IREN has raised capital in their main company structure, where the founders hold capital, and what those investors expect in terms of return. For context with AIC we are looking at whether we can give certain VCs exposure to our main company of Cedric and me but we don't see yet how we can generate 20x returns in a short time. Since everything is based on how the funds perform and we are more like a fund manager at the moment

> spin up the reviewer counsel again to verify compatibility with current pledge agreement and belgian law

> create a folder on my local machine aggregating the documents for this transfer with 1 letter detailing the tx for my own records

> execute the full workplan

> Investigate, search the web

> commit to repo and PR

> Perform your search on the repo again and flag me if anything is still not in order.

> onderzoek in welke situatie we ons bevinden en wat het risico is over onze bestelde servers

> hosting is $2,900 per server atm, hoe vergelijkt dit? genereer nu de up-to-date sheet maar hou de formatting

### B5.2 Saying no, correcting, stopping

> nope, just write from our own reporting.

> nope, write only 1 simple question

> nope look for evidence of current contract being extended alr now

> nope doesnt work, any linked mention or reference does not get copied, keep it plain text

> no, anything moving forward except for passive (VC) allocations shold be split

> no, rather appreciate their work on this or helping us with this

> stop, this deed is to protect from hashblock insolvency

> stop with your drafts, strategy first, ideally we get nvidia clearance, through birgir could be an option (prevent him connecting the operator to us alr now), we could ask direct connect to nvidia through martijn (supermicro) and figure it out that way

> stop including the required power need. That's a separate conversation. For now we will offer them 32 to 64 systems but given the small difference between those, let's negotiate one of 64 only now create a table again of our open target, the floor and cash at signing. Do include in that table the IRR over a 5-year forecast period based on our financial model.

> dont mention hashblock yet, anywhere, name them as Pool Operator

> dont say "some" make the numbers exact if they're confirmed and they are. Now generate a docx from this

> Don't talk that much. Is it okay to keep the cash flow in there as is or what is the feedback?

> dont use .md files, they only read pdf or docx, and check whether its ok to upload all files in your folder

> dont update the google drive, you have no access to the relevant gdrive

> Don't fold the full questions into the PR, only the relevant statement from a counter-party like Michiel. Now we turn the overview of the job that you prepared. Then I will fork this conversation and hand it over to this new agent. One agent will work on the data center agreement. The other one on closing the hardware transaction.

> dont bother tax is we indeed plan a fund here, continue with the model, ill review it anyways

> dont speak out on what we prefer, just ack we'll take it into account

> We do not need to forward this. We will just say that this is already handled because of the operational setup. Give away the minimum amount of information only and just a clear short reason

> you shouldnt log this yet, its not sent yet

> not to my vault, to the repo

> Wait what are you doing?

> wait so less is going to investors than initial investment?

> wait how is "roaldp/investor-due-diligence-sweep" impacting this session? its a compeltely differen repo right?

> nope let's reformat:
>
> * lets create a doc with details of our operator belgian, icelandic and US company details, only with address

### B5.3 Asking for clarity

> this is unclear to me "One timing point may make it largely moot:" meaning i dont get, keep it basic

> this is unclear, reword: In practice there isn't a general spot pool: each machine is dedicated to one end customer, so there is no spot-allocation step when capacity looks spare.

> dont think this is clear yet? From full payment our real protection is ownership, with Iceland as the country that matters, hence the Icelandic contact.

> Wait what is the data list that I should add? Make it very short and clear what documents I should add and prepare because this is the only doc I have at the moment.

> i want to know your reasoning before OK'

> And what does that and that cash flow actually mean

> tell me first where these services run and how i can keep an overview as i have a lot running on this machine alr

> wat is fronting?

> are they talking about single gpu's or systems of 8?

> is this a proper response on topology? Networking topology:
> Ethernet with RoCE, the fleet will consist 2× dual-port 100GbE QSFP28 per system and 8× 800G ConnectX-8 OSFP per node.

> fact check me response, make it an ELI20-basic engineering kind of wording: Read about it a week ago or so, it's a know custom ASICs are more efficiënt but require you to know which kind of models you'll run on them and offer less flexibility for training or different kind of model architectures. Talked to an ex-Google datacenter engineer (experience with NPU's) and he's convinced we've not landed on the "best" architecture to run AI, in his view LLMs is brute forcing intelligence, and there will be competing architectures soon, just like Yan Lecnun (ex-meta) believes.

### B5.4 Bringing a live problem

> supermicro guy called me, nvidia called borealis, they dont know us. I called our operator, they said that smith now puts claim on all tx via supermicro and will fck us with 20% markup, operator does not want to be disclosed to any of these parties. What to do

> bro you just need to help me finalize this draft: Hi Scott, Yvonne,
>
> Good to connect properly! Also adding my co-founder Cédric.
>
> Next week works. I have Monday 3 and Tuesday 4 August open in the morning. Any of these:
>
> Mon 3 Aug — 15:00 JST / 08:00 CEST
> Mon 3 Aug — 16:30 JST / 09:30 CEST
> Tue 4 Aug — 15:00 JST / 08:00 CEST
>
> For context: we operate on the supply side by funding and operating the systems. Our current configuration is B300-based, but we are open to various setups.
>
> Anything particular you'd like to cover?
>
> Best,
> Roald

> cant use browser, costs too much tokens, i could see the html but no data loaded couldnt select term etc

> we should tighten it to only the nodao website repo and no other, the other are super confidential

> ok do wp4, Ill handle zapier and app script, do return me instructions for app script install

> you do the instruction, i can authorize

## B6. Commit messages that read as his

From `~/conductor/repos/*`. Kept only short, lowercase-leaning, non-bulleted messages with no
`Co-Authored-By` trailer.

> basic IC memo creation

> pdf processing

> batch processing imgs

> merge itempass digital twin into item_view working branch

> hardware-resale: all 10 deployer prospects contacted 2026-09-05

> hardware-resale: Hut 8 sent; recurring-supply line added to pitch

> chore(crm): regenerate stale index

> docs(security): record manual serial photo review

> docs(security): sort serial evidence filenames by serial

> docs(model): open the v4 edit log

> Update pulse_onboarding.md

> Add privacy-safe companion MVP scaffold and templates

## B7. Spoken, transcribed verbatim

Source: `~/conductor/workspaces/ai-infrastructure-capital/bozeman/docs/pitch-materials/intros/2026-09-03-roald-verbal-intro-rwa-odl.md`,
which reproduces a Fireflies transcript line for line including filler and self-corrections. This
is the only long unedited sample of him explaining the business without a keyboard.

> No, long story short, basically I'm based in Belgium.
> Cedric was actually one of our first customers when I started my own msp.
> So managed service provider.
> We basically maintained and operated servers in both the us, Europe and Singapore for infrastructure investors in the Internet computer ecosystem, which is a decentralized cloud where Cedric was actually one of the co founders.
> And then about one and a half years ago we started talking.
> So I was already in the industry seeing the demand for GPU based compute.
> Before that I was fully focused on CPU based compute.
> Cedric and I started talking.
> Cedric is very much into working with agents.
> Already over a year ago he had his own agents consuming a lot of tokens.
> We of course support the idea that we will see our token count go 10x.
> I'm using it literally forever.
> There are agents running so I can only see it like we're really the early adopters.
> So I can only see it go up.
> So long term I think there we are set.
> Of course there are nuances in how we will reach to that point, but that's a different story.
> Cedric specifically is also is an entrepreneur and investor by now and he was looking for energy exposure and exposure to the AI build out.
> So that's basically when I run a few ideas by him.
> Um, and initially I had experience with a pool that was running on demand inference.
> So basically we would collect GPUs, hook them up to aggregator platforms and make decent money there.
> But when I got talking to Cedric for his potential investment, he had a preference of, of a more stable kind of setup because you're dealing with utilization.
> It's, it's less, it's more variable if you do only mask.
> So long story short, we involved some more people to pull up capital and as soon as we reached about 10 million USD we unlocked basically the initial contracts like you also shared.
> Some of them are in the thousands of GPUs so you're talking billions.
> We now sort of find a sweet spot that we can do between 32 and 96 servers.
> So each server has about 8B3 hundreds in our case and then we're talking from 60 million USD to about 45 ish that we can use to, to finance up to 96 in terms of energy.
> Then we're talking about half a megawatt to 1.5 megawatt build build outs.
> The way we are structured is I coordinate the project, I deal with with all stakeholders to procure the servers, get the right pricing, get the customer agree and land on customer details before we do any capital calls.
> I have a close connection to our operators that I've been working with for some time.
> But you have to know like we outsource it so that liabilities are well aligned and we can focus on our job and yeah, that's pretty much it.
> We are primarily in the European Nordics deploying and we still have a couple megawatts secured and we're of course negotiating to get more.

And, on the terms:

> So today actually we are, I mean yesterday at the moment we are in talks for our next batch which is about 72 GPUs to start with, scaling up to 144 which would be a capex investment of, of starting with about 40 million.
> And at the moment we are in talks with investors that we can offer an asset backed investment opportunity where you will net slightly above 30% IRR for five years.
> It's on five year contract, customer pays around 20% prepay upon deployment and then we're in the low $4 per hour on the GPUs themselves.

---

# Section C — Observed patterns

Every claim cites samples above it. Claims the samples do not support are not made.

## C1. He writes to a person, not to a file

Almost every message opens by naming the recipient or by acknowledging what they just did: `Hi
@Jeff De Paepe heb je nog foto's` (B2.3), `Hi Alireza and Brittni` (B3.1), `@Cédric investor update
is OK` (B1.20), `Thanks for offering to rent it incl Friday, but…` (B1.12). Even the pasted
outreach drafts start `Hi Theron,` on its own line (B1.3). The exception is his instruction
register to agents, which has no greeting at all (all of B5).

## C2. Sentences are short but joined by commas, not full stops

He rarely writes a sentence over about 30 words, but he chains clauses with commas where English
would take a full stop or a semicolon. `If they are in Reykjavik, sure, it's always good to know
lawyers and they seemed highly placed and well connected` (B1.8). `Read your background and looking
to learn as we deploy <5MW projects at a time` (B1.3). `Talked to Michiel, it'd be better if I see
the machines tomorrow as they started unpacking the first one just now and it takes some time to do
so carefully` (B1.40). This comma-splice habit is one of the most consistent surface markers in the
corpus and an agent imitating him should reproduce it rather than correct it.

## C3. He drops subjects and auxiliaries

`Read your background and looking to learn` (B1.3), with no `I`. `Mis nog 9 serials` (B2.3), no
`ik`. `Heb ook een foto toegevoegd` (B4.1), no `ik`. `Had inquired with Alta for my nodes as well
but were lowballing it` (B3.9), no `I` and no `they`. `Was nice to meet you today` (A1.7), no `it`.
`Just seen this on Lyceum's site, didn't have the impression they were deploying that many` (B1.36),
no subject in either clause.

## C4. Hedging is frequent and explicit, and it is attached to the specific uncertain item

He does not soften a whole message; he marks the one thing he is unsure about. `they have 3400 (GPUs
i think) going live in December` (B1.16). `1 photograph was cut short but we can infer the number
(logical sequence) and will be confirmed in Iceland` (B1.6). `not sure about their edge there`
(B1.13). `probably rented from Verda` (B1.36). `not that well though, I talked to him once or twice`
(B1.37). In Dutch: `Ik vermoed dat deze eerder besteld zijn` (B2.1), `nooit met zekerheid te zeggen
maar de meeste defecten komen de eerste 2 weken` (B4.7). Compare A1.2, where he replaced the
committing `Low USD 4… fixed for the term` with the open `Around USD 4 per GPU-hour`.

## C5. He ends on a question or an offer, not on a conclusion

`Worth to do another call?` (B1.13). `Anything else needed?` (B1.25). `Hi guys, ik plan om er rond
11u te zijn Ok?` (B2.10). `Bel me gerust, of laat weten indien er nog verdere vragen zijn` (B4.1).
`Bij vragen spring ik graag op een call, laat maar weten` (B4.5). `Anything particular you'd like to
cover?` (B5.4). `Bel me gerust op.` (B4.8). He does not write summarising closers; the only
"closing" he writes is an availability offer or a direct question. This matches A1.5, where he
deleted the drafted `Happy to go deeper once the NDA is signed.` entirely.

## C6. Bullets are used for facts, prose for judgement

Every list in the corpus is a list of facts with no argument: serial prefixes (B2.1), travel legs
(B1.25), call attendees (B1.24), terms (B4.4, A1.7). Where a judgement is being made it is in
running prose, after the list: `For your 200MW project… I think it makes the most sense to secure a
neocloud as the first customer` (A1.7); `Wat we daarom kunnen voorstellen: een mogelijkheid is om
jullie bestelling nu al te plaatsen` (B4.5). His bullets carry no verbs of persuasion.

## C7. Instructions to agents are imperative, lowercase, unpunctuated, and stacked

`execute the full workplan`. `commit to repo and PR`. `Investigate, search the web`. `spin up the
reviewer counsel again to verify compatibility with current pledge agreement and belgian law`. When
there is more than one thing he uses a hyphen list with no capitals and no full stops (B5.1, the
funding-timeline and website messages). He routinely fuses the task and the constraint into one
line: `add the custom domain but halt if you get stuck somewhere, do not touch anything else than
the nodao.org domain`.

## C8. He says no in one word and then immediately gives the replacement

`nope, just write from our own reporting.` `nope, write only 1 simple question`. `no, rather
appreciate their work on this or helping us with this`. `stop, this deed is to protect from hashblock
insolvency`. `stop with your drafts, strategy first, ideally we get nvidia clearance…` (all B5.2).
The rejection is never explained at length; a single clause of reason follows if any. He never
writes a paragraph of disagreement.

## C9. He discloses less than the draft does, deliberately

`Give away the minimum amount of information only and just a clear short reason` (B5.2). `dont
mention hashblock yet, anywhere, name them as Pool Operator` (B5.2). `dont speak out on what we
prefer, just ack we'll take it into account` (B5.2). `we should tighten it to only the nodao website
repo and no other, the other are super confidential` (B5.4). This is the same instinct as A1.1,
where he cut the customer-sizing criterion `USD 1bn+ scale, who resell into the AI labs` from a
message to a counterparty.

## C10. He takes blame and gives credit

`Ik heb hem ook uitgelegd dat ik ook een vertragende factor hierin ben` (B4.8). `mijn excuses dat we
dit vrijdag niet zagen aankomen` (B4.6). `En vind ik ook dat Thomas zijn cut zeer zeker verdient…
Zonder hem zouden we in geen enkele vorm bijde geïnvesteerd zijn` (B4.8). `no, rather appreciate
their work on this` (B5.2). `Hah thanks always feel it can be better` (B1.34). `It's really just
phrasing, and I was only there on 1st of September, in the warehouse` (B1.23), downplaying his own
correction.

## C11. Contractions, always; formal registers, never

`we're`, `didn't`, `it'd`, `they're`, `don't` appear throughout, including in outbound email to
counterparties: `if you're available on Monday Sept. 14` (B3.1), `so they don't increase their debt`
(A1.7). No instance in the corpus of `we are pleased to`, `please find attached`, `kindly`, or a
passive construction with an unnamed actor.

## C12. Punctuation habits

- Em dashes appear only in agent-written text and in his own list labels; in his own sentences he
  uses commas (`Hi Joseph, was good meeting you` — A1.3 — replacing the drafted `Hi Joseph —`).
  Exceptions exist in structured notes he wrote himself: `Andy Chen, VP Global Business & Product
  Development, Taipei — the senior commercial one` (B1.24).
- Trailing `..` instead of `...` is frequent: `so less interest in our next batch.. for now at
  least` (B1.16), `it's not that far ..` (B1.12), `raising his own fund for datacenter, chips...`
  (B1.13), `niemand die het project nog actief managed..` (B2.16).
- Doubled exclamation marks in warm messages: `Alvast bedankt!!` (B2.3), `merci!!` (B2.14), `Really
  looking forward to see the PNP team again!!` (B3.1).
- Emoji are used, sparingly, and only in internal or warm channels: `:wink:` (B1.2),
  `:slightly_smiling_face:` (B1.12, B1.32, B2.1), `:star-struck:` (B1.42), `:sweat_smile:` (B2.13),
  `:)` in email to a Dutch counterparty (B4.1) and to a warm US contact (B3.2). No emoji in the
  rundown to Alexander (A1.7) or in any cold outreach.

## C13. Non-native constructions to preserve, not fix

These recur often enough to be voice rather than accident. `Worth to do another call?` (B1.13, for
"worth doing"). `Looking forward to talk.` (B3.6) and `looking forward to see the PNP team` (B3.1),
both with a bare infinitive. `focus on operating cost effective` (B1.3). `Ist fascinating` (B1.33).
`36 B300 serves going live` (B1.36). `variate` for variation (B4.4). `Im`, `alr`, `atm`, `wdy?`,
`LMK`, `wym` as everyday abbreviations. Missing apostrophes in `dont`, `doesnt`, `its`, `thats`.

## C14. Dutch and English are mixed inside a single sentence

`Keep me posted als jullie al shipments (plannen) te maken` (B2.8). `yes got it en no worries hoor`
(B2.5). `Hallo, yes, morgen past ook` (B2.11). `hosting is $2,900 per server atm, hoe vergelijkt
dit? genereer nu de up-to-date sheet maar hou de formatting` (B5.1). English is the default with
Cédric and all non-Belgians; Dutch with Michiel, Jeff, Quint, family and Belgian counterparties.

## C15. Numbers carry their units and their source, but he does not bold them

In his own writing figures appear plainly: `$7m - $9m per rack` (B1.1), `2,000+ GPUs, ~1 MW live`
(B1.24), `245 km, ~3h each way` (B1.25), `€825 per server` (B4.5). The bolded-figure convention in
`STYLE.md` §5 is a document rule; it does not appear in his own Slack or email. Where he does bold
in email it is a label, not a number: `*Samenvatting*`, `*Investering*`, `*Belangrijk:*` (B4.1).

---

# Section D — Divergence from agent output

Derived from Section A only, ranked by how often the same edit recurs.

**D1. He cuts the explanation of a fact and keeps the fact.** Recurs in A1.1 (drops `who resell into
the AI labs`), A1.4 (drops `We own the hardware outright; a contracted operator runs the site`),
A2.2 (drops two sentences interpreting the pension foundation), A2.3 (deletes seven closing lines).
His own instruction confirms it as a rule he holds consciously: `Give away the minimum amount of
information only and just a clear short reason` (B5.2).

**D2. He deletes the close.** A1.5 removes `Happy to go deeper once the NDA is signed.` and his own
signature. A2.3 removes every summarising line. Where a close survives in his own writing it is an
offer or a question, never a conclusion (C5).

**D3. He replaces a committing word with an open one.** A1.2, `Low USD 4… fixed for the term` becomes
`Around USD 4 per GPU-hour`. A1.6 shows he applied the same softening to his own spoken phrasing.
Related instruction: `dont speak out on what we prefer, just ack we'll take it into account` (B5.2).

**D4. He breaks one sentence into labelled lines.** A1.4 turns a company-name-as-subject sentence
into a bare header plus a capability line plus a footprint line. A1.7 shows the resulting shape as
he actually sends it.

**D5. He swaps a descriptor we invented for the label the reader's industry already uses.** A1.1,
`US neoclouds, USD 1bn+ scale` becomes `Tier 1 and 2 (US) neoclouds`.

**D6. He replaces an em dash in a greeting with a comma, and adds warmth.** A1.3, `Hi Joseph — good
speaking.` becomes `Hi Joseph, was good meeting you.` The dropped subject in `was good meeting you`
is characteristic (C3).

**D7. He removes instructions to the reader.** A1.3 drops `Short rundown you can forward to Samson.`
Consistent with `MESSAGES.md` §3.4 and with his own habit of ending on a question rather than a
directive (C5).

**D8. Where compression removes an argument, he restores it — but with an operational fact, not a
flourish.** A2.1 and A2.3 both replace a rhetorical line with `All our operations are optimized for
frequent deployments of this size.` This is the one direction in which his edit makes text longer.

---

# Section E — Gaps

Registers with no sample, or too thin a sample, in this corpus.

1. **English long-form prose written by him alone.** The only substantial English business email
   found in 180 days is the Alexander rundown (A1.7), and that is a list plus one paragraph.
   Everything longer in English either passed through an agent or is a Slack briefing. His longest
   self-written prose in the corpus is Dutch (B4.5, B4.6, B4.8). If we need an exemplar of him
   arguing at length in English, we do not have one.

2. **Cold outbound email to a stranger.** B1.3 and B1.4 are cold conference outreach, but he pasted
   them into Slack asking for critique (`feel free to roast`), so they may not represent what he
   actually sent. No sent cold email to a new counterparty was found in `in:sent`.

3. **Investor updates and board email.** These exist as PRs and drafts in the AIC repos but the
   shipped text is agent-drafted and reviewed by him. His contribution is visible only as review
   comments (B1.15, B1.22). We have his edits but not a document he wrote from scratch.

4. **Bad news to an external party in English.** The one clear bad-news message in the corpus is
   Dutch (B4.6, the AtNorth price increase). We have no English equivalent, so the English
   apology/escalation register is unattested.

5. **Anything longer than about 400 words that he typed himself.** The single longest continuous
   thing he wrote unaided is the Wellguard quote update (B4.5), roughly 320 words of Dutch. Every
   longer English artefact in the repos has agent involvement.

6. **Formal or legal register.** He instructs counsel agents (`spin up the reviewer counsel again`)
   but does not write legal prose himself in any sample found.

7. **Public or marketing writing.** No blog post, LinkedIn post, press statement or website copy
   attributable to him was found on the machine.

## Sources unavailable

None. Slack MCP, Gmail MCP and the local filesystem were all reachable. Several other MCP servers
(Notion, Zapier, Evertrace, Off The Radar, Cloudflare) require re-authorisation and were not used;
none of them was expected to hold his prose.
