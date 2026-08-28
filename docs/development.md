# Development

## Running a published image

Most people want this rather than a source build:

```bash
docker pull ghcr.io/bothari/athenaeum:latest
```

| tag | what it is |
|-----|------------|
| `latest` | the newest release |
| `1.0.0`, `1.0` | a specific release, or the newest patch in that minor series |
| `testing` | the `dogfood` branch: in-flight changes merged together, may break |

Pin to `1.0` if you want bugfixes without feature changes.

## Building from source

```bash
git clone https://github.com/Bothari/Athenaeum.git
cd Athenaeum
docker compose up -d --build
```

## Running tests

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/python -m pytest tests/ -v
```

## Branches and releases

| branch | image tag | role |
|--------|-----------|------|
| `main` | `latest`, `x.y.z`, `x.y` | always releasable; tagging it publishes a release |
| `topic/*` | — | one change each, however long it takes |
| `dogfood` | `testing` | throwaway integration branch |

A topic branch graduates to `main` on its own via PR, and is then tagged. It never
reaches main by way of `dogfood`, which exists only to answer "what do all the
in-flight changes look like together" — it is rebuilt from main rather than merged
back, and is force-pushed, so never branch off it.

Versions follow semver: patch for bugfixes, minor for features, major for breaking
changes.

### Contributing

Pull requests should target `main`. CI runs the test suite on every PR.

Schema changes go through the migration system in `app/database.py` (PRAGMA
`user_version` blocks) — never a bare `CREATE TABLE IF NOT EXISTS`. If a migration
rebuilds a table, test it against a *populated* copy of a database: an empty test
database will not catch a foreign key or row-preservation mistake.
