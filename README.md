# Loisirs Skating Calendar Sync

Python scraper/sync tool for Loisirs Montréal skating availability.

Current status: Phase 3. It calls the hidden Loisirs Montréal JSON API, prints normalized skating windows, classifies primary vs secondary skating activities, and can compare timed windows against local SQLite sync state.

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
python3 src/main.py --kind figure --include-untimed
python3 src/main.py --kind public --future-only
python3 src/main.py --kind public --next
python3 src/main.py --kind public --sync-plan
python3 src/main.py --json
```

Skating activity kinds:

| Kind | Importance | Meaning |
| --- | --- | --- |
| `figure_skating` | `primary` | `Patinage artistique`; the main activity we care about |
| `public_skate` | `secondary` | `Patin libre` / `Patinage libre`; useful add-on events |
| `other_skating` | `other` | Ice-sport rows that do not match the first two categories |

Current caveat: the live Loisirs API returns `Patinage artistique` as a date-range activity with no timed schedule. The scraper keeps it visible with `--include-untimed`, but it cannot make a precise timed calendar event for that row until the API exposes start/end times or we find another endpoint.

## SQLite Sync State

SQLite is a small database stored in one local file:

```text
data/sync.sqlite
```

The sync state remembers which Loisirs windows have already been matched to Google Calendar events:

| Column | Meaning |
| --- | --- |
| `source_key` | Stable ID for one Loisirs skating window |
| `google_event_id` | The matching Google Calendar event ID |
| `content_hash` | Fingerprint of event content, used to detect changes |
| `last_seen_at` | When the scraper last saw this window |

Run a safe dry-run plan:

```bash
python3 src/main.py --kind public --sync-plan
```

This does not create, update, or delete Google Calendar events. It only compares the current timed skating windows with the local SQLite state and prints what a real sync would do.

Untimed activities, such as the current `Patinage artistique` date range, are intentionally not included in calendar sync planning because they do not have precise start and end times.

## Calendar Sync

After Google OAuth is configured, run:

```bash
python3 src/main.py --kind public --sync-calendar
```

On the first run, the app creates Google Calendar events and saves their Google event IDs in SQLite. On the second run with the same Loisirs data, those same rows become `keep` actions instead of duplicate events.

The sync only considers future timed windows. Saved past events are not deleted just because they are no longer future windows.

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
3. Test real Google Calendar sync end to end.
4. Schedule with `launchd`.
