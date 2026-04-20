# Phase 2-3 Research Plan: Deferred Technical Unknowns

**Document:** Framework for measuring and validating Phase 1 MVP outcomes to inform Phase 2-3 architecture
**Date:** 2025-11-12
**Version:** 1.0 (Research agenda for Phase 1 → Phase 2 transition)
**Status:** Ready for Phase 1 execution

---

## Executive Summary

Phase 1 (MVP) deliberately defers 5 major technical decisions to Phase 2, with measurement taking priority over speculation. This document outlines:

1. **What we need to measure** during Phase 1 execution
2. **How we'll measure it** (metrics, collection methods)
3. **What threshold answers the question** (decision gates)
4. **How findings inform Phase 2-3 architecture** (impact on costs, scope, design)

**Key principle:** Data from real pilot networks trumps theoretical models. Phase 1's job is to **instrument the system** so Phase 2 can make informed choices.

---

## Research Questions Framework

| Research Q | Why It Matters | Phase 1 Data Collection | Decision Gate | Phase 2 Impact |
|------------|----------------|------------------------|----------------|--|
| **Q1: Node Ranking Metric** | How to route queries to fastest node? | Response time percentiles per node | p95 <200ms on rank leader | Traffic routing algorithm |
| **Q2: IPFS Consistency Model** | Is eventual consistency acceptable? | Snapshot latency, sync failures | <2h max drift acceptable? | Federation protocol design |
| **Q3: Local SLM Quality** | Can 7B model replace Mistral? | SLM vs Mistral accuracy, latency | >90% accuracy on Cypher? | €420/year cost saving |
| **Q4: Hardware Requirements** | What do validator nodes need? | CPU/memory/storage usage per node | CPU-only viable? | Network adoption barrier |
| **Q5: Main Node Selection** | Should main node be special? | Consolidation workload, write pressure | <10ms writes? | Governance model (rotating vs fixed) |

---

## Q1: Node Ranking & Traffic Routing Metric

### Question
**"What metric should rank nodes for query routing? Response time? Uptime? Throughput?"**

### Why This Matters

- **Fallback if central hub fails:** Without a ranking metric, we can't route queries to the next-best node
- **Scale efficiently:** As more validator nodes join, we need automated load balancing
- **Cost implication:** Wrong metric = wasted bandwidth on slow nodes; right metric = optimal utilization

### Phase 1 Data Collection

**What to measure:**
- Response time (p50, p95, p99) for each query type per node
- Uptime % (detect when nodes go offline)
- Throughput (queries/second capacity)
- Bandwidth utilization
- Network latency (round-trip time to each node)

**Collection method:**
```
Implementation (Week 3-4 of Phase 1):
├─ Add response time logging to every API endpoint
├─ Store in admin dashboard: /admin/health/performance
├─ For each node in system:
│  ├─ Track p50/p95/p99 latency
│  ├─ Calculate uptime %
│  └─ Monitor error rate
└─ Weekly report: Which node is fastest? Most reliable?
```

**Data structure:**
```json
{
  "timestamp": "2025-11-12T14:30:00Z",
  "nodes": [
    {
      "node_id": "central-hub",
      "region": "eu-west-1",
      "uptime_percent": 99.87,
      "response_times": {
        "spaces_query_p95_ms": 120,
        "partnerships_query_p95_ms": 210,
        "lnm_query_p95_ms": 1200
      },
      "throughput_queries_per_second": 25,
      "rank_score": 0.95  // Calculated from above
    }
  ]
}
```

### Success Criteria (Decision Gate)

✅ **Q1a: Is response time variance >50ms across nodes?**
- If YES → Implement ranking by p95 latency (fastest wins)
- If NO → Uptime + reliability matter more; use hybrid scoring

✅ **Q1b: Can we achieve <200ms p95 on any node?**
- If YES → Distributed model viable; proceed with Phase 2 validator rollout
- If NO → May need to reconsider node placement (closer to users?)

✅ **Q1c: Which query type is most expensive?**
- Track cost (Mistral tokens) vs latency for LLM queries
- If LLM queries <5% of traffic → Focus optimization on graph queries
- If LLM queries >20% of traffic → Prioritize SLM migration to Phase 2

### Phase 2-3 Impact

**If routing by latency works:**
- Implement automatic node ranking in Phase 2
- Add DNS round-robin or API gateway health checks
- Cost: <€5k development

**If routing is unreliable:**
- Consider sticky sessions (users always talk to same node)
- Rethink validator node deployment (maybe don't need many)
- Cost impact: May delay Phase 3 federation; stays centralized longer

**Successor research:** Q5 (Main node role) depends on Q1 answer

---

## Q2: IPFS Consistency Model & Snapshot Integrity

### Question
**"Is eventual consistency (IPFS latency) acceptable for Maps of Making? How fresh does data need to be?"**

### Why This Matters

- **Data freshness guarantee:** If main hub fails at 2pm, when can replicas see the latest data?
- **Cost:** More frequent snapshots = higher IPFS pinning costs
- **User experience:** Stale map data erodes trust ("Space closed last week but still shows as open")

### Phase 1 Data Collection

**What to measure:**
- Snapshot frequency (how often do we export to IPFS?)
- Snapshot latency (time between data change in Neo4j → availability on IPFS)
- Snapshot integrity (do snapshots match live Neo4j?)
- Consumer behavior (do networks care about freshness?)

**Collection method:**
```
Implementation (Week 2-8 of Phase 1):
├─ Scheduled exports (nightly = baseline)
│  ├─ Every night at 2am UTC, export full GraphML
│  ├─ Calculate hash of export
│  ├─ Store on IPFS
│  └─ Log to admin dashboard: /admin/federation/snapshots
├─ Verification script (nightly)
│  ├─ Download latest snapshot from IPFS
│  ├─ Compare sample of 50 random spaces vs live Neo4j
│  ├─ Report: Any discrepancies?
│  └─ Alert if mismatch >0.1%
└─ Weekly cost tracking
   ├─ IPFS storage size (current snapshot + archive)
   ├─ Pinning cost (monthly projection)
   └─ Vs. COST-SUSTAINABILITY.md budget (€30-50/month)
```

**Data structure:**
```json
{
  "period": "2025-11-05 to 2025-11-12",
  "snapshots": [
    {
      "timestamp": "2025-11-12T02:00:00Z",
      "ipfs_hash": "QmXxxx...",
      "size_mb": 52,
      "neo4j_snapshot_time": "2025-11-12T02:00:00Z",
      "ipfs_availability_time": "2025-11-12T02:15:00Z",
      "latency_minutes": 15,
      "spaces_in_snapshot": 250,
      "integrity_check": {
        "passed": true,
        "sample_size": 50,
        "mismatches": 0,
        "confidence_percent": 100
      }
    }
  ],
  "archive_summary": {
    "total_snapshots_stored": 30,
    "total_size_mb": 1560,
    "estimated_monthly_cost_eur": 31.50,
    "snapshots_reachable_on_ipfs": 30,
    "availability_percent": 100
  },
  "consistency_questions": {
    "worst_case_latency_hours": 15,
    "average_latency_minutes": 7,
    "max_stale_data_tolerance_hours": "?"  // Network feedback needed
  }
}
```

### Success Criteria (Decision Gate)

✅ **Q2a: Is IPFS latency <1 hour for 99% of snapshots?**
- If YES → Reasonable for fallback use; data freshness acceptable
- If NO → May need more frequent snapshots or alternative (CRDTs, P2P replication)

✅ **Q2b: Is snapshot integrity >99%?**
- If YES → IPFS is trustworthy as backup
- If NO → Investigate corruption; may need checksums/signatures

✅ **Q2c: Do networks care about 12-24h data staleness?**
- Survey during Phase 1: "If main hub dies, is yesterday's data acceptable?"
- If YES (>80% say yes) → Nightly snapshots sufficient; stay with current model
- If NO (>50% need fresher) → Increase to 4-6 hour snapshots; cost impact: +€10-15/month

✅ **Q2d: Is IPFS cost tracking accurate?**
- Does real pinning cost match COST-SUSTAINABILITY.md budget (€30-50)?
- If YES → Scaling cost predictable; proceed with Phase 2
- If NO (significantly more) → Reconsider archive strategy (e.g., keep only 2 weeks of snapshots instead of 30)

### Phase 2-3 Impact

**If IPFS consistency is acceptable:**
- Proceed with Phase 2 validator node rollout
- Networks can download snapshots, restore locally
- Implement Phase 3 P2P replication for faster sync
- Cost: Minor (~€5k); focus shifts to validator infrastructure

**If IPFS is too slow/expensive:**
- Evaluate alternatives: CRDTs, P2P replication, blockchain (unlikely)
- May postpone federation until Phase 3 or beyond
- Cost impact: €10-20k additional research/implementation

**Successor research:** Q4 (Hardware requirements) depends on validator deployment, which depends on Q2

---

## Q3: Local SLM (Small Language Model) vs Mistral API

### Question
**"Can a 7B parameter fine-tuned model (Llama 3.1, Phi, Mistral 7B) generate Cypher queries as accurately as Mistral 8x7B?"**

### Why This Matters

- **Cost:** Mistral API costs €420/year; self-hosted SLM costs €0 (Phase 2 development cost only)
- **Sustainability:** If SLM works, we permanently eliminate €420/year cost dependency
- **Privacy:** Local SLM keeps queries off external APIs (better for sensitive ecosystems)

### Phase 1 Data Collection

**What to measure:**
- Gather training dataset (50-100 real/synthetic Cypher queries + intents)
- Measure Mistral accuracy baseline (when user asks "Find spaces with electronics", does API generate correct Cypher?)
- Log all LLM queries for later analysis

**Collection method:**
```
Implementation (Week 1-8 of Phase 1):
├─ Instrument Mistral API
│  ├─ Log every query + generated Cypher
│  ├─ Log user feedback (did result match intent?)
│  ├─ Store in admin dashboard: /admin/lnm/queries
│  └─ Calculate accuracy %: (correct_queries / total_queries)
├─ Build training dataset
│  ├─ Extract 50+ successful Cypher generations from logs
│  ├─ Tag with: intent, Cypher query, correct_flag
│  └─ Store in /data/training/cypher-intents.jsonl
├─ Collect failure cases
│  ├─ Which types of queries fail? (complex joins, temporal, aggregations?)
│  ├─ User feedback: "This result was wrong because..."
│  └─ Identify improvement opportunities
└─ Cost tracking
   ├─ Mistral tokens per query type
   ├─ Weekly LLM cost (€35-50/month typical?)
   └─ Vs. projected usage for Phase 2-4
```

**Data structure:**
```json
{
  "period": "2025-11-05 to 2025-11-12",
  "mistral_baseline": {
    "total_queries": 500,
    "by_complexity": {
      "simple": {
        "count": 300,
        "accuracy_percent": 98,
        "avg_tokens": 120,
        "avg_latency_ms": 340
      },
      "moderate": {
        "count": 150,
        "accuracy_percent": 92,
        "avg_tokens": 280,
        "avg_latency_ms": 580
      },
      "complex": {
        "count": 50,
        "accuracy_percent": 78,
        "avg_tokens": 450,
        "avg_latency_ms": 1200
      }
    },
    "overall_accuracy_percent": 93,
    "failure_modes": [
      {
        "type": "temporal_queries",
        "count_failures": 8,
        "example": "Show spaces that existed in 2024 but not 2025",
        "root_cause": "Model struggles with temporal logic"
      },
      {
        "type": "nested_aggregations",
        "count_failures": 5,
        "example": "Count partnerships per skill per region",
        "root_cause": "Over-complex Cypher generation"
      }
    ]
  },
  "cost_baseline": {
    "weekly_queries": 125,
    "weekly_tokens": 45000,
    "weekly_cost_eur": 8.10,
    "monthly_projection_eur": 32.50,
    "annual_cost_eur": 420,
    "vs_budget": "On target ✅"
  },
  "training_dataset_ready": {
    "examples_collected": 87,
    "by_type": {
      "simple_skill_query": 45,
      "partnership_discovery": 25,
      "temporal_analysis": 8,
      "complex_aggregation": 9
    },
    "ready_for_fine_tuning": true,
    "estimated_fine_tuning_time_hours": 4
  }
}
```

### Success Criteria (Decision Gate)

✅ **Q3a: Is Mistral accuracy >90% across all query types?**
- If YES → Good baseline; SLM needs to match or exceed this
- If NO (Mistral itself is unreliable) → Maybe focus on improving prompt engineering before investing in SLM

✅ **Q3b: Are failure modes systematic (e.g., always fails on temporal)?**
- If YES → SLM fine-tuning can target these; improvements possible
- If NO (random failures) → May be harder to improve; re-evaluate SLM viability

✅ **Q3c: Can we fine-tune 7B model to >85% accuracy on collected dataset?**
- **Phase 2 task:** Fine-tune Phi-3.5-mini or Mistral 7B on 87-example dataset
- If accuracy >85% → Proceed with SLM deployment (savings: €420/year)
- If accuracy <85% → Continue with Mistral API; revisit in Phase 3 with more training data

✅ **Q3d: What's the latency of local SLM vs Mistral API?**
- Measure after Phase 2 fine-tuning
- If SLM latency <2s (acceptable) → Deploy widely
- If SLM latency >5s → GPU acceleration needed; cost impact: +€100-250/month for networks

### Phase 2-3 Impact

**If SLM reaches >90% accuracy:**
- Develop fine-tuning pipeline in Phase 2 (1-2 weeks, ~€2-3k)
- Deploy to all networks by Phase 3
- Savings: €420/year (Mistral license)
- Hero feature: "No cost LLM, privacy-preserving" (marketing advantage)

**If SLM accuracy <85%:**
- Continue with Mistral API through Phase 3
- Revisit SLM in Phase 4 with larger training dataset (500+ examples)
- No savings until Phase 4; keep €420/year in budget

**If SLM latency requires GPU:**
- Recommend networks buy T4 GPU (€25-50/month) for fast queries
- Cost impact: Increases network adoption barrier
- Alternative: Batch processing (generate Cypher offline, serve cached results)

**Successor research:** Q3 impact on cost projections; may change Phase 2-3 sustainability timeline

---

## Q4: Validator Node Hardware Requirements

### Question
**"What hardware do networks need to run a validator node? CPU-only viable, or GPU required?"**

### Why This Matters

- **Adoption barrier:** Higher hardware requirements = fewer networks can participate
- **Cost:** GPU nodes cost €100-250/month; CPU-only cost €30-50/month
- **Scalability:** If nodes need powerful hardware, federation doesn't scale to 50+ networks

### Phase 1 Data Collection

**What to measure:**
- Monitor central hub resource usage (CPU, memory, disk, bandwidth)
- Model what a replica node would need (load depends on regional traffic)
- Test restore time from IPFS snapshot (how long to spin up a replica?)

**Collection method:**
```
Implementation (Week 1-4 of Phase 1):
├─ Central hub monitoring (continuous)
│  ├─ CPU usage: Is it >80%? Spike patterns?
│  ├─ Memory usage: Current 62%; trajectory?
│  ├─ Disk I/O: Snapshot export workload?
│  └─ Network bandwidth: Ingress/egress per operation
├─ Replica simulation (Week 4)
│  ├─ Estimate regional load: "Brussels network = 28 spaces"
│  ├─ Scale central metrics: "If 28 spaces on local node, CPU = ?"
│  └─ Hardware lookup: "What Hetzner/Linode instance covers this?"
├─ Restore time benchmark (Week 5)
│  ├─ Download snapshot from IPFS (simulated latency)
│  ├─ Time Neo4j restore: "How long to import GraphML?"
│  ├─ Measure: "Cold start → serving queries" = X minutes
│  └─ Impact: "Can a network failover in <10 minutes?"
└─ Cost matrix
   ├─ CPU-only instance (Hetzner CX11): €11/month, capacity for 100 spaces
   ├─ With GPU (NVIDIA T4): €150/month, capacity for 500 spaces
   └─ Determine: Which is cost-justified?
```

**Data structure:**
```json
{
  "period": "2025-11-05 to 2025-11-12",
  "central_hub_usage": {
    "cpu": {
      "average_percent": 45,
      "peak_percent": 78,
      "instance_type": "Hetzner CX21",
      "capacity_factor": "78% of max = headroom OK"
    },
    "memory": {
      "average_percent": 62,
      "peak_percent": 85,
      "instance_size": "4GB",
      "note": "Stable; no OOM events"
    },
    "disk": {
      "used_gb": 8.5,
      "capacity_gb": 40,
      "growth_rate_gb_per_week": 0.15,
      "estimated_full_weeks": "Too far out; not a concern"
    },
    "bandwidth": {
      "ingress_gb": 12,
      "egress_gb": 8,
      "cost_eur": 0.80,
      "monthly_projection_eur": 3.20
    }
  },
  "replica_node_hardware_estimate": {
    "scenario_small_network": {
      "network_name": "Example: Brussels (28 spaces)",
      "estimated_daily_queries": 450,
      "estimated_cpu_usage_percent": 35,
      "estimated_memory_usage_percent": 48,
      "required_instance": "Hetzner CX11 (1 vCPU, 2GB RAM)",
      "monthly_cost_eur": 11,
      "gpu_needed": false,
      "cost_of_gpu_alternative": 150,
      "recommendation": "CPU-only viable; GPU not justified"
    },
    "scenario_large_network": {
      "network_name": "Example: Berlin (147 spaces)",
      "estimated_daily_queries": 2500,
      "estimated_cpu_usage_percent": 72,
      "estimated_memory_usage_percent": 68,
      "required_instance": "Hetzner CX21 (2 vCPU, 4GB RAM)",
      "monthly_cost_eur": 25,
      "gpu_needed": false,
      "note": "CX21 sufficient; GPU still not needed unless SLM deployed"
    },
    "scenario_with_slm": {
      "scenario": "If local SLM runs on node",
      "if_cpu_only": {
        "slm_latency_ms": 4500,
        "user_experience": "Poor (4.5s is too slow)"
      },
      "if_gpu": {
        "slm_latency_ms": 800,
        "user_experience": "Acceptable",
        "gpu_cost_monthly_eur": 150,
        "total_node_cost_eur": 175
      },
      "decision": "If SLM deployed, GPU recommended for latency; cost impact ~€150/month"
    }
  },
  "failover_time_estimate": {
    "scenario": "Network's primary hub fails; restore from IPFS",
    "steps": [
      {
        "step": "Download snapshot from IPFS",
        "time_seconds": 45,
        "notes": "Assuming 50MB snapshot, ~1MB/s bandwidth"
      },
      {
        "step": "Neo4j import GraphML",
        "time_seconds": 180,
        "notes": "250 spaces, 3k relationships; measured on CX21"
      },
      {
        "step": "Startup checks",
        "time_seconds": 30,
        "notes": "Connectivity tests, index verification"
      }
    ],
    "total_failover_time_seconds": 255,
    "total_failover_minutes": 4.25,
    "acceptable_threshold": "Should be <10 min for most networks",
    "result": "✅ PASS; failover is fast"
  },
  "adoption_readiness": {
    "cpu_only_barrier_low": true,
    "note": "Networks already have €30-50/month hosting; adding Maps node ~€10 more is justified"
  }
}
```

### Success Criteria (Decision Gate)

✅ **Q4a: Is CPU-only instance sufficient for <200 spaces per validator node?**
- If YES → Low adoption barrier; proceed with Phase 2 validator rollout
- If NO → Need GPU; higher cost = fewer networks participate; reconsider federation strategy

✅ **Q4b: Is failover time <10 minutes?**
- If YES → Resilience acceptable; IPFS replication strategy works
- If NO → May need more frequent snapshots or local replication; cost impact: +€20-50/month

✅ **Q4c: Does SLM deployment increase hardware requirements significantly?**
- If NO (CPU-only still works) → SLM is viable Phase 2-3 enhancement
- If YES (GPU required) → SLM deployment must be optional; CPU-only maps stay with Mistral API

### Phase 2-3 Impact

**If CPU-only sufficient:**
- Recommend Hetzner CX11 (€11/month) for small networks
- Validator nodes become widely adoptable
- Decentralization strategy succeeds; proceed with Phase 2 rollout
- Cost: Minimal (~€2k for validator infrastructure setup)

**If GPU required:**
- Validator nodes become expensive (€150+/month)
- Only well-funded networks participate
- Decentralization is limited; federation remains hub-and-spoke
- Cost impact: Increases validation barrier; phase 3 may be delayed

**If failover time is too long:**
- Increase snapshot frequency (more IPFS cost)
- Implement incremental snapshots (more complexity)
- Cost impact: Trade-off between failover speed and pinning cost

---

## Q5: Main Node Role & Operations Model

### Question
**"Should the main node be fundamentally different from validator nodes? Or just the highest-ranked node?"**

### Why This Matters

- **Governance:** Is main node fixed, rotates, or elected?
- **Cost:** Main node responsibility determines infrastructure needs
- **Resilience:** If main fails, can any validator become main, or is recovery complex?

### Phase 1 Data Collection

**What to measure:**
- Write pressure on Neo4j (how many updates/second during normal operations?)
- Consolidation workload (nightly snapshot export cost in CPU/memory/time)
- Coordination overhead (managing validator nodes, resolving conflicts)

**Collection method:**
```
Implementation (Week 2-8 of Phase 1):
├─ Neo4j write metrics
│  ├─ Log all writes (magic-link verifications, partnership suggestions)
│  ├─ Measure write latency (p95, p99)
│  ├─ Track peak write volume (busiest hour?)
│  └─ Determine: Does write load require specialized hardware?
├─ Consolidation workload (simulated)
│  ├─ Export full GraphML nightly
│  ├─ Measure CPU/memory/time required
│  ├─ Calculate: How much overhead for 10 nodes? 50 nodes?
│  └─ Trend: Does consolidation complexity scale linearly?
├─ Coordination overhead
│  ├─ If main node fails, can a validator automatically take over?
│  ├─ Manual process or automated? Time required?
│  └─ Need for distributed consensus (RAFT, Paxos)?
└─ Cost analysis
   ├─ Dedicated main node cost
   ├─ Minimal main node cost (just consolidation)
   ├─ Shared main node cost (main = highest-ranked validator)
   └─ Which is most sustainable?
```

**Data structure:**
```json
{
  "period": "2025-11-05 to 2025-11-12",
  "write_metrics": {
    "total_writes": 1200,
    "writes_per_second_average": 1.6,
    "writes_per_second_peak": 8,
    "peak_hour": "Wednesday 14:00 UTC",
    "write_latency": {
      "p50_ms": 12,
      "p95_ms": 45,
      "p99_ms": 120
    },
    "write_failure_rate_percent": 0.0,
    "note": "Write volume is low; any reasonable hardware suffices"
  },
  "consolidation_workload": {
    "nightly_export": {
      "graphml_size_mb": 52,
      "export_time_seconds": 180,
      "cpu_usage_percent": 65,
      "memory_usage_mb": 800,
      "disk_io_mb_per_second": 15
    },
    "scaling_estimate": {
      "scenario_10_nodes": {
        "estimated_graphml_size_mb": 52,  // Data doesn't grow (same single source)
        "estimated_export_time_seconds": 180,
        "cpu_load": "Minimal; consolidation is not CPU-bound"
      },
      "scenario_50_nodes": {
        "estimated_graphml_size_mb": 52,
        "estimated_export_time_seconds": 180,
        "note": "Consolidation workload is FLAT (doesn't scale with node count)"
      }
    },
    "insight": "Consolidation is trivially parallelizable; main node is not a bottleneck"
  },
  "coordination_overhead": {
    "current_model": "Single centralized main node (MVP)",
    "failover_scenario": {
      "main_node_dies": "Who takes over?",
      "options": [
        {
          "option": "Manual failover",
          "process": "Admin selects highest-ranked validator, points DNS",
          "time_minutes": 5,
          "governance": "Top-down"
        },
        {
          "option": "Automated failover",
          "process": "Health check fails; API gateway routes to next validator automatically",
          "time_minutes": "<1 min (DNS TTL dependent)",
          "governance": "Decentralized"
        },
        {
          "option": "Distributed consensus",
          "process": "Validators vote on new main via RAFT/Paxos",
          "time_minutes": "10-30",
          "governance": "Consensus-based",
          "complexity": "High; worth it?"
        }
      ]
    },
    "recommendation": "Automated failover (Option 2) is simplest; proceed with Phase 2"
  },
  "main_node_role_options": {
    "option_a_dedicated": {
      "description": "Main node is special; higher-spec hardware",
      "infrastructure_cost_eur": 50,  // Premium instance
      "governance": "Fixed or rotates among core team",
      "resilience": "If main fails, validators serve stale data until main recovers",
      "setup_complexity": "Low",
      "adoption_barrier": "Low (clear roles)"
    },
    "option_b_minimal": {
      "description": "Main is just a consolidation service; any validator can be main",
      "infrastructure_cost_eur": 25,  // Regular CX21
      "governance": "Automatic; highest-ranked node is 'main'",
      "resilience": "If main fails, next highest-ranked takes over seamlessly",
      "setup_complexity": "Medium (need health checks, DNS failover)",
      "adoption_barrier": "Medium (less clear roles initially)"
    },
    "option_c_distributed": {
      "description": "No main; all nodes are equal; consensus for writes",
      "infrastructure_cost_eur": "Same as option_b",
      "governance": "Fully decentralized",
      "resilience": "Highest (no single point of failure)",
      "setup_complexity": "Very high (RAFT implementation needed)",
      "adoption_barrier": "High (complex mental model)",
      "readiness": "Phase 4+ (requires Ostrom governance maturity)"
    }
  },
  "recommendation": {
    "phase_1": "Stick with option_a_dedicated (simple, works)",
    "phase_2": "Test option_b_minimal (automated failover, lower cost)",
    "phase_3": "Evaluate option_c_distributed (if governance ready)",
    "decision_gate": "Phase 2 results on failover automation will inform Phase 3 choice"
  }
}
```

### Success Criteria (Decision Gate)

✅ **Q5a: Is write load low enough for any CX21 instance?**
- If YES → Decentralized model viable; no need for specialized main
- If NO → Dedicated main might be necessary; cost impact: +€25/month

✅ **Q5b: Can automated failover work with <1 min downtime?**
- Phase 2 task: Implement health checks, DNS failover
- If YES → Proceed with option_b (minimal main); resilience gains
- If NO (too unpredictable) → Stick with option_a (dedicated main, manual failover)

✅ **Q5c: Is distributed consensus (RAFT) needed, or is automation sufficient?**
- Phase 2-3 decision: If 10+ nodes, do we need distributed consensus?
- If NO (automation works) → Stay with leader-based model (simpler)
- If YES (conflicts emerge) → Invest in RAFT implementation (Phase 3-4)

### Phase 2-3 Impact

**If main node can be minimal:**
- Option B: Any validator can become main automatically
- Cost savings: €25/month (€300/year)
- Resilience gains: Decentralized recovery model
- Governance: Aligns with Ostrom principles (shared authority)

**If main needs to be dedicated:**
- Option A: Keep current model
- Cost: €50/month for main, €25/month per validator
- Resilience: Hub-and-spoke (main is bottleneck)
- Governance: Centralized (core team manages main)

**If distributed consensus needed:**
- Option C: Implement RAFT (Phase 3-4)
- Development cost: €15-20k (significant)
- Resilience: Maximum; no single point of failure
- Governance: Fully decentralized; aligns with Ostrom 8 principles

**Successor research:** Q5 directly impacts cost projections and Phase 3 timeline

---

## Integration: How Q1-5 Inform Each Other

```
┌─── Q1: Node Ranking
│    ├─ Answer determines: Can we automatically select fastest node?
│    └─→ Feeds into Q5: If automated ranking works, main can be automatic
│
├─── Q2: IPFS Consistency
│    ├─ Answer determines: How fresh does fallback data need to be?
│    └─→ Feeds into Q5: If eventual consistency is OK, distributed recovery is viable
│
├─── Q3: SLM vs Mistral
│    ├─ Answer determines: Do nodes need GPU?
│    └─→ Feeds into Q4: GPU requirement impacts adoption barrier
│
├─── Q4: Hardware Requirements
│    ├─ Answer determines: Can networks afford validator nodes?
│    └─→ Feeds into Q5: If affordable, more decentralization is possible
│
└─── Q5: Main Node Role
     ├─ Answer determines: Governance model (dedicated vs distributed)
     └─→ Feeds back into Q1-2: Affects routing complexity, failover model
```

**Example decision cascade:**

```
IF (Q3 = "SLM accuracy >85%")
  AND (Q4 = "CPU-only sufficient")
  THEN: SLM deployment + decentralized nodes + low adoption barrier ✅

IF (Q3 = "SLM accuracy <85%")
  THEN: Keep Mistral API + validator nodes stay expensive
    IF (Q4 = "GPU required") THEN: Fewer networks adopt; Phase 3 delayed ❌
```

---

## Phase 1 Measurement Execution Plan

### Timeline (8 Weeks)

| Week | Q1 | Q2 | Q3 | Q4 | Q5 | Deliverable |
|------|----|----|----|----|----|----|
| **1** | Logging | Export script | Mistral API | Central monitoring | Write metrics | Instrumentation ready |
| **2** | p50/p95 baseline | Snapshot #1 | Query logging | Resource forecast | Consolidation test |
| **3-7** | Collect response times | Integrity checks | Train dataset | Replica simulation | Failover simulation |
| **8** | Final analysis | IPFS cost | Accuracy report | Hardware rec. | Governance recommendation | **Phase 2 Research Briefing** |

### Ownership & Tools

| Research Q | Owner | Tools Needed | Phase 2 Next Step |
|------------|-------|------------|---|
| **Q1** | DevOps/Backend | Admin dashboard, metrics collection | Implement ranking algorithm |
| **Q2** | Storage/Backend | IPFS API, snapshot verification script | Evaluate P2P replication alternatives |
| **Q3** | ML/Backend | Mistral API, training framework (PyTorch) | Fine-tune SLM (Ollama + Phi) |
| **Q4** | DevOps | Hetzner API, benchmark script | Procure validator node instances |
| **Q5** | Architecture/Governance | Failover testing framework | Design consensus model (if needed) |

---

## Phase 2 Briefing Document Structure

At the end of Phase 1 (Week 8), we'll produce a "Phase 2 Briefing" that answers:

### Research Q Briefing Template

```markdown
## Q1: Node Ranking Metric

### Finding
[Exact metrics from Phase 1]

### Recommendation
- Primary ranking metric: [Response time / Uptime / Hybrid]
- Implementation: [DNS round-robin / API gateway / Client-side]

### Cost Impact
- Bandwidth overhead: [X GB/month if routing fails]
- Development cost (Phase 2): [€Y]

### Decision
[ ] Proceed with [option] in Phase 2
[ ] Defer to Phase 3
[ ] Revisit in Phase 4

### Owner & Timeline
- Phase 2 implementation: [Timeline]
- Owner: [Team member]
```

---

## Success Criteria: End of Phase 1

✅ **All 5 research questions have preliminary answers**
✅ **Data quality is sufficient for Phase 2 decisions** (not perfect, but informative)
✅ **Cost projections from COST-SUSTAINABILITY.md have been validated against real metrics**
✅ **Phase 2-3 roadmap can be updated with confidence** (not speculation)
✅ **Pilot networks have provided feedback** on realistic hardware/operational costs

---

## Funding & Resource Implications

### Phase 1 (Included in NLNet €18,555 MVP)

- **Instrumentation development:** Part of M1-M4 (built into backend + admin dashboard)
- **Data collection:** Ongoing (no additional cost)
- **Analysis:** Done by team (part of M4 integration week)

### Phase 2-3 (Estimated €20-30k Erasmus+ / Fediversity)

- **Q1 implementation:** Node ranking algorithm (~€2-3k)
- **Q2 alternatives:** CRDTs or P2P replication research (~€3-5k if needed)
- **Q3 fine-tuning:** SLM training infrastructure (~€2-4k)
- **Q4 validation:** Procure test hardware, scale tests (~€2k)
- **Q5 automation:** Failover testing, health checks (~€2-3k)

**Total: €13-20k of Phase 2 budget is "research & validation"; rest is feature development**

---

## Related Documents

- **COST-SUSTAINABILITY.md:** Section 7 (deferred Q's), Section 11 (open research plan)
- **admin-dashboard-spec.md:** Defines metrics + collection methods for Phase 1 measurement
- **round-1-roadmap.md:** Week-by-week execution plan (implementation)
- **architecture.md:** Current technical decisions that Phase 2 research may validate or challenge

---

## Conclusion

Phase 1 is not just "build MVP"; it's "build MVP **while measuring** to inform Phase 2-3 architecture."

By instrumenting the system with admin dashboard metrics and collecting real data from pilot networks, we replace speculation with evidence. The Phase 2 Briefing will be grounded in actual outcomes, not assumptions.

This pragmatic approach—deferring unknowns until we have data—is how digital commons stay sustainable. We measure, learn, adapt. Repeat.

---

_Phase 2-3 Research Plan prepared for Phase 1 execution_
_Next: Implement measurement framework in Phase 1 M1-M4_
_Briefing date: End of Phase 1 (Week 8)_

