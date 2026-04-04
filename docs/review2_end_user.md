# End User Review — Athenaeum PLAN.md (Round 2)

## Persona
I want to manage my audiobook and ebook library. I run this on a home server. I'm not a developer. I find things in my media library I don't have yet, I request them, I wait for them to download, and they show up in AudiobookShelf. I come back to this app when something needs attention — it should tell me what that is.

---

## Findings

### HIGH

- **No first-run onboarding**: The app boots empty. Settings must be configured before anything works. But there is no guidance: no "Welcome — configure your services to get started" screen, no indication of which settings tabs are required (ABS and output_dir) versus optional (Pushover). A first-time user who skips to the Library page will see an empty table with no explanation of why. The app should tell the user what to do first.

- **No way to see download history**: The Downloads page shows only active downloads (snatched/downloading). Once a download completes, it vanishes from this page. If the user wants to see what downloaded last night — what was found, from which indexer, how long it took — there is nowhere to look. The `downloads` table has the data, but no page surfaces it. A "Recent Downloads" section or a completed-downloads list on the Requests page would address this.

- **Failed requests are hard to find**: A request that fails through the auto-organize pipeline shows up on the individual book detail page — but only if you know which book to look at. There is no "all failed requests" view. The Requests page can filter by status (the API supports `?status=failed`) but the UI filter spec isn't described. If a user wakes up to 3 failed organizes, they have to hunt through books to find them.

- **`Requests` page columns are never specified**: The plan describes `renderTable` and the Requests API endpoint but never lists what columns the Requests table has. Every other list page at least implies its columns from the data shapes. Without this, the user can't predict what information will be available at a glance (book title, author, type, status, created date?), and the implementer will guess.

### MEDIUM

- **No bulk operations on requests**: A user with 20 "requested" books who wants to monitor them all for background searching must click each one individually. Similarly, clearing all failed requests requires individual deletes. The plan has no bulk-action mechanism described anywhere. For a library app that may accumulate dozens of requests, this becomes tedious quickly.

- **Series "missing books" has no visible time warning for large series**: The series detail page loads missing books async and shows a loading indicator. For a 50-book series at 250ms per call, this takes at least 12.5 seconds. The user will see a spinner with no indication of why it's slow or how much is left. At minimum, the loading indicator should show `(N / Total)` progress. The truncation at 50 books is also silent — `truncated: true` in the API response is never described as surfacing to the user.

- **Sync status has no UI**: `GET /api/sync/status` returns sync task state, but where does the user see this? The Settings page is described in detail without mentioning sync status. The `POST /api/sync/library` manual trigger exists but there's no described feedback while it runs or when it completes. A user who manually triggers a sync has no way to know when it's done or if it succeeded.

- **No way to see "all missing books" across series**: The series detail page shows what's missing per series, but if a user tracks 10 series, they must visit each one to find everything missing. An aggregate view ("across your tracked series, 47 books are missing") is not described and would be very useful. This could be part of the Dashboard spec that is currently empty.

### LOW

- **No notification history**: Pushover notifications are sent when a download is snatched. If the user doesn't see the notification (phone was off, app was muted), there's no way to see what was snatched in the last 24 hours. The `downloads` table records this, but no UI surfaces "recently snatched" without digging into individual requests.

- **Requesting multiple books from search is possible but undescribed as a flow**: The plan says `onSearchRequestSuccess` stays on the page and updates the card in-place, which is great. But if a user wants to request 5 books from a search result page, they request one, the card updates, and they continue. There's no cart/queue metaphor. This is fine — but when they go to the Requests page, there's no summary of "you just added 5 requests." The feedback for a multi-book session is entirely per-card.

- **Book cover images in search results**: The plan includes `cover_url` in search results but never describes image loading behaviour — placeholder on failure, lazy loading, aspect ratio handling. For a book list this matters: a broken image breaks the visual rhythm of a card grid.
