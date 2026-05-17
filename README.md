# Loisirs Skating Calendar Sync

Python scraper/sync tool for Loisirs Montréal skating availability.

Current status: Phase 1. It calls the hidden Loisirs Montréal JSON API and prints normalized skating windows. Google Calendar sync comes next.

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

## Test

```bash
python3 -m unittest discover -s tests
```

## Next Milestones

1. Keep Phase 1 stable: direct API fetch plus normalized skating windows.
2. Add SQLite sync state.
3. Add Google Calendar client using a dedicated `Patinage Montréal` calendar.
4. Wire create/update/delete sync.
5. Schedule with `launchd`.
