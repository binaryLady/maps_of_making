# Admin Dashboard Specification: Maps of Making

**Document:** Operational monitoring, cost tracking, data quality dashboards
**Date:** 2025-11-12
**Version:** 1.0 (Phase 1-2 implementation plan)
**Status:** Ready for development planning

---

## Executive Summary

The admin dashboard is an **internal operations tool** (not user-facing) designed to track three critical aspects:

1. **Cost Tracking** — Understand infrastructure spend, identify optimization opportunities
2. **System Health** — Monitor performance, uptime, error rates
3. **Data Quality** — Detect freshness decay, engagement drops, identify at-risk spaces

**Key Design Principle:** Dashboard enables data-driven decisions about Phase 2-3 architecture (node ranking, SLM quality, network scaling costs).

---

## 1. Scope & Access Control

### What the Dashboard Does

✅ **Real-time metrics** on API performance, costs, data freshness
✅ **Historical trends** to identify patterns (usage growth, cost trajectory)
✅ **Alerting** for critical issues (high error rates, cost overruns, data quality drops)
✅ **Export** raw metrics for analysis (JSON/CSV)

### What It Does NOT Do

❌ **User-facing** — Not designed for spaces, networks, or public access
❌ **Decision automation** — Alerts notify, but humans decide actions
❌ **Financial reporting** — Not a complete cost accounting system (supplements, doesn't replace accounting)
❌ **Fine-grained access control** — Single API key for now; Phase 2 can add role-based access

### Access Control (MVP - Phase 1)

```
Endpoint: GET /admin/dashboard?api_key=SECRET_KEY

Authentication:
├─ Single API key (stored in .env)
├─ Rotated quarterly
└─ Rate limit: 10 requests/minute

Phase 2+: Add role-based access (viewer, editor, admin)
```

---

## 2. Dashboard Metrics & Structure

### Priority 1: Cost Tracking (Weekly Reporting)

**Purpose:** Understand infrastructure spend, validate cost scenarios from COST-SUSTAINABILITY.md

#### Central Infrastructure Costs

**Endpoint:** `GET /admin/costs/central?period=week&api_key=...`

**Response Structure:**

```json
{
  "period": "2025-11-05 to 2025-11-12",
  "central_costs": {
    "mistral_ai": {
      "api_calls": 1250,
      "tokens_used": {
        "embeddings": 25000,
        "chat_completions": 20000
      },
      "estimated_cost_usd": 8.50,
      "cost_eur": 8.10,
      "rate_per_1k_tokens": 0.12,
      "monthly_projection_eur": 32.50,
      "monthly_projection_usd": 34.20,
      "trend": "+12% from previous week"
    },
    "hetzner_vps": {
      "instance_type": "CX21",
      "monthly_cost_eur": 25,
      "weekly_cost_eur": 5.77,
      "resource_metrics": {
        "cpu_usage_percent": 45,
        "memory_usage_percent": 62,
        "disk_usage_percent": 38,
        "bandwidth_gb": 12.5,
        "bandwidth_cost_eur": 0.50
      },
      "uptime_percent": 99.87,
      "estimated_monthly_eur": 25.50
    },
    "ipfs_pinning": {
      "service": "Pinata or Protocol Labs",
      "monthly_cost_eur": 30,
      "weekly_cost_eur": 6.92,
      "storage_metrics": {
        "current_size_mb": 52,
        "snapshots_stored": 30,
        "snapshot_age_hours": [24, 48, 72, 96, 120],
        "average_snapshot_size_mb": 1.7
      },
      "bandwidth_gb": 3.2,
      "estimated_monthly_eur": 31.50,
      "trend": "Stable"
    },
    "domain_and_ssl": {
      "cost_eur": 0,
      "notes": "Already paid / part of corporate hosting"
    },
    "operational_overhead": {
      "notes": "Monitoring, alerts, admin labor (estimated €15/week)",
      "estimated_eur": 15
    }
  },
  "central_total": {
    "weekly_actual_eur": 26.79,
    "weekly_projected_eur": 28.50,
    "monthly_projection_eur": 114,
    "annual_projection_eur": 1368,
    "vs_budget": {
      "budgeted_monthly_eur": 100,
      "variance_eur": +14,
      "variance_percent": "+14%"
    }
  }
}
```

**Validation:**
- ✅ Weekly cost data from Mistral invoice API
- ✅ Hetzner resource usage from cloud API or monitoring tools
- ✅ IPFS pinning from Pinata API
- ✅ Manual network cost reports (aggregated separately)

---

#### Network-Reported Infrastructure Costs

**Endpoint:** `GET /admin/costs/networks?period=week&api_key=...`

**Purpose:** Track network contributions to operational costs

**Response Structure:**

```json
{
  "period": "2025-11-05 to 2025-11-12",
  "networks": [
    {
      "network_id": "brussels-network",
      "network_name": "Brussels Makerspace Collective",
      "reported_infrastructure": {
        "vps_provider": "Hetzner",
        "vps_instance": "CX11",
        "monthly_cost_eur": 40,
        "spaces_hosting": 28,
        "cost_per_space_eur": 1.43,
        "status": "active"
      },
      "reported_maintenance": {
        "hours_this_week": 5,
        "person": "Alice M. (volunteer)",
        "tasks": ["Database backup", "Schema migration", "Incident response"],
        "estimated_value_eur": 75  // €15/hour volunteer rate
      },
      "last_report_date": "2025-11-12",
      "next_report_due": "2025-11-19"
    },
    {
      "network_id": "vienna-network",
      "network_name": "Vienna Digital Fabrication Network",
      "reported_infrastructure": {
        "vps_provider": "AWS",
        "vps_instance": "t3.small",
        "monthly_cost_eur": 45,
        "spaces_hosting": 35,
        "cost_per_space_eur": 1.29,
        "status": "active"
      },
      "reported_maintenance": {
        "hours_this_week": 3,
        "person": "Bob K. (staff)",
        "tasks": ["Monitoring", "Alerting setup"],
        "estimated_value_eur": 120  // €40/hour staff rate
      },
      "last_report_date": "2025-11-10",
      "next_report_due": "2025-11-17"
    },
    {
      "network_id": "barcelona-network",
      "network_name": "Fab Lab Barcelona Collective",
      "reported_infrastructure": {
        "vps_provider": "Linode",
        "vps_instance": "Nanode 1GB",
        "monthly_cost_eur": 35,
        "spaces_hosting": 22,
        "cost_per_space_eur": 1.59,
        "status": "reporting_delayed"  // Warning: overdue
      },
      "reported_maintenance": null,  // No report yet
      "last_report_date": "2025-11-05",
      "next_report_due": "2025-11-12",
      "days_overdue": 0,
      "status_notes": "Expected report today"
    }
  ],
  "network_aggregate": {
    "reporting_networks": 3,
    "total_spaces_reported": 85,
    "total_infrastructure_cost_eur": 120,  // €40 + €45 + €35
    "total_maintenance_hours": 8,
    "total_maintenance_value_eur": 195,
    "average_cost_per_space_eur": 1.41,
    "cost_vs_central_ratio": "4.9x",  // Networks spend 4.9× what central spends
    "notes": "Cost per space for networks: €1.41/month; central: €0.28/month"
  },
  "combined_ecosystem": {
    "central_monthly_eur": 114,
    "networks_monthly_eur": 120,
    "total_monthly_eur": 234,
    "cost_per_space_eur": 2.76,  // €234 / 85 spaces
    "vs_scenario_5networks": {
      "scenario_projected_eur": 235,
      "actual_eur": 234,
      "variance_eur": -1,
      "note": "Reality matches scenario! (With 5 networks)"
    }
  }
}
```

**Data Collection Method:**
- **Weekly form:** Networks submit via email/form with: VPS cost, maintenance hours, person-hours, notes
- **Aggregation:** Admin consolidates into JSON report
- **Automation (Phase 2):** API endpoint for networks to POST costs directly

---

### Priority 2: System Health & Performance (Weekly)

**Purpose:** Understand API reliability, identify performance regressions

**Endpoint:** `GET /admin/health/performance?period=week&api_key=...`

**Response Structure:**

```json
{
  "period": "2025-11-05 to 2025-11-12",
  "system_status": {
    "overall_uptime_percent": 99.87,
    "status": "healthy",
    "alerts_active": [
      {
        "severity": "warning",
        "message": "Memory usage at 62%, recommend scaling",
        "first_detected": "2025-11-11T14:30:00Z",
        "action": "Hetzner upgrade from CX21 to CX31 in Phase 2"
      }
    ]
  },
  "api_performance": {
    "total_requests": 8540,
    "request_breakdown": {
      "spaces_queries": 3250,
      "partnerships_queries": 2100,
      "skills_queries": 1890,
      "verification_endpoints": 800,
      "lnm_queries": 500
    },
    "response_times": {
      "spaces_query": {
        "p50_ms": 45,
        "p95_ms": 120,
        "p99_ms": 280,
        "average_ms": 62,
        "trend": "↓ -8% faster than last week"
      },
      "partnerships_query": {
        "p50_ms": 78,
        "p95_ms": 210,
        "p99_ms": 520,
        "average_ms": 115,
        "trend": "Stable"
      },
      "skills_query": {
        "p50_ms": 35,
        "p95_ms": 95,
        "p99_ms": 180,
        "average_ms": 52,
        "trend": "↑ +12% (more complex queries)"
      },
      "lnm_query": {
        "p50_ms": 340,
        "p95_ms": 1200,
        "p99_ms": 2500,
        "average_ms": 580,
        "notes": "Expected (LLM latency). Mistral overhead."
      }
    },
    "error_rates": {
      "total_errors": 8,
      "error_rate_percent": 0.09,
      "status": "healthy",
      "errors_by_type": {
        "timeout": 3,
        "invalid_params": 2,
        "neo4j_unavailable": 2,
        "other": 1
      },
      "errors_needing_action": [
        {
          "type": "neo4j_unavailable",
          "count": 2,
          "last_occurred": "2025-11-11T03:15:00Z",
          "root_cause": "Database restart during scheduled maintenance",
          "action_taken": "Notification sent to DB admin"
        }
      ]
    }
  },
  "database_health": {
    "neo4j_status": "healthy",
    "connection_pool": {
      "active_connections": 12,
      "max_pool_size": 50,
      "utilization_percent": 24
    },
    "query_performance": {
      "slow_queries": [
        {
          "query": "MATCH (s:Space)-[:HAS_SKILL]-(k) RETURN s, count(k)",
          "average_execution_ms": 280,
          "count_last_week": 450,
          "recommendation": "Add index on Space.id + Skill.name"
        }
      ]
    },
    "storage": {
      "total_size_gb": 2.3,
      "growth_rate_gb_per_week": 0.15,
      "estimated_full_in_weeks": "Not applicable (plenty of headroom)"
    }
  },
  "deployment": {
    "current_version": "0.1.0-alpha",
    "last_deployment": "2025-11-10T18:30:00Z",
    "deployments_this_week": 3,
    "rollbacks": 0,
    "notes": "Stable. No critical issues."
  }
}
```

---

### Priority 3: Data Quality & Engagement (Daily)

**Purpose:** Detect freshness decay, identify spaces needing outreach, track adoption

**Endpoint:** `GET /admin/quality/freshness?date=2025-11-12&api_key=...`

**Response Structure:**

```json
{
  "date": "2025-11-12",
  "spaces_total": 250,
  "freshness_snapshot": {
    "fresh_verified_14d_or_less": {
      "count": 170,
      "percent": "68%",
      "status_emoji": "✅",
      "trend": "↑ +2% from yesterday"
    },
    "aging_verified_15_to_30d": {
      "count": 55,
      "percent": "22%",
      "status_emoji": "⚠️",
      "trend": "↓ -1% (improving)"
    },
    "zombie_verified_31_to_90d": {
      "count": 20,
      "percent": "8%",
      "status_emoji": "🧟",
      "trend": "Stable",
      "action_required": "Send outreach emails"
    },
    "dead_verified_91d_plus": {
      "count": 5,
      "percent": "2%",
      "status_emoji": "💀",
      "trend": "Stable",
      "action_required": "Escalate to network coordinator"
    }
  },
  "verification_metrics": {
    "verified_in_last_30_days": {
      "count": 225,
      "percent": "90%",
      "trend": "↑ +5% from previous week",
      "status": "excellent"
    },
    "verified_in_last_7_days": {
      "count": 170,
      "percent": "68%",
      "trend": "↑ +2%"
    },
    "never_verified": {
      "count": 3,
      "percent": "1.2%",
      "action": "Reach out with onboarding"
    }
  },
  "verification_trend": {
    "weekly_trend": [
      {
        "week": "2025-10-22",
        "verifications_count": 45,
        "percent_verified": "72%"
      },
      {
        "week": "2025-10-29",
        "verifications_count": 52,
        "percent_verified": "78%"
      },
      {
        "week": "2025-11-05",
        "verifications_count": 58,
        "percent_verified": "85%"
      },
      {
        "week": "2025-11-12",
        "verifications_count": 62,
        "percent_verified": "90%"
      }
    ],
    "forecast": "If trend continues, 95%+ verification by Dec 1"
  },
  "at_risk_spaces": {
    "zombie_or_dead": [
      {
        "space_id": "space-brussels-001",
        "name": "Old Fab Lab (Moved)",
        "last_verified": "2025-09-01",
        "days_since_verification": 72,
        "status": "🧟 zombie",
        "network": "Brussels Network",
        "network_contact": "alice@brussels.net",
        "outreach_action": "Email sent 2025-11-09; awaiting response"
      },
      {
        "space_id": "space-vienna-045",
        "name": "Defunct Makerspace",
        "last_verified": "2025-08-15",
        "days_since_verification": 89,
        "status": "🧟 zombie → 💀 dead (tomorrow)",
        "network": "Vienna Network",
        "network_contact": "bob@vienna.at",
        "outreach_action": "Escalation email sent; call scheduled"
      }
    ],
    "total_at_risk": 25,
    "action_summary": "25 spaces need outreach this week"
  },
  "partnerships": {
    "spaces_with_partnerships": {
      "count": 85,
      "percent": "34%",
      "trend": "↑ +4% from previous week"
    },
    "pending_partnership_suggestions": {
      "count": 23,
      "trend": "↑ +2 new suggestions",
      "note": "System-generated; awaiting Space B confirmation"
    },
    "completed_handshakes": {
      "count": 85,
      "trend": "↑ +5 new partnerships"
    },
    "partnership_by_type": {
      "skill_exchange": 42,
      "mentorship": 18,
      "co_hosting": 15,
      "resource_sharing": 10
    }
  },
  "skills_coverage": {
    "total_skill_types": 28,
    "spaces_teaching_each_skill": {
      "metalworking": {
        "spaces": 18,
        "professionals": 7,
        "advanced": 8,
        "intermediate": 3,
        "trend": "Stable"
      },
      "electronics": {
        "spaces": 22,
        "professionals": 9,
        "advanced": 10,
        "intermediate": 3,
        "trend": "↑ +2 new professionals"
      },
      "ceramics": {
        "spaces": 12,
        "professionals": 4,
        "advanced": 5,
        "intermediate": 3,
        "trend": "↓ -1 professional (closure)"
      }
    },
    "gaps": [
      {
        "skill": "textile_arts",
        "spaces_teaching": 3,
        "professionals": 1,
        "note": "Underrepresented; opportunity for new space"
      }
    ]
  },
  "network_health": {
    "networks_reporting": 5,
    "network_breakdown": [
      {
        "network_name": "Brussels Network",
        "spaces": 28,
        "fresh_percent": 71,
        "status": "↑ +3% improvement"
      },
      {
        "network_name": "Vienna Network",
        "spaces": 35,
        "fresh_percent": 68,
        "status": "Stable"
      },
      {
        "network_name": "Barcelona Network",
        "spaces": 22,
        "fresh_percent": 65,
        "status": "↓ -5% degradation (outreach in progress)"
      },
      {
        "network_name": "Milan Network",
        "spaces": 18,
        "fresh_percent": 72,
        "status": "↑ +8% rapid improvement"
      },
      {
        "network_name": "Berlin Network",
        "spaces": 147,
        "fresh_percent": 64,
        "status": "Stable (large network)"
      }
    ]
  },
  "recommendations": [
    {
      "priority": "High",
      "action": "Send reminder emails to 25 aging/zombie spaces",
      "why": "These will decay to dead status within 1-2 weeks",
      "owner": "Network coordinators",
      "template": "See /admin/outreach-templates/aging-space-reminder.md"
    },
    {
      "priority": "Medium",
      "action": "Investigate ceramics skill decline",
      "why": "One professional left; rebuilding this community would strengthen network diversity",
      "owner": "Program coordinator"
    },
    {
      "priority": "Low",
      "action": "Celebrate partnership growth",
      "why": "4% week-on-week growth is excellent; continue momentum",
      "owner": "Communications"
    }
  ]
}
```

---

### Priority 4: Federation Health (Weekly, Phase 2+)

**Endpoint:** `GET /admin/federation/health?period=week&api_key=...`

**Purpose:** Monitor IPFS replication, validator node sync, data integrity

**Note:** Deferred to Phase 2 when validator nodes deployed

```json
{
  "period": "2025-11-05 to 2025-11-12",
  "status": "not_applicable_phase_1",
  "note": "Federation monitoring deferred until Phase 2 when validator nodes are deployed",
  "will_track": [
    "IPFS snapshot availability (% replicated)",
    "Validator node sync lag (max age of data)",
    "Data integrity checks (hash mismatches)",
    "P2P connection count"
  ]
}
```

---

## 3. Alert Configuration & Escalation

### Alert Rules (MVP Phase 1)

| Metric | Threshold | Severity | Action |
|--------|-----------|----------|--------|
| **Cost Overrun** | Central costs exceed budget by 20% | Warning | Email admin; investigate Mistral usage |
| **API Error Rate** | >1% of requests fail | Critical | Page oncall; investigate Neo4j |
| **Response Time P95** | >500ms for non-LLM queries | Warning | Review slow queries; consider indexing |
| **Uptime** | <99% any day | Warning | Review logs; ensure backup power |
| **Freshness Decay** | Fresh % drops below 60% | Warning | Alert network coordinators; campaign |
| **Zombie/Dead** | >10% of spaces in zombie/dead | Critical | Escalate to network leadership |
| **Database Size** | >80% of allocated storage | Warning | Plan for expansion |
| **Network Report Overdue** | >3 days past due | Reminder | Send follow-up to network coordinator |

### Alert Delivery (MVP)

**Phase 1:** Email to `admin-alerts@maps.making`

**Phase 2+:**
- Slack integration
- Dashboard notifications
- SMS for critical issues

---

## 4. Implementation Timeline

### Phase 1 MVP (Week 1-8)

| Week | Task | Deliverable |
|------|------|-------------|
| **1** | API endpoint `/admin/costs/central` | JSON response with Mistral, Hetzner, IPFS costs |
| **2** | API endpoint `/admin/health/performance` | Response time, error rate, uptime metrics |
| **3** | API endpoint `/admin/quality/freshness` | Freshness distribution, at-risk spaces |
| **4-5** | Network cost collection form | Email template + aggregation script |
| **6** | Manual dashboard generation | Weekly markdown report from JSON endpoints |
| **7** | Alert rules + notification | Email alerts for key thresholds |
| **8** | Documentation + runbook | How to interpret, when to escalate |

### Phase 2+ (Post-MVP)

- **Week 9-12:** HTML dashboard + visualization (charts, trends)
- **Week 13-16:** Slack integration + automated alerting
- **Phase 3:** Federation health monitoring (IPFS, validator nodes)
- **Phase 4+:** Advanced analytics (predictive alerts, cost optimization suggestions)

---

## 5. Data Sources & Collection

### Automated (API-Based)

| Metric | Source | Frequency | Effort |
|--------|--------|-----------|--------|
| Mistral usage | Mistral invoice API | Daily | Low (API key auth) |
| Hetzner resources | Hetzner API | Hourly | Low (metrics API) |
| Neo4j performance | Built-in monitoring | Real-time | Medium (custom exporter) |
| API errors | Application logs | Real-time | Low (FastAPI built-in) |
| Freshness distribution | Neo4j query | Daily | Low (simple query) |

### Manual (Form-Based)

| Metric | Source | Frequency | Effort |
|--------|--------|-----------|--------|
| Network costs | Network coordinators | Weekly | Low (email form) |
| Network maintenance hours | Network coordinators | Weekly | Low (email form) |
| Incident reports | Team members | As-needed | Low (Slack → issue) |

### Phase 2 Automation

- Network cost self-reporting API
- Slack slash command: `/cost-report brussels €40`
- Automated IPFS monitoring

---

## 6. JSON Response Schemas (OpenAPI)

### Common Error Response

```json
{
  "error": "string",
  "code": "INVALID_API_KEY",
  "timestamp": "2025-11-12T14:30:00Z"
}
```

### Pagination (Future)

```json
{
  "data": [...],
  "pagination": {
    "limit": 50,
    "offset": 0,
    "total": 250
  }
}
```

---

## 7. Security & Access Control

### API Key Rotation

- **Frequency:** Quarterly
- **Process:** Generate new key, update .env, revoke old key
- **Backup:** Store previous key for 24h grace period

### Rate Limiting

- **Limit:** 10 requests/minute per API key
- **Lockout:** 1 hour after 3 failed attempts
- **Monitoring:** Track API key usage to detect abuse

### Data Sensitivity

- **PII excluded:** No individual names, emails in public dashboard
- **Cost data:** Sensitive to networks; don't publish detailed breakdowns
- **Access logs:** Track who accessed what, when

---

## 8. Metrics Glossary

### Freshness States

| State | Definition | Icon | Days Since Verification |
|-------|-----------|------|-------------------------|
| **Fresh** | Recently verified, data is current | ✅ | 0-14 days |
| **Aging** | Not verified recently, approaching stale | ⚠️ | 15-30 days |
| **Zombie** | Very stale, likely inactive but not confirmed dead | 🧟 | 31-90 days |
| **Dead** | No activity or verification for 90+ days | 💀 | 91+ days |

### Cost Metrics

| Metric | Definition | Formula |
|--------|-----------|---------|
| **Cost per space** | Annual operational cost divided by number of spaces | `(Central Cost + Network Costs) / Total Spaces` |
| **Cost per network** | Annual operational cost for one network | `VPS Cost + Maintenance Value + Allocated Central Cost` |
| **Monthly projection** | Annualized monthly average | `Weekly actual × 4.33` |

### Performance Metrics

| Metric | Definition | Target |
|--------|-----------|--------|
| **P50 latency** | 50th percentile response time | <100ms (non-LLM) |
| **P95 latency** | 95th percentile response time | <300ms (non-LLM) |
| **P99 latency** | 99th percentile response time | <500ms (non-LLM) |
| **Error rate** | % of requests resulting in 5xx errors | <0.5% |
| **Uptime** | % of time system is available | >99% |

---

## 9. Reporting & Escalation

### Weekly Admin Report (Every Monday)

**Distribution:** Email to team@maps.making
**Contents:**
1. Cost summary (central + networks)
2. Performance highlights (errors, latency)
3. Freshness snapshot (% fresh, at-risk spaces)
4. Action items for coordinators

**Template:** See `/docs/admin/weekly-report-template.md`

### Monthly Review (1st Wednesday)

**Attendees:** Team leads, network coordinators
**Agenda:**
1. Review Phase 1 metrics vs. cost scenarios (validating cost.md)
2. Discuss any anomalies or alerts
3. Plan Phase 2-3 based on growth trajectory
4. Celebrate wins (partnership growth, adoption improvements)

### Escalation Path

```
Threshold exceeded (automated check)
  ↓
Alert sent (email immediately)
  ↓
If not resolved in 4 hours → Slack notification (Phase 2+)
  ↓
If not resolved in 24 hours → Phone call to on-call engineer
```

---

## 10. Success Criteria

### Phase 1 (MVP)

✅ Can answer: "What were our central costs last week?"
✅ Can answer: "How many spaces are at risk of becoming zombie?"
✅ Can answer: "Did API performance degrade?"
✅ Can identify: Outreach opportunities (spaces aging)
✅ Can validate: Cost scenarios from COST-SUSTAINABILITY.md

### Phase 2

✅ Visual dashboard with charts
✅ Automated alerts via Slack
✅ Network cost self-reporting
✅ Trend forecasting (freshness trajectory)
✅ Predictive alerts (e.g., "3 spaces will go dead in 7 days")

### Phase 3+

✅ Federation health monitoring
✅ Validator node performance tracking
✅ Cost optimization recommendations
✅ Ecosystem health scoring

---

## 11. Future Enhancements (Phase 2-4)

### Dashboards Beyond MVP

1. **Network coordinator view** (Phase 2)
   - "How healthy is my network?" dashboard
   - Freshness trends, partnership recommendations, growth metrics
   - Accessible to network leaders (role-based access)

2. **Researcher view** (Phase 2-3)
   - Temporal queries ("Show ecosystem in Jan 2025 vs now")
   - Export data for academic analysis
   - Anonymized trend reports

3. **Cost optimization** (Phase 3)
   - "If we scale to X networks, total cost = Y"
   - ROI calculator (value delivered per euro spent)
   - Break-even timeline for new networks

4. **Ecosystem health scoring** (Phase 4)
   - Overall system health: freshness + partnerships + growth
   - Predictive churn risk (which spaces likely to close?)
   - Intervention scoring (where to focus outreach?)

---

## 12. Operational Runbook

### "Freshness % dropped below 60%"

**Trigger:** Daily dashboard check shows <60% fresh spaces

**Steps:**
1. Review `/admin/quality/freshness?date=today` to identify at-risk networks
2. Email network coordinators: "Please verify aging spaces"
3. Provide outreach templates: `/admin/outreach-templates/aging-space-reminder.md`
4. Schedule follow-up call in 1 week to discuss campaigns
5. Document lessons learned (why did this happen?)

### "Mistral cost exceeded €40/week"

**Trigger:** Weekly cost check shows >€40/week LLM spend

**Steps:**
1. Check query volume: Are more users querying?
2. Check query complexity: Are queries consuming more tokens?
3. Email team: "LLM usage up X%; investigating root cause"
4. Options: Optimize prompts, implement query caching, or escalate to Phase 2 SLM migration
5. Decision: Is this sustainable, or do we need intervention?

### "Network report overdue >3 days"

**Trigger:** Automated check for missing weekly cost reports

**Steps:**
1. Email network coordinator: "Hi Alice, we haven't received Brussels Network's cost report. Can you send by EOD?"
2. If no response in 24h: Send escalation to network leadership
3. If report contains obvious errors: Respond with questions before aggregating
4. Add to Phase 2 roadmap: Self-reporting API to eliminate manual collection

---

## Summary: Admin Dashboard Purpose

The dashboard transforms the cost & sustainability models from COST-SUSTAINABILITY.md from **theory into measurement**. By instrumenting the system with these metrics, we can:

1. ✅ **Validate cost scenarios** — Are real operational costs matching projections?
2. ✅ **Inform architecture decisions** — Data from Phase 1 will guide Phase 2-3 choices
3. ✅ **Enable data-driven scaling** — Know when/how to add networks or regions
4. ✅ **Demonstrate NLNet impact** — Show that commons governance actually works (metrics prove it)
5. ✅ **Support network coordinators** — Give them visibility into their ecosystem health

**Key insight:** The dashboard is not about watching numbers; it's about enabling the collaborative decisions that keep a digital commons healthy.

---

_Specification prepared for Phase 1 development planning_
_Next: Engineering refinement + API endpoint implementation (Week 1 of Phase 1)_

