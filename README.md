# Loisirs Skating Calendar Sync

Python scraper/sync tool for Loisirs Montréal skating availability.

Current status: Phase 2. It calls the hidden Loisirs Montréal JSON API, prints normalized skating windows, and has a Google Calendar client ready for a fake-event smoke test.

## Discovered Endpoints

Search init/filter metadata:

```text
GET https://loisirs.montreal.ca/IC3/api/U5200/public/search/init/
```

Activity search:

```text
POST https://loisirs.montreal.ca/IC3/api/U5200/public/search/
```

Activity detail:

```text
GET https://loisirs.montreal.ca/IC3/api/U5200/public/view/?id=<activity_id>
```

The pasted browser URL used `expertiseFieldIds=365`, but on May 16, 2026 that returned zero rows. The live category returning ice-sport rows was `361`, named `Sports sur glace`.

## Run

```bash
python3 src/main.py
```

Useful options:

```bash
python3 src/main.py --search patin --expertise-field-id 361
python3 src/main.py --json
```

## Google Calendar Smoke Test

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Then place your Google OAuth desktop client secrets file at:

```text
credentials.json
```

That file is intentionally ignored by Git.

Run:

```bash
python3 src/main.py --calendar-smoke-test
```

The first run opens a Google OAuth browser flow and saves `token.json`, also ignored by Git. The command creates or finds a dedicated calendar named `Patinage Montréal`, then creates one hardcoded test event.

To create and immediately delete the test event:

```bash
python3 src/main.py --calendar-smoke-test --delete-smoke-event
```

## Test

```bash
python3 -m unittest discover -s tests
```

## Next Milestones

1. Keep Phase 1 stable: direct API fetch plus normalized skating windows.
2. Confirm Google Calendar OAuth with the smoke test.
3. Add SQLite sync state.
4. Wire create/update/delete sync.
5. Schedule with `launchd`.
