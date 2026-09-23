# Audit Procedures

## Document Information

- **Document ID**: GOV-004
- **Version**: 1.0.0
- **Last Updated**: 2025-10-17
- **Owner**: Internal Audit / Compliance Team
- **Status**: Active
- **Related Documents**:
  - GOV-001: Model Governance Framework
  - GOV-002: Data Governance Policy
  - GOV-003: Compliance Requirements Mapping

## Executive Summary

This document defines comprehensive audit procedures for the Enterprise MLOps Platform to ensure compliance with governance policies, regulatory requirements, and operational best practices. It establishes standardized approaches for planning, conducting, documenting, and following up on audits across security, data governance, model governance, and compliance domains.

The procedures support:
1. **Internal Audits**: Self-assessments and continuous monitoring
2. **External Audits**: SOC 2, HIPAA, GDPR, CCPA compliance audits
3. **Regulatory Audits**: Government and supervisory authority examinations
4. **Vendor Audits**: Third-party assessments and due diligence

### Audit Types and Frequency

| Audit Type | Frequency | Scope | Owner |
|------------|-----------|-------|-------|
| Model Governance Audit | Quarterly | Model lifecycle compliance, approval workflows | ML Governance Team |
| Data Access Audit | Quarterly | Access controls, RBAC, least privilege | Security Team |
| Data Quality Audit | Monthly | Data quality metrics, validation effectiveness | Data Engineering |
| Security Controls Audit | Quarterly | Security configuration, vulnerabilities | Security Team |
| HIPAA Compliance Audit | Semi-annual | HIPAA administrative, physical, technical safeguards | HIPAA Security Officer |
| GDPR Compliance Audit | Semi-annual | Data subject rights, lawfulness of processing | Data Protection Officer |
| Vendor Compliance Audit | Annual (per vendor) | Vendor security, BAA/DPA compliance | Procurement/Legal |
| SOC 2 Type II Audit | Annual | Trust service criteria (Security, Availability, etc.) | External Auditor |
| Penetration Testing | Annual | Technical security vulnerabilities | External Firm |
| Disaster Recovery Audit | Annual | DR procedures, RTO/RPO validation | SRE Team |

## 1. Audit Planning

### 1.1 Annual Audit Calendar

**Q1 (January - March)**:
- SOC 2 Type II audit fieldwork
- Q4 access reviews validation
- HIPAA training compliance audit
- Annual penetration testing
- Vendor risk assessment updates (25%)

**Q2 (April - June)**:
- Model governance audit
- Data quality audit
- Security controls audit
- GDPR/CCPA compliance audit
- HIPAA risk analysis update
- Disaster recovery test and audit
- Vendor risk assessment updates (25%)

**Q3 (July - September)**:
- Model governance audit
- Data access audit
- Security controls audit
- ISO 27001 preparation activities (starting 2025)
- Vendor risk assessment updates (25%)

**Q4 (October - December)**:
- Model governance audit
- Data quality audit
- Data access audit
- Security controls audit
- Year-end compliance reporting
- SOC 2 preparation activities
- Vendor risk assessment updates (25%)

### 1.2 Risk-Based Audit Prioritization

Audits are prioritized based on risk factors:

**Priority 1 - Critical (Quarterly or more frequent)**:
- Controls protecting PHI/PII
- Access to production environments
- High-risk model deployments
- Security vulnerabilities
- Regulatory compliance requirements

**Priority 2 - High (Semi-annual)**:
- Medium-risk model governance
- Data quality for ML
- Vendor management
- Change management
- Incident response effectiveness

**Priority 3 - Medium (Annual)**:
- Low-risk model governance
- Internal data handling
- Operational procedures
- Training effectiveness
- Documentation quality

**Priority 4 - Low (As needed)**:
- Non-critical operational areas
- Process efficiency
- User experience
- Innovation initiatives

### 1.3 Audit Planning Process

**Step 1: Define Audit Scope** (2-4 weeks before)
- Identify audit objectives
- Determine audit criteria (policies, regulations, standards)
- Select audit sample size (statistical sampling for large populations)
- Identify systems and data sources
- Define audit period
- Assign audit team

**Step 2: Develop Audit Program** (1-2 weeks before)
- Create detailed audit procedures
- Prepare checklists and testing scripts
- Define evidence requirements
- Establish communication plan
- Schedule interviews and walkthroughs
- Request preliminary documentation

**Step 3: Communicate Audit** (1 week before)
- Notify stakeholders
- Distribute audit schedule
- Confirm availability of personnel
- Ensure system access for auditors
- Set up audit workspace (virtual or physical)

**Step 4: Kick-off Meeting**
- Review audit scope and objectives
- Clarify expectations
- Discuss logistics and timeline
- Address initial questions
- Establish communication protocols

## 2. Audit Execution

### 2.1 Evidence Collection Methods

#### Documentation Review
**Purpose**: Verify policies, procedures, and records exist and are current.

**Procedure**:
1. Request documents from evidence repository (see GOV-003, Section 6.1)
2. Verify document version, approval, and effective date
3. Check document completeness and accuracy
4. Review for consistency with regulatory requirements
5. Document findings in audit workpapers

**Evidence**: Policies, procedures, standards, meeting minutes, training records, contracts

**Sample Size**:
- 100% for policies and high-risk procedures
- 10-20% sample for operational records
- All exceptions and waivers

#### Inquiry and Interview
**Purpose**: Understand processes and validate documentation through personnel interviews.

**Procedure**:
1. Prepare interview questions aligned with audit objectives
2. Schedule interviews (30-60 minutes typical)
3. Conduct interview with note-taking
4. Confirm understanding with interviewee
5. Document responses in audit workpapers
6. Follow up on unclear or inconsistent responses

**Interview Targets**:
- Policy owners
- Process operators (data scientists, engineers)
- Managers and approvers
- Security personnel
- Compliance officers

**Best Practices**:
- Interview multiple people for critical controls
- Cross-validate interview responses with documentary evidence
- Use open-ended questions
- Maintain professional and objective tone

#### Observation
**Purpose**: Witness processes and controls in action.

**Procedure**:
1. Schedule observation session
2. Observe process without interference
3. Document steps observed
4. Note any deviations from documented procedures
5. Ask clarifying questions after observation
6. Record findings with timestamp and participants

**Observation Targets**:
- Model deployment process
- Access request approval workflow
- Data quality validation procedures
- Incident response activities
- Change management meetings (CAB)

#### Inspection
**Purpose**: Examine physical or digital assets and configurations.

**Procedure**:
1. Obtain access to systems/assets
2. Review configuration settings
3. Compare to security baselines
4. Document discrepancies
5. Take screenshots or export configurations as evidence
6. Verify remediation if issues found

**Inspection Targets**:
- AWS IAM policies and roles
- Security group configurations
- Encryption settings (KMS, S3, RDS)
- Logging configurations (CloudWatch)
- Network architecture (VPC, subnets, NACLs)
- Application configurations
- Data classification tags

#### Testing and Validation
**Purpose**: Verify controls operate effectively through hands-on testing.

**Procedure**:
1. Define test scenarios
2. Prepare test data/accounts
3. Execute tests in controlled environment
4. Document test steps and results
5. Compare actual results to expected outcomes
6. Identify control gaps or failures

**Testing Types**:

**Access Control Testing**:
- Attempt unauthorized access
- Verify least privilege enforcement
- Test access revocation procedures
- Validate MFA enforcement
- Check for orphaned accounts

**Data Protection Testing**:
- Verify encryption at rest (sample datasets)
- Verify encryption in transit (network capture)
- Test data masking in non-production
- Validate pseudonymization effectiveness
- Check for exposed sensitive data

**Model Governance Testing**:
- Sample model deployments and verify approval
- Test risk classification accuracy
- Validate monitoring alerts
- Check documentation completeness
- Verify retraining schedules

**Incident Response Testing**:
- Simulate security incident
- Measure detection time
- Validate alert escalation
- Test communication procedures
- Review incident documentation

#### Data Analytics
**Purpose**: Analyze large datasets to identify patterns, anomalies, or compliance violations.

**Procedure**:
1. Extract relevant data (audit logs, access logs, etc.)
2. Define analysis criteria
3. Run automated scripts or queries
4. Identify outliers and anomalies
5. Investigate high-risk findings
6. Document analysis methodology and results

**Analytics Use Cases**:

**Access Pattern Analysis**:
```sql
-- Example: Identify users accessing data outside business hours
SELECT user_id, dataset_id, COUNT(*) as access_count
FROM audit_logs
WHERE event_type = 'data_access'
  AND data_classification IN ('confidential', 'restricted')
  AND EXTRACT(HOUR FROM timestamp) NOT BETWEEN 6 AND 20
GROUP BY user_id, dataset_id
HAVING COUNT(*) > 10
ORDER BY access_count DESC;
```

**Failed Access Analysis**:
```sql
-- Example: Identify repeated failed access attempts (potential unauthorized access)
SELECT user_id, dataset_id, COUNT(*) as failed_attempts
FROM audit_logs
WHERE event_type = 'data_access'
  AND success = false
  AND timestamp > NOW() - INTERVAL '30 days'
GROUP BY user_id, dataset_id
HAVING COUNT(*) > 5
ORDER BY failed_attempts DESC;
```

**Orphaned Resource Analysis**:
```sql
-- Example: Identify IAM users without access review in >90 days
SELECT user_id, last_access_review_date, DATEDIFF(NOW(), last_access_review_date) as days_overdue
FROM iam_users
WHERE last_access_review_date < NOW() - INTERVAL '90 days'
  OR last_access_review_date IS NULL
ORDER BY days_overdue DESC;
```

**Data Quality Trend Analysis**:
```sql
-- Example: Identify datasets with declining quality scores
SELECT dataset_id, AVG(quality_score) as avg_quality,
       LAG(AVG(quality_score)) OVER (PARTITION BY dataset_id ORDER BY month) as prev_month_quality
FROM data_quality_metrics
WHERE month >= NOW() - INTERVAL '6 months'
GROUP BY dataset_id, month
HAVING avg_quality < prev_month_quality * 0.9  -- 10% decline
ORDER BY dataset_id, month;
```

### 2.2 Sampling Methodologies

#### Statistical Sampling
**When to Use**: Large populations where testing 100% is impractical.

**Approach**:
1. Define population size (N)
2. Determine desired confidence level (typically 95%)
3. Determine acceptable error rate (typically 5%)
4. Calculate sample size using statistical formula:

   ```
   n = (Z² × p × (1-p)) / E²

   Where:
   n = sample size
   Z = Z-score (1.96 for 95% confidence)
   p = estimated proportion (use 0.5 for maximum sample size)
   E = margin of error (0.05 for 5%)

   Example: n = (1.96² × 0.5 × 0.5) / 0.05² = 384
   ```

5. Select random sample from population
6. Project findings to population with confidence interval

**Example Application**:
- Population: 5,000 model deployments in past year
- Sample size: 384 (for 95% confidence, 5% margin of error)
- Selection method: Random number generator
- Testing: Verify approval workflow compliance
- Result: If 5% of sample has issues, population estimate is 5% ± 5% (0-10%)

#### Risk-Based Sampling
**When to Use**: Focus audit effort on highest-risk items.

**Approach**:
1. Classify population by risk (high/medium/low)
2. Sample 100% of high-risk items
3. Sample 25-50% of medium-risk items
4. Sample 10-25% of low-risk items
5. Focus detailed testing on higher-risk samples

**Example Application**:
- Population: 500 models in production
- High-risk (10 models): 100% sampled (10 models)
- Medium-risk (150 models): 30% sampled (45 models)
- Low-risk (340 models): 15% sampled (51 models)
- Total sample: 106 models (21% of population)

#### Judgmental Sampling
**When to Use**: Auditor expertise suggests specific items warrant examination.

**Approach**:
1. Use auditor judgment and experience
2. Select items based on:
   - Known issues or complaints
   - Complex or unusual transactions
   - High-value or high-impact items
   - Areas of suspected control weakness
3. Cannot project findings to population (not statistically valid)
4. Best used in combination with statistical sampling

**Example Application**:
- Select all models handling PHI (regardless of total population)
- Select models developed by new team members
- Select models with performance degradation
- Select highest-cost infrastructure components

### 2.3 Audit Testing Procedures by Control Area

#### 2.3.1 Model Governance Audit

**Objective**: Verify models are developed, validated, and deployed in accordance with governance policies.

**Scope**: Sample of models across all risk tiers deployed in audit period.

**Sample Size**:
- High-risk: 100% (typically 10-20 models/year)
- Medium-risk: 30% (statistical sample)
- Low-risk: 15% (statistical sample)

**Test Procedures**:

**Test 1: Risk Classification Accuracy**
- Select sample of models
- Re-perform risk assessment questionnaire
- Compare auditor classification to recorded classification
- Investigate discrepancies
- **Pass Criteria**: <5% misclassification rate

**Test 2: Approval Workflow Compliance**
- Obtain model registry data for sample
- Verify approval requirements met per risk tier:
  - Low: Team lead or automated approval
  - Medium: Manager + senior data scientist
  - High: CAB approval with all required reviewers
- Check approval timing (within SLA)
- Review approval documentation (justification, sign-offs)
- **Pass Criteria**: 100% compliance for high-risk, 95% for medium/low

**Test 3: Documentation Completeness**
- Verify model card exists and complete (all required sections)
- For medium/high risk: Check technical documentation (architecture, runbook)
- For high risk: Verify business case, compliance documentation
- Review documentation quality (not just existence)
- **Pass Criteria**: 100% for high-risk, 95% for medium-risk

**Test 4: Performance Monitoring**
- Verify monitoring dashboards configured per risk tier
- Check alert configuration (thresholds, recipients)
- Review monitoring logs for past 30 days
- Verify performance issues were detected and addressed
- **Pass Criteria**: 100% monitoring coverage, alerts tested

**Test 5: Retraining Compliance**
- Check scheduled retraining frequency per risk tier
- Verify retraining occurs on schedule
- Review retraining approval (should follow same workflow as initial)
- Check performance comparison (new vs. old model)
- **Pass Criteria**: 95% on-time retraining

**Test 6: Model Retirement**
- Identify deprecated models in sample
- Verify deprecation notice was issued (30+ days)
- Check migration plan documented
- Verify endpoint removal after retirement
- Validate archival to Glacier
- **Pass Criteria**: 100% compliance with retirement procedures

**Findings Documentation**:
- Control deficiencies (what control failed?)
- Root cause (why did it fail?)
- Risk/impact (what's the consequence?)
- Recommendation (how to fix?)
- Management response (do they agree? timeline?)

#### 2.3.2 Data Access Audit

**Objective**: Verify access to data is appropriately controlled, monitored, and reviewed.

**Scope**: All users with access to confidential/restricted data.

**Sample Size**:
- Restricted data access: 100%
- Confidential data access: 30% (statistical sample)
- Internal data access: 10% (risk-based sample)

**Test Procedures**:

**Test 1: Principle of Least Privilege**
- Extract IAM roles and permissions for sample users
- Compare assigned roles to job function
- Identify excessive permissions (access not needed for role)
- Check for direct policy attachments (should use groups/roles)
- **Pass Criteria**: <5% users with excessive permissions

**Test 2: Access Request Approval**
- Sample access requests from past quarter
- Verify request includes:
  - Business justification
  - Data classification identified
  - Time-bound access (expiration date)
- Verify appropriate approval:
  - Manager approval for confidential
  - Data owner + compliance for restricted
- Check approval timing (within SLA)
- **Pass Criteria**: 100% for restricted, 95% for confidential

**Test 3: Access Reviews**
- Verify quarterly access reviews completed on time
- Sample access review records
- Check review completeness (all users reviewed)
- Verify access removals were executed
- Test a sample of removed access (confirm no longer functional)
- **Pass Criteria**: 100% completion within 30 days of quarter-end

**Test 4: Termination Access Removal**
- Obtain list of terminated employees from HR (past quarter)
- Verify access was revoked on termination date
- Check for any post-termination access (audit logs)
- Validate asset returns (laptops, badges, etc.)
- **Pass Criteria**: 100% same-day access removal

**Test 5: Privileged Access Monitoring**
- Identify privileged users (admin, root, etc.)
- Review audit logs for privileged actions
- Check for suspicious activity (after-hours, unusual commands)
- Verify all privileged access is logged
- Test log integrity (cannot be modified)
- **Pass Criteria**: 100% privileged actions logged, no integrity issues

**Test 6: Access Anomalies**
- Run data analytics on access logs (see Section 2.1)
- Investigate anomalies:
  - Off-hours access
  - Failed access attempts
  - Unusual data volume
  - Access from unusual locations
- Document investigation results
- **Pass Criteria**: All anomalies investigated and resolved

#### 2.3.3 Data Governance Audit

**Objective**: Verify data is classified, protected, and managed according to policies.

**Scope**: Sample of datasets across all classification tiers.

**Sample Size**:
- Restricted data: 100% of datasets
- Confidential data: 30% (statistical sample)
- Internal/Public: 10% (risk-based sample)

**Test Procedures**:

**Test 1: Data Classification Accuracy**
- Select sample of datasets
- Re-perform classification assessment
- Compare auditor classification to recorded classification
- Check for unclassified data
- Verify classification tags in data catalog
- **Pass Criteria**: <5% misclassification, 0% unclassified restricted data

**Test 2: Data Protection Controls**
- Verify encryption at rest (check S3, RDS, EBS encryption)
- Verify encryption in transit (TLS certificate inspection)
- For restricted data: Confirm FIPS 140-2 encryption
- Test pseudonymization for PHI (if applicable)
- Check for exposed data (public S3 buckets, open databases)
- **Pass Criteria**: 100% for restricted, 99% for confidential

**Test 3: Data Retention Compliance**
- Sample datasets and verify retention period defined
- Check automated deletion configuration (lifecycle policies)
- Verify data past retention period is deleted
- Review legal holds (appropriate and documented)
- **Pass Criteria**: 100% retention policies defined, 95% automated deletion

**Test 4: Data Quality Validation**
- Review data quality framework configuration
- Sample datasets and check quality scores
- Verify quality checks are running (not disabled)
- Test quality check effectiveness (inject bad data, verify detection)
- Review quality incident response (were issues addressed?)
- **Pass Criteria**: 100% quality monitoring, 95% incident resolution

**Test 5: Data Subject Rights (DSR)**
- Sample DSR requests from past quarter
- Verify identity verification performed
- Check response timing (30 days GDPR, 45 days CCPA)
- Verify completeness of response (all requested data)
- For deletion requests: Confirm data deleted (query databases)
- Test DSR portal functionality (submit test request)
- **Pass Criteria**: 100% identity verification, 95% within SLA

**Test 6: Data Lineage**
- Sample critical datasets
- Verify lineage documented in catalog
- Trace data flow end-to-end (source to consumption)
- Check lineage accuracy (does it match actual data flow?)
- Verify lineage updates when pipelines change
- **Pass Criteria**: 100% lineage for restricted, 90% for confidential

#### 2.3.4 Security Controls Audit

**Objective**: Verify technical security controls are properly configured and effective.

**Scope**: All AWS accounts and critical infrastructure components.

**Test Procedures**:

**Test 1: Network Security**
- Review VPC configurations (subnets, route tables, NACLs)
- Check security group rules for over-permissive access (0.0.0.0/0)
- Verify network segmentation (production isolated from non-production)
- Test WAF rules (inject test payloads, verify blocking)
- Check VPN and PrivateLink configurations
- **Pass Criteria**: No critical misconfigurations

**Test 2: Identity and Access Management**
- Run IAM Access Analyzer and review findings
- Check for IAM users without MFA (should be zero)
- Verify IAM password policy (12+ chars, complexity, rotation)
- Review cross-account roles (appropriate trust policies)
- Check for unused credentials (90+ days)
- **Pass Criteria**: MFA 100%, no unused credentials >120 days

**Test 3: Encryption**
- Verify default encryption enabled (S3, EBS, RDS)
- Check KMS key policies (appropriate permissions)
- Verify key rotation enabled (annual)
- Test encryption in transit (TLS 1.2+)
- Check certificate validity and expiration
- **Pass Criteria**: 100% encryption for restricted, 99% for confidential

**Test 4: Logging and Monitoring**
- Verify CloudTrail enabled in all regions
- Check CloudWatch Logs retention (7 years for audit logs)
- Verify log integrity (cannot be modified)
- Test SIEM integration (logs flowing to Splunk)
- Review GuardDuty findings and remediation
- **Pass Criteria**: 100% logging coverage, <5% open findings >30 days

**Test 5: Vulnerability Management**
- Review vulnerability scan results (Security Hub, Inspector)
- Check patching compliance (OS, application, container images)
- Verify vulnerability remediation within SLA:
  - Critical: 7 days
  - High: 30 days
  - Medium: 90 days
- Test vulnerability scanning coverage (all instances)
- **Pass Criteria**: 95% remediation within SLA

**Test 6: Incident Detection and Response**
- Review security incidents from past quarter
- Verify detection time (MTTD - Mean Time To Detect)
- Check incident response procedures followed
- Review post-incident reports (root cause, remediation)
- Test incident response plan (tabletop exercise)
- **Pass Criteria**: 100% incidents documented, <24 hour MTTD

#### 2.3.5 HIPAA Compliance Audit

**Objective**: Verify HIPAA administrative, physical, and technical safeguards are implemented and effective.

**Scope**: All systems processing PHI, all users with PHI access.

**Test Procedures**:

**Administrative Safeguards** (see Section 2 for detailed requirements):
- Review HIPAA risk analysis (current and complete)
- Verify HIPAA Security Officer designated
- Check workforce training (100% completion, annual)
- Review Business Associate Agreements (BAAs)
- Verify incident response plan includes breach procedures

**Physical Safeguards**:
- Review AWS SOC 2 report (physical controls)
- Check office access controls (badge logs, visitor logs)
- Verify workstation security (encryption, screen lock)
- Review media disposal procedures (certificates of destruction)

**Technical Safeguards**:
- Test unique user identification (no shared accounts for PHI)
- Verify MFA for PHI access (100%)
- Check session timeout (15 minutes max)
- Verify encryption (FIPS 140-2 for PHI)
- Review audit logs (comprehensive, 7-year retention)
- Test emergency access procedures (break-glass)

**Breach Notification**:
- Review breach assessment procedures
- Verify 60-day notification timeline
- Check HHS reporting procedures
- Test breach notification templates

**Pass Criteria**: 100% compliance with HIPAA required specifications, 95% compliance with addressable specifications

#### 2.3.6 GDPR/CCPA Compliance Audit

**Objective**: Verify compliance with data subject rights and privacy obligations.

**Scope**: All personal data processing activities.

**Test Procedures**:

**Test 1: Lawfulness of Processing**
- Review data processing inventory (Art. 30 records)
- Verify legal basis documented for each processing activity
- Check consent records (if consent is legal basis)
- Review legitimate interest assessments (if applicable)
- **Pass Criteria**: 100% processing activities have legal basis

**Test 2: Data Subject Rights**
- Test DSR portal functionality (submit test requests)
- Verify identity verification procedures
- Check response timing (GDPR: 30 days, CCPA: 45 days)
- Sample completed DSRs and verify completeness
- Test "Do Not Sell" mechanism (CCPA)
- **Pass Criteria**: 100% functional DSR portal, 95% responses within SLA

**Test 3: Privacy Notices**
- Review privacy policy (current, complete, accessible)
- Verify notice at collection (all data collection points)
- Check cookie notices and consent management
- Review employee privacy notices
- **Pass Criteria**: 100% collection points have notices

**Test 4: Data Protection Impact Assessment (DPIA)**
- Identify high-risk processing activities (automated decisions, PHI, large-scale PII)
- Verify DPIA completed for each high-risk activity
- Review DPIA quality (risks identified, mitigations documented)
- Check DPO consultation documented
- **Pass Criteria**: 100% high-risk activities have current DPIA

**Test 5: Vendor Management**
- Sample vendors processing personal data
- Verify Data Processing Agreements (DPAs) signed
- Review DPA completeness (all required clauses)
- Check subprocessor disclosure and approval
- Verify vendor security assessments
- **Pass Criteria**: 100% vendors have signed DPAs

**Test 6: International Data Transfers**
- Identify all cross-border data transfers
- Verify appropriate transfer mechanism (adequacy, SCCs, BCRs)
- Review Transfer Impact Assessments (TIA) for high-risk transfers
- Check data residency controls (EU data in EU region)
- **Pass Criteria**: 100% transfers have legal mechanism

**Test 7: Breach Notification**
- Review data breaches from past year
- Verify 72-hour notification to supervisory authority (GDPR)
- Check notification to data subjects (if high risk)
- Verify breach documentation (what, when, impact, mitigation)
- **Pass Criteria**: 100% breaches properly reported

## 3. Audit Reporting

### 3.1 Audit Findings Classification

**Critical Finding**:
- **Definition**: Severe control deficiency with immediate risk of regulatory violation, data breach, or significant business impact
- **Examples**:
  - No encryption for PHI
  - Access controls completely bypassed
  - HIPAA breach not reported within 60 days
  - Critical vulnerability unpatched >30 days
- **Management Response Required**: Immediate (24-48 hours)
- **Remediation Timeline**: 7 days
- **Escalation**: Executive leadership, board notification

**High Finding**:
- **Definition**: Significant control deficiency that could lead to compliance violation or material impact
- **Examples**:
  - High-risk model deployed without CAB approval
  - Quarterly access reviews not completed
  - MFA not enforced for confidential data access
  - DPIA not completed for high-risk processing
- **Management Response Required**: 5 business days
- **Remediation Timeline**: 30 days
- **Escalation**: Senior management

**Medium Finding**:
- **Definition**: Moderate control deficiency requiring attention but limited immediate risk
- **Examples**:
  - Documentation incomplete for medium-risk models
  - Access reviews completed late (but within 60 days)
  - Data quality checks configured but not monitored
  - Training completion 85% (target 95%)
- **Management Response Required**: 10 business days
- **Remediation Timeline**: 90 days
- **Escalation**: Department management

**Low Finding**:
- **Definition**: Minor deficiency or opportunity for improvement
- **Examples**:
  - Policy formatting inconsistencies
  - Non-critical documentation gaps
  - Process inefficiencies
  - Best practice recommendations
- **Management Response Required**: 15 business days
- **Remediation Timeline**: 180 days (or next policy cycle)
- **Escalation**: Process owner

**Observation**:
- **Definition**: Notable item not rising to level of deficiency, informational
- **Examples**:
  - Upcoming regulatory changes
  - Emerging best practices
  - Process improvement opportunities
  - Positive control performance
- **Management Response Required**: Optional
- **Remediation Timeline**: N/A
- **Escalation**: None

### 3.2 Audit Report Structure

**Executive Summary** (1-2 pages):
- Audit objective and scope
- Audit period and completion date
- Overall audit opinion (Satisfactory, Needs Improvement, Unsatisfactory)
- Summary of findings (count by severity)
- Key themes and trends
- Critical action items

**Background** (0.5-1 page):
- Context for audit
- Prior audit history
- Changes since last audit
- Relevant regulations or standards

**Scope and Methodology** (1 page):
- Audit scope (what was included/excluded)
- Audit approach and procedures
- Sample sizes and selection methods
- Limitations or constraints

**Detailed Findings** (main body):
For each finding:
1. **Finding Title**: Clear, concise description
2. **Severity**: Critical/High/Medium/Low
3. **Control Objective**: What control was tested
4. **Condition**: What we found (actual state)
5. **Criteria**: What should be (required state)
6. **Cause**: Why the deficiency exists (root cause)
7. **Effect/Risk**: Consequence if not remediated
8. **Recommendation**: How to fix (specific, actionable)
9. **Management Response**:
   - Agreement or disagreement
   - Action plan
   - Responsible party
   - Target completion date
10. **Auditor Evaluation**: Auditor assessment of management response

**Positive Observations** (optional):
- Controls that worked well
- Areas of excellence
- Improvements since last audit

**Appendices**:
- Detailed testing results
- Sample lists
- Supporting documentation
- Audit team and contacts

### 3.3 Audit Opinion Levels

**Satisfactory** (Green):
- All critical controls operating effectively
- No critical or high findings
- Medium/low findings are isolated and being addressed
- Strong control culture and governance
- Recommendation: Continue current approach with minor enhancements

**Needs Improvement** (Yellow):
- Most controls operating but notable deficiencies
- May have high findings or multiple medium findings
- Some systemic issues identified
- Control culture needs strengthening
- Recommendation: Remediation plan required, follow-up audit in 6 months

**Unsatisfactory** (Red):
- Significant control deficiencies
- Critical or multiple high findings
- Systemic control failures
- Weak control culture
- Recommendation: Immediate remediation, executive involvement, follow-up audit in 3 months

### 3.4 Report Distribution

**Internal Audit Reports**:
- Auditee (process owner, department manager)
- Senior management (VP, Director)
- Compliance team
- Risk management
- Internal audit department

**External Audit Reports** (SOC 2, HIPAA):
- Executive leadership (CEO, CTO, CFO)
- Board of directors (audit committee)
- Compliance team
- External auditor
- Legal counsel
- Customers (SOC 2 report upon request)

**Regulatory Audit Reports**:
- Regulatory authority (as required)
- Executive leadership
- Legal counsel
- Board of directors
- External counsel (if applicable)

## 4. Audit Follow-Up

### 4.1 Corrective Action Plan (CAP)

**Required Components**:
1. **Finding Reference**: Link to original finding
2. **Root Cause Analysis**: Why the deficiency occurred
3. **Corrective Actions**: Specific steps to remediate (not just "will improve")
4. **Preventive Actions**: How to prevent recurrence
5. **Responsible Party**: Named individual (not just role)
6. **Target Completion Date**: Realistic, risk-based timeline
7. **Status Updates**: Progress reports (monthly for critical/high)
8. **Evidence of Completion**: Documentation showing remediation

**CAP Template**:
```markdown
### Corrective Action Plan - [Finding ID]

**Finding Summary**: [Brief description]
**Severity**: [Critical/High/Medium/Low]
**Target Completion**: [Date]

#### Root Cause Analysis
[Why did this happen? Identify underlying causes, not just symptoms]

#### Corrective Actions
1. [Specific action to fix the immediate issue]
2. [Additional action if needed]
3. [...]

#### Preventive Actions
1. [How to prevent this from happening again]
2. [Process improvements, automation, training, etc.]

#### Responsible Party
- Owner: [Name, Title]
- Support: [Names of supporting team members]

#### Timeline and Milestones
| Milestone | Target Date | Status | Completion Date |
|-----------|-------------|--------|-----------------|
| [Action 1] | [Date] | [Not Started/In Progress/Complete] | [Actual date] |
| [Action 2] | [Date] | [Not Started/In Progress/Complete] | [Actual date] |

#### Evidence of Completion
[What evidence will demonstrate this is fixed?]
- [ ] Policy updated and approved
- [ ] Controls implemented and tested
- [ ] Training completed
- [ ] Documentation updated
- [ ] [Other evidence...]

#### Status Updates
- [Date]: [Update on progress]
- [Date]: [Next update]
```

### 4.2 Follow-Up Audit Procedures

**Timing**:
- Critical findings: 30-day follow-up
- High findings: 90-day follow-up
- Medium findings: Next scheduled audit
- Low findings: Next annual audit

**Procedure**:
1. **Review CAP**: Verify actions are appropriate and complete
2. **Test Controls**: Re-perform original audit tests
3. **Inspect Evidence**: Review documentation of remediation
4. **Interview Personnel**: Confirm understanding and adoption
5. **Validate Effectiveness**: Ensure control is operating over time (not just fixed once)

**Outcomes**:

**Closed - Remediated**:
- Finding fully addressed
- Control operating effectively
- Evidence sufficient
- No further action needed

**Closed - Accepted Risk**:
- Management accepts residual risk
- Executive approval documented
- Compensating controls in place
- Periodic re-evaluation scheduled

**Open - In Progress**:
- Actions underway but not complete
- Revised timeline approved
- Progress satisfactory
- Continue monitoring

**Open - Overdue**:
- Past target completion date
- Insufficient progress
- Escalation required
- Executive notification

**Re-opened**:
- Originally closed but issue recurred
- Control not sustainable
- New finding created
- Root cause re-analysis needed

### 4.3 Audit Issue Tracking

**Audit Issue Register**:
All findings are tracked in centralized register with:

- Issue ID (unique identifier)
- Audit name and date
- Finding severity
- Finding description
- Control area
- Root cause
- Recommendation
- Management response
- Responsible party
- Target completion date
- Current status
- Closure date
- Evidence location

**Reporting**:
- Monthly: Critical and high findings to executive leadership
- Quarterly: All open findings to senior management
- Annual: Summary of year's findings and trends to board

**Metrics**:
- Open findings by severity
- Average time to closure
- Overdue findings count
- Repeat findings (same issue multiple audits)
- Findings by control area (identify weak areas)

## 5. Continuous Monitoring and Automated Auditing

### 5.1 Continuous Monitoring Program

**Objective**: Detect control deficiencies in real-time or near real-time, rather than waiting for periodic audits.

**Monitoring Categories**:

**Security Monitoring**:
- AWS Config rules (continuous compliance checks)
- GuardDuty alerts (threat detection)
- Security Hub findings (aggregated security posture)
- CloudWatch alarms (infrastructure monitoring)
- SIEM alerts (security events)

**Access Monitoring**:
- IAM Access Analyzer (overly permissive access)
- Failed authentication attempts
- Privilege escalation attempts
- Access from unusual locations
- Off-hours access to sensitive data

**Data Governance Monitoring**:
- Data quality scores (daily)
- Unclassified datasets
- Retention policy violations
- DSR SLA compliance
- Encryption status

**Model Governance Monitoring**:
- Unapproved model deployments
- Missing documentation
- Performance degradation
- Retraining schedule compliance
- Monitoring gaps

**Compliance Monitoring**:
- HIPAA control status
- GDPR/CCPA compliance metrics
- SOC 2 control effectiveness
- Training completion rates
- Policy acknowledgments

### 5.2 Automated Audit Procedures

**Infrastructure as Code (IaC) Scanning**:
```bash
# Example: Automated Terraform compliance checking
terraform plan -out=tfplan
terraform show -json tfplan | tfsec --no-color
terraform-compliance -p tfplan -f compliance-rules/

# Checks:
# - Encryption enabled for all S3 buckets
# - Security groups not open to 0.0.0.0/0
# - IAM policies follow least privilege
# - Required tags present
```

**Policy-as-Code with OPA (Open Policy Agent)**:
```rego
# Example: Verify model deployment has required approval

package mlops.model_governance

deny[msg] {
  input.model.risk_classification == "high"
  not input.approvals.cab_approval
  msg := sprintf("High-risk model %s requires CAB approval", [input.model.name])
}

deny[msg] {
  input.model.risk_classification == "medium"
  not input.approvals.manager_approval
  msg := sprintf("Medium-risk model %s requires manager approval", [input.model.name])
}
```

**Automated Access Reviews**:
```python
# Example: Automated access review script

import boto3
from datetime import datetime, timedelta

iam = boto3.client('iam')

def audit_unused_access():
    issues = []
    users = iam.list_users()['Users']

    for user in users:
        # Check last activity
        access_keys = iam.list_access_keys(UserName=user['UserName'])['AccessKeyMetadata']
        for key in access_keys:
            last_used = iam.get_access_key_last_used(AccessKeyId=key['AccessKeyId'])
            if last_used.get('AccessKeyLastUsed'):
                last_used_date = last_used['AccessKeyLastUsed']['LastUsedDate']
                days_unused = (datetime.now(last_used_date.tzinfo) - last_used_date).days

                if days_unused > 90:
                    issues.append({
                        'user': user['UserName'],
                        'access_key': key['AccessKeyId'],
                        'days_unused': days_unused,
                        'finding': 'Access key unused for >90 days'
                    })

    return issues

# Run daily, alert on findings
```

**Automated Compliance Reporting**:
```python
# Example: Daily compliance dashboard update

def generate_compliance_dashboard():
    metrics = {
        'encryption': {
            's3_buckets': check_s3_encryption(),
            'ebs_volumes': check_ebs_encryption(),
            'rds_instances': check_rds_encryption(),
            'compliance_rate': calculate_encryption_compliance()
        },
        'access_control': {
            'mfa_coverage': check_mfa_coverage(),
            'unused_credentials': count_unused_credentials(),
            'excessive_permissions': count_excessive_permissions()
        },
        'data_governance': {
            'classified_datasets': count_classified_datasets(),
            'quality_score': calculate_avg_quality(),
            'dsr_sla_compliance': check_dsr_sla()
        },
        'model_governance': {
            'approved_models': count_approved_models(),
            'documentation_complete': check_documentation(),
            'monitoring_coverage': check_monitoring_coverage()
        }
    }

    # Push to dashboard, alert on thresholds
    update_dashboard(metrics)
    alert_on_thresholds(metrics)
```

### 5.3 Audit Dashboard and Metrics

**Key Performance Indicators (KPIs)**:

| Metric | Target | Critical Threshold | Measurement Frequency |
|--------|--------|-------------------|---------------------|
| Encryption Coverage (Restricted Data) | 100% | <99% | Daily |
| MFA Coverage (PHI Access) | 100% | <100% | Daily |
| Unused Credentials (>90 days) | 0 | >5 | Daily |
| Data Classification Coverage | 100% | <95% | Daily |
| High-Risk Model Approval Compliance | 100% | <100% | Weekly |
| DSR Response Time (GDPR) | <30 days | >35 days | Daily |
| Critical Vulnerability Remediation | <7 days | >14 days | Daily |
| Access Review Completion | 100% | <90% | Quarterly |
| Training Completion | 100% | <95% | Monthly |
| Open Critical Findings | 0 | >1 | Continuous |

**Audit Dashboard Components**:
1. **Compliance Scorecard**: Overall health (green/yellow/red) by control area
2. **Trend Charts**: Metrics over time (improving/stable/declining)
3. **Open Findings**: Count by severity, age, responsible party
4. **Remediation Progress**: CAP status, % complete, overdue items
5. **Upcoming Audits**: Schedule, preparation status
6. **Key Risks**: Top risks from recent audits
7. **Recent Activity**: Latest audit reports, findings closed

## 6. Roles and Responsibilities

### 6.1 Audit Roles

| Role | Responsibilities | Required Skills |
|------|-----------------|----------------|
| **Internal Audit Manager** | - Audit program oversight<br>- Annual audit planning<br>- Resource allocation<br>- Stakeholder communication<br>- Executive reporting | - CPA, CIA, or equivalent<br>- 10+ years audit experience<br>- Management experience<br>- IT/security knowledge |
| **Lead Auditor** | - Audit planning and execution<br>- Team supervision<br>- Report writing<br>- Finding classification<br>- Follow-up audits | - 5+ years audit experience<br>- Technical expertise in audit area<br>- Communication skills<br>- Certifications (CISA, CISSP, etc.) |
| **IT Auditor** | - Technical testing<br>- Data analytics<br>- System configuration review<br>- Security testing<br>- Documentation | - 3+ years IT audit experience<br>- Technical skills (AWS, Linux, SQL)<br>- Security knowledge<br>- CISA or equivalent |
| **Data Privacy Auditor** | - GDPR/CCPA compliance testing<br>- DSR process audit<br>- Consent management review<br>- Privacy impact assessment | - Privacy certifications (CIPP, CIPM)<br>- Legal/compliance background<br>- Data protection expertise |
| **Compliance Specialist** | - Regulatory requirements mapping<br>- Compliance testing<br>- Evidence collection<br>- Remediation tracking | - Regulatory knowledge (HIPAA, SOC2)<br>- Attention to detail<br>- Compliance experience |
| **Auditee (Process Owner)** | - Provide evidence<br>- Respond to findings<br>- Implement corrective actions<br>- Maintain controls | - Domain expertise<br>- Control ownership<br>- Remediation authority |
| **Management** | - Approve CAPs<br>- Allocate resources<br>- Executive reporting<br>- Risk acceptance decisions | - Business judgment<br>- Resource authority<br>- Risk management |

### 6.2 Auditee Responsibilities

**Before Audit**:
- Review audit scope and prepare
- Gather requested documentation
- Ensure system access for auditors
- Designate audit liaison
- Brief team on audit process

**During Audit**:
- Respond promptly to auditor requests
- Provide accurate and complete information
- Facilitate interviews and observations
- Escalate blockers or concerns
- Maintain professional cooperation

**After Audit**:
- Review draft findings for factual accuracy
- Develop management responses and CAPs
- Obtain approvals for CAPs
- Implement corrective actions
- Provide progress updates
- Maintain evidence of remediation

## 7. Audit Documentation and Retention

### 7.1 Audit Workpapers

**Required Documentation**:
- Audit planning documents (scope, program, risk assessment)
- Evidence collection records (interviews, observations, testing)
- Analysis and conclusions
- Review notes (supervisory review)
- Correspondence with auditee
- Final audit report and management responses

**Workpaper Standards**:
- Clear and concise
- Sufficient to support conclusions
- Cross-referenced (finding → testing → evidence)
- Reviewed and approved by lead auditor
- Organized and indexed

**Electronic Workpaper Management**:
- Stored in secure, access-controlled repository
- Version controlled
- Searchable
- Backed up regularly

### 7.2 Retention Requirements

| Document Type | Retention Period | Storage Location | Disposal Method |
|--------------|------------------|------------------|-----------------|
| Audit reports (internal) | 7 years | Audit repository | Secure deletion |
| Audit workpapers | 7 years | Audit repository | Secure deletion |
| SOC 2 reports | Indefinite | Compliance repository | N/A |
| HIPAA audit records | Indefinite | Compliance repository | N/A |
| GDPR audit records | 7 years | Compliance repository | Secure deletion |
| CAPs and remediation evidence | 7 years | Issue tracking system | Secure deletion |
| Audit logs (system) | 7 years | S3 (Glacier after 1 year) | Lifecycle policy |
| External audit reports | Indefinite | Compliance repository | N/A |

**Legal Hold**: All retention periods subject to legal hold requirements. Do not dispose of documents under legal hold.

## 8. Training and Competency

### 8.1 Auditor Training Requirements

**Initial Training**:
- Audit methodology and standards
- Platform architecture and technology
- Governance policies and procedures
- Regulatory requirements (HIPAA, GDPR, etc.)
- Tool training (AWS, data analytics, etc.)

**Annual Training**:
- Regulatory updates
- New technologies and techniques
- Audit tool updates
- Lessons learned from audits
- 40 hours CPE (for certified auditors)

**Specialized Training (as needed)**:
- Machine learning and MLOps concepts
- Cloud security (AWS, Azure, GCP)
- Data privacy and protection
- Advanced data analytics
- Forensics and incident response

### 8.2 Auditee Training

**Audit Awareness Training** (Annual, all employees):
- Purpose of audits
- Audit process overview
- Employee responsibilities
- How to respond to audit requests
- Confidentiality and professionalism

**Control Owner Training** (Annual):
- Control design and operation
- Evidence collection and documentation
- Self-assessment techniques
- Corrective action planning
- Continuous improvement

## 9. Document Control

### 9.1 Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-10-17 | Internal Audit / Compliance Team | Initial audit procedures |

### 9.2 Review and Approval

- **Author**: Internal Audit Manager, Compliance Manager
- **Reviewed by**: CISO, Data Protection Officer, Legal Counsel
- **Approved by**: Chief Audit Executive, CTO
- **Next Review**: 2026-04-17 (Semi-annual)

### 9.3 Related Documents

- [Model Governance Framework](./model-governance-framework.md)
- [Data Governance Policy](./data-governance-policy.md)
- [Compliance Requirements Mapping](./compliance-requirements-mapping.md)
- [ADR-007: Security & Compliance Architecture](../architecture/adrs/007-security-compliance-architecture.md)
- [Risk Assessment](../business/risk-assessment.md)

## 10. Appendices

### Appendix A: Audit Checklists

See `/templates/audit-checklists/` for detailed checklists:
- Model Governance Audit Checklist
- Data Access Audit Checklist
- HIPAA Compliance Audit Checklist
- GDPR Compliance Audit Checklist
- Security Controls Audit Checklist

### Appendix B: Sample Audit Programs

See `/templates/audit-programs/` for detailed audit programs with step-by-step procedures.

### Appendix C: Audit Report Templates

See `/templates/audit-reports/` for standard audit report templates.

### Appendix D: Data Analytics Scripts

See `/scripts/audit-analytics/` for automated audit scripts and queries.

### Appendix E: Contact Information

- **Internal Audit**: internal-audit@company.com
- **Compliance Team**: compliance@company.com
- **HIPAA Security Officer**: hipaa-security@company.com
- **Data Protection Officer**: dpo@company.com
- **CISO**: ciso@company.com

---

**Document Classification**: Internal Use
**Last Review Date**: 2025-10-17
**Next Review Date**: 2026-04-17
