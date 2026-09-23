# ADR-010: ML Governance Framework Design

**Status**: Accepted
**Date**: 2024-10-20
**Decision Makers**: Principal Architect, CTO, Chief Compliance Officer, VP Engineering
**Stakeholders**: Data Science Teams, ML Platform Team, Legal, Security, Audit, Executive Leadership

## Context

Our enterprise MLOps platform needs comprehensive governance to:
- Ensure models are safe, fair, and compliant before production deployment
- Meet regulatory requirements (SOC2, HIPAA, GDPR, EU AI Act)
- Manage risk of deploying ML models at scale (500+ models)
- Balance speed (enable data scientists) with safety (protect company/customers)
- Provide audit trails for compliance and incident investigation

### Current State

**Governance Gaps**:
- No formal approval process for model deployment
- Models deployed to production without review
- No bias or fairness testing
- Limited model documentation
- No audit trail of who deployed what
- Unclear ownership and accountability

**Recent Incidents**:
- Model deployed with 15% accuracy drop (not caught)
- Biased model caused customer complaints
- Unable to explain model decision for regulatory audit
- Model using outdated/incorrect data (training-serving skew)

**Regulatory Pressure**:
- SOC2 audit identified 12 control gaps
- HIPAA compliance requires model governance
- EU AI Act may classify some models as "high-risk"
- Potential fines: $10M+ for violations

### Forces

- **Speed vs Safety**: Data scientists want to move fast, compliance wants thorough review
- **Scale**: 500+ models by Year 3, can't manually review every change
- **Risk Variability**: Different models have different risk levels
- **Team Autonomy**: Teams want independence, governance requires centralization
- **Cost**: Heavy governance processes expensive ($2M+ fully manual)

## Decision

We will implement a **Risk-Based, Automated Governance Framework** with human oversight for high-risk models.

### Governance Philosophy

**Principles**:
1. **Risk-Proportionate**: Governance rigor matches model risk level
2. **Automated First**: Automate checks where possible, human review for exceptions
3. **Continuous**: Governance applies throughout model lifecycle (not just deployment)
4. **Transparent**: Clear policies, documented decisions, audit trails
5. **Enabling**: Help teams succeed, not block progress

### Risk-Based Classification

```
┌────────────────────────────────────────────────────────────┐
│           ML Model Risk Classification                      │
├────────────────────────────────────────────────────────────┤
│                                                              │
│  Risk Factors (each scored 1-5):                            │
│  1. Data Sensitivity (public, confidential, PII, PHI)       │
│  2. Decision Impact (informational, operational, critical)  │
│  3. Financial Impact (<$100K, $100K-1M, >$1M annually)     │
│  4. Regulatory Scope (none, SOC2, HIPAA, PCI, EU AI Act)  │
│  5. Reversibility (easy rollback, moderate, irreversible)   │
│  6. Scale (users affected: <1K, 1K-100K, >100K)            │
│                                                              │
│  Total Score → Risk Classification:                         │
│                                                              │
│  ┌──────────────────────────────────────────────────┐      │
│  │  LOW RISK (Score: 6-12)                          │      │
│  │  Examples:                                        │      │
│  │  - Internal analytics dashboards                │      │
│  │  - Experimental features (<1% users)            │      │
│  │  - Non-customer-facing tools                    │      │
│  │                                                   │      │
│  │  Governance: ✅ Automated approval               │      │
│  │  - Automated checks (performance, schema)        │      │
│  │  - Self-service deployment                       │      │
│  │  - Post-deployment monitoring                    │      │
│  │  Time to production: <1 day                     │      │
│  └──────────────────────────────────────────────────┘      │
│                                                              │
│  ┌──────────────────────────────────────────────────┐      │
│  │  MEDIUM RISK (Score: 13-22)                      │      │
│  │  Examples:                                        │      │
│  │  - Product recommendations                       │      │
│  │  - Search ranking                                │      │
│  │  - Content moderation (non-critical)            │      │
│  │                                                   │      │
│  │  Governance: 👤 ML Engineer review               │      │
│  │  - Automated checks +                            │      │
│  │  - ML Engineer approval (performance review)     │      │
│  │  - Model card required                           │      │
│  │  - Bias testing                                  │      │
│  │  Time to production: 1-3 days                   │      │
│  └──────────────────────────────────────────────────┘      │
│                                                              │
│  ┌──────────────────────────────────────────────────┐      │
│  │  HIGH RISK (Score: 23-30)                        │      │
│  │  Examples:                                        │      │
│  │  - Fraud detection                               │      │
│  │  - Credit scoring                                │      │
│  │  - Healthcare diagnosis support                 │      │
│  │  - Automated decision-making                    │      │
│  │                                                   │      │
│  │  Governance: 👥 Multi-level review               │      │
│  │  - Automated checks +                            │      │
│  │  - ML Engineer approval +                        │      │
│  │  - Model Owner (Sr. DS) approval +              │      │
│  │  - Compliance review +                           │      │
│  │  - Comprehensive model card                      │      │
│  │  - Bias audit                                    │      │
│  │  - Explainability analysis                       │      │
│  │  - Legal review (if regulated)                   │      │
│  │  Time to production: 1-2 weeks                  │      │
│  └──────────────────────────────────────────────────┘      │
│                                                              │
└────────────────────────────────────────────────────────────┘
```

### Governance Stages (Model Lifecycle)

```
┌────────────────────────────────────────────────────────────┐
│              Model Lifecycle Governance                      │
├────────────────────────────────────────────────────────────┤
│                                                              │
│  Stage 1: Development                                        │
│  ┌────────────────────────────────────────────────────┐   │
│  │ - Data lineage tracking (training data recorded)    │   │
│  │ - Experiment logging (MLflow tracking)             │   │
│  │ - Code review (if model code)                      │   │
│  │ - Security scan (dependencies, vulnerabilities)    │   │
│  └────────────────────────────────────────────────────┘   │
│                           │                                  │
│                           ▼                                  │
│  Stage 2: Validation                                        │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Automated Checks (all models):                     │   │
│  │ ✓ Performance > baseline (+/- 5% acceptable)       │   │
│  │ ✓ Schema validation (input/output types)           │   │
│  │ ✓ Unit tests passing (100% pass rate)             │   │
│  │ ✓ Integration tests (for deployable models)        │   │
│  │ ✓ Bias metrics (if applicable)                     │   │
│  │ ✓ Data drift detection                             │   │
│  │ ✓ Model size & latency (within limits)            │   │
│  │                                                      │   │
│  │ Manual Checks (medium/high risk):                  │   │
│  │ 👤 Code review by ML Engineer                      │   │
│  │ 👤 Performance review (is improvement real?)       │   │
│  │ 👤 Model card review (documentation complete?)     │   │
│  └────────────────────────────────────────────────────┘   │
│                           │                                  │
│                           ▼                                  │
│  Stage 3: Pre-Deployment Approval                          │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Low Risk: ✅ Auto-approve (if checks pass)         │   │
│  │                                                      │   │
│  │ Medium Risk: Approval workflow                     │   │
│  │ 1. ML Engineer reviews and approves               │   │
│  │                                                      │   │
│  │ High Risk: Multi-stage approval                    │   │
│  │ 1. ML Engineer reviews                             │   │
│  │ 2. Model Owner (Senior DS) approves               │   │
│  │ 3. Compliance review (if regulated domain)         │   │
│  │ 4. Legal review (if high regulatory risk)          │   │
│  │                                                      │   │
│  │ SLA: 24 hours for medium, 5 days for high         │   │
│  └────────────────────────────────────────────────────┘   │
│                           │                                  │
│                           ▼                                  │
│  Stage 4: Deployment                                        │
│  ┌────────────────────────────────────────────────────┐   │
│  │ - Canary deployment (5% → 50% → 100%)             │   │
│  │ - Health checks (latency, error rate)              │   │
│  │ - Automated rollback (if metrics degrade)          │   │
│  │ - Deployment logged (who, what, when, why)        │   │
│  └────────────────────────────────────────────────────┘   │
│                           │                                  │
│                           ▼                                  │
│  Stage 5: Monitoring & Re-validation                       │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Continuous Monitoring:                              │   │
│  │ - Performance metrics (accuracy, latency)          │   │
│  │ - Data drift (input distribution changes)          │   │
│  │ - Prediction drift (output distribution)           │   │
│  │ - Fairness metrics (ongoing bias monitoring)       │   │
│  │                                                      │   │
│  │ Re-validation Triggers:                            │   │
│  │ - Performance drop >5%                             │   │
│  │ - Significant data drift detected                  │   │
│  │ - Quarterly scheduled review (high-risk models)    │   │
│  │ - Regulatory changes                               │   │
│  │                                                      │   │
│  │ Action: Re-approval required if issues detected    │   │
│  └────────────────────────────────────────────────────┘   │
│                                                              │
└────────────────────────────────────────────────────────────┘
```

### Automated Checks (Applied to All Models)

**1. Performance Validation**
- Metrics > baseline (configurable threshold, default: -5%)
- Metrics calculated on holdout test set
- Multiple metrics: accuracy, precision, recall, F1, AUC, etc.

**2. Schema Validation**
- Input/output schemas match expected
- Data types correct
- Required fields present
- Value ranges within bounds

**3. Bias & Fairness (if applicable)**
- Demographic parity (for protected attributes)
- Equal opportunity
- Equalized odds
- Disparate impact <1.25
- Threshold: Fails if bias metrics outside policy

**4. Data Quality**
- Training data lineage complete
- No PII in model artifacts
- Data quality checks passed
- Feature importance analyzed

**5. Security**
- Dependency scan (no critical vulnerabilities)
- Model artifact scan (no malicious code)
- Secrets not embedded in model

**6. Testing**
- Unit tests: 100% pass
- Integration tests: 100% pass
- Performance tests: Within latency/throughput limits

### Model Card (Documentation)

**Required for Medium/High Risk Models**:

**Section 1: Model Details**
- Model type, framework, version
- Training date, re-training frequency
- Owner (team and individual)
- Contact information

**Section 2: Intended Use**
- Primary use case
- Out-of-scope uses
- Target users/audience

**Section 3: Factors (if applicable)**
- Relevant demographic factors
- Environmental factors
- Instrumentation details

**Section 4: Metrics**
- Performance metrics (test set)
- Fairness metrics (by demographic)
- Decision thresholds
- Confidence intervals

**Section 5: Training Data**
- Datasets used
- Data collection method
- Data preprocessing steps
- Data limitations

**Section 6: Evaluation Data**
- Test set details
- Evaluation methodology
- Known limitations

**Section 7: Ethical Considerations**
- Bias analysis
- Fairness concerns
- Privacy implications
- Environmental impact

**Section 8: Caveats and Recommendations**
- Known limitations
- Recommended uses
- Monitoring recommendations

**Generation**: Template auto-populated from MLflow metadata, human review/edit for high-risk

### Approval Workflow

**Approval Roles**:
1. **Data Scientist** (Model Creator): Submits model for approval
2. **ML Engineer** (Model Reviewer): Technical review, performance validation
3. **Model Owner** (Senior Data Scientist): Business impact review, owns model in production
4. **Compliance Officer**: Regulatory review (high-risk only)
5. **Legal**: Legal review (regulated domains only)

**Approval SLAs**:
- **Low Risk**: <1 hour (automated)
- **Medium Risk**: <24 hours (ML Engineer review)
- **High Risk**: <5 business days (multi-level review)

**Escalation**: If SLA breached, escalate to VP Engineering

### Audit Trail

**Logged Events** (immutable, 7-year retention):
- Model registration with metadata
- All approval/rejection decisions with rationale
- Production deployments with timestamp and deployer
- Model updates (retraining, config changes)
- Performance monitoring alerts
- Incidents and resolutions
- Re-validation events

**Compliance Reports** (quarterly):
- Models deployed by risk level
- Approval metrics (time, approvers)
- Policy violations
- Incidents and root causes
- Bias audit results

## Alternatives Considered

### Alternative 1: Fully Manual Governance

**Pros**:
- Maximum oversight and control
- Thorough human review of every model

**Cons**:
- **Too slow**: 2-4 weeks per model approval
- **Doesn't scale**: Need 10+ reviewers for 500 models
- **Expensive**: $2M+/year in reviewer salaries
- **Blocks innovation**: Data scientists frustrated

**Decision**: Rejected - doesn't scale, too slow

---

### Alternative 2: No Governance (Self-Service Only)

**Pros**:
- Maximum speed
- Data scientist autonomy
- Low cost

**Cons**:
- **High risk**: Unvalidated models in production
- **Compliance failure**: Can't meet SOC2, HIPAA requirements
- **Regulatory fines**: $10M+ potential fines
- **Reputation damage**: Biased/broken models harm brand

**Decision**: Rejected immediately - too risky

---

### Alternative 3: Same Governance for All Models

**Pros**:
- Simple to understand
- Consistent process

**Cons**:
- **Overkill for low-risk**: Slows down experimentation
- **Insufficient for high-risk**: Not thorough enough
- **Inefficient**: Wastes reviewer time on low-risk models

**Decision**: Rejected - one-size-fits-all doesn't work

---

### Alternative 4: Commercial Governance Platform (e.g., Fiddler, Arthur)

**Pros**:
- Pre-built governance features
- Model monitoring included
- Enterprise support

**Cons**:
- **Expensive**: $300-500K/year
- **Limited customization**: Can't adapt to our risk model
- **Vendor lock-in**: Proprietary system
- **Integration complexity**: Another tool to integrate

**Decision**: Rejected - too expensive, limited customization

## Consequences

### Positive

✅ **Balanced**: Speed for low-risk, thorough review for high-risk
- **Low-risk**: <1 day to production (vs 2-4 weeks manual)
- **High-risk**: Thorough review (vs no governance)

✅ **Scales**: Automates 70% of governance checks
- **Automation**: Handles 500+ models without scaling review team
- **Cost**: $400K (development) vs $2M/year (fully manual)

✅ **Compliance**: Meets SOC2, HIPAA, GDPR, EU AI Act requirements
- **Audit trails**: Complete, immutable, 7-year retention
- **Risk reduction**: $10M+ regulatory risk mitigated

✅ **Transparent**: Clear policies, documented decisions
- **No surprises**: Teams know approval requirements upfront
- **Accountability**: Audit trail shows who approved what

✅ **Flexible**: Policies can evolve with regulations
- **Configurable**: Risk thresholds, approval workflows adjustable
- **Future-proof**: Can add new checks without rearchitecture

### Negative

⚠️ **Development Cost**: $400K (6 months, 3 engineers)
- *Trade-off*: Worth it to enable scale and compliance

⚠️ **Process Overhead**: Teams must follow governance workflow
- *Mitigation*: Streamlined for low-risk (automated)
- *Training*: Clear documentation, onboarding for teams

⚠️ **False Positives**: Automated checks may reject valid models
- *Mitigation*: Override mechanism for ML Engineers
- *Continuous Improvement**: Refine checks based on feedback

⚠️ **Approval Bottleneck**: High-risk models may wait for review
- *Mitigation*: 24hr/5-day SLAs, escalation process
- *Capacity Planning**: Add reviewers as volume grows

### Risks and Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Governance too strict (slows teams) | Medium | Medium | Quarterly review of policies, false positive tracking, fast-track process |
| Governance too loose (incident) | Low | High | Regular audits, incident reviews, tighten as needed, insurance |
| Approval bottleneck | Medium | Medium | SLAs, on-call reviewers, auto-approval expansion, capacity planning |
| Policy drift (governance ineffective) | Medium | Medium | Annual governance audit, compliance reviews, executive sponsorship |
| Tool complexity | Medium | Low | Training, documentation, usability testing, feedback loop |

## Implementation Plan

### Phase 1: Foundation (Months 1-3)
- Define risk classification model
- Build automated check framework
- Implement audit logging
- Create model card templates
- **Deliverable**: 50 low-risk models approved automatically

### Phase 2: Approval Workflow (Months 4-6)
- Build approval workflow engine
- Implement Slack/Email notifications
- Create review UI for approvers
- Train ML Engineers on review process
- **Deliverable**: Medium-risk approval workflow operational

### Phase 3: Advanced Governance (Months 7-9)
- Bias & fairness testing framework
- Explainability tools integration
- High-risk approval workflow
- Compliance reporting dashboard
- **Deliverable**: Full governance for all risk levels

### Phase 4: Monitoring & Refinement (Months 10-12)
- Continuous monitoring system
- Re-validation triggers
- Policy refinement based on data
- SOC2 audit preparation
- **Deliverable**: Production-ready governance platform

## Success Metrics

| Metric | Target |
|--------|--------|
| **Auto-Approval Rate (low-risk)** | >95% |
| **Approval Time (medium-risk)** | <24 hours (avg) |
| **Approval Time (high-risk)** | <5 days (avg) |
| **False Positive Rate** | <5% |
| **Governance-Related Incidents** | 0 per quarter |
| **SOC2 Audit Findings** | 0 |
| **Team Satisfaction** | >8/10 |

## Related Decisions

- [ADR-005: Model Registry Approach](./005-model-registry-approach.md) - Registry integration
- [ADR-007: Security and Compliance](./007-security-compliance-architecture.md) - Security controls
- [ADR-002: Feature Store Selection](./002-feature-store-selection.md) - Data lineage

## Review and Update

- **Next Review**: Quarterly
- **Trigger for Revision**:
  - Regulatory changes (new laws)
  - Governance-related incident
  - Approval bottleneck (>3 day average)
  - Team satisfaction <7/10
- **Owner**: Principal Architect + Chief Compliance Officer

## References

- Model Cards: https://arxiv.org/abs/1810.03993
- EU AI Act: https://artificialintelligenceact.eu/
- NIST AI Risk Management Framework: https://www.nist.gov/itl/ai-risk-management-framework
- Internal: `docs/ml-governance-policy-v2.pdf`

---

**Approved by**: CTO (Jane Smith), Chief Compliance Officer (Tom Brown), Principal Architect (Your Name), VP Engineering (John Doe)
**Date**: 2024-10-20
