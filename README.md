# Athenaeum

*From the Greek — a temple of Athena, and later any institution devoted to learning. A place where knowledge is gathered, catalogued, and kept.*

A self-hosted book manager that bridges [AudiobookShelf](https://www.audiobookshelf.org/) and [Hardcover](https://hardcover.app/). Search for books, request audiobook and ebook formats, and have them automatically downloaded, organised, and added to your library.

[![Tests](https://github.com/Bothari/Athenaeum/actions/workflows/test.yml/badge.svg)](https://github.com/Bothari/Athenaeum/actions/workflows/test.yml)
[![Docker](https://github.com/Bothari/Athenaeum/actions/workflows/docker.yml/badge.svg)](https://github.com/Bothari/Athenaeum/actions/workflows/docker.yml)

---

## Features

- **Library sync** — mirrors your AudiobookShelf library and links every book to Hardcover metadata (cover, release date, series position, slug)
- **Search and request** — search Hardcover by title, author, or series; request audiobook or ebook formats in one tap
- **Series tracking** — shows what you own, what is requested, and what is missing for each series, compared against Hardcover series data
- **Automated downloads** — searches Prowlarr indexers on a schedule and sends matched releases to your download client; filters by allowed file formats
- **Download clients** — qBittorrent, SABnzbd, and Deluge supported; multiple clients of the same type can coexist
- **Series pack downloads** — grab a whole series torrent and map files to individual books with a review UI before organising
- **Auto-organise** — moves completed downloads into `Author/Title` directories, writes OPF sidecar metadata, and triggers an ABS library scan
- **Authentication** — local username/password or OIDC (Authentik, Authelia, Keycloak, etc.); role-based access (admin / user)
- **User requests** — non-admin users submit requests that admins approve or reject
- **Notifications** — Apprise-compatible notification URLs (Pushover, ntfy, Slack, Gotify, and many more)
- **Mobile-first UI** — bottom nav bar, poster view, safe-area padding; works well on desktop too

---

## Requirements

| Service | Purpose | Required |
|---|---|---|
| [AudiobookShelf](https://www.audiobookshelf.org/) | Media server and library source | Yes |
| [Hardcover](https://hardcover.app/) | Book metadata, series data, covers | Yes (free API key) |
| [Prowlarr](https://github.com/Prowlarr/Prowlarr) | Indexer aggregation | For downloads |
| qBittorrent / SABnzbd / Deluge | Download client | For downloads |

---

## Quick Start

**1. Create a directory and add a `docker-compose.yml`:**

```yaml
services:
  athenaeum:
    image: ghcr.io/bothari/athenaeum:latest
    container_name: athenaeum
    ports:
      - "8741:8741"
    volumes:
      - ./data:/data
      - /path/to/your/library:/output
      - /path/to/downloads:/downloads
    restart: unless-stopped
```

See [Volume Setup](#volume-setup) below for details on what each path does.

**2. Start it:**

```bash
docker compose up -d
```

**3. Open `http://localhost:8741`**

On first boot you will be prompted to create an admin account. After that, go to **Settings** and connect your services.

---

## Volume Setup

| Container path | Purpose |
|---|---|
| `/data` | Database (`athenaeum.db`) and settings (`settings.yaml`). Back this up. |
| `/output` | Where Athenaeum places organised books. Point this at the root of your AudiobookShelf library. |
| `/downloads` | Where Athenaeum reads completed downloads from. Must match the path your download client sees. |

### Making download paths consistent

Athenaeum needs to read files that your download client already wrote. The path it uses is whatever the download client reports — so the `/downloads` mount in Athenaeum must be the same filesystem location that the download client writes to.

If your download client runs in its own container, mount the same host directory into both:

```yaml
services:
  athenaeum:
    image: ghcr.io/bothari/athenaeum:latest
    volumes:
      - ./data:/data
      - /mnt/media/books:/output
      - /mnt/downloads:/downloads   # <-- same host path

  qbittorrent:
    image: lscr.io/linuxserver/qbittorrent:latest
    volumes:
      - /mnt/downloads:/downloads   # <-- same host path
```

Then in qBittorrent, set the default save path to `/downloads/complete` (or whatever subdirectory you prefer) and Athenaeum will be able to find the files at the same path.

---

## Configuration

All settings live in **Settings** in the UI. The underlying file is `/data/settings.yaml` (never edit it while the container is running).

### AudiobookShelf

| Field | Description |
|---|---|
| URL | Browser-accessible URL of your ABS instance (used for deep links) |
| Internal URL | URL Athenaeum uses for API calls — set this if ABS is on the same Docker network, e.g. `http://audiobookshelf:13378` |
| API Key | An ABS API key with library access |
| Library | Select which ABS library to sync (after a successful connection test) |

### Hardcover

| Field | Description |
|---|---|
| API Key | Your Hardcover API key from [hardcover.app/account/api](https://hardcover.app/account/api) |
| Preferred language | Filters edition preferences — set to your reading language |

### Prowlarr

| Field | Description |
|---|---|
| URL | Prowlarr URL, e.g. `http://prowlarr:9696` |
| API Key | Prowlarr Settings → General → API Key |
| Tag | Optional — restricts searches to indexers with this tag |

### Download Clients

Add one or more clients from the **Downloaders** tab. Each client has:

| Field | All types |
|---|---|
| Name | Display name (shown in the Queue) |
| Enabled | Toggle without removing the client |
| URL | Base URL of the client |

**qBittorrent** additionally needs Username and Password (leave blank if no auth is configured), and an optional Download directory override.

**SABnzbd** additionally needs an API Key (SABnzbd Config → General), a Category (must match a category configured in SABnzbd), and an optional "Remove completed from history" toggle (removes the history entry after Athenaeum reads the path; files are kept).

**Deluge** additionally needs a Password (the Deluge Web UI password) and an optional Download directory override.

### General

| Field | Description |
|---|---|
| Output directory | Where organised books land inside the container — default `/output` |
| Separate type directories | Put audiobooks and ebooks in separate top-level directories |
| Audiobook prefix | Subdirectory name for audiobooks, e.g. `Audiobooks` |
| Ebook prefix | Subdirectory name for ebooks, e.g. `Ebooks` |
| Merge multi-file audiobooks | Combine split-chapter MP3 downloads into a single M4B |
| Group series in search | Collapse multiple series entries in search results |
| Allowed audiobook formats | Comma-separated list — Prowlarr results not matching are filtered out. Default: `m4b, mp3, flac` |
| Allowed ebook formats | Same for ebooks. Default: `epub, pdf, mobi, azw3` |

### Scheduled Tasks

Tasks run on [cron expressions](https://crontab.guru). Leave a field blank to disable that task.

| Task | Default | Description |
|---|---|---|
| Library sync | `0 2 * * *` (2 AM daily) | Pulls all items from ABS and upserts the local database |
| Cache refresh | `0 3 * * *` (3 AM daily) | Links local books/authors/series to Hardcover metadata |
| Auto search | `0 */6 * * *` (every 6 hours) | Searches Prowlarr for all requested items and snatches the best result |

Tasks can also be triggered manually from the **Dashboard**.

---

## Authentication

### Local login

Enable **Form login** in Settings → Auth, then create users from the **Profile** page. The first account created is admin.

### OIDC (Single Sign-On)

Athenaeum supports any OIDC provider. In Settings → Auth:

| Field | Description |
|---|---|
| Provider URL | The OIDC issuer URL — Athenaeum will auto-discover endpoints from `{provider_url}/.well-known/openid-configuration` |
| Client ID | OAuth2 client ID from your provider |
| Client Secret | OAuth2 client secret |
| Scopes | Space-separated — `openid email profile` works for most providers |

The redirect URI to register with your provider is: `{your Athenaeum URL}/auth/oidc/callback`

**Authentik example:**
1. Create an OAuth2/OIDC provider in Authentik
2. Set the redirect URI to `https://athenaeum.example.com/auth/oidc/callback`
3. Copy the issuer URL (e.g. `https://sso.example.com/application/o/athenaeum/`) into Provider URL
4. Copy Client ID and Client Secret

Users who sign in via OIDC for the first time are created with the **user** role. Promote them to admin from **Settings → Users**.

### Roles

| Role | Capabilities |
|---|---|
| Admin | Full access — settings, sync, approve/reject requests, manage users |
| User | Search, browse library, submit requests (require admin approval) |

---

## Upgrading

```bash
docker compose pull
docker compose up -d
```

Athenaeum runs database migrations automatically on startup. No manual steps required.

---

## Building from Source

```bash
git clone https://github.com/Bothari/Athenaeum.git
cd Athenaeum
docker compose up -d --build
```

### Running tests

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/python -m pytest tests/ -v
```

---

## Data and Backups

Everything lives in your `/data` mount:

- `athenaeum.db` — SQLite database (library, requests, downloads, users)
- `settings.yaml` — all configuration including API keys

Back up this directory. The database can be copied safely while the container is running — it uses WAL mode.

---

## Built with

Developed with [Claude Code](https://claude.ai/code) (Claude Sonnet 4.6). Spec, architecture, and adversarial review process documented in `docs/`.
