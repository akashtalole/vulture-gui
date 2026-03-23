# Vulture-GUI Agentic Platform — Ideas & Vision

> Exploring how Vulture-GUI's existing frontend architecture could power a Claude-style
> agent orchestration platform with pluggable skills, multi-agent pipelines, and a
> visual workflow builder.

---

## 1. Vision

Vulture-GUI already contains a sophisticated policy engine with:
- **Visual workflow DAG builder** (`workflow.js` + vis.js)
- **Pluggable filter chains** (Darwin engine)
- **Async task queue** (MessageQueue + daemon threads)
- **Polymorphic module registry** (BaseRepository pattern)
- **Multi-tenant cluster management** (Nodes + Tenants)

The idea is to **extend this existing infrastructure** to orchestrate AI agents and skills
— much like Claude's co-work plugin system, but built into a self-hosted security platform.

---

## 2. Core Concepts

| Concept | Analogy in Vulture-GUI | New Meaning |
|---|---|---|
| **Agent** | `BaseRepository` (polymorphic model) | An AI/rule/script actor with skills |
| **Skill** | `DarwinFilter` type | A callable capability (tool use) |
| **Pipeline** | `FilterPolicy.next_filter` chain | Multi-step agent processing chain |
| **Workflow** | `workflow_json` DAG | Visual multi-agent routing graph |
| **Trigger** | `Frontend` node in workflow | Entry point (HTTP, schedule, event) |
| **Gate** | `WorkflowACL` | Access control before agent runs |
| **Task** | `MessageQueue` entry | Async unit of agent work |
| **Memory** | MongoDB `JSONField` | Persistent agent context/state |

---

## 3. Idea 1 — Agent Registry (Pluggable Agent Types)

**Inspired by:** `BaseRepository.get_daughter()` polymorphism pattern in
`vulture_os/authentication/base_repository.py`

Each agent is a registered subtype with its own config schema.

```
BaseAgent (abstract)
├── LLMAgent            — Claude, GPT, local models via API
├── RuleBasedAgent      — HAProxy ACL-style conditional logic
├── ScriptAgent         — Execute arbitrary Python/shell scripts
├── HumanInTheLoopAgent — Pause for human approval
├── APIAgent            — Call external REST APIs as a skill
└── CompositeAgent      — Wraps a full sub-workflow as an agent
```

**How it maps:** Exactly like `REPO_LIST = ["ldaprepository", "openidrepository", ...]`,
an `AGENT_REGISTRY` dict maps agent types to validator/config schemas.

**UI:** New `Agents` menu section (like `Authentication`), listing registered agents
as Bootstrap panel cards with status indicators.

---

## 4. Idea 2 — Skill / Tool Registry

**Inspired by:** `DARWIN_FILTER_CONFIG_VALIDATORS` dict in
`vulture_os/darwin/policy/models.py`

A skill is a Python callable registered by name with an input/output schema:

```python
SKILL_REGISTRY = {
    "web_search":        WebSearchSkill,
    "read_file":         ReadFileSkill,
    "send_email":        SendEmailSkill,
    "query_mongodb":     MongoQuerySkill,
    "call_haproxy_api":  HAProxySkill,
    "run_darwin_filter": DarwinSkill,   # reuse existing Darwin filters!
    "generate_report":   ReportSkill,
    "human_approval":    HumanApprovalSkill,
}
```

Skills are dispatched via the existing `import_string()` mechanism in
`MessageQueue.execute()` — **zero new infrastructure needed** for async skill execution.

**UI:** A `Skills` library page showing available tools as Bootstrap tiles
(icon, name, description, input/output schema). Similar to an app store listing.

---

## 5. Idea 3 — Visual Agent Workflow Builder

**Inspired by:** `vulture_os/gui/static/js/workflow.js` (vis.js + jsTree DAG editor)

The existing workflow builder renders a directed graph of Frontends → ACLs → Backends.
**Re-skin this for agent orchestration:**

```
Trigger Node ──► Agent A ──► Skill 1 ──► Agent B ──► Output Node
                    │                        │
                    └──► Fallback Agent ◄────┘
                                │
                            Human Gate
```

**New node types** (alongside existing ones):

| Node Type | Purpose |
|---|---|
| `agent` | An LLM or rule-based agent |
| `skill` | A specific tool call |
| `memory_read` / `memory_write` | Context persistence |
| `branch` | Conditional routing (reuse `action_satisfy/action_not_satisfy`) |
| `human_gate` | Pause for human approval |
| `parallel` | Fan-out to multiple agents simultaneously |
| `aggregate` | Collect results from parallel branches |

**Key reuse:** The `workflow_json` tree format, `WorkflowACL` ordering, and vis.js
rendering are all directly extensible — only new node type renderers are needed.

---

## 6. Idea 4 — Agent Pipeline (Darwin-Style Filter Chaining)

**Inspired by:** `FilterPolicy.next_filter` self-referential FK in
`vulture_os/darwin/policy/models.py`

An agent pipeline is a linear chain where each agent's output feeds the next:

```
Input ──► Classifier Agent ──► Routing Agent ──► Responder Agent ──► Output
               │                      │
           (tag: spam)           (route: support)
```

**DarwinBuffering analogy:** If Agent A outputs raw text and Agent B expects structured
JSON, an automatic `ParserAgent` is inserted in between — mirroring how `update_buffering()`
auto-inserts buffer filters for incompatible output types.

**Output types** (mirror Darwin's `NONE/LOG/RAW/PARSED`):

| Type | Behaviour |
|---|---|
| `NONE` | Discard result |
| `LOG` | Write to audit log only |
| `FORWARD` | Pass to next agent |
| `RESPOND` | Send as final response |
| `STORE` | Persist to memory/MongoDB |

---

## 7. Idea 5 — Async Agent Execution Engine

**Inspired by:** `MessageQueue` + `TasksJob` daemon in
`vulture_os/system/cluster/` and `vulture_os/daemons/`

The existing system already queues and dispatches arbitrary Python callables.
Extend it for agent tasks:

```python
# Queue an agent run anywhere in the codebase
Cluster.api_request(
    action="agents.llm.claude_agent.run",
    config=json.dumps({
        "agent_id": "uuid",
        "skill": "web_search",
        "input": "latest CVEs for HAProxy",
        "context_id": "session-xyz"
    }),
    run_delay=0  # Immediate or scheduled
)
```

**New daemon:** `AgentJob` thread (alongside existing `TasksJob`, `MonitorJob`)
polls for agent-specific queue entries every 1 second.

**Scheduling:** Combine with `django-crontab` for periodic agents
(e.g., daily threat report agent, weekly compliance summary).

---

## 8. Idea 6 — Agent Memory & Context Store

**New concept** built on MongoDB's flexible document storage:

Each agent session has a `ContextStore` document:

```json
{
  "session_id": "uuid",
  "agent_id": "uuid",
  "created_at": "2026-03-23T...",
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "agent", "content": "...", "skill_calls": [...]}
  ],
  "metadata": {"workflow_id": "...", "triggered_by": "..."},
  "working_memory": {}
}
```

Agents can `memory_read` previous context and `memory_write` findings —
enabling multi-turn reasoning across multiple async task queue executions.

MongoDB's flexible `JSONField` schema is **ideal** for this: no predefined columns,
arbitrary nesting, and native array operations.

---

## 9. Idea 7 — Access Control Gates for Agents

**Inspired by:** `AccessControl` ACL rules in
`vulture_os/darwin/access_control/models.py`

Before any agent executes, a `WorkflowACL` gate evaluates conditions:

```
IF  user.group == "security_team"
AND request.path starts_with "/api/agents/"
AND time.hour between 9 and 17
THEN  allow
ELSE  queue_for_human_approval
```

**Reuse `generate_rules()` HAProxy ACL syntax exactly** — criteria like `src`, `hdr`,
`http_auth_group` already exist. Proposed new criteria:

| Criterion | Purpose |
|---|---|
| `agent.cost_estimate` | Budget gate (block if >$10 per run) |
| `agent.risk_score` | Darwin-computed risk classification |
| `workflow.depth` | Prevent infinite agent recursion |
| `agent.skill` | Whitelist specific skills per user group |

---

## 10. Idea 8 — Agent Dashboard & Observability

**Inspired by:** `dashboard_services.html` Vue.js polling dashboard
(`vulture_os/gui/templates/gui/dashboard_services.html`)

Extend the existing dashboard with an **Agent Operations Center**:

```
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│   Active Agents  3  │  │  Skills Executed 47  │  │   Queue Depth   12  │
│   ● Claude Agent    │  │  Top: web_search      │  │  🟢 Running:  3    │
│   ● Report Agent    │  │  Top: send_email      │  │  🟡 Waiting:  6    │
│   ● Classifier      │  │  Top: query_mongo     │  │  🔴 Failed:   3    │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
```

Vue.js polling every 3 seconds from `/api/v1/agents/monitor/` — mirrors the
existing `ServiceStatus` monitoring API pattern exactly.

**Per-agent drill-down panel** shows:
- Execution timeline with duration per step
- Skill call tree (what tools were called in what order)
- Token/cost usage for LLM agents
- Input/output preview (collapsible)
- Error trace with stack if failed

---

## 11. Idea 9 — Multi-Tenant Agent Isolation

**Inspired by:** `Tenants` module in `vulture_os/system/tenants/`

Each tenant gets isolated agent execution:

| Isolation Layer | Detail |
|---|---|
| Agent registry | Tenant can only see its own registered agents |
| Skill whitelist | Tenant A can use `web_search`; Tenant B cannot |
| Context/memory namespace | MongoDB documents namespaced by tenant ID |
| Resource quotas | Max concurrent agents, token budget per month |
| Audit trail | Per-tenant MongoDB collection |

**HAProxy ACL integration:** Route agent API requests to the right tenant's agent
cluster using existing frontend/backend proxying infrastructure.

---

## 12. Idea 10 — Prompt Templates via Jinja2

**Inspired by:** Jinja2 config generation in `vulture_os/services/service.py`

LLM agents use Jinja2 templates for system prompts — the **exact same templating
engine** already used for generating HAProxy, rsyslog, and OpenVPN configs:

```jinja2
{# templates/agents/security_analyst.j2 #}
You are a security analyst for {{ tenant.name }}.
Your cluster has {{ node_count }} nodes:
{% for node in nodes %}  - {{ node.name }} ({{ node.status }})
{% endfor %}
Current threat level: {{ darwin_risk_score }}.

Available skills: {% for skill in agent.skills %}{{ skill.name }}{% endfor %}

Analyze the following event and respond with a risk assessment:
{{ input.event_data }}
```

Same `Environment(loader=FileSystemLoader(...))` pattern from `service.py` —
zero new infrastructure needed for prompt management.

---

## 13. Idea 11 — Agent Plugin Auto-Discovery

**Inspired by:** Menu registration in `vulture_os/applications/apps.py` +
`vulture_os/gui/context_processors.py`

Each agent plugin is a standard Django app with a manifest:

```python
# agents/claude_agent/apps.py
class ClaudeAgentApp:
    @property
    def menu(self):
        return {
            'link': 'claude_agent',
            'icon': 'fa fa-robot',
            'text': 'Claude Agent',
            'url': '/agents/claude/',
        }

    @property
    def skills(self):
        return ['web_search', 'code_generation', 'analysis']

    @property
    def agent_type(self):
        return 'llm'
```

The central context processor auto-discovers installed agent apps and registers them in:
1. The sidebar navigation
2. The skill registry
3. The monitoring dashboard

**Installing a new agent = `pip install vulture-agent-xyz` + add to `INSTALLED_APPS`.**

---

## 14. Idea 12 — Human-in-the-Loop Approval Workflow

**New concept** using existing notification (`PNotify`) + `MessageQueue` patterns:

1. Agent requests a high-risk skill (e.g., `delete_firewall_rule`)
2. `MessageQueue` entry created with status `WAITING_APPROVAL`
3. Notification pushed to admin via PNotify toast + optional email
4. Admin sees pending approval card on dashboard
5. Admin approves/rejects with optional override note
6. Entry transitions to `NEW` → `TasksJob` daemon executes it

**UI:** Approval queue panel on the dashboard, similar to existing process queue
at `/process_queue/`. Action buttons: Approve / Reject / Modify & Approve.

---

## 15. Idea 13 — Agent-to-Agent Communication Bus

**New concept** built on Redis (already running at `127.0.0.5:6379`):

Redis Pub/Sub channels for inter-agent messaging:

```
agents.broadcast          — broadcast to all agents
agents.<agent_id>         — direct message to specific agent
agents.skills.web_search  — results from a shared skill
agents.workflows.<id>     — messages scoped to a workflow run
```

Agents publish results and subscribe to inputs — enabling **event-driven agent
chaining** without polling. This is also the **WebSocket upgrade path**: Django
Channels + the existing Redis backend enables real-time agent status in the browser
without changing the message bus.

---

## 16. Idea 14 — Security-First Agent Sandboxing

**Unique to Vulture-GUI** — agents run inside the existing **FreeBSD jail architecture**:

- Each agent type gets its own jail (like `jails.haproxy`, `jails.portal`)
- Skill execution is isolated — an agent cannot escape its jail
- Filesystem access limited to designated mount points
- Network access controlled by PF firewall rules (already managed by Vulture)
- Agent logs written to `/var/log/vulture/agents/<agent_id>.log`

This gives Vulture-GUI's agentic platform a **security advantage** over cloud-hosted
agent platforms — all agent execution is self-hosted, jailed, and fully auditable.

---

## 17. Idea 15 — Darwin-Powered Agent Input Filtering

**Unique integration** — all input to agents passes through the Darwin security
engine before the agent ever sees it:

```
Incoming Request / User Prompt
            │
            ▼
    Darwin Filter Chain
    ├── DGA Detection       — Is a URL in the prompt malicious?
    ├── Anomaly Detection   — Is this a prompt injection attempt?
    ├── Host Lookup         — Is the source IP in threat intel feeds?
    └── YARA Rules          — Does the input match known malware patterns?
            │
            ▼  (only if all filters pass)
    Agent Execution
```

**Prompt injection defense** implemented at the infrastructure level —
not as fragile application-layer heuristics.

---

## 18. Summary Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                      Vulture-GUI Frontend                         │
│          (Django + Bootstrap + Vue.js + vis.js)                  │
├──────────────────────┬─────────────────────┬─────────────────────┤
│   Agent Registry     │   Skill Registry    │  Workflow Builder   │
│   (BaseAgent         │   (SKILL_REGISTRY   │  (workflow_json DAG │
│    polymorphism)     │    + Jinja2 prompts)│   + vis.js/jsTree)  │
├──────────────────────┴─────────────────────┴─────────────────────┤
│                   Async Execution Engine                          │
│       (MessageQueue + TasksJob + AgentJob daemon threads)        │
├─────────────────────────────────┬────────────────────────────────┤
│  Access Control & Safety Gates  │  Observability & Dashboard     │
│  (WorkflowACL + Darwin ACLs     │  (Monitor model + Vue.js       │
│   + Human-in-the-Loop queue)    │   polling + drill-down panels) │
├─────────────────────────────────┴────────────────────────────────┤
│                  Context / Memory Store                           │
│       (MongoDB flexible JSONField documents per session)         │
├──────────────────────────────────────────────────────────────────┤
│                      Infrastructure Layer                         │
│   HAProxy  |  FreeBSD Jails  |  Redis Pub/Sub  |  Darwin Engine  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 19. What Makes This Unique vs Generic Agent Platforms

| Feature | Generic Cloud Platforms | Vulture-GUI Agentic |
|---|---|---|
| Security isolation | Application-level sandboxing | FreeBSD jail + PF firewall |
| Input filtering | Prompt engineering only | Darwin ML filter chain |
| Access control | API keys / RBAC | HAProxy ACL rule trees (full DSL) |
| Multi-tenancy | Extra cost / complex config | Built-in tenant system |
| Audit trail | Logs only | MongoDB time-series synced across cluster |
| Workflow builder | Separate third-party tool | Already in the UI (vis.js DAG) |
| Deployment model | Cloud-only / SaaS | Self-hosted, air-gapped capable |
| Agent scheduling | External cron service | `django-crontab` native |
| High availability | Managed service | MongoDB replica set + HAProxy |
| Prompt templating | Proprietary DSL | Jinja2 (same engine as configs) |

---

## 20. Quickstart Ideas for Prototyping

These are the lowest-effort starting points that reuse the most existing code:

1. **Skill via MessageQueue** — Register a new `action` path in `INSTALLED_APPS`,
   call `Cluster.api_request("agents.skills.web_search.run", config=...)`.
   The entire async execution infrastructure already works.

2. **Agent card on dashboard** — Copy `dashboard_services.html` panel structure,
   point polling at a new `/api/v1/agents/status/` endpoint.

3. **Agent menu entry** — Add a new `apps.py` class returning a `menu` dict and
   register it in `context_processors.py`. Sidebar entry appears immediately.

4. **Prompt template** — Drop a `.j2` file into `services/` templates directory,
   render it with the existing `jinja2_env.get_template()` call pattern.

5. **LLM repo type** — Create `LLMRepository` extending `BaseRepository`,
   add it to `REPO_LIST`. Appears in the authentication/repo dropdown automatically.

---

*Document generated: 2026-03-23*
*Based on Vulture-GUI v2.35.1 codebase analysis*
