---
name: nlnet-grant-assessor
description: Evaluates grant applications for NLnet NGI Zero Commons Fund against their criteria. Use when user wants to assess an NGI grant application or asks for feedback on a commons-focused funding proposal. Provides structured evaluation across technical excellence, impact/relevance, and cost-effectiveness dimensions.
license: Apache 2.0
---

# NLnet NGI Zero Commons Fund - Grant Assessor

Evaluates grant applications against NLnet NGI Zero Commons Fund criteria.

## Evaluation Framework

NLnet judges applications on weighted criteria:
- **30%** Technical excellence/feasibility
- **40%** Relevance/Impact/Strategic potential (largest weight)
- **30%** Cost effectiveness/Value for money

Minimum score: 5.0/7.0 to advance to second stage.

## Hard Eligibility Requirements (Knockout Criteria)

Applications MUST:
- Align with NGI vision and Commons Fund focus
- Have R&D as primary objective
- Be open source (Apache 2.0, GPL, MIT, etc.)
- Demonstrate European dimension
- First proposal: ≤€50,000
- Lifetime cap per entity: €500,000

## Section-by-Section Assessment

### Section 3: Abstract (1200 chars)

**Look for:**
- ✅ Leads with community problem, not tech solution
- ✅ Clear outcomes and deliverables
- ✅ Why commons/sustainability matters to this project
- ✅ Differentiation from existing efforts

**Red flags:**
- ❌ All technical details, no impact story
- ❌ Vague promises ("revolutionize," "transform")
- ❌ No mention of sustainability beyond grant
- ❌ Over-engineered solution for simple problem

### Section 4: Experience (2500 chars)

**Look for:**
- ✅ Team actually understands the domain
- ✅ Relevant track record (not just credentials)
- ✅ Mix of technical + community skills
- ✅ Honest about limitations

**Red flags:**
- ❌ No domain experience (just general dev skills)
- ❌ Solo founder with no co-leads or advisors
- ❌ Overselling ("I'm expert in everything")
- ❌ No evidence of completing complex projects

### Section 5: Budget (2500 chars)

**Look for:**
- ✅ Milestone-based payments
- ✅ Rates explicit (€/hour clearly stated)
- ✅ Reasonable scope for requested amount
- ✅ Infrastructure costs itemized
- ✅ Both technical AND community work budgeted

**Red flags:**
- ❌ Vague "development costs" without breakdown
- ❌ No milestones or deliverables tied to payment
- ❌ Rates hidden or unclear
- ❌ All budget on coding, zero on user validation
- ❌ Over-ambitious scope for budget

**Reasonable rates (Brussels 2025):**
- Junior: €40-60/hour
- Mid-level: €60-80/hour  
- Senior: €80-100/hour
- Specialist: €100-120/hour

### Section 6: Comparison (4000 chars)

**Look for:**
- ✅ Names actual competitors/alternatives
- ✅ Honest about what competitors do well
- ✅ Clear differentiation (not just "we're better")
- ✅ Understands why existing solutions failed

**Red flags:**
- ❌ No competitors mentioned ("nobody does this")
- ❌ Dismissive of existing work
- ❌ Differentiation is minor features, not fundamental approach
- ❌ Doesn't understand competitive landscape

### Section 7: Technical Challenges (5000 chars)

**Look for:**
- ✅ Focuses on HARD problems, not normal implementation
- ✅ Honest about risks and unknowns
- ✅ Validation strategy for each challenge
- ✅ Behavioral challenges alongside technical
- ✅ Decision gates and fallback plans

**Red flags:**
- ❌ Lists normal dev tasks as "challenges"
- ❌ No risk assessment
- ❌ Over-confident ("this will definitely work")
- ❌ Only technical challenges (ignores adoption risk)
- ❌ Premature optimization (solving problems they don't have)

### Section 8: Ecosystem (2500 chars)

**Look for:**
- ✅ Named pilot partners or letters of intent
- ✅ Clear engagement strategy
- ✅ Sustainability plan beyond grant
- ✅ Promotion strategy (conferences, publications)
- ✅ Community governance plan

**Red flags:**
- ❌ Vague "we'll reach out to users"
- ❌ No pilot partners confirmed
- ❌ Sustainability = "apply for more grants"
- ❌ No plan to transition to community ownership

## Commons-Specific Assessment

NLnet prioritizes true commons over platforms. Check:

**✅ Good commons indicators:**
- Decentralized architecture (IPFS, federation, P2P)
- Community can fork/maintain without original team
- Governance transitions to users
- Ostrom principles explicitly applied
- Data sovereignty for contributors
- No platform lock-in

**❌ Platform red flags:**
- Centralized control with no exit strategy
- Vendor lock-in by design
- "Commons" mentioned but architecture is centralized
- No sustainability without continued founder involvement

## Authenticity vs Grant-Speak

**Authentic (good):**
- Specific problems with concrete examples
- Honest about what might not work
- Clear why THIS team can solve it
- Natural language, not buzzwords
- Shows understanding through specificity

**Grant-speak (bad):**
- Generic impact statements
- Buzzword bingo (blockchain, AI, decentralized)
- Vague about actual implementation
- Overselling without evidence
- Copy-paste from other grants

## Final Assessment Template

When evaluating, structure feedback as:

```
OVERALL IMPRESSION: [1-2 sentences]

STRENGTHS:
- [Specific strength with evidence]
- [Specific strength with evidence]

CONCERNS:
- [Specific concern with suggestion]
- [Specific concern with suggestion]

SCORING GUIDANCE:

Technical Excellence (30%): [score/7]
- [Brief justification]

Relevance/Impact (40%): [score/7]
- [Brief justification]

Cost Effectiveness (30%): [score/7]
- [Brief justification]

WEIGHTED TOTAL: [score/7]

RECOMMENDATION: [Pass to Stage 2 / Request revisions / Decline]
```

## Usage Notes

- Read the entire application before scoring
- Check character counts match limits
- Verify budget math adds up
- Look for GitHub/portfolio links and check them
- If letters of intent mentioned, they should be attached
- European dimension must be clear (team location, beneficiaries, infrastructure)
- First proposals >€50k are auto-disqualified

## Common Failure Patterns

1. **Tech solution looking for problem**: All features, no user validation
2. **Academic exercise**: Interesting technically, no community need
3. **Platform in commons clothing**: Says "commons" but architecture is centralized
4. **Scope creep**: Trying to solve 10 problems at once
5. **No sustainability**: Entire model depends on continued grants
6. **Missing community**: No pilot users, no letters, no validation
7. **Vague budget**: Can't tell what money actually buys
8. **Solo hero**: One person doing everything, no team

## Good Application Patterns

1. **Problem-first**: Leads with documented community pain
2. **Validated need**: Letters of intent, pilot partners committed
3. **Behavioral + technical**: Understands human incentives matter
4. **Honest scope**: Walking skeleton, not full product
5. **Commons by design**: Decentralization isn't afterthought
6. **Clear milestones**: Testable outcomes per milestone
7. **Sustainability built in**: Incentive alignment, not dependency
8. **Mixed team**: Technical + community + domain expertise
