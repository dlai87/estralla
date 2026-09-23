# ADR-003: Inter-Cloud Networking Architecture

**Status**: Accepted
**Date**: 2024-01-15
**Impact**: High - Performance and Reliability

---

## Context

Multi-cloud requires inter-cloud communication for:
- Model artifact replication (10TB+ monthly)
- Cross-cloud API calls (1M+ requests/day)
- Disaster recovery failover
- Unified observability data

**Requirements**:
- Latency <50ms P95 (SLO for cross-cloud API calls)
- Bandwidth: 10+ Gbps sustained
- Security: Encrypted, private connectivity
- Cost: Minimize egress fees ($0.08-$0.12/GB)

---

## Decision

**Hybrid Approach**:

### Production: Dedicated Interconnects
- **AWS Direct Connect** + **GCP Cloud Interconnect** + **Azure ExpressRoute**
- Via **Megaport Cloud Router** (cloud exchange)
- 10 Gbps per link, 99.99% SLA
- Cost: $15K/month (cheaper than egress fees at scale)

```
┌────────────┐   10 Gbps    ┌──────────────┐   10 Gbps    ┌────────────┐
│    AWS     │◄────────────►│   Megaport   │◄────────────►│    GCP     │
│ us-east-1  │              │ Cloud Router │              │us-central1 │
└────────────┘              └──────┬───────┘              └────────────┘
                                   │ 10 Gbps
                                   ▼
                            ┌──────────────┐
                            │    Azure     │
                            │   eastus     │
                            └──────────────┘
```

### Dev/Staging: Site-to-Site VPN
- IPSec VPN over public internet
- 1 Gbps throughput
- Cost: $100/month (AWS VPN Gateway)
- Use case: Lower traffic, cost-sensitive environments

### Application Layer: Service Mesh
- **Istio** for cross-cloud service-to-service communication
- mTLS encryption
- Traffic shaping, retries, circuit breakers

---

## Alternatives Considered

**Alternative 1**: Public Internet Only
- ❌ Rejected: Latency unpredictable (100-500ms), security concerns

**Alternative 2**: Full Mesh Dedicated Circuits
- ❌ Rejected: $50K/month cost, overkill for current traffic

**Alternative 3**: SD-WAN (Cisco Meraki, VMware VeloCloud)
- ⚠️ Deferred: Consider for >20 regions, current scope doesn't justify

---

## Consequences

✅ **Performance**: 25-30ms latency (well under 50ms SLO)
✅ **Reliability**: 99.99% uptime on interconnects
✅ **Cost**: $15K/month interconnect vs $40K/month egress fees (62% savings)
✅ **Security**: Private connectivity, no public internet exposure
⚠️ **Complexity**: 3 interconnects to manage
⚠️ **Vendor Dependency**: Megaport as critical path

**Mitigation**: Maintain VPN as backup, monitor Megaport SLA

---

**Approved By**: Cloud Architect, VP Engineering, Network Team Lead
