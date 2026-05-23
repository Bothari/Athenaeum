# Hardcover Linking

Athenaeum links every book, author, and series in your library to a corresponding Hardcover entry. These links are what power cover art, release dates, series positions, and series completion tracking.

---

## Automatic linking

Links are created during the **Cache refresh** task (runs nightly by default, or trigger it manually from the Dashboard). Athenaeum searches Hardcover by title and author name and picks the best match. For most libraries this works well, but it can fail or pick the wrong edition for books with unusual titles, multiple editions, or transliterated names.

Any item that failed to auto-link — or was linked to the wrong entry — can be fixed manually.

---

## Fixing a bad or missing link

Open the book, author, or series detail page. At the bottom you will find a **Hardcover** card.

**If the item is unlinked:**

1. Click **Find Hardcover match** — Athenaeum will search Hardcover and show the top candidates
2. Click **Link** next to the correct result

If none of the candidates are right, paste a Hardcover URL or numeric ID directly into the input field and click **Set**. You can find the ID in the URL on hardcover.app (e.g. `https://hardcover.app/books/the-name-of-the-wind` — paste the full URL or just the slug).

**If the item is linked to the wrong entry:**

Click **Unlink** to remove the current link, then follow the steps above to set the correct one.

**For books**, there is also a **Refresh HC data** button once linked — use this to pull updated metadata (cover, release date, series position) from Hardcover without waiting for the next scheduled cache refresh.

---

## Manual requests

If you want to request a book that is not yet in your library or searchable via Hardcover, you can submit a manual request from the **Queue** page.

Click **+ Manual Request** (top right of the Queue), then fill in:

- **Title** — the book title
- **Author** — the author name
- **Format** — Audiobook or Ebook

The request is created and queued for admin approval (or processed immediately if you are an admin). Athenaeum will search Prowlarr for a matching release and download it when approved.

Manual requests bypass the Hardcover search, so they are useful for books that are not in the Hardcover catalogue or that you know by a title Hardcover would not recognise.
