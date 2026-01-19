# Coffee DB Feature Roadmap

> **Audience**: AI coding agents working on this project
> **Autonomy Level**: Decision framework - propose approaches for human approval before building
> **Last Updated**: January 2026

---

## Project Context

### What This Is
A personal coffee brewing experiment tracker built by an intermediate-to-advanced home brewer. Currently a Streamlit app with CSV storage, used to log brews, measure TDS/extraction, and understand what makes a great cup.

### Who It's For
- **Today**: Solo developer tracking personal brewing experiments
- **6-12 months**: Small group of coffee-enthusiast friends (3-5 people) sharing a collective database to learn from each other's experiments

### Core Problems Being Solved
1. **Scientific understanding** - Which parameters actually influence extraction and flavor?
2. **Measurable improvement** - Track progress over time, find optimal recipes
3. **Collective learning** - Pool data with friends to accelerate everyone's brewing skills
4. **Fun** - This is a hobby project, enjoyment matters

### User Context
- **Skill level**: Intermediate brewers who understand extraction science
- **Equipment**: Advanced (refractometers, precise grinders, temp-controlled kettles)
- **Brewing methods**: Everything - pour-over, immersion, espresso
- **Timeline**: Motivated hobbyist pace (few hours/week, steady progress)

---

## Feature 1: Data Visualization & Exploration

### Product Manager View

**Strategic Goal**: Transform raw brewing data into actionable insights that help users understand *why* certain brews succeed and *what* to try next.

**Success Metrics**:
- User can identify their optimal brewing parameters for a given bean
- User can visualize improvement trajectory over time
- User can discover non-obvious correlations (e.g., "my afternoon brews extract higher")

**User Stories**:
1. *"As a brewer, I want to see how my extraction consistency has improved over the past month"*
2. *"As a brewer, I want to compare my results across different beans to find patterns"*
3. *"As a brewer, I want to understand which variables (grind, temp, ratio) most impact my results"*

**Constraints**:
- Must work with existing CSV data structure
- Must handle sparse data (not every field filled for every brew)
- Should degrade gracefully with small datasets (<20 brews)

**Open Questions for Agent**:
- What visualization library best balances interactivity with Streamlit compatibility?
- How should we handle beans with only 1-2 brews in comparison views?
- What's the minimum data needed to show meaningful correlations?

---

### Designer View

**Design Principles**:
1. **Data density over decoration** - Users are analytical; show information, not chrome
2. **Progressive disclosure** - Simple overview first, drill-down for details
3. **Actionable insights** - Every chart should answer "so what should I do?"

**Information Architecture**:
```
Analytics Tab
├── Overview Dashboard (key metrics at a glance)
├── Trend Analysis (time-series of chosen metrics)
├── Bean Comparison (side-by-side or overlay)
└── Parameter Correlation (what influences what)
```

**Interaction Patterns**:
- Date range selector (last 7/30/90 days, all time, custom)
- Metric picker (TDS, extraction yield, overall rating, specific scores)
- Bean multi-select for comparisons
- Hover for details, click for drill-down

**Visual Language**:
- Use existing brewing control chart color scheme for consistency
- Extraction zones (under/ideal/over) should be recognizable across charts
- Highlight personal bests and anomalies

**Open Questions for Agent**:
- How do we visualize multi-dimensional data (grind + temp + ratio) without overwhelming?
- What's the right chart type for bean comparison - radar, grouped bar, small multiples?
- How do we indicate statistical confidence when sample sizes are small?

---

### Developer View

**Technical Approach**:

1. **New Service**: `AnalyticsService`
   - Encapsulates all statistical calculations
   - Returns structured data that visualization layer consumes
   - Fully testable independent of UI

2. **Extend**: `VisualizationService`
   - Add new chart methods using Altair (already in stack)
   - Keep charts composable and reusable

3. **New UI Tab**: Analytics dashboard in main app

**Key Methods to Implement**:
```python
# AnalyticsService
calculate_improvement_trend(df, metric, window_days) -> TrendData
calculate_bean_comparison(df, bean_names) -> ComparisonData
calculate_parameter_correlations(df) -> CorrelationMatrix
identify_optimal_parameters(df, bean_name?) -> OptimalParams
calculate_consistency_metrics(df, bean_name?) -> ConsistencyData
```

**Data Considerations**:
- Handle NaN/missing values in statistical calculations
- Consider caching for expensive correlation calculations
- Ensure timezone-aware date handling for trend analysis

**Testing Requirements** (TDD per project standards):
- Unit tests for each analytics calculation with known inputs/outputs
- Edge cases: empty data, single row, all same values
- Integration test: full flow from data load to chart render

**Open Questions for Agent**:
- Should AnalyticsService live alongside existing services or in a new `analytics/` module?
- What's the right data structure for trend data - dataclass, TypedDict, or plain dict?
- How do we handle the case where a user's data has columns the analytics expect but are always empty?

---

## Feature 2: MCP Support (Model Context Protocol)

### Product Manager View

**Strategic Goal**: Enable natural language interaction with brewing data through Claude, turning the database into an intelligent brewing assistant.

**Success Metrics**:
- User can ask "Why am I consistently under-extracting?" and get a data-backed answer
- User can request "Suggest my next experiment" and receive a reasoned recommendation
- Claude can reference specific brews and parameters in its responses

**User Stories**:
1. *"As a brewer, I want to ask Claude what my best Ethiopian brew was and why"*
2. *"As a brewer, I want Claude to analyze my data and tell me what I should focus on improving"*
3. *"As a brewer, I want Claude to suggest an experiment based on gaps in my data"*

**Evolution Path**:
- **Phase 1**: Query and understand data (read-only)
- **Phase 2**: Generate insights and recommendations
- **Phase 3**: (Future) Recipe recommendations based on preferences and patterns

**Constraints**:
- Must work with Claude Code's MCP integration
- Should leverage AnalyticsService from Feature 1 (build order dependency)
- Keep data local (no cloud sync required for MCP)

**Open Questions for Agent**:
- What's the right granularity for MCP resources - individual brews or aggregated views?
- How do we structure tool responses for optimal Claude reasoning?
- Should MCP prompts be opinionated (suggest specific analyses) or open-ended?

---

### Designer View

**Interaction Design**:

MCP is invisible UI - the "design" is in how Claude communicates with the user about their data.

**Response Patterns**:
1. **Data queries**: Concise, factual, reference specific brews by date/bean
2. **Analysis**: Lead with insight, support with data, suggest action
3. **Recommendations**: Explain reasoning, acknowledge uncertainty, offer alternatives

**Example Interaction Flows**:

```
User: "What's my best V60 brew?"
Claude: "Your highest-rated V60 was the Ethiopian Hamararo on Jan 12 -
        you scored it 4.5/5 with 21.2% extraction. You used a 1:16 ratio
        at 96°C. Want me to analyze what made it work?"

User: "Why do my morning brews score lower?"
Claude: "Looking at your data, morning brews (before 10am) average 3.2
        while afternoon brews average 3.8. The pattern suggests your
        grind is 0.5 steps coarser in mornings - possibly rushing?
        Your extraction is consistently 1.2% lower."
```

**Tone Guidelines**:
- Knowledgeable but not preachy
- Data-driven but conversational
- Suggest, don't prescribe

**Open Questions for Agent**:
- How verbose should tool responses be - minimal data for Claude to interpret, or pre-formatted insights?
- Should we include brewing science context in prompts, or rely on Claude's knowledge?

---

### Developer View

**Technical Approach**:

1. **MCP Server**: Standalone Python module that wraps existing services
2. **Resources**: Expose data as browsable URIs
3. **Tools**: Expose analytics as callable functions
4. **Prompts**: Pre-built templates for common analysis patterns

**Directory Structure**:
```
mcp_server/
├── __init__.py
├── server.py        # Main MCP server, entry point
├── resources.py     # Data resource handlers
├── tools.py         # Analysis tool implementations
└── prompts.py       # Pre-built prompt templates
```

**MCP Resources**:
```
coffee://brews/all              # All brew records (JSON)
coffee://brews/recent/{n}       # Last N brews
coffee://beans/list             # Unique beans with stats
coffee://beans/{name}/brews     # Brews for specific bean
coffee://stats/summary          # Overall statistics
```

**MCP Tools**:
```python
analyze_improvement(metric: str, days: int) -> str
compare_beans(bean_names: list[str]) -> str
find_optimal_parameters(bean_name: str | None) -> str
diagnose_brew(tds: float, extraction: float, ...) -> str
query_brews(filters: dict) -> str
suggest_experiment() -> str
```

**MCP Prompts**:
- `weekly_review` - Summarize brewing activity and trends
- `bean_deep_dive` - Comprehensive analysis of a specific bean
- `experiment_suggestion` - Data-driven next experiment recommendation

**Integration**:
- Create `.claude/mcp.json` for Claude Code auto-discovery
- Server reads from same CSV as main app
- Reuse `DataManagementService` and `AnalyticsService`

**Testing Requirements**:
- Unit tests for each tool with mock data
- Integration test with MCP client library
- Test resource serialization round-trips

**Open Questions for Agent**:
- Which MCP SDK/library should we use for Python? (mcp package vs building from spec)
- How do we handle concurrent access if main app and MCP server both read CSV?
- Should tools return raw data or formatted Markdown for Claude?

---

## Feature 3: Hosting (View-Only Initially)

### Product Manager View

**Strategic Goal**: Enable friends to view brewing data and insights, laying groundwork for future collaborative data contribution.

**Success Metrics**:
- Friends can access the app via URL without setup
- Data updates are visible within reasonable time (same day)
- Clear path to enabling data contribution later

**User Stories**:
1. *"As an owner, I want to share a link so friends can see my brewing experiments"*
2. *"As a viewer, I want to browse the data and analytics without needing to log in"*
3. *"As an owner, I want to retain full edit access while others can only view"*

**Evolution Path**:
- **Phase 1**: Read-only public access, owner edits locally
- **Phase 2**: Authentication, friends can view their own login state
- **Phase 3**: Multi-user contribution to shared database

**Constraints**:
- Start simple - Streamlit Cloud is acceptable
- No sensitive data (coffee brews aren't PII)
- Data sync can be manual (git push) initially

**Open Questions for Agent**:
- Is Streamlit Cloud sufficient, or do we need more control (Railway/Render)?
- How do we communicate "this is read-only for you" without confusing viewers?
- What's the simplest auth model for owner vs viewer?

---

### Designer View

**UX Considerations**:

**Read-Only Mode**:
- Hide tabs/buttons that modify data (Add Brew, Edit, Delete)
- Keep all viewing and analytics functionality intact
- Subtle indicator that user is in "view-only" mode (not an error state)

**Visual Differentiation**:
```
Owner View:                    Viewer View:
[Add Brew] [View] [Analytics]  [View] [Analytics]
     ↑ full access                 ↑ read-only
```

**Messaging**:
- Avoid "you don't have permission" language
- Frame as "Viewing [Owner]'s brewing data"
- If contribution is coming soon, could tease "Want to add your brews? Coming soon!"

**Mobile Considerations**:
- Streamlit has basic mobile responsiveness
- Ensure charts are readable on phone screens
- Consider touch-friendly controls for date pickers

**Open Questions for Agent**:
- Should viewers see who the data belongs to, or is it anonymous?
- How do we handle the transition UX when multi-user goes live?

---

### Developer View

**Technical Approach**:

1. **Read-Only Mode**: Environment variable controls UI visibility
2. **Simple Auth**: Streamlit secrets for owner password
3. **Deployment**: Streamlit Cloud (simplest) or Docker for more control
4. **Data Sync**: Git-based initially (owner commits, deploy pulls)

**Implementation**:

```python
# In coffee_app_refactored.py
import os

READ_ONLY = os.environ.get('COFFEE_DB_READ_ONLY', 'false').lower() == 'true'

def run(self):
    if READ_ONLY:
        tabs = st.tabs(["View Data", "Analytics"])
    else:
        tabs = st.tabs(["Add Brew", "View Data", "Edit Data", "Analytics", "Settings"])
```

**Owner Authentication** (optional, for unlocking edit mode):
```python
# Using Streamlit secrets
if st.sidebar.text_input("Owner Access", type="password") == st.secrets.get("owner_password", ""):
    READ_ONLY = False
```

**Deployment Config**:

For Streamlit Cloud:
- Connect GitHub repo
- Set `COFFEE_DB_READ_ONLY=true` in secrets
- Add `owner_password` to secrets

For Docker (Railway/Render):
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV COFFEE_DB_READ_ONLY=true
EXPOSE 8501
CMD ["streamlit", "run", "coffee_app_refactored.py", "--server.port=8501"]
```

**Data Sync Strategy**:
- CSV stays in git repo
- Owner works locally, commits changes
- Hosted app redeploys on push (or periodic pull)
- Future: Move to cloud storage (S3/R2) for real-time sync

**Testing Requirements**:
- Test that read-only mode hides write operations
- Test owner password unlocks full access
- Test app runs successfully with `READ_ONLY=true`
- Load test: multiple concurrent viewers

**Open Questions for Agent**:
- Should we add health check endpoint for monitoring?
- How do we handle the case where CSV is updated mid-session?
- Is there value in adding basic analytics (page views, active users)?

---

## Build Order & Dependencies

```
┌─────────────────────────────────────┐
│  1. DATA VISUALIZATION              │
│  Creates AnalyticsService that      │
│  MCP tools will leverage            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  2. MCP SUPPORT                     │
│  Wraps AnalyticsService as tools,   │
│  useful locally before hosting      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  3. HOSTING                         │
│  Deploys complete app with all      │
│  features for friends to view       │
└─────────────────────────────────────┘
```

**Rationale**:
1. Visualization creates reusable analytics logic
2. MCP leverages that logic for intelligent responses
3. Hosting wraps the complete, polished product

---

## Agent Instructions

### Before Starting Any Feature

1. **Read this document fully** - understand context and constraints
2. **Propose an approach** - outline your plan before implementing
3. **Identify open questions** - flag anything ambiguous for human input
4. **Follow TDD** - write tests first per project standards (see CLAUDE.md)

### When Proposing an Approach

Include:
- Files you'll create or modify
- Key design decisions and alternatives considered
- Edge cases you've identified
- Testing strategy
- Any questions or concerns

### Success Criteria

Your implementation is successful when:
- All existing tests still pass
- New functionality has comprehensive test coverage
- Code follows existing patterns in the codebase
- Changes are documented in README release notes
- Human can verify the feature works as intended

---

## Appendix: Current Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Streamlit 1.47+ |
| Language | Python 3.13 |
| Data Storage | CSV (pandas) |
| Visualization | Altair |
| Testing | pytest |
| Deployment | None (local only) |

## Appendix: Key Files

| File | Purpose |
|------|---------|
| `coffee_app_refactored.py` | Main Streamlit application |
| `src/services/` | Business logic services |
| `src/models/` | Domain models (BrewRecord, CoffeeBean) |
| `src/ui/` | UI components (wizard, forms) |
| `data/cups_of_coffee.csv` | All brewing data |
| `tests/` | Test suite (232 tests) |
