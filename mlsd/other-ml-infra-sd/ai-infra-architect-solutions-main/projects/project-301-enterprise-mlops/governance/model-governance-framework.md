# Model Governance Framework

## Document Information

- **Document ID**: GOV-001
- **Version**: 1.0.0
- **Last Updated**: 2025-10-17
- **Owner**: AI Infrastructure Architecture Team
- **Status**: Active
- **Related Documents**:
  - ADR-010: Governance Framework
  - ADR-005: Model Registry Approach
  - ARCHITECTURE.md: Section 10 (Governance)

## Executive Summary

This document defines the comprehensive governance framework for machine learning models deployed on the Enterprise MLOps Platform. It establishes policies, processes, and controls to ensure models are developed, validated, deployed, and monitored in accordance with organizational standards, regulatory requirements, and industry best practices.

The framework covers the complete model lifecycle from development through retirement, with risk-based controls that balance innovation velocity with appropriate oversight.

### Key Objectives

1. **Risk Management**: Ensure models are classified by risk and subject to appropriate controls
2. **Regulatory Compliance**: Meet SOC2, HIPAA, GDPR, and industry-specific requirements
3. **Quality Assurance**: Maintain high standards for model performance and reliability
4. **Audit Trail**: Provide complete lineage and decision documentation for all models
5. **Operational Excellence**: Enable efficient model deployment while maintaining governance
6. **Innovation Balance**: Avoid over-governance that slows legitimate innovation

## 1. Model Lifecycle Governance

### 1.1 Lifecycle Stages

Every model progresses through defined stages, each with specific governance requirements:

#### Development Stage
- **Definition**: Model is being researched, prototyped, and initially trained
- **Governance Level**: Minimal (encourage experimentation)
- **Requirements**:
  - Model registered in MLflow with development tag
  - Basic metadata captured (owner, purpose, dataset)
  - No formal approvals required
  - Self-service access for data scientists
- **Duration**: Unlimited
- **Exit Criteria**: Model achieves baseline performance metrics

#### Validation Stage
- **Definition**: Model is being rigorously tested and validated
- **Governance Level**: Moderate
- **Requirements**:
  - Formal test plan documented
  - Performance metrics evaluated against baselines
  - Bias and fairness testing completed
  - Security scan passed
  - Data quality validation
  - Model card created
- **Duration**: 2-4 weeks typical
- **Exit Criteria**: All validation tests pass, stakeholder approval obtained

#### Staging Stage
- **Definition**: Model deployed to pre-production environment
- **Governance Level**: High
- **Requirements**:
  - A/B testing plan approved
  - Monitoring dashboards configured
  - Rollback procedures documented
  - Performance baseline established
  - Shadow mode testing (if applicable)
- **Duration**: 1-2 weeks typical
- **Exit Criteria**: Staging performance meets production requirements

#### Production Stage
- **Definition**: Model actively serving production traffic
- **Governance Level**: Very High
- **Requirements**:
  - Change Advisory Board (CAB) approval for high-risk models
  - Automated monitoring active
  - Incident response procedures in place
  - Model performance SLOs defined
  - Regular retraining schedule established
- **Duration**: Until model is replaced or retired
- **Exit Criteria**: Model deprecated or replaced by better version

#### Deprecated Stage
- **Definition**: Model no longer recommended for new use
- **Governance Level**: Moderate
- **Requirements**:
  - Deprecation notice published (30 days minimum)
  - Migration path documented
  - Support window defined
  - Automated alerts for usage
- **Duration**: 90 days typical
- **Exit Criteria**: All traffic migrated to replacement model

#### Retired Stage
- **Definition**: Model decommissioned and archived
- **Governance Level**: Minimal
- **Requirements**:
  - Model artifacts archived to S3 Glacier
  - Metadata preserved in registry
  - Audit logs retained per compliance requirements
  - Production endpoints removed
- **Duration**: Permanent (archive)

### 1.2 Stage Transition Controls

Transitions between stages require explicit approval based on model risk classification:

| Transition | Low Risk | Medium Risk | High Risk |
|------------|----------|-------------|-----------|
| Dev → Validation | Automated | Automated | Team Lead Approval |
| Validation → Staging | Team Lead | Senior DS + Manager | Senior DS + Manager + Domain Expert |
| Staging → Production | Manager | Manager + Architect | CAB (Multi-stakeholder) |
| Production → Deprecated | Manager | Manager + Architect | CAB |
| Deprecated → Retired | Automated (after 90 days) | Manager | Manager + Legal |

**Approval SLAs**:
- Team Lead: 24 hours
- Manager: 48 hours
- Architect: 72 hours
- CAB: 5 business days (weekly meeting)

## 2. Model Risk Classification

### 2.1 Risk Classification Framework

Models are classified into three risk tiers based on impact assessment:

#### Low Risk
**Definition**: Models with limited impact if they fail or produce incorrect predictions.

**Characteristics**:
- Non-customer-facing applications
- Recommendations that are easily overridden
- Internal productivity tools
- Low financial impact (<$10K per incident)
- No regulatory concerns
- No PII processing

**Examples**:
- Email subject line recommendations
- Internal search ranking
- Meeting time suggestions
- Prototype/experimental models

**Governance Controls**:
- Automated approval workflows
- Monthly performance reviews
- Self-service deployment
- Standard monitoring

#### Medium Risk
**Definition**: Models with moderate impact requiring human oversight.

**Characteristics**:
- Customer-facing but not mission-critical
- Financial impact $10K-$500K per incident
- Handles PII but not PHI/financial data
- Affects user experience significantly
- Requires explainability

**Examples**:
- Product recommendation engines
- Content moderation (with human review)
- Customer churn prediction
- Inventory forecasting

**Governance Controls**:
- Manager + senior data scientist approval
- Bi-weekly performance reviews
- A/B testing required
- Enhanced monitoring with alerting
- Quarterly bias audits

#### High Risk
**Definition**: Models with significant business, regulatory, or ethical impact.

**Characteristics**:
- Mission-critical applications
- Financial impact >$500K per incident
- Processes PHI, financial data, or sensitive PII
- Regulatory compliance required (HIPAA, SOC2, etc.)
- Affects legal/compliance decisions
- Public-facing with reputational risk

**Examples**:
- Fraud detection systems
- Credit decisioning models
- Healthcare diagnosis support
- Automated trading models
- Content moderation (fully automated)

**Governance Controls**:
- Change Advisory Board approval
- Weekly performance reviews
- Mandatory A/B testing with statistical significance
- Real-time monitoring with automated circuit breakers
- Monthly bias audits
- Quarterly model revalidation
- External audit trail

### 2.2 Risk Assessment Process

**Step 1: Initial Classification** (Model Owner)
- Complete risk assessment questionnaire (20 questions)
- Submit classification recommendation
- Provide business impact analysis

**Step 2: Review** (Governance Team)
- Review questionnaire responses
- Validate impact assessment
- Consult with legal/compliance if needed
- Confirm or adjust classification

**Step 3: Documentation** (Automated)
- Record classification in model registry
- Apply appropriate governance policies
- Generate compliance checklist
- Configure monitoring based on risk tier

**Step 4: Periodic Re-assessment**
- Low Risk: Annual review
- Medium Risk: Semi-annual review
- High Risk: Quarterly review
- Triggered review: After incidents or significant changes

### 2.3 Risk Classification Questionnaire

Automated scoring system (each question scored 0-5):

1. **Business Impact**: What is the estimated financial impact if this model fails?
2. **Customer Exposure**: How many customers are directly affected?
3. **Data Sensitivity**: What is the most sensitive data type processed?
4. **Regulatory Scope**: Which regulations apply to this model?
5. **Reversibility**: Can decisions be easily reversed or overridden?
6. **Automation Level**: Is there human review in the loop?
7. **Explainability Need**: Must decisions be explained to customers/regulators?
8. **Reputational Risk**: What is the PR/brand risk if model performs poorly?
9. **Legal Exposure**: Could model errors result in litigation?
10. **Security Sensitivity**: Does the model process authentication/authorization data?

**Scoring**:
- 0-15 points: Low Risk
- 16-30 points: Medium Risk
- 31-50 points: High Risk

## 3. Model Approval Workflows

### 3.1 Low Risk Model Workflow

```
┌─────────────────────┐
│   Development       │
│   (Self-service)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Automated Checks    │
│ - Code quality      │
│ - Security scan     │
│ - Basic tests       │
└──────────┬──────────┘
           │
           ▼
    ┌──────────┐
    │ All Pass?│──No──► Fix Issues
    └──────────┘
           │
          Yes
           │
           ▼
┌─────────────────────┐
│ Auto-approve to     │
│ Staging             │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Staging Tests       │
│ (24 hours minimum)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Manager Approval    │
│ (Click to approve)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Production Deploy   │
│ (Canary rollout)    │
└─────────────────────┘
```

**Timeline**: 2-3 days typical

### 3.2 Medium Risk Model Workflow

```
┌─────────────────────┐
│   Development       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Validation Suite    │
│ - Performance tests │
│ - Bias analysis     │
│ - Model card        │
│ - Security scan     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Senior DS Review    │
│ (2 business days)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Manager Approval    │
│ (2 business days)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Staging Deploy      │
│ + A/B Test Setup    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 7-Day A/B Test      │
│ (Automated analysis)│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Results Review      │
│ (Manager + Architect)│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Production Deploy   │
│ (Gradual rollout)   │
└─────────────────────┘
```

**Timeline**: 2-3 weeks typical

### 3.3 High Risk Model Workflow

```
┌─────────────────────┐
│   Development       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Comprehensive       │
│ Validation          │
│ - All medium checks │
│ - Fairness audit    │
│ - External review   │
│ - Compliance check  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Technical Review    │
│ - Senior DS         │
│ - ML Architect      │
│ - Domain Expert     │
│ (5 business days)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Change Advisory     │
│ Board (CAB)         │
│ - Engineering       │
│ - Product           │
│ - Legal/Compliance  │
│ - Security          │
│ (Weekly meeting)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Staging Deploy      │
│ + Shadow Mode       │
│ (2 weeks minimum)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ A/B Test            │
│ (Statistical        │
│  significance req'd)│
│ (2+ weeks)          │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ CAB Production      │
│ Approval            │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Phased Rollout      │
│ - 5% → 24 hours     │
│ - 25% → 48 hours    │
│ - 100% → final      │
└─────────────────────┘
```

**Timeline**: 6-8 weeks typical

### 3.4 Change Advisory Board (CAB)

**Purpose**: Review and approve high-risk model deployments and significant platform changes.

**Membership**:
- Chair: VP of Engineering (decision authority)
- Required: ML Architect, Senior Data Scientist, Product Manager
- As needed: Legal, Compliance, Security, Domain Experts

**Meeting Schedule**:
- Weekly standing meeting (Thursdays 2-4 PM)
- Emergency meetings as needed (24-hour notice for critical issues)

**Quorum**: Minimum 4 members including chair or delegate

**Agenda Items**:
1. Review of high-risk model deployments
2. Major platform changes
3. Incident retrospectives
4. Policy updates
5. Metrics review

**Decision Process**:
- Consensus preferred
- Chair has final decision authority
- Dissenting opinions recorded in minutes
- All decisions documented with rationale

**Documentation Requirements** (per model):
- Model card (technical specifications)
- Business case
- Risk assessment
- Test results and A/B analysis
- Rollback plan
- Monitoring strategy

## 4. Model Documentation Standards

### 4.1 Model Card

Every model must have a Model Card containing:

**Model Details**:
- Model name and version
- Model type/architecture
- Training date
- Owner and contact
- Intended use cases
- Out-of-scope use cases

**Model Performance**:
- Training metrics
- Validation metrics
- Test set performance
- Comparison to baseline
- Performance by subgroup (if applicable)

**Training Data**:
- Dataset description
- Size and composition
- Date range
- Preprocessing steps
- Known limitations or biases

**Ethical Considerations**:
- Potential biases
- Fairness metrics
- Privacy considerations
- Environmental impact (carbon footprint)

**Caveats and Recommendations**:
- Known edge cases
- Recommended operating conditions
- Update frequency requirements
- Monitoring recommendations

### 4.2 Technical Documentation

**Required for Medium/High Risk**:

1. **Architecture Document**
   - Model architecture diagram
   - Feature engineering pipeline
   - Inference architecture
   - Integration points

2. **Operational Runbook**
   - Deployment procedures
   - Monitoring dashboards
   - Alert response procedures
   - Rollback procedures
   - Incident escalation

3. **Data Lineage**
   - Source systems
   - Transformation logic
   - Feature dependencies
   - Data quality checks

4. **Performance Baseline**
   - Expected latency (p50, p95, p99)
   - Throughput requirements
   - Resource utilization
   - Cost per prediction

### 4.3 Business Documentation

**Required for High Risk**:

1. **Business Case**
   - Expected value/ROI
   - Success metrics
   - Cost-benefit analysis

2. **Stakeholder Analysis**
   - Impacted teams/users
   - Communication plan
   - Training requirements

3. **Compliance Documentation**
   - Applicable regulations
   - Compliance controls
   - Audit requirements

## 5. Model Monitoring and Performance Management

### 5.1 Monitoring Requirements by Risk Tier

#### Low Risk
- **Frequency**: Daily batch checks
- **Metrics**:
  - Prediction volume
  - Error rate
  - Average latency
- **Alerting**: Email notification for critical issues
- **Review**: Monthly dashboard review

#### Medium Risk
- **Frequency**: Real-time monitoring
- **Metrics**:
  - All low-risk metrics, plus:
  - Data drift detection
  - Prediction distribution
  - Feature importance shifts
  - Business metric correlation
- **Alerting**: PagerDuty for critical issues, Slack for warnings
- **Review**: Weekly dashboard review, bi-weekly deep dive

#### High Risk
- **Frequency**: Real-time with automated circuit breakers
- **Metrics**:
  - All medium-risk metrics, plus:
  - Fairness metrics by protected class
  - Regulatory compliance metrics
  - Explainability scores
  - Shadow model comparison (if applicable)
- **Alerting**: Immediate PagerDuty, automated rollback triggers
- **Review**: Daily dashboard check, weekly deep dive, monthly executive report

### 5.2 Performance Degradation Response

**Automated Responses**:
- **Minor Degradation** (10-20% performance drop): Warning alert, increase monitoring
- **Moderate Degradation** (20-40% drop): Critical alert, trigger investigation
- **Severe Degradation** (>40% drop): Automatic traffic reduction, immediate escalation

**Manual Response Procedures**:
1. **Initial Response** (0-30 minutes): Acknowledge alert, assess scope
2. **Investigation** (30 minutes - 2 hours): Root cause analysis, impact assessment
3. **Mitigation** (2-4 hours): Implement fix or rollback
4. **Recovery** (4-24 hours): Full restoration, monitoring confirmation
5. **Retrospective** (1-3 days): Document learnings, update procedures

### 5.3 Model Retraining Policies

**Scheduled Retraining**:
- Low Risk: Quarterly or as needed
- Medium Risk: Monthly
- High Risk: Weekly or more frequently

**Triggered Retraining**:
- Data drift detected (>threshold)
- Performance degradation
- Significant business changes
- New data sources available
- Regulatory requirement changes

**Retraining Governance**:
- Retrained models treated as new versions
- Follow same approval workflow as original
- Compare performance to current production
- Require improvement or compelling reason to deploy

## 6. Model Retirement

### 6.1 Retirement Triggers

Models should be retired when:
- Replaced by superior model
- Business use case no longer valid
- Maintenance cost exceeds value
- Regulatory changes make model non-compliant
- Persistent performance issues
- Technology obsolescence

### 6.2 Retirement Process

**Step 1: Deprecation Notice** (90 days before retirement)
- Announce to all stakeholders
- Document migration path
- Provide timeline and support

**Step 2: Support Period** (60-90 days)
- Continue full support
- Assist with migrations
- Monitor usage decline

**Step 3: Decommissioning** (30 days)
- Reduce to critical support only
- Implement usage warnings
- Prepare archival

**Step 4: Retirement**
- Remove production endpoints
- Archive model artifacts to S3 Glacier
- Preserve metadata in registry
- Document final state
- Retain audit logs per compliance requirements

### 6.3 Emergency Retirement

For critical issues (security, legal, ethical):
- Immediate traffic shutdown
- Root cause analysis
- Stakeholder notification
- Incident report
- Lessons learned

## 7. Roles and Responsibilities

### 7.1 Model Owner (Data Scientist)

**Responsibilities**:
- Develop and train models
- Complete model documentation
- Submit governance approvals
- Monitor model performance
- Respond to performance issues
- Schedule retraining
- Communicate with stakeholders

**Accountabilities**:
- Model quality and performance
- Compliance with governance policies
- Timely issue resolution

### 7.2 Team Lead / Senior Data Scientist

**Responsibilities**:
- Review model designs
- Approve low/medium risk models
- Mentor data scientists
- Ensure best practices
- Technical escalation point

**Accountabilities**:
- Team model quality
- Technical standards compliance
- Knowledge sharing

### 7.3 ML Architect

**Responsibilities**:
- Define architecture standards
- Review high-risk models
- Platform governance policies
- Technology selection
- CAB participation

**Accountabilities**:
- Platform reliability
- Architectural consistency
- Scalability and performance

### 7.4 Engineering Manager

**Responsibilities**:
- Approve production deployments
- Resource allocation
- Priority management
- Team performance
- Stakeholder communication

**Accountabilities**:
- Team delivery
- Budget management
- Operational excellence

### 7.5 Governance Team

**Responsibilities**:
- Maintain governance framework
- Risk classification reviews
- Compliance monitoring
- Policy updates
- Audit support
- Metrics reporting

**Accountabilities**:
- Governance effectiveness
- Regulatory compliance
- Risk management

### 7.6 Change Advisory Board

**Responsibilities**:
- Review high-risk deployments
- Platform change approvals
- Incident reviews
- Policy decisions

**Accountabilities**:
- Platform stability
- Risk acceptance
- Strategic alignment

## 8. Compliance and Audit

### 8.1 Audit Trail Requirements

All governance-related activities must be logged:

**Required Logs**:
- Model registration and updates
- Risk classification decisions
- Approval requests and decisions
- Stage transitions
- Deployment events
- Configuration changes
- Access to model artifacts
- Performance issues and resolutions
- Retraining events

**Log Retention**:
- Production models: 7 years
- Non-production models: 3 years
- Audit logs: Indefinite (S3 Glacier after 7 years)

**Log Format**:
```json
{
  "timestamp": "2025-10-17T10:30:00Z",
  "event_type": "approval_decision",
  "model_id": "fraud-detection-v2.1",
  "model_version": "2.1.0",
  "user_id": "jane.smith@company.com",
  "action": "approved",
  "risk_level": "high",
  "approver_role": "manager",
  "comments": "Performance metrics meet requirements, A/B test successful",
  "related_documents": ["model-card-v2.1.pdf", "test-results-2025-10-15.pdf"]
}
```

### 8.2 Compliance Reporting

**Monthly Reports**:
- Models deployed by risk tier
- Approval times by workflow
- Performance issues and resolutions
- Compliance violations (if any)
- Retraining activity

**Quarterly Reports**:
- Risk classification distribution
- Governance effectiveness metrics
- Audit findings and remediation
- Policy updates

**Annual Reports**:
- Full governance assessment
- Regulatory compliance status
- Strategic recommendations
- Industry benchmarking

### 8.3 Audit Support

**Internal Audits** (Quarterly):
- Sample models from each risk tier
- Review documentation completeness
- Verify approval workflows followed
- Test monitoring effectiveness
- Validate log integrity

**External Audits** (Annual for SOC2):
- Provide audit trail exports
- Demonstrate control effectiveness
- Document policy adherence
- Evidence of continuous monitoring

## 9. Exceptions and Waivers

### 9.1 Exception Process

Exceptions to governance policies may be granted in limited circumstances:

**Valid Reasons**:
- Emergency business need
- Technical limitations (temporary)
- Pilot/proof-of-concept programs
- Regulatory deadline pressures

**Process**:
1. Submit exception request with justification
2. Document compensating controls
3. Obtain approval from:
   - Medium Risk: ML Architect + Manager
   - High Risk: CAB + CTO
4. Set expiration date (maximum 90 days)
5. Create remediation plan

**Tracking**:
- All exceptions logged in registry
- Monthly review of open exceptions
- Automatic expiration and re-evaluation

### 9.2 Policy Waivers

Permanent waivers (rare):
- Require CTO approval
- Annual revalidation required
- Must not violate regulatory requirements
- Documented in exception register

## 10. Continuous Improvement

### 10.1 Governance Metrics

**Efficiency Metrics**:
- Average approval time by risk tier
- Percentage of automated approvals
- Time from development to production
- Retraining cycle time

**Effectiveness Metrics**:
- Production incidents per 100 models
- Policy compliance rate
- Audit findings count
- Model performance sustainability

**Balance Metrics**:
- Innovation velocity (models deployed per quarter)
- Governance overhead (hours per model)
- Developer satisfaction (survey)

### 10.2 Feedback Loops

**Quarterly Governance Review**:
- Analyze metrics
- Gather stakeholder feedback
- Identify friction points
- Propose policy improvements

**Annual Framework Review**:
- Comprehensive assessment
- Industry benchmarking
- Regulatory update review
- Major policy revisions

### 10.3 Community Engagement

- Monthly governance office hours
- Slack channel for questions (#ml-governance)
- Quarterly town halls
- Documentation wiki
- Training programs

## 11. Getting Started

### 11.1 For Data Scientists

**Deploying Your First Model**:
1. Register model in MLflow
2. Complete risk assessment questionnaire
3. Create model card (use template)
4. Run automated validation tests
5. Submit for approval
6. Monitor governance dashboard for status
7. Deploy per approved workflow

**Resources**:
- Model Card Template: `/templates/model-card.md`
- Risk Assessment Tool: `https://mlops.company.com/risk-assessment`
- Governance Dashboard: `https://mlops.company.com/governance`
- Training: "Model Governance 101" (30 minutes, online)

### 11.2 For Managers

**Approval Responsibilities**:
- Review requests within SLA
- Verify documentation completeness
- Consult with experts as needed
- Document decision rationale
- Monitor team compliance

**Resources**:
- Approval Dashboard: `https://mlops.company.com/approvals`
- Decision Guidelines: `/docs/approval-guidelines.md`
- Escalation Contacts: `/docs/escalation-matrix.md`

## 12. Document Control

### 12.1 Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-10-17 | AI Infrastructure Team | Initial framework |

### 12.2 Review and Approval

- **Author**: ML Architect
- **Reviewed by**: Engineering Manager, Compliance Lead, Security Architect
- **Approved by**: VP of Engineering, CTO
- **Next Review**: 2026-04-17 (6 months)

### 12.3 Related Documents

- [ADR-010: Governance Framework](../architecture/adrs/010-governance-framework.md)
- [ADR-005: Model Registry Approach](../architecture/adrs/005-model-registry-approach.md)
- [Data Governance Policy](./data-governance-policy.md)
- [Compliance Requirements Mapping](./compliance-requirements-mapping.md)
- [Audit Procedures](./audit-procedures.md)

## Appendix A: Risk Assessment Questionnaire

**Instructions**: Answer each question with a score from 0 (lowest risk) to 5 (highest risk).

1. **Business Impact**: If this model produces incorrect results, what is the estimated financial impact?
   - 0: <$1K
   - 1: $1K-$10K
   - 2: $10K-$50K
   - 3: $50K-$200K
   - 4: $200K-$500K
   - 5: >$500K

2. **Customer Exposure**: How many customers could be directly affected by model errors?
   - 0: 0 (internal only)
   - 1: <100
   - 2: 100-1,000
   - 3: 1,000-10,000
   - 4: 10,000-100,000
   - 5: >100,000

3. **Data Sensitivity**: What is the highest sensitivity level of data processed?
   - 0: Public data
   - 1: Internal non-sensitive
   - 2: Customer data (non-PII)
   - 3: PII (personally identifiable)
   - 4: PHI (protected health) or financial
   - 5: Highly regulated (ITAR, classified, etc.)

4. **Regulatory Scope**: Which regulations apply to this model?
   - 0: None
   - 1: Internal policies only
   - 2: Industry standards (non-binding)
   - 3: SOC2, ISO 27001
   - 4: GDPR, CCPA, HIPAA
   - 5: Multiple strict regulations (HIPAA + financial + GDPR)

5. **Reversibility**: Can model decisions be easily reversed or overridden?
   - 0: Fully automated reversal
   - 1: Easy manual reversal (<1 minute)
   - 2: Moderate effort (1-10 minutes)
   - 3: Significant effort (>10 minutes)
   - 4: Difficult to reverse (requires multiple approvals)
   - 5: Irreversible or extremely costly to reverse

6. **Automation Level**: Is there human oversight?
   - 0: Human in the loop (every decision)
   - 1: Human review of high-confidence decisions
   - 2: Human review of edge cases
   - 3: Automated with human spot-checks
   - 4: Fully automated with periodic review
   - 5: Fully automated, no regular human review

7. **Explainability Need**: Must model decisions be explainable?
   - 0: No explainability needed
   - 1: Internal explainability (team only)
   - 2: Business stakeholder explainability
   - 3: Customer explainability (simple)
   - 4: Regulatory explainability required
   - 5: Legal/adversarial explainability required

8. **Reputational Risk**: If this model fails, what is the PR/brand impact?
   - 0: None (internal tool)
   - 1: Minimal (small user frustration)
   - 2: Moderate (customer complaints)
   - 3: Significant (social media criticism possible)
   - 4: High (likely media coverage)
   - 5: Severe (major brand damage, executive testimony)

9. **Legal Exposure**: Could model errors result in legal action?
   - 0: No legal exposure
   - 1: Minimal (contract disputes unlikely)
   - 2: Low (potential customer complaints)
   - 3: Moderate (possible arbitration)
   - 4: High (likely lawsuits)
   - 5: Severe (class action potential, regulatory penalties)

10. **Security Sensitivity**: Does the model make security or access control decisions?
    - 0: No security role
    - 1: Minor security feature
    - 2: Security monitoring (detection only)
    - 3: Access recommendations (human approved)
    - 4: Automated access control
    - 5: Critical security infrastructure

**Total Score**: _____ / 50

**Risk Classification**:
- 0-15: Low Risk
- 16-30: Medium Risk
- 31-50: High Risk

## Appendix B: Model Card Template

See `/templates/model-card-template.md` for the complete template.

## Appendix C: Governance Workflow Diagrams

Detailed workflow diagrams available in `/docs/governance-workflows.md`.

## Appendix D: Contact Information

- **Governance Questions**: ml-governance@company.com
- **CAB Requests**: cab-requests@company.com
- **Emergency Escalation**: ml-oncall@company.com (PagerDuty)
- **Training**: learning@company.com

---

**Document Classification**: Internal Use
**Last Review Date**: 2025-10-17
**Next Review Date**: 2026-04-17
