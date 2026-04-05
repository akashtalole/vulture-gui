# Vulture-GUI Architecture

## Project Overview

**Vulture-GUI** is an enterprise-grade Django web application that provides:
- An **administrative GUI** for managing security infrastructure (HAProxy, logging, VPN, PKI, authentication systems)
- A **user portal** for end-user self-service authentication and profile management

| Attribute | Value |
|-----------|-------|
| Version | 2.35.1 (March 2026) |
| License | GPLv3 |
| Python | 3.11+ |
| Django | 4.2.x |
| Primary DB | MongoDB 4.x |

---

## High-Level Architecture

```
                          ┌─────────────────────────────────────────┐
                          │               Clients                   │
                          │  (Admins / End Users / CI Systems)      │
                          └───────────────┬─────────────────────────┘
                                          │ HTTPS
                          ┌───────────────▼─────────────────────────┐
                          │              Nginx                       │
                          │         (Reverse Proxy / TLS)           │
                          └───────┬─────────────────┬───────────────┘
                                  │                 │
                   ┌──────────────▼──┐     ┌────────▼──────────────┐
                   │  Gunicorn       │     │  Gunicorn             │
                   │  (Admin GUI)    │     │  (User Portal)        │
                   │  vulture_os/    │     │  portal/wsgi.py       │
                   │  vulture_os/    │     └────────┬──────────────┘
                   │  wsgi.py        │              │
                   └──────┬──────────┘              │
                          │                         │
                   ┌──────▼─────────────────────────▼──────────────┐
                   │              Django Application Layer          │
                   │  gui | applications | authentication | services│
                   │  system | darwin | workflow | toolkit | portal │
                   └──────┬──────────────────────┬─────────────────┘
                          │                      │
            ┌─────────────▼──────┐    ┌──────────▼─────────┐
            │  MongoDB 4.x        │    │   Redis 4.5+        │
            │  Port 9091 (SSL)    │    │   127.0.0.5:6379   │
            │  ReplicaSet:Vulture │    │  (Cache / Sessions) │
            └────────────────────┘    └────────────────────┘
                          │
            ┌─────────────▼──────────────────────────────────────┐
            │           Managed System Services                   │
            │   HAProxy | rsyslog | OpenVPN | StrongSwan | PKI   │
            └────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Core

| Component | Technology |
|-----------|-----------|
| Web Framework | Django 4.2.x |
| Template Engine | Jinja2 + Django Templates |
| ORM / DB Adapter | Djongo (MongoDB ↔ Django ORM) |
| Primary Database | MongoDB 4.x (Replica Set) |
| Cache / Queue | Redis 4.5+ |
| App Server | Gunicorn (two instances) |
| Reverse Proxy | Nginx |
| Load Balancer | HAProxy (managed service) |

### Authentication & Security

| Feature | Library |
|---------|---------|
| LDAP / Active Directory | `python-ldap` 3.3+ |
| Kerberos | system-level integration |
| OAuth2 / OpenID Connect | `msal`, `google-auth`, custom implementation |
| JWT | `pyjwt` 2.3+ |
| TOTP / OTP | `pyotp`, `authy`, `qrcode` |
| TLS / Certificates | `pyOpenSSL`, `cryptography` |
| AWS integration | `boto3` |

### Utilities

| Purpose | Library |
|---------|---------|
| Async HTTP | `aiohttp` 3.13.3 |
| HTTP requests | `requests` |
| HTML parsing | `beautifulsoup4`, `robobrowser` |
| GeoIP | `maxminddb` |
| URL parsing | `pyfaup` |
| XML | `defusedxml`, `xmltodict` |
| File type detection | `python-magic` |
| WebSocket | `websocket-client` 1.3.2+ |
| Validation | `validators` |
| Scheduled tasks | `django-crontab` |
| Environment config | `django-environ` |

---

## Directory Structure

```
vulture-gui/
├── vulture_os/                  # Main Django project root
│   ├── manage.py                # Django management entry point
│   ├── vulture_os/              # Project settings package
│   │   ├── settings.py          # Main Django settings (450+ lines)
│   │   ├── urls.py              # Top-level URL dispatcher
│   │   └── wsgi.py              # WSGI entry point (Admin GUI)
│   ├── gui/                     # Administrative dashboard & API
│   ├── applications/            # Application backends, log forwarding, parsers
│   ├── authentication/          # Auth repositories, portals, MFA
│   ├── services/                # Service configuration (HAProxy, rsyslog, VPN)
│   ├── system/                  # Cluster, nodes, PKI, network, users, tenants
│   ├── darwin/                  # Access control policies and rules
│   ├── workflow/                # Request routing, ACLs, policy execution
│   ├── toolkit/                 # Shared utilities (API, auth, MongoDB, Redis)
│   ├── portal/                  # End-user self-service portal
│   │   ├── settings.py          # Portal-specific settings
│   │   ├── urls.py              # Portal URL patterns
│   │   └── wsgi.py              # WSGI entry point (User Portal)
│   ├── daemons/                 # Background daemon processes
│   └── templates/               # Shared HTML templates
├── home/                        # Jail configurations (Apache, Portal)
├── docs/                        # Documentation (git submodule → vulture-doc)
├── requirements.txt             # Pinned Python dependencies (407 packages)
├── requirements.in              # Unpinned source requirements
├── CHANGELOG                    # Version history
├── README.md                    # Project overview
└── .gitmodules                  # Git submodule configuration
```

---

## Core Modules

### `gui/` — Administrative Dashboard

The central administrative interface. Provides:
- Login/logout and session management
- Main dashboard with service status overview
- RSS feed for notifications
- Process queue state management
- **CI Integration API:** `GET /api/ci/get/<objclass>/<object_id>` — programmatic access to all views
- **Services Monitoring API:** `GET /api/v1/services/monitor/` — real-time service health (requires `cluster_api_key`)

Key files:
- `gui/views/main.py` — dashboard views
- `gui/views/api.py` — CI and monitoring API handlers
- `gui/models/monitor.py` — service monitoring models
- `gui/urls.py` — GUI URL patterns

### `applications/` — Application Management

Manages backend application definitions and log pipelines:
- **Backends** — upstream servers and health check configurations (`applications/backend/models.py`, 29KB)
- **Log Forwarding** — configures rsyslog forwarding rules
- **Parsers** — log format parsers for structured ingestion

### `authentication/` — Authentication Repositories

Provides adapters for all supported authentication sources:
- LDAP / Active Directory
- Kerberos
- OAuth2 / OpenID Connect (Microsoft, Google, custom)
- RADIUS
- Local user databases
- MFA: TOTP, OTP, Authy

### `services/` — Service Configuration

Generates and manages configuration for managed system services:
- **HAProxy** — load balancer and application delivery controller
- **rsyslog** — system log aggregation and forwarding
- **OpenVPN** — VPN gateway configuration
- **StrongSwan** — IPsec/IKEv2 VPN configuration

### `system/` — System Administration

Infrastructure-level configuration:
- **Cluster** — multi-node cluster management (`system/cluster/models.py`)
- **Nodes** — individual node registration and status
- **PKI** — certificate authority and certificate lifecycle
- **Network** — interface and routing configuration
- **Users** — internal admin user management
- **Tenants** — multi-tenant isolation

### `darwin/` — Access Control

Policy-based access control engine:
- Access control lists (ACLs)
- Rule definitions and priorities
- Policy enforcement points

### `workflow/` — Request Routing

Defines how incoming requests are processed:
- Workflow definitions linking frontends → backends
- ACL-based conditional routing
- Policy application per request
- Test files: `workflow/tests/test_models.py`

### `toolkit/` — Shared Utilities

Cross-cutting library code used by all modules:
- `toolkit/api_parser/` — API client parsing utilities
- `toolkit/auth/` — shared authentication helpers
- `toolkit/network/` — network utility functions
- `toolkit/mongodb/` — MongoDB connection helpers
- `toolkit/redis_utils/` — Redis client helpers

Test files: `toolkit/tests/test_network.py`, `toolkit/tests/test_api_requests.py`

### `portal/` — User Self-Service Portal

A **separate WSGI application** (served by its own Gunicorn instance) for end users:
- OAuth2 / OpenID Connect provider endpoints
- User self-service profile management (`/self`, `/self/<action>`)
- Workflow-aware authentication flows
- Session management independent of the admin GUI

### `daemons/` — Background Processes

Long-running daemon processes for async operations outside the request/response cycle.

---

## Data Layer

### MongoDB (Primary Database)

| Setting | Value |
|---------|-------|
| Adapter | Djongo (ORM bridge) |
| Host | `VULTURE_MONGODB_HOST` (default: system hostname) |
| Port | 9091 (non-standard) |
| Database | `vulture` |
| SSL | Enabled (certificate verification) |
| Replica Set | `Vulture` |

Models are defined per-app in `*/models.py` files (~50 models, ~13,000 lines total). Djongo maps Django model classes to MongoDB collections.

### Redis (Cache & Sessions)

| Setting | Value |
|---------|-------|
| Host | `127.0.0.5` (isolated loopback) |
| Port | 6379 |
| Usage | Django sessions, caching, message queues |

---

## Authentication & Security

### Authentication Methods

| Method | Module |
|--------|--------|
| LDAP / AD | `python-ldap` via `authentication/` |
| Kerberos | System-level integration |
| OAuth2 / OIDC | `msal`, `google-auth`, custom flows in `portal/` |
| RADIUS | `authentication/` adapter |
| Local DB | MongoDB-backed user store |
| TOTP / OTP | `pyotp`, `authy` |
| JWT | `pyjwt` — token issuance and validation |

### Security Controls

- **CSRF:** `CsrfViewMiddleware` with secure cookies
- **Session Security:** `vltsessid` cookie, 180-minute idle timeout, 3600-second max age, HTTPS-only
- **MongoDB:** TLS with certificate verification
- **Password Policy:** similarity check, minimum length, common password list, numeric-only prevention
- **XSS:** Escaped templates + recent JS sanitization fixes (2.35.1)
- **Clickjacking:** `XFrameOptionsMiddleware`
- **Trusted Origin:** `https://vulture-nginx:8000`

---

## API Endpoints

### Admin GUI API

| Method | Path | Description |
|--------|------|-------------|
| `GET/POST` | `/login/` | Authentication |
| `POST` | `/logout/` | Session termination |
| `GET` | `/` | Main dashboard |
| `GET` | `/rss/` | RSS notifications |
| `POST` | `/process_queue/` | Queue state management |
| `GET` | `/api/ci/get/<objclass>/<object_id>` | CI integration — programmatic model access |
| `GET` | `/api/v1/services/monitor/` | Service health monitoring |

**Section routes:** `/system/`, `/applications/`, `/authentication/`, `/services/`, `/darwin/`, `/workflow/`

### User Portal API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `portal/<workflow_id>/oauth2/start/<repo_id>` | OAuth2 flow initiation |
| `GET` | `portal/<workflow_id>/oauth2/callback/<repo_id>` | OAuth2 callback handler |
| `POST` | `portal/portal_<portal_id>/oauth2/authorize` | Authorization endpoint |
| `POST` | `portal/portal_<portal_id>/oauth2/token` | Token endpoint |
| `GET` | `portal/portal_<portal_id>/oauth2/userinfo` | User info endpoint |
| `GET` | `portal/portal_<portal_id>/.well-known/openid-configuration` | OIDC discovery |
| `GET` | `portal/<workflow_id>/vulture_disconnect` | Logout / disconnect |
| `GET/POST` | `portal/portal_<portal_id>/self` | Self-service portal |
| `GET/POST` | `portal/portal_<portal_id>/self/<action>` | Self-service actions |

---

## Request Lifecycle

### Middleware Stack (Admin GUI)

Requests pass through this stack in order:

1. `SecurityMiddleware` — HTTPS enforcement, security headers
2. `SessionMiddleware` — session loading from Redis
3. `CommonMiddleware` — URL normalization, content-type handling
4. `CsrfViewMiddleware` — CSRF token validation
5. `AuthenticationMiddleware` — attaches `request.user`
6. `MessageMiddleware` — flash message framework
7. `XFrameOptionsMiddleware` — `X-Frame-Options` header
8. `JSONParsingMiddleware` *(custom)* — parses JSON request bodies
9. `PutParsingMiddleware` *(custom)* — handles PUT request bodies
10. `OsMiddleware` *(custom)* — OS-level context injection

### Request Flow

```
Client → Nginx (TLS termination)
       → Gunicorn (WSGI)
       → Django Middleware Stack
       → URL Router (urls.py)
       → View (views/*.py)
       → Model (models.py ↔ MongoDB via Djongo)
       → Template / JSON Response
       → Client
```

---

## Deployment Architecture

### Process Layout

```
systemd / RC scripts
├── nginx               ← Reverse proxy (TLS, static files)
├── gunicorn (admin)    ← vulture_os/vulture_os/wsgi.py
│                          Listens on 127.0.0.1:<admin_port>
└── gunicorn (portal)   ← vulture_os/portal/wsgi.py
                           Listens on 127.0.0.1:<portal_port>
```

### File System Paths

| Path | Purpose |
|------|---------|
| `/vulture_os/` | Django project root |
| `/vulture_os/static/` | Static assets |
| `/usr/local/etc/` | System service configuration |
| `/var/log/vulture/` | All application logs |
| `/home/jails.apache/` | Nginx jail configuration |
| `/home/jails.portal/` | Portal jail configuration |

---

## Configuration

### Settings Files

| File | Scope |
|------|-------|
| `vulture_os/vulture_os/settings.py` | Admin GUI (primary) |
| `vulture_os/portal/settings.py` | User Portal |

### Environment Variables

All variables use the `VULTURE_` prefix and are loaded via `django-environ`:

| Variable | Default | Description |
|----------|---------|-------------|
| `VULTURE_DEBUG` | `False` | Django debug mode |
| `VULTURE_DEV_MODE` | `False` | Development mode |
| `VULTURE_MONGODB_HOST` | system hostname | MongoDB host |
| `VULTURE_MONGODB_PORT` | `9091` | MongoDB port |
| `VULTURE_MONGODB_SSL` | `True` | MongoDB SSL |
| `VULTURE_REDIS_HOST` | `127.0.0.5` | Redis host |
| `VULTURE_REDIS_PORT` | `6379` | Redis port |
| `VULTURE_LOG_LEVEL` | `INFO` | Logging level |
| `SYSTEM_ROOT_PATH` | — | System root path |
| `DBS_PATH` | — | Database files path |
| `TMP_PATH` | — | Temporary files path |
| `LOGS_PATH` | — | Log files path |

### Session Configuration

| Parameter | Value |
|-----------|-------|
| Cookie name | `vltsessid` |
| Idle timeout | 180 minutes |
| Max age | 3600 seconds |
| Secure | Yes (HTTPS only) |
| Trusted CSRF origin | `https://vulture-nginx:8000` |

---

## Scheduled Tasks

Managed by `django-crontab`, registered in `settings.py`:

| Schedule | Task | Description |
|----------|------|-------------|
| Every minute | API clients parser | Parse incoming API client data |
| Daily 22:07 | Update ACME certificates | Renew Let's Encrypt certificates |
| Daily 22:08 | Update CRL | Refresh Certificate Revocation Lists |
| Daily 23:00 | Security updates feed | Fetch security threat intelligence |
| Wed & Sat 19:25 | Update reputation context | Refresh IP/domain reputation data |
| Daily 01:00 | Check internal tasks | Process queued async tasks |
| 1st of month 10:15 | Generate timezone DBs | Rebuild timezone databases |

---

## Logging

All logs are written under `/var/log/vulture/os/`:

| Log File | Content |
|----------|---------|
| `debug.log` | Debug-level application output |
| `api.log` | API request/response logging |
| `gui.log` | Admin GUI events |
| `services.log` | Service configuration changes |
| `authentication.log` | Auth attempts, successes, failures |
| `crontab.log` | Scheduled task output |

Log level is controlled by `VULTURE_LOG_LEVEL` (default: `INFO`).

---

## Testing

### Framework

Django's built-in `TestCase` class.

### Test Locations

| Module | Test File | Coverage |
|--------|-----------|---------|
| `gui/tests/` | `test_generate_tzdbs.py` | Timezone DB generation |
| `system/tests/` | `test_network.py`, `test_timezone.py`, `test_models.py` | Network utils, timezone, models |
| `workflow/tests/` | `test_models.py` | Workflow model logic |
| `toolkit/tests/` | `test_api_requests.py` | API request utilities |

### Running Tests

```bash
cd /vulture_os
python manage.py test
```

### Management Commands

| Command | Description |
|---------|-------------|
| `update_tzdbs` | Regenerate timezone databases |
| `get_api_key` | Generate or retrieve the cluster API key |
| `update_reputation_ctxs` | Manually refresh reputation contexts |
| `toggle_maintenance` | Enable or disable maintenance mode |
| `is_node_bootstrapped` | Check if the node has completed bootstrap |

---

## Multi-Tenancy & Clustering

- **Tenants:** Logical isolation configured in `system/` module
- **Cluster:** Multi-node architecture managed via `system/cluster/models.py`
- **Nodes:** Individual cluster members registered and monitored centrally
- **MongoDB Replica Set:** Named `Vulture`, provides HA for all cluster state
- **API Key:** Cluster-wide `cluster_api_key` used for inter-node API authentication
