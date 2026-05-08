# Athenaeum

A self-hosted book management app. Search Hardcover for missing books that you would like, then request for them to be added to your AudiobookShelf library. Usenet and Torrent searches driven through Prowlarr, and downloads with SABnzbd or qBittorrent.

---

## What it does

- Monitors your AudiobookShelf library and links books to Hardcover metadata
- Search Hardcover to find books and request audiobook or ebook formats that you arae interested in
- Tracks series completion - shows what you own, what's requested, and what's missing
- Searches indexers through Prowlarr and sends matched releases to your download client
- Organises completed downloads into your library and triggers an ABS scan

<!-- screenshot: library books grid -->

<!-- screenshot: series detail with missing section -->

<!-- screenshot: search and request flow -->

---

## Requirements

- [AudiobookShelf](https://www.audiobookshelf.org/) — your media server
- [Hardcover](https://hardcover.app/) — book metadata (free API key required)
- [Prowlarr](https://github.com/Prowlarr/Prowlarr) — indexer management (optional, for downloads)
- SABnzbd or qBittorrent — download client (optional, for downloads)

---

## Setup

**1. Clone the repo**

```bash
git clone https://github.com/Bothari/Athenaeum.git
cd Athenaeum
```

**2. Create a `docker-compose.yml`**

```yaml
services:
  athenaeum:
    image: ghcr.io/bothari/athenaeum:latest
    ports:
      - "8741:8741"
    volumes:
      - ./data:/data
      - /path/to/your/books:/output
      - /path/to/your/downloads:/downloads
    environment:
      - DATA_DIR=/data
    restart: unless-stopped
```

Adjust the volume paths to match your setup. `/output` is where organised books land; `/downloads` is where your download client puts completed files.

**3. Start it**

```bash
docker compose up -d
```

Open `http://localhost:8741` and go to Settings to connect AudiobookShelf, Hardcover, and any download services.

---

## Building from source

```bash
docker compose up -d --build
```

---

## Data

All state lives in `./data/`:

- `athenaeum.db` — SQLite database
- `settings.yaml` — configuration (API keys, cron schedules, etc.)

Back this directory up to preserve your library data and settings.

---

## Development

Built with Claude Code (Claude Sonnet 4.6). See `docs/PLAN.md` for the full spec and `docs/PROGRESS.md` for build history.
