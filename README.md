# Athenaeum

*From the Greek — a temple of Athena, and later any institution devoted to learning. A place where knowledge is gathered, catalogued, and kept.*

A self-hosted book manager that bridges [AudiobookShelf](https://www.audiobookshelf.org/) and [Hardcover](https://hardcover.app/). Search for books, request audiobook and ebook formats, and have them automatically downloaded, organised, and added to your library.

[![Tests](https://github.com/Bothari/Athenaeum/actions/workflows/test.yml/badge.svg)](https://github.com/Bothari/Athenaeum/actions/workflows/test.yml)
[![Docker](https://github.com/Bothari/Athenaeum/actions/workflows/docker.yml/badge.svg)](https://github.com/Bothari/Athenaeum/actions/workflows/docker.yml)
[![License](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](LICENSE)

---

Request a book → Prowlarr searches indexers → download client fetches it → files organised into your library.

---

## Features

- **Library sync** — mirrors your AudiobookShelf library and enriches every book with Hardcover metadata
- **Search and request** — search by title, author, or series; request audiobook or ebook formats in one tap
- **Series tracking** — see what you own, what is requested, and what is missing for each series
- **Downloads** — searches Prowlarr and sends releases to qBittorrent, SABnzbd, or Deluge
- **Series pack downloads** — grab a whole series torrent and map files to individual books before organising
- **Auto-organise** — moves completed downloads into `Author/Title` directories with OPF metadata sidecars, ready for ABS ingestion
- **Authentication** — local login or OIDC (Authentik, Authelia, Keycloak, etc.); admin and user roles
- **Notifications** — Apprise-compatible URLs (Pushover, ntfy, Slack, Gotify, and more)
- **Mobile-first UI** — light/dark mode, simple nav, intuitive views; works well on desktop too

---

## Requirements

| Service | Purpose | Required |
|---|---|---|
| [AudiobookShelf](https://www.audiobookshelf.org/) | Media server and library source | Yes |
| [Hardcover](https://hardcover.app/) | Book metadata, series data, covers | Yes (free API key) |
| [Prowlarr](https://github.com/Prowlarr/Prowlarr) | Indexer aggregation | For downloads |
| qBittorrent / SABnzbd / Deluge | Download client | For downloads |

---

## Docker Compose Quick Start

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

```bash
docker compose up -d
```

Open `http://localhost:8741`. On first boot you will be prompted to create an admin account, then connect your services in **Settings**.

See [volume mapping](docs/volume-mapping.md) if downloads are not being detected.

---

## Documentation

- [Configuration reference](docs/configuration.md)
- [Authentication and SSO](docs/authentication.md)
- [Volume mapping](docs/volume-mapping.md)
- [Development](docs/development.md)

---

## Upgrading

```bash
docker compose pull
docker compose up -d
```

Migrations run automatically on startup.

---

## Data and Backups

Everything lives in your `/data` mount:

- `athenaeum.db` — SQLite database (WAL mode, safe to copy while running)
- `settings.yaml` — all configuration including API keys

---

## License

[GNU Affero General Public License v3.0](LICENSE)

---

## Built with AI assistance

Athenaeum is a human-engineered application built by a software engineer with over 20 years of professional experience. [Claude Code](https://claude.ai/code) (Claude Sonnet 4.6) served as the primary development tool — a force multiplier for implementation speed, not a replacement for engineering judgement.

**The process:**

- A detailed spec and architecture document was written before any code, then put through an adversarial review process: multiple AI personas (architect, implementer, skeptic, end-user, security reviewer) independently critiqued it, and their findings were compiled and addressed in a second revision before build began
- Every feature was manually tested against real services — AudiobookShelf, Hardcover, Prowlarr, qBittorrent, SABnzbd, Deluge — on a live home server setup
- All AI-generated code was reviewed before it landed; nothing was blindly accepted

The full spec, review transcripts, and amendment history are in `docs/dev/` if you want to see how the sausage was made.

**A note on security:** I am not a professional security auditor. Athenaeum has authentication, session management, role-based access control, and was reviewed for common web vulnerabilities — but I make no formal security guarantees. Exposing it to the internet is at your own risk. That said, I run it behind a reverse proxy with SSO myself and am reasonably confident it is fine for personal use.
