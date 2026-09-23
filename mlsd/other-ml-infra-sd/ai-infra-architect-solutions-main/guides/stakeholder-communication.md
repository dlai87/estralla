# Stakeholder Communication Guide

> Companion to `architecture-patterns.md` and `enterprise-standards.md`. How a senior architect communicates with non-engineering stakeholders so that technical decisions get the air cover they need.

---

## What this guide is

A staff/principal/distinguished architect's effectiveness is often capped by communication, not by technical depth. The technical content has to land with audiences that don't share your context — finance, legal, security review boards, regulators, executives, customers — or it doesn't get funded, doesn't get approved, doesn't get used.

This guide is the field manual for that work. Audiences, formats, anti-patterns, and a small reusable kit.

---

## The audiences

Different audiences read the same artifact differently. The same architecture proposal, served to all of them as a 30-page deep-dive, will be skimmed by most and dismissed by some.

| Audience | What they care about | How they read |
|---|---|---|
| **Executive sponsor (SVP+)** | Outcome, risk, narrative arc | One page; then questions |
| **Finance / CFO partner** | $ in, $ out, when, certainty range | Numbers; sensitivities; assumptions explicit |
| **Legal / privacy counsel** | Liability exposure, regulatory fit, data handling | Specific clauses; explicit attestations |
| **Security review board** | Threat model, controls, residual risk | Threat → control → evidence chain |
| **Product partner** | Impact on roadmap, time-to-market, dependencies | Timeline, gates, what they get when |
| **Engineering peer** | Trade-offs, alternatives, hidden complexity | Architecture diagrams; failure modes; ADRs |
| **Customer-facing team** | What changes for customers, when, what to say | Comms timeline, key messages, FAQ |
| **Regulator** | Compliance with specific rule, documented evidence | Mapping table; evidence catalog |

For any cross-functional proposal, ask which audiences need to engage. Each audience needs its own artifact (or its own section of the consolidated artifact). One-document-fits-all proposals get nodded through without anyone really reading them, then fail in the implementation phase.

---

## The reusable kit

A small set of artifacts that get re-used across most cross-functional decisions:

### 1. The one-page brief

For any decision worth socializing, write a one-pager. Six sections, ~150 words each:

1. **TL;DR** (3 sentences). What we're proposing, why, what we need from the reader.
2. **Context** (1 paragraph). What's the problem; what's the world today; why now.
3. **Proposal** (1 paragraph). The actual recommendation.
4. **Trade-offs** (3 bullets). What we give up; what we accept as risk.
5. **What we need** (1 paragraph). Approval, budget, headcount, decision by when.
6. **References** (3 links). The deep-dive doc, the ADR, the cost model.

The one-pager is the artifact that 80% of stakeholders read. Spending hours polishing it is high-leverage; spending hours polishing the 30-page deep-dive that 20% will read is lower-leverage.

### 2. The decision memo

When a one-pager isn't enough — typically for decisions involving multi-quarter investment or significant risk — write a 3-5 page decision memo:

1. **Decision summary** (one-page brief, condensed)
2. **Options considered** (table: option, cost, time, risk, recommendation)
3. **Recommendation rationale** (why the chosen option beats the alternatives)
4. **Implementation summary** (phases, milestones, key dependencies)
5. **Risks + mitigations** (top 5 with leading indicators)
6. **What we want from the reviewer** (specific asks)

Decision memos are read once, archived, and become the institutional memory of "why did we choose X?" Two years later, when someone asks, the memo is the answer.

### 3. The architecture deep-dive

Reserve for technical audiences (engineering peers, security review board, sometimes regulators). Length 15-50 pages depending on scope. Standard structure: context, drivers, high-level architecture (Mermaid + prose), per-component detail, cross-cutting concerns, trade-offs, alternatives, roadmap, validation criteria. (This guide's repo has examples in `architecture-patterns.md` and the per-project `ARCHITECTURE.md` files.)

### 4. The threat model

Specific format for security audiences. STRIDE (Spoofing, Tampering, Repudiation, Information Disclosure, DoS, Elevation of Privilege) per component, with controls and residual-risk per threat. Templates available from Microsoft Threat Modeling Tool, OWASP, or roll your own — consistency matters more than format.

### 5. The compliance mapping

For regulator-facing or audit-prep: a two-column table. Left column: each regulatory clause applicable. Right column: how we satisfy it (control, evidence). Auditors live in this format. Make their job easy; they'll be friendlier.

### 6. The cost model

Spreadsheet (or repo-versioned CSV). Inputs sheet: assumptions. Calc sheet: math. Output sheet: summary table. Three scenarios: pessimistic, base, optimistic. Make sensitivities visible. Don't bury the assumptions on a hidden tab.

### 7. The comms plan

For changes that affect customers or other teams: who hears what, in what order, when. Three-column table: audience, message, channel + timing. Coordinated with comms / PR for external-facing changes.

---

## Format-by-audience cheat sheet

```text
Executive sponsor:    One-page brief + 30-min Q&A.
                       Never lead with a deck > 5 slides.

CFO partner:          Decision memo + cost model.
                       Walk through the spreadsheet live; let them
                       interrogate the assumptions.

Legal counsel:        Compliance mapping + threat model.
                       Give them the specific regulatory clauses
                       in their language, not yours.

Security board:       Threat model + architecture deep-dive section
                       on security.
                       Pre-meeting: send the materials 5 days ahead.

Product partner:      Decision memo + a simple Gantt-style timeline.
                       Show them gates and what they get at each gate.

Engineering peer:     Deep-dive + ADRs.
                       Open a draft; ask for inline comments.

Customer team:        Comms plan + FAQ.
                       Workshop the FAQ live with the team that will
                       answer the questions.

Regulator:            Compliance mapping + audit evidence package.
                       Boring is good. Specific clause numbers,
                       direct quotes, dated artifacts.
```

---

## Patterns that work

### Lead with the ask, not the context

Most engineering communication leads with context ("we noticed X about the system"). Executive communication leads with the ask ("we recommend approving Y; specifically we need decision A and budget B by date C"). The context follows.

Reason: the executive's first question is "what do you want from me?" If they have to wait 4 paragraphs to find out, attention has drifted.

### Use specific numbers, not adjectives

"This will save significant cost" tells the reader nothing. "$2.4M annually, with $4.1M payback in 16 months" tells them everything they need to evaluate. Always include the number. If you don't have the number, say so explicitly: "We estimate $2-5M; we'll have a tighter estimate after the Q2 pilot."

### Anchor on outcomes, not activities

"We will refactor the auth subsystem" is an activity. "We will reduce auth-related incidents by 50% over six months" is an outcome. Outcomes get funded; activities get questioned.

### Pre-wire major decisions

Don't bring a major proposal to a steering committee cold. Pre-wire it: 1:1 with each voting member ahead of the meeting, share the proposal, gather concerns, address them in the deck or in a private follow-up. The meeting itself should ratify a decision the members already understand.

This is true even when (especially when) the audience is friendly. Cold reveals to executives produce reactive decisions; pre-wired reveals produce considered decisions.

### Make objections cheap to raise

A proposal whose author defends every objection produces an audience that learns not to object. A proposal whose author thanks objectors and integrates the concerns produces better proposals.

In writing: "Concerns raised by [reviewer], and our response" is a section heading worth having. In meetings: "I want to hear what worries you about this" is an opening worth practicing.

### Bring bad news early

Schedules slip. Estimates were wrong. The pilot didn't work. The moment you know, brief the relevant stakeholders. The reputational cost of bad news delivered early is small; the reputational cost of bad news the stakeholder learns through a third channel is enormous.

---

## Anti-patterns

### Death by deck

The 80-slide deck delivered live to a sponsor. They check out by slide 12. The decision gets deferred for "review" that never happens.

Fix: lead with the one-pager. The deck is the backup material for questions, not the primary artifact.

### Status theater

A weekly "status update" that's actually a re-statement of the project plan, with no new information. Stakeholders learn to ignore the cadence.

Fix: status updates are signal, not noise. If nothing material has changed, send a one-line update ("on track; no change; next milestone Q2"). Reserve the long format for actual decisions and actual risk changes.

### Jargon as gatekeeping

Using technical vocabulary as a barrier to discussion. "Well, you wouldn't understand without knowing about Byzantine consensus..." Stakeholders disengage and decisions get made by other means.

Fix: explain to a smart non-specialist. If you can't, you don't understand it well enough yet. Specific technique: write a one-paragraph explanation aimed at your spouse / parent / friend without context. If it's coherent, you've cleared the bar.

### Asymmetric disclosure

Telling each audience a different story. Engineering hears "we're investing for the long term"; finance hears "we'll cut $5M next year"; security hears "we'll deliver everything they asked for." When stakeholders compare notes, trust collapses.

Fix: tell the same story to everyone, in their preferred format. The numbers, the timeline, the dependencies should be identical across audiences.

### Burying the decision

A 20-page memo where the actual decision is on page 14, three paragraphs deep into a sub-section. The decision gets missed; later, the absence of explicit approval is litigated.

Fix: surface the decision in the TL;DR. Bold it. Include a callout box. Make the decision impossible to miss.

### Hiding behind data

"The data shows X" — but the data is one source, lightly contextualized, presented as if it were the only data. Sophisticated audiences notice.

Fix: be explicit about source, methodology, limitations. "Based on Q3 incident data from the on-call rotation, with the caveat that incident definitions changed in August..." earns more trust than "the data shows."

---

## A small worked example

A platform team wants $1.8M and two new headcount to consolidate from three observability vendors to one.

**Bad version (engineering instinct):**

> *Slide 1 of 22:* "Observability Vendor Consolidation Project"
> *Slide 2-8:* current state diagrams
> *Slide 9-15:* technical comparison of vendors
> *Slide 16:* recommendation
> *Slide 17-22:* implementation plan

The sponsor will read slide 1, skim 16, and ask "how much?" Discussion never gets to the actual decision because there's no narrative arc.

**Better version:**

One-pager:

> **TL;DR.** We recommend consolidating from 3 observability vendors to 1 (Vendor A). Saves $2.4M/year steady-state for a $1.8M up-front investment; payback in 9 months. We need approval for the budget and 2 FTEs by end of Q1 to start in Q2.
>
> **Context.** We currently pay $4.1M/year across three observability products. The overlap is significant; teams report the multi-tool experience is the #2 reason for slow incident resolution.
>
> **Proposal.** Migrate all teams to Vendor A over 9 months. Existing vendor contracts terminate at end-of-contract (Q1 and Q3 next year). One platform team owns the migration; product teams self-serve via paved roads.
>
> **Trade-offs.** Vendor A's tracing is weaker than our current tracing tool; we'll fill the gap with OpenTelemetry + a self-hosted Jaeger. One-time migration cost ($1.8M); migration risk during the 9-month transition.
>
> **What we need.** $1.8M budget approval. 2 net new FTEs (platform engineer + program manager). Sponsor approval to begin migration in Q2.
>
> **References.** Decision memo `docs/decisions/observability-consolidation.md` &middot; ADR `docs/adrs/ADR-042-observability-vendor.md` &middot; Cost model `models/observability-consolidation.xlsx`

That's the artifact that gets the decision made. The 22-slide deck is the backup material for the questions that come up after.

---

## Closing note

Communication is leverage. A well-communicated proposal that's 80% technically right beats a poorly-communicated proposal that's 100% right. This isn't because communication is more important than substance — it's because communication is the path through which substance reaches the people who can act on it.

Invest in the kit. Re-use it. The first decision memo you write takes a week; the tenth takes an afternoon, and it's twice as good as the first.

---

## See also

- [`architecture-patterns.md`](./architecture-patterns.md) — the technical patterns that get communicated
- [`enterprise-standards.md`](./enterprise-standards.md) — standards governance, which lives or dies on stakeholder management
- [`cost-benefit-analysis.md`](./cost-benefit-analysis.md) — the financial language stakeholders speak
