# Configuration

All settings are managed in the UI under **Settings**. The underlying file is `/data/settings.yaml` — never edit it while the container is running.

---

## AudiobookShelf

| Field | Description |
|---|---|
| URL | Browser-accessible URL of your ABS instance (used for deep links) |
| Internal URL | URL Athenaeum uses for API calls — use this if ABS is on the same Docker network, e.g. `http://audiobookshelf:13378` |
| API Key | An ABS API key with library access |
| Library | Which ABS library to sync (populated after a successful connection test) |

---

## Hardcover

| Field | Description |
|---|---|
| API Key | Your Hardcover API key from [hardcover.app/account/api](https://hardcover.app/account/api) |
| Preferred language | Filters edition preferences — set to your reading language |

---

## Prowlarr

| Field | Description |
|---|---|
| URL | Prowlarr URL, e.g. `http://prowlarr:9696` |
| API Key | Prowlarr → Settings → General → API Key |
| Tag | Optional — restricts searches to indexers with this tag |

---

## Download Clients

Add clients from the **Downloaders** tab. One client per type (qBittorrent, SABnzbd, Deluge).

**qBittorrent**

| Field | Description |
|---|---|
| URL | Base URL, e.g. `http://qbittorrent:8080` |
| Username / Password | Leave blank if auth is disabled |
| Download directory | Override the default save path (optional) |

**SABnzbd**

| Field | Description |
|---|---|
| URL | Base URL, e.g. `http://sabnzbd:8080` |
| API Key | SABnzbd → Config → General → API Key |
| Category | Must match a category configured in SABnzbd |
| Remove completed from history | Removes the history entry after Athenaeum reads the path; files are kept |

**Deluge**

| Field | Description |
|---|---|
| URL | Base URL, e.g. `http://deluge:8112` |
| Password | Deluge Web UI password |
| Download directory | Override the default save path (optional) |

---

## General

| Field | Description |
|---|---|
| Output directory | Where organised books land inside the container — default `/output` |
| Public URL | External URL of Athenaeum — required for OIDC redirect URIs and notification links |
| Separate type directories | Put audiobooks and ebooks in separate top-level directories |
| Audiobook prefix | Subdirectory name for audiobooks, e.g. `Audiobooks` |
| Ebook prefix | Subdirectory name for ebooks, e.g. `Ebooks` |
| Merge multi-file audiobooks | Combine split-chapter MP3 downloads into a single M4B |
| Allowed audiobook formats | Comma-separated — Prowlarr results not matching are filtered out. Default: `m4b, mp3, flac` |
| Allowed ebook formats | Same for ebooks. Default: `epub, pdf, mobi, azw3` |

---

## Notifications

Athenaeum sends notifications via [Apprise](https://github.com/caronc/apprise)-compatible URLs. Enter one URL per line in the **Notifications** tab.

Examples:

| Service | URL format |
|---|---|
| Pushover | `pover://user@token` |
| ntfy | `ntfy://topic` or `ntfys://ntfy.example.com/topic` |
| Gotify | `gotify://hostname/token` |
| Slack | `slack://tokenA/tokenB/tokenC/channel` |
| Discord | `discord://webhook_id/webhook_token` |

Use **Send test notification** to verify delivery.

---

## Auto-Search

Athenaeum can automatically search Prowlarr and send the best result to your download client whenever a request is pending. Configure it in **Settings → Downloaders → Auto-Search**.

| Field | Description |
|---|---|
| Search immediately on request | Trigger a search as soon as a request is created or approved. If disabled, only the scheduled task runs searches. |
| Min seeders | Torrent results with fewer seeders than this are rejected. Set to 0 to disable the check. |
| Max attempts | Stop searching after this many failed attempts per request (default 10). |

### Result ranking

Results are first filtered by hard constraints (format not in allowed list, below min seeders, series packs), then sorted by a configurable priority stack. Drag items in the **Ranking** list to reorder; toggle the checkbox to enable or disable each criterion.

| Criterion | Notes |
|---|---|
| Format | Prefers results matching your allowed formats list — the order of the list is the order of preference |
| Seeders | Prefers more seeders (torrent only; NZB results are unaffected) |
| Size | Prefer larger or smaller files |
| Age | Prefer newer or older indexed releases |
| Indexer priority | Prefer results from higher-priority indexers as configured in Prowlarr |

### Confidence scoring

Auto-search uses fuzzy matching to score each result against the book title and author. Results scoring below 60% are rejected even if they pass all hard filters. The manual search view in a request's detail page shows each result's score as a colour-coded badge (green = would auto-download, amber/red = would not).

Titles with subtitles (e.g. "Exodus: The Helium Sea") apply stricter matching: the subtitle must appear in the result title, preventing wrong-book grabs within the same series by the same author.

---

## Scheduled Tasks

Tasks run on [cron expressions](https://crontab.guru). Leave a field blank to disable.

| Task | Default | Description |
|---|---|---|
| Library sync | `0 2 * * *` | Pulls all items from ABS and upserts the local database |
| Cache refresh | `0 3 * * *` | Links local books/authors/series to Hardcover metadata |
| Auto-search | `0 */6 * * *` | Searches Prowlarr for all pending requests |

Tasks can also be triggered manually from the **Dashboard**.
