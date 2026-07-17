# Loisirs Figure Skating Calendar Sync

Python scraper/sync tool for figure-skating windows on Loisirs Montréal.

Current status: production-ready v1. It calls the hidden Loisirs Montréal JSON API, keeps only figure-skating activities, ignores activities without precise start/end times, and syncs timed windows to Google Calendar.

## Operational proof

- Scheduled hourly with GitHub Actions since May 2026.
- More than 500 observed workflow runs with a success rate above 99%.
- Fourteen automated tests cover parsing, recurring windows, synchronization planning, idempotence and calendar state.
- At least 19 real calendar events have been managed without duplicate creation.
- The two recorded workflow failures were external: one Loisirs Montréal HTTP 500 and one temporary GitHub account suspension response.

These are durable thresholds rather than live counters. GitHub Actions remains the source of truth for current run history.

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

The figure-skating category is `365`, named `Patinage artistique`. Its parent category is `361`, named `Sports sur glace`.

Important naming detail: some timed activities are titled `Patin artistique`, while the category/filter is named `Patinage artistique`. The app handles both labels as figure skating, but the workflow searches for `patin artistique` inside category `365` because that is the combination currently returning the precise timed windows.

## Run

```bash
python3 src/main.py
```

Useful options:

```bash
python3 src/main.py --include-untimed
python3 src/main.py --sync-plan
python3 src/main.py --sync-calendar
python3 src/main.py --json
```

Default search/filter:

| Setting | Default |
| --- | --- |
| Search text | `patin artistique` |
| Category | `365` / `Patinage artistique` |
| Activity kind | Always `figure_skating` |

The scraper intentionally ignores activities without precise start and end times. Those activities are visible with `--include-untimed`, but they are not syncable calendar events.

## SQLite Sync State

SQLite is a small database stored in one local file:

```text
data/sync.sqlite
```

The sync state remembers which Loisirs windows have already been matched to Google Calendar events:

| Column | Meaning |
| --- | --- |
| `source_key` | Stable ID for one Loisirs figure-skating window |
| `google_event_id` | The matching Google Calendar event ID |
| `content_hash` | Fingerprint of event content, used to detect changes |
| `last_seen_at` | When the scraper last saw this window |

Run a safe dry-run plan:

```bash
python3 src/main.py --sync-plan
```

This does not create, update, or delete Google Calendar events. It only compares the current timed figure-skating windows with the local SQLite state and prints what a real sync would do.

Untimed figure-skating activities are intentionally not included in calendar sync planning because they do not have precise start and end times.

## Calendar Sync

After Google OAuth is configured, run:

```bash
python3 src/main.py --sync-calendar
```

On the first run, the app creates Google Calendar events and saves their Google event IDs in SQLite. On the second run with the same Loisirs data, those same rows become `keep` actions instead of duplicate events.

The sync only considers future timed windows. Saved past events are not deleted just because they are no longer future windows.

Historical note: earlier versions synced public-skate events too. The current app does not. The first sync after this change will delete old app-managed public-skate events from the calendar and keep the calendar reserved for timed figure-skating windows.

## GitHub Actions

The repository includes an hourly workflow:

```text
.github/workflows/sync-skating.yml
```

It runs:

```bash
python src/main.py --search "patin artistique" --expertise-field-id 365 --sync-calendar --state-backend calendar
```

The app always filters to `figure_skating`, so GitHub Actions cannot accidentally sync public-skate or other ice-sport activities. The `calendar` state backend reads existing managed events from Google Calendar extended properties, so GitHub Actions does not need `data/sync.sqlite`.

Add these GitHub repository secrets:

| Secret | Value |
| --- | --- |
| `GOOGLE_CREDENTIALS_JSON` | Contents of local `credentials.json` |
| `GOOGLE_TOKEN_JSON` | Contents of local `token.json` |

In GitHub, go to **Settings -> Secrets and variables -> Actions -> New repository secret**.

Google OAuth caveat: if your OAuth app remains in **Testing** mode, Google may expire the refresh token after 7 days for non-profile scopes such as Calendar. For long-running autonomous sync, move the OAuth app publishing status to **In production** in Google Cloud, then re-run the local OAuth flow once and update `GOOGLE_TOKEN_JSON`.

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

The first run opens a Google OAuth browser flow and saves `token.json`, also ignored by Git. The command creates or finds a dedicated calendar named `Patinage`, then creates one hardcoded test event.

To create and immediately delete the test event:

```bash
python3 src/main.py --calendar-smoke-test --delete-smoke-event
```

## Test

```bash
python3 -m unittest discover -s tests
```

## Security

OAuth credentials and refresh tokens are never committed. Local files are ignored, while GitHub Actions reconstructs them at runtime from encrypted repository secrets. Before this repository was made public, every historical filename and commit was scanned for credential files, private keys and common token patterns; none were found.

## Operating Notes

- GitHub Actions runs hourly at minute `17`.
- If Loisirs has no timed `Patinage artistique` / `Patin artistique` windows, the calendar should remain empty.
- When timed `Patinage artistique` / `Patin artistique` windows are published, the next scheduled run should add them automatically.
- Manual runs are still available from GitHub Actions via **Run workflow**.
