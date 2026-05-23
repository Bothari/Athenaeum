# UI Expert Review — Athenaeum PLAN.md (Round 2)

## Persona
I design and review user interfaces for a living. I'm looking at interaction patterns, information hierarchy, empty/loading/error states, and whether the described UI is actually buildable without guessing. I assume all backend issues from Round 1 are resolved.

---

## Findings

### HIGH

- **Dashboard (`/#/`) has no specified content**: The dashboard is in the nav and has a dedicated route, but the plan describes exactly zero about what it should show. `GET /api/status` returns counts by request status — presumably these go on the dashboard — but the layout, any charts, any quick-action links, and what "useful at a glance" means for this app are entirely unspecified. An implementer will either invent something arbitrary or leave it as a blank page.

- **No empty states defined for any list page**: Every list page (`Books`, `Authors`, `Series`, `Requests`, `Downloads`) will be empty on first run. None of them have a described empty state. This is a critical first-run UX gap: the first thing a new user sees is a blank table with no guidance on what to do next. The Requests page empty state is especially important — should it say "Monitor a book to start requesting" or "Go to Search to find books"?

- **`expandRequestForm` narrator input is unspecified**: The form is described as showing format selection (audiobook/ebook), but the narrator input — which is part of the deduplication key — is never described. When is it shown? Only for audiobook? Always? Is it required or optional? What is the placeholder text? The deduplication logic is narrator-aware but the form that collects the narrator has no spec.

- **Book detail ABS linking section is unspecified**: The book detail page shows "ABS items: the linked item + potential matches" — but how? A list of fuzzy-match candidates with a "Link" button each? A search field? A display of the current link with an Unlink button? There's a full `GET /api/abs/search` endpoint and `POST /api/metadata-links` for this, but the UI that drives it is never described. This is one of the more complex interactions in the app and has zero frontend spec.

- **No loading or error states for data-fetching pages**: The series stats card specifies a loading state (`⟳ loading...`) for the async missing-books call, but no other page or component specifies what to show while data is loading or when an API call fails. A user on a slow network will see blank content until the fetch completes. An API error will leave pages silently blank unless the implementer adds their own handling. Neither is described.

### MEDIUM

- **Advanced search form state is not URL-persisted**: `renderTable` state (sort, filter, offset) correctly lives in URL hash params and survives navigation. But the advanced search form (`/#/search`) has separate title/author/series inputs whose values are never described as being persisted. A user who searches, views a result, navigates back, and expects their search to still be there will find a blank form.

- **Request dropdown trigger and structure on book detail are undescribed**: The book detail page has "all requests with expandable dropdown" and "Request dropdown has: Search Prowlarr button + Delete Request button" — but what triggers the dropdown? A chevron? Clicking the row? A `⋯` menu? What does the closed state look like vs the open state? For failed requests with a retry path, where does the path input appear relative to the dropdown? The pattern is clear in intent but requires invention in implementation.

- **No 404 / unmatched-route handling specified**: The hash router matches patterns, but what happens when a user navigates to `/#/library/book?book_id=nonexistent` or `/#/anything-invalid`? The route handler will either render nothing or throw. A fallback route rendering "Not found" is not described.

- **`renderDetailStats` function described but its inputs for series page are unclear**: The function signature is `renderDetailStats(name, stats)` with `stats: { inLibrary, total, requested, missing, loadingMissing }` — but `total` for a series comes from `series.total_books` in the DB (which may be null if it was never set from Hardcover). What to display when `total` is null is not specified.

### LOW

- **No back-navigation pattern**: This is a hash-router SPA, so the browser back button works. But in-page contextual back links (e.g., "← Back to Series" on a book detail arrived from a series page) are never described. Author/series detail pages in particular would benefit from a breadcrumb or back link, but none is mentioned.

- **`library_formats` "have (Narrator A)" display format is mentioned but never shown**: The plan correctly specifies narrator-aware display — "shows as 'have (Narrator A)' next to the audiobook button" — but neither the exact string format nor its visual treatment (badge? inline text? tooltip?) is specified.

- **Settings tab validation feedback for path fields is inconsistent with masking**: Sensitive fields show `"********"` and the backend ignores them if unchanged. But path fields (`output_dir`, `download_dir`) are validated on save. If a path doesn't exist, the error feedback location ("next to the Save button") is specified, but what the error message says is not. A user who misconfigures a path will see a generic "error" with no actionable guidance.
