# Cloud Agent

A cloud coding agent built from scratch — the same category of system as Devin, Warp's agent, or Cursor's background agent. Give it a task, it clones a real repository, reasons about the codebase, makes changes, and opens a real pull request. No step is scripted or templated; every action is decided by the model through a tool-calling loop.

This project isn't a wrapper around an existing agent framework. It's built from the ground up specifically to understand — and prove, through deliberate failure testing — the distributed-systems mechanics that make a system like this reliable: message durability, idempotency, and secure credential delegation.

**Proof it works end to end:** [PR #1](https://github.com/navtej21/QuickNotesAI/pull/1) — opened autonomously by the agent: cloned the repo, made a change, committed, pushed to a new branch, and opened the PR via GitHub's API, with no manual git commands.

---

## Architecture

```
                    ┌─────────────────┐
   HTTP POST        │   Spring Boot    │
   /tasks     ─────▶│  (orchestration) │
                    └────────┬─────────┘
                             │ publishes task
                             ▼
                    ┌─────────────────┐
                    │  Redis Streams   │◀──────────────┐
                    │  (agent_tasks)   │                │
                    └────────┬─────────┘                │
                             │ consumes                  │
                             ▼                            │
                    ┌─────────────────┐   tool_requests  │
                    │  Agent Service   │─────────────────▶│
                    │  (Python)        │                  │  Redis Streams
                    │  - LLM loop      │◀─────────────────┤  (tool_requests /
                    │  - decides WHAT  │   tool_results    │   tool_results)
                    │    to do next    │                  │
                    └─────────────────┘                  │
                                                            │
                    ┌─────────────────┐                   │
                    │ Executor Service │◀──────────────────┘
                    │  (Python,        │
                    │   Dockerized)    │
                    │  - runs bash,    │
                    │    file I/O      │
                    │  - decides HOW   │
                    │    to do it      │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   GitHub App     │
                    │  JWT → scoped    │
                    │  installation    │
                    │  token → clone / │
                    │  push / open PR  │
                    └─────────────────┘
```

The system is deliberately split into two independent processes that never call each other directly:

- **Agent Service** — talks to Claude, decides what tool to call next. Has zero knowledge of *how* a tool actually executes.
- **Executor Service** — actually runs `bash`, reads/writes files, edits code. Has zero knowledge of the LLM or the conversation.

They coordinate entirely through **Redis Streams**, matching each request to its result via a `tool_call_id` correlation ID. This mirrors the real architecture used by Devin and Warp, where the reasoning process and the sandboxed execution environment run on physically separate machines for security and scale.

---

## What this demonstrates

### Distributed messaging, not just an API wrapper
Tool calls are published as messages on a Redis Stream and consumed by an independent executor process — not called as direct functions. This is the same publish/consume pattern used by Kafka, RabbitMQ, and SQS in production systems.

### At-least-once delivery, proven under real failure
Redis Streams' consumer groups guarantee a message is never silently lost — it's either acknowledged (`XACK`) or it stays pending for reclaim. I proved this directly rather than trusting the docs: killed the executor mid-task with `Ctrl+C`, confirmed the in-flight message was still sitting in `XPENDING`, then reclaimed and reprocessed it on restart.

### Idempotency, with the failure window tested precisely
At-least-once delivery means a message can be redelivered — which is dangerous if redelivery means re-running a `bash` command or rewriting a file. I added a processed-set guard (`SADD`/`SISMEMBER`) and tested the exact failure window that matters: crashing the executor **after** the work completed but **before** the acknowledgment. On restart, the guard correctly detected the duplicate and skipped re-execution instead of running it twice.

### Secure credential delegation, not a static API key
Repository access uses a GitHub App, not a personal access token. The chain: a long-lived private key signs a short-lived (10-minute) JWT, which is exchanged for a scoped, auto-expiring (1-hour) installation token. If a sandbox is ever compromised, the blast radius is time-limited and scoped only to the repos explicitly granted — not standing, unlimited access.

### Container isolation with correct secret handling
The agent runs inside Docker, fully isolated from the host filesystem. Secrets (API keys, installation tokens) are injected at container **runtime** via environment variables — never baked into the image, so a shared or leaked image never leaks a credential with it.

### Correct behavior under concurrency
Ran two agent instances simultaneously against the shared Redis streams and confirmed neither ever received the other's tool result — proving the `tool_call_id` correlation genuinely isolates concurrent sessions, not just in the single-user happy path.

---

## Tech stack

| Layer | Technology | Why |
|---|---|---|
| Agent reasoning loop | Python + Anthropic SDK | Minimal boilerplate for tool-calling/function-calling |
| Message queue | Redis Streams | Consumer groups give at-least-once delivery + explicit ack, unlike plain pub/sub |
| Sandbox isolation | Docker | Process/filesystem isolation between agent and host |
| Orchestration API | Spring Boot | REST entrypoint that kicks off a task, decoupled from the agent's execution |
| Repo access | GitHub App (JWT + installation tokens) | Scoped, short-lived, revocable — not a static personal token |
| Version control ops | Git CLI via subprocess | Direct control over clone/branch/commit/push |

---

## Real bugs hit and fixed along the way

Debugging this system surfaced several genuinely instructive failures — the kind that matter more than the happy path:

- **Doubled-credential URL bug** — reused a git remote URL that already had a token embedded, then re-injected a second token on top of it, producing a malformed URL git couldn't parse. Fixed by always constructing the authenticated URL fresh instead of mutating a stored one.
- **Silent stream-replay bug** — a cursor variable was declared with `global` but assigned to a differently-named local variable, so it silently never advanced. Every read replayed the very first message in the stream forever, masquerading as duplicate task execution.
- **Idempotency ordering bug (design decision, not a mistake)** — deliberately mark a message as processed *before* acknowledging it, not after. If a crash happens in between, the message is safely skipped on redelivery instead of either being lost or silently re-run.
- **Cross-boundary field name mismatches** — a Java service publishing `session_id` while the Python consumer read `sessionId` — a reminder that service boundaries need as much care around naming contracts as the logic itself.

---

## Project phases

- [x] **Phase 0** — Local CLI agent: full tool-calling loop (`read_file`, `write_file`, `bash`, `edit_file`), error handling as data (not crashes), multi-step chained reasoning
- [x] **Phase 1** — GitHub App auth: JWT signing, installation token exchange, real repo cloning
- [x] **Phase 2** — Dockerized the agent, runtime secret injection, full loop proven inside a container: clone → edit → commit → push → real PR
- [x] **Phase 3** — Decoupled agent and executor via Redis Streams; proved durability, idempotency, and concurrent-session isolation
- [x] **Spring Boot orchestration** — REST endpoint (`POST /tasks`) replacing terminal input, publishing tasks onto the queue
- [ ] **Phase 4** — Session persistence (Postgres), WebSocket streaming of live agent activity to a frontend
- [ ] **Phase 5** — Stateful shell sessions, LSP integration
- [ ] **Phase 6** — Browser automation (Playwright)
- [ ] **Phase 7** — Deployment tool (Fly.io)
- [ ] **Phase 8** — Reliability hardening at scale

---

## Running it locally

```bash
# 1. Start Redis
docker run -d --name redis-agent -p 6379:6379 redis

# 2. Start the executor (runs tools)
python executor_service.py

# 3. Start the agent (runs the LLM loop)
python agent_service.py

# 4. Start the Spring Boot orchestration service
./mvnw spring-boot:run

# 5. Trigger a task
curl -X POST http://localhost:8080/tasks \
  -H "Content-Type: application/json" \
  -d '{"task": "read notes.txt and summarize it into summary.txt"}'
```
