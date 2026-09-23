# Data Residency Matrix

**Owner**: Privacy + Cloud Architecture
**Status**: Approved input to ADR-002 (data sovereignty)
**Audience**: Architects, compliance, customer success, legal

This document is the authoritative reference for **where each class of customer data may reside**, **which clouds and regions are approved** for it, **what encryption is required**, and **what we owe customers** when something changes (relocation notice, breach notification).

The matrix is the contract we make with ourselves. Implementation enforces it through Terraform module guards (`policy-as-code` package), Crossplane `CompositionRevision` validation, and CI checks on `kustomize` overlays.

---

## 1. Data classes

We classify all data into five classes. Class drives which residency rules apply.

| Class | Examples | Default sensitivity |
|---|---|---|
| **C1 — Public** | Marketing site assets, public model cards, OSS code, documentation | Low |
| **C2 — Internal** | Internal dashboards, anonymized analytics, build artifacts | Medium |
| **C3 — Customer** | Customer account metadata, model artifacts authored by customers, non-PII inference inputs | High |
| **C4 — Personal data (GDPR / CCPA / PIPL / DPDPA / PDPL)** | Identifiable individual data, PII, customer PII, employee PII | Very high |
| **C5 — Special category** | Health data (HIPAA / PHIPA), payment data (PCI-DSS), biometric, government-restricted | Critical |

A workload's class is the **maximum** class of any data it touches. A pipeline that joins C2 with C4 is C4 end to end.

---

## 2. Regulatory map

The four regions in scope, with the regulations that bind each.

### 2.1 United States

- **CCPA / CPRA** (California) — applies to California residents' personal data; right to know, delete, opt-out of sale/share; 45-day response window; "do not sell" honored via the Global Privacy Control signal
- **HIPAA** — protected health information; Business Associate Agreement required with each cloud subprocessor; PHI must be encrypted at rest and in transit; access logged and reviewable for 6 years
- **VCDPA, CTDPA, CPA, UCPA**, etc. — state-level. Effective practice: build to CCPA, layer additional notice/opt-out per state
- **GLBA, SOX** — financial data, applicable to our enterprise FS customers
- **Section 889 NDAA, CMMC** — if government workload; not in baseline scope but capacity reserved (GovCloud + Azure Government)

### 2.2 European Union and UK

- **GDPR** — personal data, EEA + UK (UK GDPR is mirror); Schrems II and Data Privacy Framework constrain transatlantic transfer; SCCs + supplementary measures otherwise; 72-hour breach notification
- **EU AI Act** — risk-tiered obligations on AI systems; transparency, technical documentation, post-market monitoring; in force 2026 with staged applicability
- **DORA** — financial services operational resilience; multi-cloud exit plans required
- **NIS2** — cybersecurity for critical entities; incident reporting

### 2.3 APAC

- **PIPL (China)** — strict cross-border transfer assessment; data localization for "important data"; security assessment required by CAC for outbound transfers above thresholds
- **PDPA (Singapore)** — consent, purpose limitation, breach notification 72h
- **APPI (Japan)** — onward transfer requires explicit consent or approved jurisdictions
- **Privacy Act 1988 (Australia)** — APP-bound; OAIC notification required
- **DPDPA (India), 2023** — recently enacted; consent + notice; cross-border allowed except for negative list (TBD); 72h breach notification expected

### 2.4 Middle East

- **PDPL (UAE), 2021** + DIFC Data Protection Law (separate, stricter); transfers permitted to adequate jurisdictions or with SCC-equivalent
- **PDPL (Saudi Arabia), 2023** — SDAIA-administered; data localization for some sectors; transfer permits required for personal data outside KSA in defined cases
- **PDPA (Qatar, Bahrain)** — sector-aware; financial sector additionally regulated by central bank

---

## 3. The matrix

For each region (rows) and data class (columns), the allowed clouds and zones, the encryption posture, and the special obligations are listed.

### 3.1 United States

| Class | Allowed clouds | Allowed regions | Encryption at rest | Encryption in transit | Special |
|---|---|---|---|---|---|
| C1 | AWS, GCP, Azure | Any | AES-256 (cloud-managed) | TLS 1.2+ | None |
| C2 | AWS, GCP, Azure | US regions preferred; EU allowed | AES-256 (cloud-managed) | TLS 1.2+ | Egress logged |
| C3 | AWS, GCP, Azure | `us-east-1`, `us-east-2`, `us-west-2`, `us-central1`, `us-east4`, `eastus`, `westus2`, `westus3` | AES-256 (CMK in customer KMS / HSM-backed) | TLS 1.2+ mTLS for service-to-service | Cross-region replication allowed only to other US |
| C4 | AWS, GCP, Azure | Same as C3 | CMK in KMS, key rotation ≤ 365d, BYOK option for tier-1 customers | TLS 1.3 preferred; mTLS service-to-service | DSR pipeline mandatory; access logged + reviewable |
| C5 (PHI) | AWS, GCP, Azure (BAA in place for each) | Same as C3, restricted to BAA-covered services | CMK in KMS, **CMK rotation ≤ 90d**, key never crosses cloud boundary | TLS 1.3, mTLS for all inter-service | Audit log to immutable store, 6y retention; quarterly access review; HIPAA security risk assessment annual |
| C5 (PCI) | AWS, GCP, Azure (PCI-DSS Level 1 attestations on file) | PCI-scoped subaccount/project/subscription | CMK + tokenization for PAN | TLS 1.3, mTLS, FIPS 140-2 Level 2 ciphers | PCI scope reduction; pen test quarterly |

### 3.2 European Union + UK

| Class | Allowed clouds | Allowed regions | Encryption at rest | Encryption in transit | Special |
|---|---|---|---|---|---|
| C1 | AWS, GCP, Azure | Any | AES-256 (cloud-managed) | TLS 1.2+ | None |
| C2 | AWS, GCP, Azure | EU regions preferred; UK allowed | AES-256 (cloud-managed) | TLS 1.2+ | Egress to non-EU logged |
| C3 | AWS, GCP, Azure | `eu-west-1`, `eu-central-1`, `eu-north-1`, `europe-west1`, `europe-west4`, `westeurope`, `northeurope`, `uksouth` | AES-256, CMK in EU-hosted KMS | TLS 1.2+, mTLS service-to-service | Sub-processor list maintained per GDPR Art. 28 |
| C4 | AWS (`eu-west-1`, `eu-central-1`), GCP (`europe-west1`, `europe-west4`), Azure (`westeurope`, `northeurope`) | EU only | CMK in EU-hosted KMS, BYOK for tier-1; HYOK option available with HSM | TLS 1.3, mTLS | DPIA on file; SCCs + supplementary measures for any outbound transfer; DSR pipeline; 30-day fulfillment SLA; 72h breach notification |
| C4 — UK | AWS (`eu-west-2`), GCP (`europe-west2`), Azure (`uksouth`, `ukwest`) | UK only by default | CMK in UK-hosted KMS | TLS 1.3, mTLS | UK ICO-aligned; UK IDTA for transfers to non-adequate jurisdictions |
| C5 (PHI under national health systems) | AWS, GCP, Azure with national HDS/Cyber Essentials Plus where required | National-specific (e.g., HDS in FR uses AWS Paris) | CMK rotation ≤ 90d; HSM-backed | TLS 1.3, mTLS, eIDAS-compliant where applicable | National DPA notification path; sector-specific certifications (HDS, ISO 27018, C5) |

For all C4/C5 in EU: **no replication into US** unless the customer explicitly opts in via a documented Schrems II flow.

### 3.3 APAC

| Country | Class | Allowed clouds | Allowed regions | Encryption | Special |
|---|---|---|---|---|---|
| Singapore | C3/C4 | AWS, GCP, Azure | `ap-southeast-1`, `asia-southeast1`, `southeastasia` | CMK in SG-hosted KMS for C4 | PDPA; cross-border to adequate jurisdictions allowed |
| Japan | C3/C4 | AWS, GCP, Azure | `ap-northeast-1`, `asia-northeast1`, `japaneast` | CMK in JP-hosted KMS for C4 | APPI; onward transfer notice |
| Australia | C3/C4 | AWS, GCP, Azure | `ap-southeast-2`, `australia-southeast1`, `australiaeast` | CMK in AU-hosted KMS for C4 | Privacy Act + OAIC NDB scheme |
| China (mainland) | C3/C4 | AWS China (Ningxia/Beijing via Sinnet/NWCD), Azure China (operated by 21Vianet) | Per provider | CMK in CN-hosted KMS; key material never leaves CN | PIPL; security assessment for cross-border transfer; **no GCP** (no compliant region) |
| India | C3/C4 | AWS, GCP, Azure | `ap-south-1`, `ap-south-2`, `asia-south1`, `asia-south2`, `centralindia`, `southindia` | CMK in IN-hosted KMS for C4 | DPDPA; cross-border allowed except for negative list (monitored quarterly) |
| Korea | C3/C4 | AWS, GCP, Azure | `ap-northeast-2`, `asia-northeast3`, `koreacentral` | CMK in KR-hosted KMS for C4 | PIPA; cross-border requires consent + adequate safeguards |
| Indonesia | C3/C4 | AWS, GCP, Azure | `ap-southeast-3`, `asia-southeast2`, `indonesiacentral` (limited) | CMK in ID-hosted KMS for C4 | PDP Law 2022; localization for some sectors |

### 3.4 Middle East

| Country | Class | Allowed clouds | Allowed regions | Encryption | Special |
|---|---|---|---|---|---|
| UAE | C3/C4 | AWS, Azure, (GCP via Doha region or partner) | `me-central-1`, `uaenorth` (Dubai/Abu Dhabi); GCP via partner if needed | CMK in UAE-hosted KMS for C4 | PDPL (UAE) + DIFC DPL where DIFC entities; SCC-equivalent for outbound |
| Saudi Arabia | C3/C4 | AWS, Azure | `me-south-1` (Bahrain — used by some KSA workloads), local KSA region (`me-central-2` planned / Azure KSA region) | CMK in KSA-hosted KMS for C4 | SDAIA PDPL; localization for "important data"; cross-border by permit |
| Qatar / Bahrain | C3 | AWS (`me-south-1`), Azure (`qatarcentral`) | Per cloud | CMK in regional KMS | Local DPAs; financial sector additional rules |

For sovereign-cloud commitments (e.g., government tenants), see ADR-002 amendments; sovereign clouds (AWS Sovereign Cloud EU, Azure Local for KSA, GCP Sovereign Cloud partners) are tracked but not yet in production scope.

---

## 4. Encryption requirements (consolidated)

### 4.1 At rest

| Tier | Key management | Rotation | Notes |
|---|---|---|---|
| Standard (C1/C2) | Cloud-managed KMS (AWS KMS aws/, GCP Google-managed, Azure Microsoft-managed) | Provider default | OK for non-sensitive |
| Default sensitive (C3) | Customer-managed key (CMK) per workload, in regional KMS / Cloud KMS / Key Vault | ≤ 365 days | Audit logs to immutable store |
| Personal data (C4) | CMK per tenant, regional KMS | ≤ 365 days | BYOK on request; logs reviewable by tenant within 7 days |
| Special category (C5) | CMK per tenant + HSM-backed (AWS CloudHSM / GCP Cloud HSM / Azure Managed HSM); HYOK option | ≤ 90 days for PHI/PCI | Key material never crosses cloud boundary; rotation event logged |

### 4.2 In transit

- TLS 1.2 minimum everywhere; TLS 1.3 mandatory for C4/C5
- mTLS for service-to-service inside the mesh (SPIFFE-issued certs)
- VPN / private interconnect (Megaport / Direct Connect / Cloud Interconnect / ExpressRoute) for cross-cloud, never public internet for C3+
- IPSec + MACsec on Megaport between cloud edges where supported
- Sensitive document transit (e.g., contracts, audit packages) uses Signal-Protocol-based encrypted file delivery, not plain S3 pre-signed URLs

---

## 5. Customer notification SLAs

When data location or processing changes, or when something goes wrong, the platform owes customers a notice. SLAs:

| Event | SLA | Channel |
|---|---|---|
| Planned region addition (no migration) | 30 days advance | Customer portal + email to data-protection contact |
| Planned data migration (region change) | 60 days advance, opt-in confirmation required for C4/C5 | Email + DPA addendum |
| New subprocessor (cloud provider, SaaS) | 30 days advance per GDPR Art. 28 | Email + sub-processor list update |
| Security incident — confirmed personal-data breach | 72 hours from confirmation | Email + portal; regulator notification via legal |
| Security incident — suspected but unconfirmed | 24 hours acknowledgement of investigation | Email |
| Regulator data request (subpoena, lawful order) | "As soon as legally permitted" — sometimes immediate, sometimes after gag period lifts | Email + legal coordination |
| Service unavailability impacting compliance posture | 4 hours notification once confirmed | Statuspage + email |

DPA addenda are auto-rendered from a template and posted to the customer's DPA repository; the customer can withdraw consent for C4/C5 migrations and trigger an alternative path.

---

## 6. Operational enforcement

The matrix is enforced before runtime, not after.

### 6.1 Policy-as-code

- **OpenTofu module library** wraps all data-storage resources (`s3`, `gcs`, `azblob`, `rds`, `aurora`, `bigquery`, `cosmosdb`, etc.) with mandatory `class` and `region_class` inputs. Invalid combinations fail at `plan`.
- **OPA / Gatekeeper** policies on every Kubernetes cluster:
  - `disallow-c4-in-us-namespace-targeting-eu-tenant`
  - `require-cmk-on-c4-buckets`
  - `disallow-public-buckets`
  - `require-class-label`
- **Cloud Custodian** lambdas run nightly to detect drift (e.g., a manually created S3 bucket without CMK).

### 6.2 Discovery

- Macie (AWS), DLP API (GCP), Purview (Azure) scan storage for PII / PHI patterns nightly; findings raise a Jira ticket against the data owner.
- Snowflake row-access policies enforce tenant + region restrictions in the analytics warehouse.

### 6.3 Tenant tagging

Every tenant's metadata record declares:

- Primary residency (e.g., `eu`)
- Allowed residencies (e.g., `[eu, uk]`)
- Class ceiling (`c3`, `c4`, `c5`)

Placement decisions and replication policies derive from these tenant attributes; tenants cannot be silently moved.

---

## 7. Change control

Updates to this matrix follow the ADR process. A change requires:

1. Privacy counsel review
2. Compliance lead approval
3. Architecture review board (ARB) sign-off
4. Customer-success and sales review for downstream comms
5. CI update to policy-as-code with end-to-end test passing

Material changes (adding/removing a region, changing the encryption tier for a class) trigger §5 notifications.

The matrix is reviewed in full **every six months**, or sooner if:

- A new region becomes generally available in a cloud we use
- A regulation in scope materially changes (e.g., DPDPA negative list publication)
- A customer onboarding pushes us into a new jurisdiction

---

## 8. Open questions / watch list

- **EU AI Act implementing acts**: as detailed obligations land, the matrix may grow an "AI-system class" dimension separate from data class.
- **GCC Cloud-First / Sovereign Cloud**: KSA sovereignty offerings via Azure Local + AWS Dedicated Local Zones are evolving; will update Q3.
- **India DPDPA negative list**: not yet published; we treat all of C4/C5 as IN-resident until clarity arrives.
- **US state laws** (Texas, Oregon, etc.): being layered; expected unified compliance posture via "build to CCPA + Virginia VCDPA" continues to hold.
- **Schrems II successor (DPF)**: monitor for invalidation; SCC fallback already in place.

---

## 9. References

- ADR-001 (multi-cloud strategy)
- ADR-002 (data sovereignty)
- ADR-003 (intercloud networking)
- `architecture/business/cost-analysis.md` (cost implications of region restrictions)
- `architecture/research/cloud-comparison.md` (per-cloud regional service availability)
- DPA template: `legal/templates/dpa-v4.md`
- Subprocessor list: `legal/subprocessors.md`
- GDPR Art. 28, 32, 33, 44–50
- HIPAA Security Rule (45 CFR 164.302–318)
- CCPA / CPRA, PIPL, DPDPA (India), PDPL (UAE / KSA)
