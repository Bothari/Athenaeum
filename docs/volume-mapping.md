# Volume Mapping

Athenaeum needs three mounts:

| Container path | Purpose |
|---|---|
| `/data` | Database and settings. Back this up. |
| `/output` | Where organised books are placed. Point this at the root of your AudiobookShelf library. |
| `/downloads` | Where Athenaeum reads completed downloads from. Must match the path your download client sees. |

---

## Making download paths consistent

Athenaeum reads files at whatever path the download client reports. The `/downloads` mount must be the same filesystem location the download client writes to.

If your download client runs in its own container, mount the same host directory into both:

```yaml
services:
  athenaeum:
    image: ghcr.io/bothari/athenaeum:latest
    volumes:
      - ./data:/data
      - /mnt/media/books:/output
      - /mnt/downloads:/downloads   # same host path

  qbittorrent:
    image: lscr.io/linuxserver/qbittorrent:latest
    volumes:
      - /mnt/downloads:/downloads   # same host path
```

Then in qBittorrent, set the default save path to `/downloads/complete` (or any subdirectory you prefer) — Athenaeum will find the files at that same path.

---

## Output directory structure

By default, books are placed at:

```
/output/Author Name/Book Title/Book Title - Author Name.m4b
```

With **Separate type directories** enabled and prefixes set:

```
/output/Audiobooks/Author Name/Book Title/...
/output/Ebooks/Author Name/Book Title/...
```

A `metadata.opf` sidecar is written alongside each file with Hardcover metadata.
