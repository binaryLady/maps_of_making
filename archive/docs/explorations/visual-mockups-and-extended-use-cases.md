# Visual Mockups, Animations & Extended Use Cases

**Purpose:** Prototype visualization concepts, explore persona-driven features, and identify future enhancements
**Date:** 2025-11-15
**Status:** Exploration / Concept Phase

---

## Table of Contents

1. [Visual Mockup Animations](#visual-mockup-animations)
2. [Persona-Driven Use Cases](#persona-driven-use-cases)
3. [Visual Data Representation Strategies](#visual-data-representation-strategies)
4. [Partnership Handshake UX Flow](#partnership-handshake-ux-flow)
5. [MakerSkillTree Integration (Side-Quest)](#makerskilltree-integration-side-quest)
6. [MakerTour.fr Residency Patterns](#makertour-fr-residency-patterns)
7. [Prioritization & Roadmap](#prioritization--roadmap)

---

## 1. Visual Mockup Animations

### 1.1 ASCII Animation Concepts

These text-based storyboards demonstrate the partnership visualization interactions:

#### Animation 1: Selecting a Space & Revealing Buds

```
Frame 1 (Initial State - Zoom Level 12)
════════════════════════════════════════
│                                      │
│        🟢 (ElektroLab)              │
│                                      │
│   🟡              🟢                 │
│                                      │
│        🧟                            │
════════════════════════════════════════
User clicks ElektroLab marker...


Frame 2 (Buds Appear - 0.3s transition)
════════════════════════════════════════
│                                      │
│         ○  (TextileWorks)            │
│        ╱│╲                           │
│      🔴 ◉ 🟢  ← ElektroLab enlarged  │
│         ╲│                           │
│          🟡  (pending partnership)   │
│                                      │
│        🧟                            │
════════════════════════════════════════
Buds (○) sprout around ElektroLab
🔴 = pending, 🟢 = active, 🟡 = dormant


Frame 3 (Edges Grow - 0.5s animation)
════════════════════════════════════════
│                                      │
│         ○  🟢 TextileWorks           │
│        ╱│╲  (highlighted + pulsing)  │
│      🔴 ◉═══════╗                    │
│         ╲│      ║                    │
│          🟡═════╝ MetalWorks         │
│                  (highlighted)       │
│        🧟                            │
════════════════════════════════════════
Curved edges animate from ElektroLab
Partners highlighted with glow effect


Frame 4 (Hover on Bud - Tooltip)
════════════════════════════════════════
│         ┌─────────────────────┐      │
│         │ Skill Exchange      │      │
│         │ Active since 2024   │🟢    │
│        ╱│ 12 joint activities │      │
│      🔴 ◉═══════╗└─────────────┘    │
│         ╲│      ║                    │
│          🟡═════╝                    │
════════════════════════════════════════
Hovering bud shows partnership details
```

#### Animation 2: Zoom Out - Network Visualization

```
Frame 1 (City View - ElektroLab selected)
════════════════════════════════════════
│                                      │
│         🟢 (TextileWorks)            │
│          ║                           │
│          ◉ (ElektroLab - selected)   │
│         ╱│╲                          │
│       🟡  🔴                          │
│    (MetalWorks) (pending)            │
════════════════════════════════════════


Frame 2 (Zooming Out - Zoom Level 10)
════════════════════════════════════════
│    🟢────────────🟢                  │
│     │╲          ╱│                   │
│     │ ╲        ╱ │                   │
│     │  ◉──────○  │                   │
│     │ ╱  ╲  ╱ ╲  │                   │
│    🟡────🔴────🟢                    │
│  (Network web forms)                 │
════════════════════════════════════════
Edges persist and grow visually
More partnerships become visible


Frame 3 (Regional View - Zoom Level 8)
════════════════════════════════════════
│  [Cluster: 5 spaces]                 │
│         ┃                            │
│         ┃ (8 partnerships)           │
│         ┃                            │
│  [Cluster: 3 spaces]════[Cluster: 4] │
│    (2 partnerships)     (6 links)    │
════════════════════════════════════════
Clusters show partnership counts
Individual spaces hidden at this zoom
```

#### Animation 3: Multi-Space Selection

```
Frame 1 (User Ctrl+Click on 3 Spaces)
════════════════════════════════════════
│         ◉A (ElektroLab)              │
│        ╱│╲                           │
│      ◉B  │  ◉C                       │
│   (Lab2) │ (Lab3)                    │
│          │                           │
════════════════════════════════════════
All 3 selected spaces highlighted


Frame 2 (Combined Network Revealed)
════════════════════════════════════════
│         ◉A══════╗                    │
│        ╱│╲      ║                    │
│      ◉B══╬══════◉C                   │
│        ╲ ║    ╱                      │
│         ╲║   ╱                       │
│          ◉D  (shared partner!)       │
════════════════════════════════════════
Shows overlapping partnerships
◉D is a "bridge node" connecting A, B, C
```

### 1.2 Interactive HTML/SVG Prototype Concept

To create an actual clickable prototype, we would build:

```html
<!-- Simplified structure -->
<div id="map-container">
  <svg id="partnership-layer" class="overlay">
    <!-- Curved partnership edges -->
    <path class="edge active" d="M100,100 Q150,50 200,100" />
    <path class="edge pending" d="M100,100 Q120,150 140,200" />
  </svg>

  <div id="leaflet-map"></div>

  <div id="bud-layer" class="overlay">
    <!-- Buds positioned absolutely -->
    <div class="bud active"
         style="transform: translate(25px, -30px) rotate(45deg)"
         data-partner-id="textile-works">
    </div>
  </div>
</div>

<style>
@keyframes budAppear {
  0% {
    transform: translate(0, 0) scale(0);
    opacity: 0;
  }
  100% {
    transform: translate(var(--bud-x), var(--bud-y)) scale(1);
    opacity: 1;
  }
}

@keyframes edgeGrow {
  0% {
    stroke-dashoffset: 1000;
    opacity: 0;
  }
  100% {
    stroke-dashoffset: 0;
    opacity: 0.8;
  }
}

@keyframes partnerPulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7);
  }
  50% {
    box-shadow: 0 0 0 15px rgba(34, 197, 94, 0);
  }
}

.bud {
  animation: budAppear 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.edge {
  stroke-dasharray: 1000;
  animation: edgeGrow 0.8s ease-out forwards;
}

.partner-highlight {
  animation: partnerPulse 2s infinite;
}
</style>
```

### 1.3 Prototype Development Plan

**Phase 1: Static Mockup (1 day)**
- Single HTML file with hardcoded space positions
- CSS animations for buds and edges
- No real map, just positioned divs
- Demonstrates visual concept only

**Phase 2: Interactive Demo (2-3 days)**
- Integrate real Leaflet.js map
- Add click handlers for space selection
- Implement zoom-level visibility toggling
- Use sample GeoJSON data (5-10 spaces)

**Phase 3: Neo4j Connected (1 week)**
- Connect to actual Neo4j instance
- Real partnership data from graph queries
- Dynamic edge rendering based on query results
- Performance testing with 100+ spaces

---

## 2. Persona-Driven Use Cases

Based on `/docs/planning/PERSONAS.md`, here are extended use cases with visualization requirements:

### 2.1 Persona 1: Individual Maker / Digital Nomad

**Primary Need:** Find trustworthy spaces quickly

#### Use Case 1.1: "Show me ALL metalworking spaces in Europe"

**Current Limitation:** Standard maps show points, but no skill depth

**Visual Enhancement:**
```
Map View:
┌────────────────────────────────────┐
│  Europe View (Zoom 5)              │
│                                    │
│  [Berlin Cluster]                  │
│   ├─ 3 beginner metalworking       │
│   ├─ 5 advanced metalworking   ★   │ ← Star = professional level
│   └─ 2 professional metalworking   │
│                                    │
│  [Paris Cluster]                   │
│   ├─ 1 beginner                    │
│   └─ 2 advanced                    │
└────────────────────────────────────┘

Visual Encoding:
- Marker size = total instructors at space
- Marker color = freshness (green/yellow/red)
- Star badge overlay = professional-level instruction available
```

**Data Required:**
```cypher
MATCH (s:Space)-[has:HAS_SKILL]->(skill:Skill {name: "metalworking"})
WHERE has.professionals > 0 OR has.advanced > 0
RETURN s.name, s.lat, s.lon,
       has.professionals, has.advanced, has.intermediate,
       s.last_verified
```

#### Use Case 1.2: "I need both textiles AND electronics - rare combo!"

**Visual Enhancement:**
```
Venn Diagram Overlay on Map:
┌────────────────────────────────────┐
│                                    │
│    ╭──── Textiles ────╮            │
│    │  ◉ Lab1          │            │
│    │     ╭─────────╮  │            │
│    │     │  ◉ Lab2 │  │            │ ← Lab2 has BOTH
│    │     │ (BOTH!) │  │            │
│    │     ╰─────────╯  │            │
│    ╰──────────────╯   │            │
│           Electronics ─╯            │
│              ◉ Lab3                │
└────────────────────────────────────┘

Filter UI:
[X] Textiles (advanced+)
[X] Electronics (intermediate+)
[ ] Metalworking

Result: 1 space matches both criteria
```

**Data Required:**
```cypher
MATCH (s:Space)-[:HAS_SKILL]->(textiles:Skill {name: "textiles"})
MATCH (s)-[:HAS_SKILL]->(electronics:Skill {name: "electronics"})
WHERE textiles.level IN ['advanced', 'professional']
  AND electronics.level IN ['intermediate', 'advanced', 'professional']
RETURN s
```

### 2.2 Persona 2: Researcher / Ecosystem Analyst

**Primary Need:** Understand temporal patterns and network evolution

#### Use Case 2.1: "Show me COVID impact on maker ecosystems"

**Visual Enhancement: Timeline Slider**

```
Timeline Control:
┌────────────────────────────────────┐
│  [Jan 2020]────●────────[Nov 2025] │
│               (slider)              │
│                                    │
│  Active Spaces: 142 → 98 → 127    │
│  (peak)        (trough)  (recovery)│
│                                    │
│  Event Markers:                    │
│  ▼ Mar 2020: First lockdowns       │
│  ▼ Sep 2020: Closure spike         │
│  ▼ Jan 2022: Recovery begins       │
└────────────────────────────────────┘

Map animates to show:
- Spaces fading out (closures)
- New spaces appearing (openings)
- Color change (active → dormant → closed)
```

**Data Required:**
```cypher
// Temporal query
MATCH (s:Space)
WHERE s.created_at <= $targetDate
  AND (s.closed_at IS NULL OR s.closed_at > $targetDate)
RETURN s, s.status_at_date($targetDate)

// Closure analysis
MATCH (s:Space)-[:STATE_CHANGE]->(change)
WHERE change.to = 'closed'
  AND change.timestamp >= $startDate
  AND change.timestamp <= $endDate
RETURN change.timestamp, change.reason, count(*) as closures
ORDER BY change.timestamp
```

#### Use Case 2.2: "Which skill communities cluster together?"

**Visual Enhancement: Skill Network Graph**

```
Side Panel: Skill Correlation Matrix
┌─────────────────────────────────────┐
│  Skills taught together frequently: │
│                                     │
│  Electronics ←══(0.73)══→ Robotics  │
│  Textiles    ←══(0.45)══→ Fashion   │
│  Woodwork    ←══(0.82)══→ Furniture │
│  3D Print    ←══(0.91)══→ CAD       │
│                                     │
│  (Correlation score: spaces with    │
│   both skills / total spaces)       │
└─────────────────────────────────────┘

Map View:
- Cluster spaces by dominant skill combo
- Color-code by "skill profile"
- Show unexpected combinations
```

**Data Required:**
```cypher
// Skill co-occurrence
MATCH (s:Space)-[:HAS_SKILL]->(skill1:Skill)
MATCH (s)-[:HAS_SKILL]->(skill2:Skill)
WHERE id(skill1) < id(skill2)  // Avoid duplicates
WITH skill1, skill2, count(s) as spaces_with_both
MATCH (s1:Space)-[:HAS_SKILL]->(skill1)
WITH skill1, skill2, spaces_with_both, count(s1) as total_skill1
MATCH (s2:Space)-[:HAS_SKILL]->(skill2)
WITH skill1, skill2, spaces_with_both, total_skill1, count(s2) as total_skill2
RETURN skill1.name, skill2.name,
       toFloat(spaces_with_both) / (total_skill1 + total_skill2 - spaces_with_both) as jaccard_similarity
ORDER BY jaccard_similarity DESC
LIMIT 20
```

### 2.3 Persona 3: Space Operator / Network Coordinator

**Primary Need:** Monitor network health and facilitate partnerships

#### Use Case 3.1: "Health Dashboard at a Glance"

**Visual Enhancement: Network Dashboard**

```
Dashboard View:
┌─────────────────────────────────────────────────┐
│  NETWORK HEALTH OVERVIEW                        │
│  ══════════════════════════════════════════    │
│                                                 │
│  Freshness Distribution:                        │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓░░░ 89% Fresh (<30d)      ✅    │
│  ▓▓░░░░░░░░░░░░░  9% Aging (30-90d)     ⚠️     │
│  ▓░░░░░░░░░░░░░░  2% Zombie (>90d)      🧟    │
│                                                 │
│  Partnership Activity:                          │
│  ┌─────────────────────────────────────┐       │
│  │  Active partnerships:    12         │       │
│  │  Pending (awaiting handshake): 5    │       │
│  │  Suggested by algorithm: 8          │       │
│  │                                     │       │
│  │  Top connected hubs:                │       │
│  │   1. ElektroLab (7 partnerships) ★  │       │
│  │   2. MakerZone (5 partnerships)     │       │
│  │   3. FabCentral (4 partnerships)    │       │
│  └─────────────────────────────────────┘       │
│                                                 │
│  At-Risk Spaces (Action Required):              │
│  ⚠️  Space Alpha - 45 days since verification  │
│      [Send Reminder] [Mark Investigating]      │
│                                                 │
│  🧟 Space Beta - 92 days (CRITICAL)            │
│      [Escalate Call] [Mark Closed]             │
└─────────────────────────────────────────────────┘
```

**Data Required:**
```cypher
// Network health summary
MATCH (s:Space)-[:MEMBER_OF]->(n:Network {id: $networkId})
WITH s,
     duration.between(s.last_verified, datetime()).days as days_stale
RETURN
  count(CASE WHEN days_stale <= 30 THEN 1 END) as fresh_count,
  count(CASE WHEN days_stale > 30 AND days_stale <= 90 THEN 1 END) as aging_count,
  count(CASE WHEN days_stale > 90 THEN 1 END) as zombie_count,
  collect(CASE WHEN days_stale > 30 THEN {
    id: s.id,
    name: s.name,
    days_stale: days_stale
  } END) as at_risk_spaces
```

#### Use Case 3.2: "Suggest partnerships based on complementary skills"

**Visual Enhancement: Partnership Matchmaking UI**

```
Matchmaking Panel:
┌─────────────────────────────────────────────────┐
│  PARTNERSHIP SUGGESTIONS                        │
│  ══════════════════════════════════════════    │
│                                                 │
│  🔍 Space A (ElektroLab) ↔ Space B (TextileHub) │
│                                                 │
│  Match Score: 87%  ⭐⭐⭐⭐☆                      │
│                                                 │
│  Why this match?                                │
│  ✓ Complementary skills:                        │
│    - ElektroLab: electronics, robotics          │
│    - TextileHub: textiles, fashion tech         │
│    → Potential: Wearable electronics projects!  │
│                                                 │
│  ✓ Geographic proximity: 2.3 km apart           │
│  ✓ Similar freshness: both active               │
│  ✓ No existing partnership                      │
│                                                 │
│  Suggested partnership type:                    │
│  [ ] Skill exchange                             │
│  [X] Joint workshops                            │
│  [ ] Equipment sharing                          │
│                                                 │
│  [Propose to Both Spaces]  [Dismiss]            │
└─────────────────────────────────────────────────┘
```

**Data Required:**
```cypher
// Partnership recommendations
MATCH (a:Space)-[:MEMBER_OF]->(n:Network {id: $networkId})
MATCH (b:Space)-[:MEMBER_OF]->(n)
WHERE id(a) < id(b)  // Avoid duplicates
  AND NOT (a)-[:PARTNERSHIP]-(b)
  AND NOT (a)-[:SUGGESTS_PARTNERSHIP]-(b)

// Get skills for both
OPTIONAL MATCH (a)-[:HAS_SKILL]->(skillA:Skill)
OPTIONAL MATCH (b)-[:HAS_SKILL]->(skillB:Skill)

WITH a, b,
     collect(DISTINCT skillA.name) as skills_a,
     collect(DISTINCT skillB.name) as skills_b,
     point.distance(
       point({latitude: a.lat, longitude: a.lon}),
       point({latitude: b.lat, longitude: b.lon})
     ) / 1000.0 as distance_km

// Calculate complementarity (low overlap = high complement)
WITH a, b, skills_a, skills_b, distance_km,
     [skill IN skills_a WHERE NOT skill IN skills_b] as unique_to_a,
     [skill IN skills_b WHERE NOT skill IN skills_a] as unique_to_b,
     [skill IN skills_a WHERE skill IN skills_b] as overlap

WITH a, b, distance_km, unique_to_a, unique_to_b, overlap,
     toFloat(size(unique_to_a) + size(unique_to_b)) /
     toFloat(size(unique_to_a) + size(unique_to_b) + size(overlap)) as complementarity_score

WHERE distance_km < 50  // Within 50km
  AND complementarity_score > 0.5  // At least 50% unique skills

RETURN a, b, distance_km, unique_to_a, unique_to_b,
       complementarity_score * (1 - (distance_km / 100)) as match_score
ORDER BY match_score DESC
LIMIT 10
```

### 2.4 Persona 4: Potential Founder

**Primary Need:** Identify market gaps and differentiation opportunities

#### Use Case 4.1: "Where are the skill gaps in Vienna?"

**Visual Enhancement: Heatmap + Gap Analysis**

```
Vienna Ecosystem View:
┌─────────────────────────────────────────────────┐
│  VIENNA SKILL COVERAGE (12 existing spaces)     │
│  ══════════════════════════════════════════    │
│                                                 │
│  Saturated (avoid):                             │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ 3D Printing    (9 spaces) 🔴  │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓░░ Laser Cutting  (8 spaces)     │
│  ▓▓▓▓▓▓▓▓▓▓▓░░░░ Woodworking    (7 spaces)     │
│                                                 │
│  Moderately Covered:                            │
│  ▓▓▓▓▓▓░░░░░░░░░ Electronics    (4 spaces) 🟡  │
│  ▓▓▓▓▓░░░░░░░░░░ Metalworking   (3 spaces)     │
│                                                 │
│  GAPS (opportunity):                            │
│  ▓▓░░░░░░░░░░░░░ Textiles       (1 space)  🟢  │
│  ▓░░░░░░░░░░░░░░ Biolab         (0 spaces) ⭐  │
│  ▓░░░░░░░░░░░░░░ Ceramics       (0 spaces) ⭐  │
│                                                 │
│  💡 Recommendation:                             │
│  Focus on BIOLAB + TEXTILES combination         │
│  - Zero local competition                       │
│  - Growing trend in Central Europe (+23% 2023-25)│
│  - Potential partnership with existing electronics│
│    spaces for bio-sensor projects               │
└─────────────────────────────────────────────────┘
```

**Data Required:**
```cypher
// Skill saturation in region
MATCH (s:Space)
WHERE point.distance(
  point({latitude: s.lat, longitude: s.lon}),
  point({latitude: 48.2082, longitude: 16.3738})  // Vienna
) < 20000  // 20km radius

MATCH (s)-[:HAS_SKILL]->(skill:Skill)
WITH skill.name as skill_name, count(s) as space_count
ORDER BY space_count DESC

RETURN skill_name, space_count,
       CASE
         WHEN space_count >= 7 THEN 'saturated'
         WHEN space_count >= 3 THEN 'moderate'
         ELSE 'gap'
       END as market_status
```

### 2.5 Persona 5: LLM / AI Agent

**Primary Need:** Answer natural language queries with graph intelligence

#### Use Case 5.1: "Recommend a maker journey for a beginner"

**Agent Query Flow:**

```
User → Agent: "I'm new to making. Where should I start in Brussels?"

Agent Internal Reasoning:
1. Parse intent: Beginner level, location-based
2. Query API for beginner-friendly spaces
3. Check for progression pathways
4. Recommend learning sequence

Agent → Maps of Making API:
GET /api/spaces?
  city=Brussels&
  beginner_friendly=true&
  freshness=14d

Response:
[
  {
    "id": "openfab",
    "name": "OpenFab",
    "skills": [
      {"name": "3D printing", "novice": 8, "beginner_workshops": true},
      {"name": "laser cutting", "novice": 5, "beginner_workshops": true}
    ],
    "partnerships": [
      {"partner_id": "brussels-makerspace", "type": "skill_progression"}
    ]
  }
]

Agent → User Response:
"I recommend starting at **OpenFab** in Brussels (verified 3 days ago ✅).

They offer beginner-friendly workshops in:
- 3D printing (8 novice-level members)
- Laser cutting (5 novice-level members)

Once you're comfortable, they partner with **Brussels Makerspace** for
advanced courses in electronics and robotics. This progression pathway
helps you level up naturally.

Would you like me to show you their location on the map?"
```

**Visual Enhancement: Skill Progression Pathways**

```
Map Overlay: Learning Journey
┌─────────────────────────────────────────────────┐
│                                                 │
│  START HERE                                     │
│   ◉ OpenFab                                     │
│   │ (Beginner: 3D print, laser)                 │
│   │                                             │
│   ↓ (After 3-6 months)                          │
│   │                                             │
│   ◉ Brussels Makerspace                         │
│   │ (Intermediate: Electronics, robotics)       │
│   │                                             │
│   ↓ (After 6-12 months)                         │
│   │                                             │
│   ◉ Advanced Fab Lab                            │
│     (Advanced: Custom PCB, CNC machining)       │
│                                                 │
│  Estimated journey: 12-18 months to advanced    │
└─────────────────────────────────────────────────┘
```

**Data Required:**
```cypher
// Skill progression pathways
MATCH path = (beginner:Space)-[:PARTNERSHIP*1..3]->(advanced:Space)
WHERE (beginner)-[:HAS_SKILL]->(:Skill {level: 'beginner'})
  AND (advanced)-[:HAS_SKILL]->(:Skill {level: 'advanced'})
  AND point.distance(
    point({latitude: beginner.lat, longitude: beginner.lon}),
    point({latitude: 50.8503, longitude: 4.3517})  // Brussels
  ) < 15000

RETURN path,
       [node IN nodes(path) | node.name] as journey,
       length(path) as steps
ORDER BY steps ASC
LIMIT 5
```

---

## 3. Visual Data Representation Strategies

### 3.1 Skills Diversity Visualization

**Challenge:** How to show skill breadth AND depth without cluttering the map?

#### Strategy 1: Skill Flower / Petal Chart

```
Marker Detail View:
┌─────────────────────────────────────┐
│  ElektroLab                         │
│  ═══════════════════════════════   │
│                                     │
│         Electronics                 │
│              │                      │
│         ╱────┼────╲                 │
│    Robotics  │  Textiles            │
│         ╲    │    ╱                 │
│          ╲   │   ╱                  │
│           ╲  │  ╱                   │
│            ╲ │ ╱                    │
│        3D Print──Metalwork          │
│                                     │
│  Petal length = proficiency level   │
│  Petal color = instructor count     │
└─────────────────────────────────────┘

Implementation: SVG overlay on marker
```

#### Strategy 2: Stacked Ring Chart

```
Marker Icon:
    ╭─────╮
    │ ░▓█ │  ← Rings from center:
    │ ▓█░ │     - Center: Primary skill
    │ █░▓ │     - Middle ring: Secondary skills
    ╰─────╯     - Outer ring: Tertiary skills

Color legend:
▓ = Electronics
█ = Metalworking
░ = Textiles
```

#### Strategy 3: Heatmap Clustering by Skill Dominance

```
Map View (Zoom 8):
┌─────────────────────────────────────────────────┐
│                                                 │
│   [Electronics Hub]                             │
│    🔵🔵🔵🔵🔵                                    │
│    🔵🔵🔵🔵                                      │
│                                                 │
│            [Textile Cluster]                    │
│             🟣🟣🟣                               │
│                                                 │
│   [Mixed Making]                                │
│    🟡🟢🔴🟠                                     │
│    🟠🟡🟢                                        │
│                                                 │
│  Legend:                                        │
│  🔵 = Electronics-dominant                      │
│  🟣 = Textiles-dominant                         │
│  🟡 = Woodworking-dominant                      │
│  🟢 = Multi-skill balanced                      │
└─────────────────────────────────────────────────┘
```

### 3.2 Skill Level Encoding

**Options for showing proficiency without text:**

| Encoding | Visual | Pros | Cons |
|----------|--------|------|------|
| **Marker Size** | Small → Large | Intuitive | Clutters at high zoom |
| **Badge Count** | ⭐⭐⭐ (3 stars) | Clear hierarchy | Requires space |
| **Concentric Rings** | ◎ vs ○ | Compact | Less obvious |
| **Color Saturation** | 🟢 → 🟩 → 🟦 | Subtle | Color-blind issues |
| **Icon Variant** | 🎓 vs 🏆 vs 👑 | Fun, memorable | Requires legend |

**Recommended Hybrid:**
- **Marker color** = Freshness (green/yellow/red)
- **Marker size** = Total community size
- **Badge overlay** = Professional-level instruction (⭐ icon)
- **Popup detail** = Full skill breakdown

### 3.3 Partnership Strength Visualization

```
Edge thickness = Activity score
╔═══════════╗ = Active partnership (thick)
╠───────────╣ = Moderate (medium)
╟ ─ ─ ─ ─ ─ ╢ = Dormant (dashed)

Edge color = Partnership type
────────── = Skill exchange (blue)
━━━━━━━━━━ = Equipment sharing (green)
┄┄┄┄┄┄┄┄┄┄ = Joint events (purple)
```

**Example:**
```
ElektroLab ════════ TextileWorks
           (Active skill exchange - 12 events in last 90 days)

OpenFab ─ ─ ─ ─ ─ ─ MakerZone
        (Dormant equipment sharing - no activity in 60 days)
```

### 3.4 Temporal Decay Animation

**Real-time freshness decay visualization:**

```
Day 0 (just verified):
◉ ← Bright, solid, prominent

Day 15:
◉ ← Slight fade

Day 30:
◎ ← Border appears, color shifts

Day 60:
○ ← More transparent, pulsing border

Day 90+:
◌ ← Nearly transparent, urgent pulse
```

**CSS Implementation:**
```css
.marker-fresh {
  opacity: 1;
  box-shadow: 0 0 10px rgba(34, 197, 94, 0.6);
}

.marker-aging {
  opacity: 0.8;
  border: 2px solid #eab308;
  animation: gentlePulse 3s infinite;
}

.marker-zombie {
  opacity: 0.5;
  border: 3px dashed #ef4444;
  animation: urgentPulse 1.5s infinite;
}

@keyframes urgentPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}
```

---

## 4. Partnership Handshake UX Flow

### 4.1 The Handshake Concept

**Problem:** How do we validate partnerships are mutual and current?

**Solution:** Two-sided confirmation ("handshake") required for partnership to appear as "active"

### 4.2 User Flow Diagram

```
Flow 1: Space A Initiates Partnership
════════════════════════════════════════════════════

Step 1: Space A proposes partnership
┌─────────────────────────────────────┐
│  ElektroLab Dashboard               │
│  ─────────────────────────────────  │
│  Nearby Spaces:                     │
│   ◉ TextileWorks (2.3 km)           │
│      Skills: Textiles, Fashion      │
│      [+ Suggest Partnership]   ← CLICK
└─────────────────────────────────────┘

Step 2: Select partnership type
┌─────────────────────────────────────┐
│  Propose Partnership to TextileWorks│
│  ─────────────────────────────────  │
│  Select type(s):                    │
│  [X] Skill exchange                 │
│  [ ] Equipment sharing              │
│  [X] Joint workshops                │
│  [ ] Residency exchange             │
│                                     │
│  Optional message:                  │
│  ┌───────────────────────────────┐ │
│  │ We'd love to collaborate on   │ │
│  │ wearable electronics projects! │ │
│  └───────────────────────────────┘ │
│                                     │
│  [Send Proposal]                    │
└─────────────────────────────────────┘

Step 3: Pending state created in Neo4j
CYPHER:
CREATE (a:Space {id: 'elektrolab'})
      -[:SUGGESTS_PARTNERSHIP {
        types: ['skill_exchange', 'joint_workshops'],
        message: '...',
        proposed_at: datetime(),
        status: 'pending'
      }]->
      (b:Space {id: 'textileworks'})

Step 4: TextileWorks receives notification
┌─────────────────────────────────────┐
│  TextileWorks Dashboard             │
│  ─────────────────────────────────  │
│  🔔 New Partnership Proposal        │
│                                     │
│  ElektroLab wants to partner!       │
│  Types: Skill exchange, Joint workshops│
│  Message: "We'd love to..."         │
│                                     │
│  [View Details]                     │
└─────────────────────────────────────┘

Step 5: TextileWorks reviews and accepts
┌─────────────────────────────────────┐
│  Partnership Proposal Details       │
│  ─────────────────────────────────  │
│  From: ElektroLab                   │
│  Distance: 2.3 km                   │
│  Their skills: Electronics, Robotics│
│  Our skills: Textiles, Fashion      │
│                                     │
│  Synergy analysis:                  │
│  ✓ Complementary skills (87% match) │
│  ✓ Geographic proximity             │
│  ✓ Both active spaces               │
│                                     │
│  [Accept Partnership]  [Decline]    │
└─────────────────────────────────────┘

Step 6: Handshake complete! 🤝
CYPHER:
MATCH (a:Space {id: 'elektrolab'})
     -[prop:SUGGESTS_PARTNERSHIP]->
     (b:Space {id: 'textileworks'})
DELETE prop
CREATE (a)-[:PARTNERSHIP {
  types: prop.types,
  since: datetime(),
  activity_score: 1.0,
  last_activity: datetime(),
  status: 'active'
}]-(b)  ← Bidirectional relationship

Step 7: Partnership appears on map
┌─────────────────────────────────────┐
│  Map View                           │
│                                     │
│   ◉ ElektroLab                      │
│   ║                                 │
│   ║  [New! partnership formed]      │
│   ║                                 │
│   ◉ TextileWorks                    │
│                                     │
│  Both spaces now see "buds" and     │
│  edges connecting them              │
└─────────────────────────────────────┘
```

### 4.3 Incentive Design

**Why would users complete handshakes?**

✅ **Visibility Reward:**
- Partnered spaces get highlighted in searches
- "Well-connected" badge on profile
- Higher ranking in recommendations

✅ **Discovery Boost:**
- "Users who visited ElektroLab also visited TextileWorks"
- Cross-promotion in partner's visitor flow

✅ **Social Proof:**
- "This space has 7 active partnerships" = trusted
- Partnership count visible on marker

✅ **Network Effects:**
- Algorithms suggest partnerships to isolated spaces
- Coordinators get alerts: "You have 0 partnerships - want suggestions?"

### 4.4 Ongoing Activity Tracking

**Problem:** Partnerships decay over time if not maintained

**Solution:** Activity signals refresh partnership vitality

```
Activity Sources:
1. Manual ping: "We just did a joint workshop!" (form submission)
2. Mutual verification: Both spaces verify partnership during annual check
3. Cross-referencing: Space A mentions Space B in social media (webhook)
4. Event data: Calendar integration shows joint events

Neo4j Update:
MATCH (a:Space)-[p:PARTNERSHIP]-(b:Space)
WHERE id(p) = $partnershipId
SET p.last_activity = datetime(),
    p.activity_score = p.activity_score * 0.9 + 0.1  // Boost score

If no activity for 90 days:
SET p.status = 'dormant'  // Visual change on map (dashed edge)

If no activity for 180 days:
// Keep historical record, but fade on map
SET p.status = 'archived'
```

### 4.5 Partnership Dissolution

```
Either space can end partnership:
┌─────────────────────────────────────┐
│  Your Partnerships                  │
│  ─────────────────────────────────  │
│  ◉ TextileWorks                     │
│     Active since 2024-03-15         │
│     Last activity: 45 days ago      │
│                                     │
│     [View Details]  [End Partnership]│
└─────────────────────────────────────┘

Confirmation dialog:
┌─────────────────────────────────────┐
│  End Partnership?                   │
│  ─────────────────────────────────  │
│  This will:                         │
│  • Remove active partnership status │
│  • Preserve historical record       │
│  • Notify TextileWorks              │
│                                     │
│  Optional reason (improves algorithm):│
│  [ ] Collaboration completed        │
│  [ ] Space focus changed            │
│  [ ] Distance too far               │
│  [ ] Other: _________               │
│                                     │
│  [Confirm End]  [Cancel]            │
└─────────────────────────────────────┘

Neo4j Update:
MATCH (a)-[p:PARTNERSHIP]-(b)
SET p.status = 'ended',
    p.ended_at = datetime(),
    p.end_reason = $reason
// Relationship persists for historical analysis
```

---

## 5. MakerSkillTree Integration (Side-Quest)

### 5.1 What is MakerSkillTree?

**Project:** https://github.com/sjpiper145/MakerSkillTree

**Purpose:** Printable skill progression templates across 70+ domains
- Visual skill trees with hexagonal tiles (73 per tree)
- Hierarchical: Base level → Advanced levels
- Covers tech (robotics, 3D printing), crafts (sewing, metalworking), life skills

**Data Format:**
- SVG (visual)
- YAML (machine-readable)
- JSON schema (interoperability)

### 5.2 Integration Vision

**Problem:** Maps of Making tracks "spaces teach metalworking" but not "what metalworking skills?"

**Solution:** Link MakerSkillTree taxonomy to space skill profiles

#### Example: Metalworking Skill Tree

```
MakerSkillTree: Metalworking
══════════════════════════════

Level 1 (Foundation):
├─ Safety basics
├─ Tool identification
├─ Material properties
└─ Basic cuts

Level 2 (Intermediate):
├─ Welding (MIG)
├─ Lathe operation
├─ Press brake
└─ Sheet metal forming

Level 3 (Advanced):
├─ TIG welding
├─ CNC mill operation
├─ Complex assemblies
└─ Finishing techniques

Maps of Making Integration:
════════════════════════════
MATCH (s:Space)-[:HAS_SKILL]->(skill:Skill {name: 'metalworking'})
SET skill.skill_tree_id = 'makerskilltree:metalworking-v1.0'

CREATE (s)-[:TEACHES {
  skill_id: 'metalworking.level2.welding_mig',
  proficiency: 'advanced',
  instructors: 3
}]->(SkillNode {
  tree: 'metalworking',
  node_id: 'level2.welding_mig',
  name: 'MIG Welding'
})
```

### 5.3 User-Facing Features

#### Feature 1: Skill Coverage Visualization

```
Space Detail Page:
┌─────────────────────────────────────────────────┐
│  ElektroLab - Skill Profile                     │
│  ══════════════════════════════════════════    │
│                                                 │
│  Electronics Skill Tree Coverage:               │
│                                                 │
│         [Microcontrollers] ✓                    │
│              │                                  │
│      ┌───────┼───────┐                          │
│      │       │       │                          │
│   [Arduino] [ESP32] [STM32]                     │
│      ✓       ✓       ✗  ← Not taught here      │
│      │       │                                  │
│  [Sensors] [Actuators]                          │
│      ✓       ✓                                  │
│                                                 │
│  ✓ = Taught here (click for instructor details)│
│  ✗ = Not available (suggest nearby space?)     │
│                                                 │
│  Missing STM32? Try:                            │
│   → AdvancedLab (3.5 km) - Professional level   │
└─────────────────────────────────────────────────┘
```

#### Feature 2: Skill Gap Finder

```
User Query: "I know Arduino, want to learn ESP32"

Map Response:
┌─────────────────────────────────────────────────┐
│  Spaces teaching ESP32 (next step from Arduino):│
│                                                 │
│  1. ◉ ElektroLab (verified 2d ago) ✅           │
│     Distance: 1.2 km                            │
│     Level: Intermediate → Advanced              │
│     Instructors: 2 professionals                │
│     [View Details]                              │
│                                                 │
│  2. ◉ MakerHub (verified 12d ago)               │
│     Distance: 4.7 km                            │
│     Level: Beginner → Intermediate              │
│     [View Details]                              │
└─────────────────────────────────────────────────┘
```

#### Feature 3: Skill Progression Pathways

```
Learning Journey Planner:
┌─────────────────────────────────────────────────┐
│  Your Goal: Master Robotics                     │
│  ══════════════════════════════════════════    │
│                                                 │
│  Recommended Path:                              │
│                                                 │
│  Phase 1 (0-3 months): Foundations              │
│  ┌─────────────────────────────────┐            │
│  │ ◉ OpenFab                        │            │
│  │   - Arduino basics               │            │
│  │   - Sensor integration           │            │
│  │   - Basic motors                 │            │
│  └─────────────────────────────────┘            │
│                                                 │
│  Phase 2 (3-8 months): Intermediate             │
│  ┌─────────────────────────────────┐            │
│  │ ◉ ElektroLab                     │            │
│  │   - ESP32 programming            │            │
│  │   - Servo control                │            │
│  │   - Basic kinematics             │            │
│  └─────────────────────────────────┘            │
│                                                 │
│  Phase 3 (8-12 months): Advanced                │
│  ┌─────────────────────────────────┐            │
│  │ ◉ RoboticsCentral                │            │
│  │   - ROS framework                │            │
│  │   - Computer vision              │            │
│  │   - Autonomous navigation        │            │
│  └─────────────────────────────────┘            │
│                                                 │
│  Total journey: ~12 months to autonomous robots │
└─────────────────────────────────────────────────┘
```

### 5.4 Data Requirements

**Neo4j Schema Extension:**

```cypher
// New node type: SkillTreeNode
CREATE (node:SkillTreeNode {
  tree_id: 'makerskilltree:metalworking-v1.0',
  node_id: 'level2.welding_mig',
  name: 'MIG Welding',
  level: 2,
  prerequisites: ['level1.safety_basics', 'level1.material_properties'],
  description: 'Metal Inert Gas welding technique',
  external_url: 'https://makerskilltree.org/metalworking/mig-welding'
})

// Link spaces to specific skill tree nodes
MATCH (s:Space {id: 'elektrolab'})
CREATE (s)-[:TEACHES {
  proficiency: 'advanced',
  instructors: 3,
  last_verified: datetime()
}]->(node)

// Query: Find spaces teaching specific skill
MATCH (s:Space)-[t:TEACHES]->(n:SkillTreeNode)
WHERE n.node_id = 'level2.welding_mig'
  AND t.proficiency IN ['advanced', 'professional']
RETURN s, t.instructors
```

### 5.5 Implementation Phases

**Phase 0 (Research):**
- Contact MakerSkillTree maintainers
- Review license (CC BY-NC-SA 4.0 - compatible!)
- Map existing skill categories to skill trees

**Phase 1 (MVP - Optional):**
- Import 5-10 core skill trees (electronics, metalworking, textiles, woodworking, 3D printing)
- Allow spaces to self-report: "We teach these specific nodes"
- Basic visualization in space detail popup

**Phase 2 (Enhanced):**
- Full skill tree browser
- Progression pathway recommendations
- Skill gap analysis

**Phase 3 (Advanced):**
- Individual user skill tracking (privacy-preserving!)
- "Find spaces teaching my next skill" personalized search
- Skill tree completion badges

### 5.6 Privacy Considerations

**Problem:** We don't want to track individual user skills (privacy issue)

**Solution:** Space-level aggregation only

```
❌ BAD (tracks individuals):
User Alice: [skill1, skill2, skill3] - visited ElektroLab

✅ GOOD (space-level aggregate):
ElektroLab teaches:
- skill1: 8 people at advanced level (anonymized)
- skill2: 3 professionals (no names)
- skill3: 12 intermediate learners
```

**If we ever add user accounts (Phase 3+):**
- Skill tracking is opt-in only
- Data stored locally in browser (localStorage)
- Never sent to server without explicit consent
- Export/delete capabilities (GDPR compliant)

---

## 6. MakerTour.fr Residency Patterns

### 6.1 What is MakerTour.fr?

**Platform:** Connects makers with community workshops worldwide (2,500+ spaces)

**Focus:** Residency matchmaking between:
- **Nomad makers** (traveling creators, researchers, digital nomads)
- **Spaces offering residencies** (FabLabs, makerspaces with guest programs)

### 6.2 Residency Types Observed

| Program Type | Duration | Support | Target Audience |
|--------------|----------|---------|-----------------|
| **Long-term residency** | 11 months | Accommodation + food + €360/month | Ages 18-30 (FABLAB l'ATELIER) |
| **Short intensive** | 1 week | Accommodation + meals | International makers (Mountain Makers) |
| **Project-specific** | Up to 10 days | Transport + accommodation | EU-based makers (JRC Makerspace) |
| **Cultural program** | 9 days | Accommodation + food + €50/day | European makers (FabLab Chemnitz) |
| **Hackathon** | 2-4 days | Varies | Collaborative projects (La Fabrique Caylus) |

### 6.3 Integration Opportunities

#### Opportunity 1: Residency Filter on Map

```
Map Filter UI:
┌─────────────────────────────────────┐
│  Show spaces with:                  │
│  ─────────────────────────────────  │
│  [ ] All spaces                     │
│  [X] Residency programs available   │
│                                     │
│  Residency type:                    │
│  [X] Short-term (<2 weeks)          │
│  [ ] Medium-term (1-3 months)       │
│  [ ] Long-term (>3 months)          │
│                                     │
│  Support offered:                   │
│  [X] Accommodation                  │
│  [ ] Financial stipend              │
│  [ ] Materials budget               │
└─────────────────────────────────────┘

Map shows only spaces with residencies
Marker has special icon: 🏠
```

#### Opportunity 2: Nomad Maker Persona (New!)

**Add Persona 6: Nomad Maker**

```
Profile:
- Who: Traveling makers, digital nomads, maker-in-residence applicants
- Goal: Find spaces with residency programs matching their skills
- Pain: Residency programs scattered across websites, hard to discover
- Time: 1-6 months per location

Use Case:
"I'm a nomad maker specializing in bioart. Where can I do a residency
 in Europe that has biolab equipment and offers accommodation?"

Maps of Making shows:
- Spaces with biolab skill + residency programs
- Accommodation support indicator
- Application deadlines
- Past residents' projects (if shared)
```

#### Opportunity 3: Data Schema Extension

```cypher
// New relationship: OFFERS_RESIDENCY
CREATE (s:Space {id: 'fablab-atelier'})
      -[:OFFERS_RESIDENCY {
        type: 'long_term',
        duration_months: 11,
        accommodation: true,
        food_included: true,
        stipend_euro: 360,
        age_restriction: '18-30',
        application_url: 'https://...',
        application_deadline: date('2025-05-01'),
        status: 'open'
      }]->
      (r:ResidencyProgram {
        id: 'fablab-atelier-residency-2025',
        name: 'FABLAB l\'ATELIER Residency',
        description: '11-month maker residency in France'
      })

// Query: Find residencies for bioart
MATCH (s:Space)-[:HAS_SKILL]->(skill:Skill)
WHERE skill.name IN ['biolab', 'bioart', 'biology']
MATCH (s)-[offers:OFFERS_RESIDENCY]->(r:ResidencyProgram)
WHERE offers.status = 'open'
  AND offers.application_deadline > date()
RETURN s, offers, r
ORDER BY offers.application_deadline ASC
```

### 6.4 Potential Partnership with MakerTour.fr

**Collaboration Model:**

1. **Data Sharing:**
   - MakerTour.fr provides residency data → Maps of Making ingests
   - Maps of Making provides freshness signals → MakerTour.fr shows live status

2. **Embeddable Widget:**
   - MakerTour.fr embeds Maps of Making widget on residency pages
   - Shows location context, nearby spaces, partnerships

3. **Cross-Promotion:**
   - "Looking for a residency? Check MakerTour.fr"
   - "Want to see this on a map? Visit Maps of Making"

4. **Shared Infrastructure:**
   - Both use IPFS for decentralization?
   - Common API standards for space data?

**Reach out to:** residency@vulca.eu (MakerTour.fr contact)

---

## 7. Prioritization & Roadmap

### 7.1 Feature Priority Matrix

| Feature | Impact | Effort | Priority | Phase |
|---------|--------|--------|----------|-------|
| **Partnership buds visualization** | 🔴 High | 🟡 Medium | **P0** | 1 |
| **Handshake UX flow** | 🔴 High | 🟡 Medium | **P0** | 1 |
| **Skill diversity markers** | 🟡 Medium | 🟢 Low | **P1** | 1-2 |
| **Health dashboard (Persona 3)** | 🔴 High | 🔴 High | **P1** | 1 |
| **Temporal timeline slider** | 🟡 Medium | 🔴 High | **P2** | 2 |
| **MakerSkillTree integration** | 🟢 Low | 🔴 High | **P3** | Side-quest |
| **Residency filter** | 🟢 Low | 🟢 Low | **P2** | 2 |
| **Skill progression pathways** | 🟡 Medium | 🔴 High | **P3** | 3 |
| **Community detection overlay** | 🟡 Medium | 🔴 High | **P2** | 2 |
| **Multi-space network selection** | 🟢 Low | 🟡 Medium | **P2** | 2 |

### 7.2 Phase 1 MVP Additions

**Add to existing Phase 1 sprint plan:**

| Story ID | Description | Effort | Dependencies |
|----------|-------------|--------|--------------|
| **3.6** | Partnership bud visualization (basic) | 3 days | Stories 2.1, 2.3 (partnerships exist) |
| **3.7** | Partnership handshake UI flow | 2 days | Story 1.11 (magic link auth) |
| **3.8** | Skill diversity markers (stacked ring) | 1 day | Story 2.2 (skill data) |

**Total added effort:** 6 days → Phase 1 becomes 15.5 days (still <3 weeks!)

### 7.3 Phase 2 Enhancements

**Research-focused features (for Persona 2):**
- Temporal timeline slider
- Closure pattern analysis dashboard
- Skill evolution heatmaps

**Network coordinator features (for Persona 3):**
- Partnership matchmaking algorithm
- At-risk space alerts
- Network health trends

### 7.4 Side-Quest Roadmap

**MakerSkillTree Integration:**
- **Phase 0 (Research):** Contact maintainers, assess license - 1 week
- **Phase 1 (Prototype):** Import 5 core skill trees - 2 weeks
- **Phase 2 (Integration):** Link to space profiles - 3 weeks
- **Phase 3 (Advanced):** Progression pathways - 4 weeks

**Total side-quest:** 10 weeks (parallel to main roadmap)

**Suggested approach:**
- Assign to separate developer or community contributor
- Not blocking for MVP launch
- Can be added incrementally

### 7.5 Next Steps

**Immediate (This Week):**
1. ✅ Review this exploration document
2. ⬜ Prioritize which visualizations to prototype first
3. ⬜ Create HTML/SVG mockup for partnership buds
4. ⬜ Test handshake UX flow with 2-3 space operators

**Short-term (Next 2 Weeks):**
1. ⬜ Integrate partnership visualization into Phase 1 sprint
2. ⬜ Update PRD with residency use case (if desired)
3. ⬜ Contact MakerSkillTree maintainers (if pursuing integration)
4. ⬜ Reach out to MakerTour.fr for partnership discussion

**Long-term (Phase 2+):**
1. ⬜ Build temporal analysis features for Persona 2
2. ⬜ Expand skill tree integration
3. ⬜ Launch residency matchmaking features

---

## Appendix: Data Model Additions

### A.1 Partnership Handshake States

```cypher
// State 1: Proposed (one-sided)
(:Space)-[:SUGGESTS_PARTNERSHIP {
  status: 'pending',
  proposed_at: datetime(),
  types: ['skill_exchange'],
  message: 'Would love to collaborate!'
}]->(:Space)

// State 2: Active (handshake complete)
(:Space)-[:PARTNERSHIP {
  status: 'active',
  since: datetime(),
  types: ['skill_exchange', 'joint_workshops'],
  activity_score: 0.85,
  last_activity: datetime()
}]-(:Space)  // Bidirectional

// State 3: Dormant (no activity)
(:Space)-[:PARTNERSHIP {
  status: 'dormant',
  since: datetime(),
  last_activity: datetime('2024-06-01'),  // 5+ months ago
  activity_score: 0.2
}]-(:Space)

// State 4: Ended (historical record)
(:Space)-[:PARTNERSHIP {
  status: 'ended',
  since: datetime('2024-03-01'),
  ended_at: datetime('2025-01-15'),
  end_reason: 'collaboration_completed'
}]-(:Space)
```

### A.2 Residency Program Schema

```cypher
CREATE (r:ResidencyProgram {
  id: 'uuid',
  name: 'Program Name',
  type: 'short_term' | 'medium_term' | 'long_term' | 'project_specific',
  duration_days: 90,

  // Support offered
  accommodation: true,
  food_included: false,
  stipend_euro: 360,
  materials_budget_euro: 500,
  transport_reimbursement: true,

  // Restrictions
  age_min: 18,
  age_max: 30,
  region_restriction: 'EU',

  // Application
  application_url: 'https://...',
  application_deadline: date('2025-05-01'),
  status: 'open' | 'closed' | 'rolling',

  // Metadata
  created_at: datetime(),
  last_updated: datetime()
})

CREATE (s:Space)-[:OFFERS_RESIDENCY]->(r)
```

### A.3 Skill Tree Node Schema

```cypher
CREATE (node:SkillTreeNode {
  tree_id: 'makerskilltree:metalworking-v1.0',
  node_id: 'level2.welding_mig',
  name: 'MIG Welding',
  level: 2,
  category: 'metalworking',
  prerequisites: ['level1.safety_basics'],
  description: 'Description text',
  external_url: 'https://makerskilltree.org/...',
  difficulty: 'intermediate',
  estimated_hours: 40
})

CREATE (s:Space)-[:TEACHES {
  proficiency: 'advanced',
  instructors: 3,
  last_verified: datetime()
}]->(node)
```

---

**Document Status:** Exploration complete
**Next Action:** Review with team, prioritize features for Phase 1
**Estimated Review Time:** 30-45 minutes

---

_Prepared: 2025-11-15_
_Authors: Claude (AI Assistant) + Nicolas (Product Vision)_
