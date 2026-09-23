# SOLUTION — IaC and GitOps

> Read this *after* you have stood up the GitOps reference. This
> document explains *why* the GitOps patterns are what they are.

## What this module is really teaching

GitOps is the discipline of making Git the single source of
truth for desired cluster state. Done right, it eliminates an
entire class of incidents (manual changes, drift, ad-hoc
rollbacks). Done wrong, it adds layers of indirection without
solving the underlying problem.

## Architectural decisions and *why*

### Decision 1: Argo CD over Flux

The reference uses Argo CD. Both are mature; Argo CD's UI is
better, ecosystem larger, and ApplicationSet pattern more
flexible. Flux's CLI-only operation is sometimes preferred by
ops-heavy teams.

### Decision 2: App-of-apps for cluster bootstrapping

Cluster bootstrap is itself an Argo CD Application that points
at a Git repo of additional Applications. The reason: this
makes the cluster's entire desired state captured in one repo
ref. Recreating the cluster reduces to "deploy Argo CD; apply
root Application."

### Decision 3: Helm for templating, Kustomize for overlays

The reference uses Helm for parameterized application templates
and Kustomize for environment-specific overlays. The reason:
each tool fits its job. Helm-only deployments end up with
massive ``values.yaml`` files; Kustomize-only deployments
struggle with conditional logic.

### Decision 4: Sealed-secrets / external-secrets for secret
management

Secrets never live in plain Git. The reference uses Sealed
Secrets (encrypted at rest, decrypted by an in-cluster
controller) for self-contained deploys, and External Secrets
Operator (pulls from Vault / AWS Secrets Manager) for shared
secret stores.

The reason: storing secrets in git, even private repos, is the
single biggest violation of "Git is the source of truth"
hygiene. The encrypted-at-rest pattern keeps the source-of-truth
property while not leaking secrets.

### Decision 5: Pull-based deployment, not push

Argo CD pulls desired state from Git; CI does not push to the
cluster. The reason: pull-based deploys mean CI doesn't need
cluster credentials. This dramatically reduces the blast radius
of a compromised CI runner.

### Decision 6: Sync-waves for ordered deployment

Argo CD's sync-waves let related resources deploy in order
(CRDs first, then operators, then custom resources). The
reference uses this rather than splitting into multiple
Applications.

## Trade-offs we deliberately accepted

### Argo CD adds a control-plane dependency

If Argo CD is down, deploys stop. The reference HAs Argo CD
itself and treats its uptime as a SEV1 dependency.

### Helm + Kustomize learning curve

Two templating systems is more to learn than one. The
combined power is worth it, but it's real complexity.

### Git history as audit log

Audit-quality git history requires discipline (signed commits,
no force-pushes to main, branch protection). The reference
documents the required policies.

## Common mistakes graders see

1. **Cluster changes made via kubectl**: drift accumulates;
   Argo CD's "OutOfSync" status becomes noise.
2. **Auto-sync enabled with manual approval missing for prod**:
   PRs go straight to production. Disable auto-sync for prod
   and require manual sync.
3. **Long-running Helm templates not refactored to Kustomize
   bases**: one mega-chart that becomes unmaintainable.
4. **Secret values committed to git "temporarily"**: the
   commit remains in history forever.
5. **No drift detection alerting**: drift exists but nobody
   notices. Alert on "OutOfSync" duration.

## When to go beyond this implementation

- Adopt **ApplicationSet** for multi-cluster fleet management.
- Move to **Crossplane** if you want to manage cloud resources
  with the same GitOps tooling.
- Add **policy-as-code** enforcement (Kyverno) so admission
  control mirrors GitOps's desired state.

## Related curriculum touchpoints

- ``engineer/mod-109-infrastructure-as-code`` — Terraform
  foundations.
- ``senior-engineer/mod-201-advanced-kubernetes`` — the
  cluster-level resources GitOps manages.
- ``ml-platform/mod-001-platform-fundamentals`` — platform-
  level GitOps patterns.
