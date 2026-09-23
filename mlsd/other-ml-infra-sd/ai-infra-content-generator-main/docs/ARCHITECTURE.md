# AICG Runner Architecture

End-to-end view of the AI Infrastructure Curriculum runner: how the
pieces hang together, what fires when, and where data lives.

For day-to-day operations, see [RUNBOOK.md](RUNBOOK.md). For the
autonomous-mode reference, see [AUTONOMOUS_ORG_AUTOMATION.md](AUTONOMOUS_ORG_AUTOMATION.md).

---

## 1. The orchestration loop

The high-level chain: research updates the plan → plan scaffolds
skeletons → audit finds gaps → daily remediate fills them → steward
merges → monthly release tags everything.

```mermaid
flowchart TD
    M["manifest (aicg-org.yaml)<br/>12 roles × 2 repos = 24<br/>+ .github"]
    Sync["aicg org sync<br/>(clone or ff-only every repo)"]
    M --> Sync

    Sync --> Research["org research --apply<br/>(monthly)"]
    Sync --> Audit["org audit<br/>(structural gaps)"]
    Sync --> Boot["bootstrap-role<br/>(new role scaffolding)"]

    Research --> DeltaMerge["delta-merge into<br/>curriculum-plan.json"]
    DeltaMerge --> Exec["execute-plan<br/>(scaffold skeletons)"]
    Exec --> Queue[("work-queue.json")]
    Audit --> Queue
    Boot --> Queue

    Queue --> Daily["org daily<br/>(hourly tick · 1 item / run)"]
    Daily --> Verify["verify (+ judge)"]
    Verify --> Prop["propagate<br/>VERSIONS.md · CURRICULUM.md"]
    Prop --> PR["gh pr create"]
    PR --> Steward["steward --apply<br/>(daily 04:40 · auto-merge)"]
    Steward --> Release["monthly release<br/>v2026.MM tags"]

    Queue -. failed_permanently / stuck .-> Issues["daily-issues<br/>(GitHub issues)"]
    Sync -. read-only sweep .-> Disc["daily-discussions<br/>(report only)"]

    classDef state fill:#fef3c7,stroke:#92400e,color:#451a03
    classDef agent fill:#dbeafe,stroke:#1e3a8a,color:#0c1226
    classDef gh fill:#dcfce7,stroke:#14532d,color:#052e16
    class Queue state
    class Daily,Verify,Research,Exec,Audit agent
    class PR,Steward,Release,Issues,Disc gh
```

---

## 2. Timer cadence

Local time on the SBC is `America/Phoenix` (MST, no DST).

```mermaid
timeline
    title AICG systemd timers (local MST)
    section Hourly
        00:00 → 23:00 : daily-remediate (every hour, on the hour)
    section Daily (early morning)
        04:20 : daily-issues (--apply)
        04:40 : daily-steward (--apply)
        05:00 : daily-discussions (dry-run)
    section Weekly
        Sun 03:00 : weekly-audit (sync + freshness + learning/pairing/curriculum/profile audits + audit)
    section Monthly
        1st 02:00 : monthly-release (sync + release --apply)
    section Quarterly
        Mar/Jun/Sep/Dec 1st 05:30 : monthly-research (writes proposals, opens PRs, NO auto-merge)
        Mar/Jun/Sep/Dec 1st 06:00 : monthly-review (LLM freshness review across all solutions)
    section One-off override
        2026-06-15 02:00 : monthly-release shifted from June 1 to give the cold-start drain runway
```

The freshness audits flow into the work queue alongside structural
gaps. High-severity refresh items (broken security guidance, EOL'd
tools, dead citations) jump above new-content gaps via a priority
bias; medium and low severities sit below structural work and get
worked when the queue is otherwise drained.

---

## 3. `daily-remediate` (hourly) — work-item lifecycle

One ready item per hourly tick. Subscription-limit-aware: deferred
items resume after their `retry_after` timestamp.

```mermaid
flowchart TD
    Timer["systemd timer fires<br/>(every hour)"]
    Lock["acquire lock<br/>.aicg/org/aicg-org.lock"]
    Pick["read work-queue.json<br/>pick highest-priority<br/>ready item"]
    Prompt["write prompt packet<br/>&lt;repo&gt;/.aicg/work-prompts/<br/>&lt;work_id&gt;/prompt.md"]
    Agent["run-claude-content.sh<br/>--permission-mode acceptEdits<br/>--add-dir &lt;repo&gt;<br/>--allowedTools ..."]
    LimitCheck{"subscription<br/>limit hit?"}
    Defer["mark deferred<br/>+ retry_after"]
    Verify["verify contracts:<br/>headings · source policy ·<br/>marker freedom"]
    JudgeCheck{"judge enabled?"}
    Judge["judge (read-only):<br/>score vs threshold"]
    JudgePass{"score ≥ threshold<br/>and no blockers?"}
    Fail["status = verification_failed"]
    Propagate["propagate:<br/>VERSIONS.md row<br/>CURRICULUM.md ship row"]
    PR["gh pr create<br/>+ audit body<br/>+ diff body"]
    UpdateQueue["update work-queue.json<br/>status = verified"]

    Timer --> Lock
    Lock --> Pick
    Pick --> Prompt
    Prompt --> Agent
    Agent --> LimitCheck
    LimitCheck -- yes --> Defer
    LimitCheck -- no --> Verify
    Verify --> JudgeCheck
    JudgeCheck -- no --> Propagate
    JudgeCheck -- yes --> Judge
    Judge --> JudgePass
    JudgePass -- no --> Fail
    JudgePass -- yes --> Propagate
    Propagate --> PR
    PR --> UpdateQueue

    classDef branch fill:#fef3c7,stroke:#92400e
    classDef terminal fill:#fee2e2,stroke:#991b1b
    classDef success fill:#dcfce7,stroke:#14532d
    class LimitCheck,JudgeCheck,JudgePass branch
    class Defer,Fail terminal
    class UpdateQueue success
```

---

## 4. `monthly-research --apply` — proposal-only research loop

Runs the 1st of Mar/Jun/Sep/Dec at 05:30. **The runner never adds
modules, exercises, or projects to the curriculum on its own.** Every
proposal goes through a human-reviewable PR. Caps from the manifest
prevent the agent from drowning the PR with weakly-justified
additions.

```mermaid
flowchart TD
    Tick["timer fires:<br/>Mar/Jun/Sep/Dec 1st, 05:30"]
    Loop["for role in list-roles"]
    WritePrompt[".aicg/org/research/&lt;YYYY-MM&gt;/<br/>&lt;role&gt;.md prompt packet"]
    Agent["run-claude-research.sh<br/>(WebFetch · WebSearch enabled)"]
    Outputs["agent writes 3 files<br/>into the learning repo"]
    JRM["JOB_REQUIREMENTS.md (committed)"]
    JRJ[".aicg/job-requirements.json (committed)"]
    Delta[".aicg/curriculum-plan-delta.json<br/>(transient · raw agent output)"]
    Validate["validate_delta_against_caps()<br/>· evidence ≥ N citations<br/>· max N modules/exercises/projects<br/>· highest-evidence first"]
    Filtered[".aicg/curriculum-plan-delta-filtered.json"]
    Md["RESEARCH_PROPOSAL_&lt;month&gt;.md<br/>(rationale, accepted, rejected)"]
    PR["gh pr create<br/>label: aicg:plan-proposal"]
    Human{"human reviews<br/>and merges PR?"}
    Promote["aicg org promote-plan<br/>(manual or weekly-audit)"]
    Plan["curriculum-plan.json<br/>(merged)"]
    Exec["execute-plan scaffolds<br/>skeletons"]
    Audit["audit picks up new<br/>structural gaps"]
    Discard["PR closed — no change"]

    Tick --> Loop
    Loop --> WritePrompt --> Agent --> Outputs
    Outputs --> JRM
    Outputs --> JRJ
    Outputs --> Delta
    Delta --> Validate
    Validate --> Filtered
    Validate --> Md
    Filtered --> PR
    Md --> PR
    PR --> Human
    Human -- yes --> Promote --> Plan --> Exec --> Audit
    Human -- no --> Discard

    classDef io fill:#dbeafe,stroke:#1e3a8a
    classDef gate fill:#fef3c7,stroke:#92400e
    classDef terminal fill:#fee2e2,stroke:#991b1b
    class JRM,JRJ,Delta,Filtered,Md,Plan io
    class Validate,Human gate
    class Discard terminal
```

---

## 5. State-file data flow

Each target repo has its own gitignored `.aicg/` diary. The runner
itself owns a separate `.aicg/org/` directory that is the single
source of truth for org-wide state.

```mermaid
flowchart LR
    subgraph TargetRepo["per target repo (gitignored .aicg/)"]
        AR["audit-report.json"]
        WP["work-plan.json"]
        RS["run-state.json"]
        VR["verify-report.json"]
        VAL["validation-report.json"]
        PR["propagate-report.json"]
        DR["diff-report.json"]
        Judge["judge/&lt;work_id&gt;/<br/>prompt.md<br/>response.json<br/>raw-output.md"]
        Prompts["work-prompts/<br/>&lt;work_id&gt;/prompt.md"]
        ResearchRuns["research/runs/<br/>&lt;role&gt;/"]
    end

    subgraph LearningRepo["per learning repo (committed)"]
        JRM["JOB_REQUIREMENTS.md"]
        JRJ[".aicg/job-requirements.json"]
        DeltaFile[".aicg/curriculum-plan-delta.json<br/>(transient)"]
        CurricPlan["curriculum-plan.json<br/>(merged, committed)"]
    end

    subgraph OrgState["runner /.aicg/org/  (single source of truth)"]
        WQ[("work-queue.json")]
        IR["issues-report.json"]
        SR["steward-report.json"]
        DiscR["discussions-report.json"]
        MRP["monthly-release-plan.json"]
        RAP["research-apply-report.json"]
        Packets["research/&lt;YYYY-MM&gt;/<br/>&lt;role&gt;.md"]
        LockDir["aicg-org.lock/<br/>(mutex)"]
    end

    subgraph Logs["logs"]
        SysLog["~/.cache/aicg/<br/>&lt;job&gt;.log (systemd)"]
        JobLog["&lt;runner&gt;/.aicg/logs/<br/>&lt;job&gt;-YYYYMMDD.log"]
    end

    AR --> WP --> RS --> VR --> PR
    Packets --> JRM
    Packets --> JRJ
    Packets --> DeltaFile
    DeltaFile --> CurricPlan
    CurricPlan --> WQ
    AR --> WQ

    classDef state fill:#fef3c7,stroke:#92400e,color:#451a03
    classDef committed fill:#dcfce7,stroke:#14532d,color:#052e16
    classDef logs fill:#e0e7ff,stroke:#3730a3,color:#1e1b4b
    class WQ,IR,SR,DiscR,MRP,RAP,Packets,LockDir,AR,WP,RS,VR,VAL,PR,DR,Judge,Prompts,ResearchRuns,DeltaFile state
    class JRM,JRJ,CurricPlan committed
    class SysLog,JobLog logs
```

---

## 6. External service surface

The runner has exactly three external dependencies. Everything else is
on-disk file manipulation.

```mermaid
flowchart LR
    subgraph AICG["AICG runner"]
        ContentWrap["run-claude-content.sh"]
        ResearchWrap["run-claude-research.sh"]
        JudgeWrap["run-claude-judge.sh"]
        CodexWrap["run-codex-control.sh"]
        Git["git<br/>(insteadOf rewrite:<br/>git@ → https://)"]
        Gh["gh CLI<br/>(keyring token)"]
    end

    subgraph Claude["Claude (OAuth subscription)"]
        ClaudeAPI["~/.claude/<br/>.credentials.json"]
    end

    subgraph Codex["Codex (OAuth subscription)"]
        CodexAPI["~/.codex/auth.json"]
    end

    subgraph GitHub["GitHub API"]
        Issues["Issues / Comments"]
        PRs["PRs / merge --auto"]
        GraphQL["Discussions GraphQL"]
        Tags["Tags / Releases"]
        HTTPS["HTTPS clone / push"]
    end

    ContentWrap --> ClaudeAPI
    ResearchWrap --> ClaudeAPI
    JudgeWrap --> ClaudeAPI
    CodexWrap --> CodexAPI

    Gh --> Issues
    Gh --> PRs
    Gh --> GraphQL
    Gh --> Tags
    Git --> HTTPS

    Issues -. used by .-> DI["daily-issues"]
    PRs -. used by .-> DS["daily-steward"]
    GraphQL -. used by .-> DD["daily-discussions"]
    Tags -. used by .-> MR["monthly-release"]
    HTTPS -. used by .-> Sync["org sync"]
    HTTPS -. used by .-> Propagate["propagate / commit"]

    classDef wrap fill:#dbeafe,stroke:#1e3a8a
    classDef ext fill:#fef3c7,stroke:#92400e
    classDef cred fill:#fee2e2,stroke:#991b1b
    class ContentWrap,ResearchWrap,JudgeWrap,CodexWrap,Git,Gh wrap
    class Issues,PRs,GraphQL,Tags,HTTPS ext
    class ClaudeAPI,CodexAPI cred
```

---

## Permission boundaries (what the runner refuses to do autonomously)

| Surface | Allowed | Refused |
|---|---|---|
| Target repo files | `Read`, `Edit`, `Write`, `Glob`, `Grep` | anything outside `--add-dir` |
| Bash in agent | `mkdir`, `ls`, `cat`, `git status`, `git diff` | everything else |
| `CURRICULUM.md` / `README.md` | Append rows to `## Shipped (autonomous)` section in CURRICULUM.md only | Direct edits anywhere else |
| `VERSIONS.md` | Append rows under current month heading | Modify historical rows |
| `curriculum-plan.json` | Additive delta merge (new modules/exercises/projects) | Remove or modify existing items |
| GitHub Discussions | Read via GraphQL | Comments, resolutions |
| Git | `clone`, `pull --ff-only`, `commit`, `push origin <branch>`, `tag` | `push --force`, `reset --hard`, `--no-verify`, branch deletion |
| Judge agent | `Read`, `Glob`, `Grep` | `Edit`, `Write` (explicitly denied) |

The runner never uses `--dangerously-skip-permissions` / `--dangerously-bypass-approvals-and-sandbox`.

---

## Failure modes and recovery

| Symptom | Cause | Recovery |
|---|---|---|
| Item stays `deferred` indefinitely | Claude subscription weekly cap hit | Wait for `retry_after`; next hourly tick resumes automatically |
| Item flips to `failed_permanently` after retries | Opaque agent error N times | `daily-issues` opens a GitHub issue with the work_id; human triage |
| `verification_failed` | Contract violation (missing heading, leaked marker, etc.) | Issue auto-opened; fix the prompt or work plan, mark item `ready` |
| Steward sees `ci_failed` | Tests broke from generated content | PR sits open; human investigates; once fixed, next steward tick merges |
| Curriculum-plan-delta merge fails | Malformed JSON from research agent | Reported in `research-apply-report.json`; plan file untouched |
| Two job-script runs collide | systemd timer overlap | Second run sees `.aicg/org/aicg-org.lock/` and exits 0 |
| PR sits in `review_blocked` after 3 auto-respond attempts | Reviewer keeps requesting changes the agent can't satisfy | Item flips to `escalated`; `daily-issues` opens an `aicg:escalated-pr-response` issue with the blocker list |

---

## PR-response loop

`daily-steward` doesn't just poll CI. After CI passes + guardrails clear,
it fetches reviews and review threads via `gh api graphql` and blocks
auto-merge on:

- A review in `CHANGES_REQUESTED` state (human or bot)
- An unresolved, non-outdated review thread (human or bot)

Blocked PRs become `respond_pr_review` work items in
`.aicg/org/pr-response-queue.json`. The next `daily-remediate` tick
picks them up at priority bias **-200000** (jumps every other type),
checks out the PR branch, invokes the agent with the full blocker list,
and pushes follow-up commits to the same branch.

The next steward pass re-checks. Bot threads typically self-resolve
when the underlying metric recovers (codecov stops complaining); human
review threads stay open until a human resolves them — the runner
never marks human threads resolved.

After **3 failed response attempts** for the same blocker signature,
the item becomes `escalated` and `daily-issues` opens an
`aicg:escalated-pr-response` issue so a human can step in.

```mermaid
flowchart TD
    Steward["daily-steward 04:40 MST"]
    CI{"CI green?"}
    Guard{"guardrails ok?"}
    ReviewFetch["fetch_review_state via gh graphql"]
    Classify{"CHANGES_REQUESTED<br/>or unresolved<br/>threads?"}
    Merge["gh pr merge --auto --squash"]
    Queue[("pr-response-queue.json")]
    Cap{"response_count<br/>>= 3?"}
    Daily["daily-remediate (next tick)<br/>checkout PR branch<br/>+ agent + push"]
    Escalated["status = escalated"]
    Issues["daily-issues opens<br/>aicg:escalated-pr-response"]

    Steward --> CI
    CI -- no --> Stop1["ci_failed / ci_pending"]
    CI -- yes --> Guard
    Guard -- no --> Stop2["guardrails_blocked"]
    Guard -- yes --> ReviewFetch
    ReviewFetch --> Classify
    Classify -- no --> Merge
    Classify -- yes --> Cap
    Cap -- no --> Queue --> Daily --> Steward
    Cap -- yes --> Escalated --> Issues

    classDef terminal fill:#fee2e2,stroke:#991b1b
    classDef ok fill:#dcfce7,stroke:#14532d
    class Stop1,Stop2,Escalated terminal
    class Merge ok
```

---

## Related docs

- [RUNBOOK.md](RUNBOOK.md) — operator playbook (one-page how-to)
- [AUTONOMOUS_ORG_AUTOMATION.md](AUTONOMOUS_ORG_AUTOMATION.md) — autonomous-mode reference
- `config/aicg-org.yaml` — single-source-of-truth manifest
- `scripts/install-schedules.sh` — timer installer
- `scripts/aicg-org-job.sh` — job wrapper invoked by every timer
