# Settings — field inventory and rewrite plan

Phase 8 is a deliberate rewrite rather than a line-by-line port, so this is the
checklist it gets built against. Settings is where a silent porting error is
most expensive: a dropped field is a setting you can no longer change, and you
may not notice for weeks.

Compiled by cross-referencing three sources: v1's `/settings` route
(`static/app.js` 3357–4507), `DEFAULT_SETTINGS` in `app/settings.py`, and the
live `settings.yaml` on the dev instance.

## 1. Tabs

v1 exposes eight, in this order. `AutoSearch` is a builder function but is
rendered inside the Downloads tab, not as a ninth tab.

| Tab | v1 builder | LOC | Save section |
|---|---|---:|---|
| General | `buildGeneralTab` | 20 | `general` |
| ABS | `buildAbsTab` | 24 | `audiobookshelf` |
| Prowlarr | `buildProwlarrTab` | 73 | `prowlarr` |
| Downloads | `buildAndWireDownloadersTab` | 257 | `downloaders`, `auto_search` |
| Hardcover | `buildHardcoverTab` | 13 | `hardcover` |
| Notifications | `buildNotificationsTab` | 30 | `notifications` |
| Tasks | `buildTasksTab` | 33 | `schedule` |
| Auth | `buildAuthTab` | 523 | `auth` |

Two tabs are 68% of the code. Downloads and Auth are not forms — they are list
editors (downloader entries, user accounts) and deserve their own components.
The other six are plain field lists and are the natural fit for a schema.

## 2. Fields to preserve

Everything below must exist in v2. Types are as v1 renders them.

**General** — `output_dir` (text), `separate_type_dirs` (bool),
`audiobook_prefix` (text), `ebook_prefix` (text), `public_url` (text),
`merge_multifile_audiobooks` (bool), `debug_view` (bool),
`allowed_audiobook_formats` (list), `allowed_ebook_formats` (list)

**ABS** — `url`, `internal_url`, `api_key`, `library_id` (multi-select, custom
UI), plus a Test Connection button

**Prowlarr** — `url`, `api_key`, `tags` (indexer tag filter, multiple), Test
Connection

**Downloads** — the `downloaders` array (add/remove/edit entries of type
qbittorrent, sabnzbd, deluge; per-entry test), plus auto-search settings:
`search_on_request` (bool), `min_seeders` (int), `max_attempts` (int),
`ranking` (ordered, toggleable criteria list)

**Hardcover** — `api_key`, `preferred_language`, Test Connection

**Notifications** — `urls` (Apprise URLs), `batch_window` (int), Test

**Tasks** — cron expressions for `library_sync`, `cache_refresh`,
`auto_search`, each with a Run-now button and next-run display

**Auth** — `form_enabled`, `oidc_enabled`, `oidc_provider_url` (with a verify
step hitting `/auth/oidc/verify`), `oidc_client_id`, `oidc_client_secret`,
`oidc_scopes`, `session_days`, plus full user management (list, create, edit
role, delete, reset password)

## 3. Drift found

Cross-referencing turned up keys that exist in stored settings but are read by
nobody. None of these are regressions from the port — they are pre-existing, and
the rewrite is a good moment to decide about them.

**Removed (2026-08-10).** These were read by nothing. Four of them were never in
`DEFAULT_SETTINGS` at all — they existed only as stale entries in the stored
`settings.yaml`, which is why nothing consumed them.

| Key | Was | Why it was dead |
|---|---|---|
| `audiobookshelf.square_book_covers` | `true` | Cover shape comes from the ABS library's own `coverAspectRatio` via `/abs/library-settings`. |
| `general.group_series_in_search` | `true` | Read like a feature toggle; nothing implemented it. |
| `pushover.app_token`, `pushover.user_key` | `""` | Superseded by `notifications.urls` (`pover://`). Not even in `KNOWN_SECTIONS`, so unsaveable via the API. |
| `auto_search.enabled` | `false` | `auto_search.py` reads `max_attempts`, `min_seeders` and `ranking` only. Auto-search is gated by `schedule.auto_search`. |
| `prowlarr.tag` | `"books"` | Superseded by the plural `tags`, which now supports several tags. |

`prowlarr.tags` was on this list too, and was **fixed rather than removed**: the
backend now reads the plural, accepts several tags, and falls back to the
singular for configs that only have it. It defaults to `["books"]`.

**Correctly hidden:** `auth.session_secret` — internal, must never be editable.

**Still to do at cutover:** the same cleanup has NOT been applied to production's
`settings.yaml`. Production runs `main`, which still reads the singular
`prowlarr.tag`; removing it before v2.0.0 ships would silently disable tag
filtering there and quietly search every indexer. Apply the same edit as part of
the release, after the new code is deployed.

## 4. Proposed structure

```
routes/(app)/settings/+page.svelte     tab shell, loads settings once
  ├── GeneralTab / AbsTab / ProwlarrTab / HardcoverTab
  │   / NotificationsTab / TasksTab      schema-driven, ~30 lines each
  ├── DownloadersTab                     list editor
  └── AuthTab + UsersTable               list editor + form
lib/components/settings/
  SettingField.svelte                    text | password | number | bool | list
  SettingSection.svelte                  heading, save button, feedback
  TestConnectionButton.svelte            wraps the five /settings/test/* calls
```

Each simple tab becomes a schema array plus a `{#each}`. v1 already works this
way in miniature — its `field(label, key, value, type, hint)` helper emits
`data-key` attributes that a save handler reads back out of the DOM — so this
formalises an existing pattern rather than inventing one.

Estimated ~450 lines against v1's 1,150, with the saving in the six simple tabs.
Downloads and Auth stay roughly the same size because they are genuinely
complex.

## 5. Risks

- **Silent field loss.** Mitigated by §2 as a checklist, verified against a live
  `GET /settings` before cutover.
- **Auth tab is 523 lines** and covers user management, which is the highest
  consequence area in the app. Worth doing as its own step.
- **Save granularity.** v1 saves per section, PUTting only that key. Preserve
  that: a whole-document save would let a stale tab clobber another's changes.
