# SOLUTION_OVERVIEW — Principal Architect Track

> Read this *after* you have skimmed the module solutions. This file
> explains the design philosophy across the principal-architect track
> and how to read the deliverables, which are unlike the deliverables
> in any other track.

## What this track is *not*

Not engineering. Not even senior architecture. A principal-architect
solution is unlikely to contain runnable code; it is much more likely
to contain a multi-quarter investment thesis with measurable success
criteria, a stakeholder coalition plan, and an industry-standards
position.

If you came here expecting Terraform modules, you are in the wrong
repo. The architect (`ai-infra-architect-solutions`) and senior
architect (`ai-infra-senior-architect-solutions`) tracks are heavier
on technical artifacts.

## What this track *is*

Five disciplines a principal architect applies at org / industry scale:

| Module | Discipline |
|---|---|
| `mod-601-org-wide-architecture` | Architecture that survives across business units and through reorganizations. |
| `mod-602-industry-standards` | Engaging with — and shaping — standards bodies, open-source consortia, regulatory dialogue. |
| `mod-603-multi-year-investment` | Capital-allocation reasoning for technology investments with 3–10 year arcs. |
| `mod-604-stakeholder-coalition` | Building and sustaining the cross-functional coalitions that turn strategy into adoption. |
| `mod-605-tech-debt-modernization` | Sequencing the modernization of legacy systems without crashing the business. |

These are **negotiated**, not **implemented**. The solutions are
templates for documents and decisions, not algorithms.

## How a "solution" looks in this track

A principal-architect solution typically contains:

- **A strategic position document** — what we believe and why.
- **A decision rationale** — the reasoning behind a multi-year bet.
- **An influence plan** — who must be convinced, in what order, with
  what argument.
- **A failure-mode analysis** — what kills this strategy and how we
  would notice.
- **A success-criteria scorecard** — measurable outcomes with named
  owners.

## How to read this track

### If you aspire to this role

Read in module order, but spend the most time in `mod-603` and
`mod-604`. Multi-year investment reasoning and coalition-building are
the highest-leverage skills and the ones least practiced in
lower-level roles.

### If you are already a principal architect

Skim and steal the templates. Note the *anti-pattern* sections — most
of the value in these solutions is in what *not* to do.

### If you are an executive evaluating "do we need a principal
architect?"

Read `mod-601-org-wide-architecture` and `mod-603-multi-year-investment`.
If your org has neither of those disciplines staffed elsewhere, you
need a principal architect — and probably needed one a year ago.

## Cross-cutting principles

### Strategy is what survives stakeholder rotation

A strategy that depends on a specific executive sponsor is not a
strategy; it is a project. Principal-architect deliverables are
written to outlive the people who commissioned them.

### Standards engagement is leverage, not vanity

Influencing industry standards (CNCF, MLCommons, NIST AI RMF) shifts
the playing field for every competitor. Done well, this is force
multiplication; done poorly, it is engineering theater.

### Tech-debt modernization is sequenced by *blast radius*

The principal architect's job in modernization is not "rip and
replace"; it is *sequencing* — what can change first because it
fails small, what must change later because it fails large.

### Capital allocation under deep uncertainty

A 5-year technology bet has a return that is not even
distributionally knowable. The deliverables in `mod-603` show how to
reason about such bets without false precision — and how to defend
the reasoning to a CFO.

## What's deliberately *not* in this repo

- **Detailed system architectures** — those live in the architect
  and senior-architect tracks.
- **Vendor-specific tool selections** — pinned bets at this level have
  a poor track record.
- **Universal answers** — the worked examples illustrate methodology.
  Applying them to a different context will rightly arrive at
  different conclusions.

## Cross-references

| Topic | Deeper reference |
|---|---|
| System-level architecture | `architect-solutions/projects/project-301/SOLUTION.md` |
| Executive-grade transformation strategy | `senior-architect-solutions/projects/project-401-transformation-strategy/SOLUTION.md` |
| Cross-org technical leadership | `principal-engineer-solutions/SOLUTION_OVERVIEW.md` |
| Team-level execution patterns | `team-lead-solutions/SOLUTION_OVERVIEW.md` |

## Time budget for the track

- **Surveyor read**: 1–2 weeks.
- **Practitioner read**: continuous — these are career-arc
  disciplines, not coursework. Re-read every 12–18 months as your
  context evolves.
