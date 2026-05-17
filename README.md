# Loisirs Figure Skating Calendar Sync

Python scraper/sync tool for **Patinage artistique** windows on Loisirs Montréal.

Current status: production-ready v1. It calls the hidden Loisirs Montréal JSON API, keeps only `Patinage artistique`, ignores activities without precise start/end times, and syncs timed windows to Google Calendar.

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

The pasted browser URL used `expertiseFieldIds=365`, but on May 16, 2026 that returned zero rows. The live category containing ice-sport rows was `361`, named `Sports sur glace`.

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
| Search text | `patinage artistique` |
| Category | `361` / `Sports sur glace` |
| Activity kind | Always `figure_skating` |

Current caveat: the live Loisirs API returns `Patinage artistique` as a date-range activity with no timed schedule. The scraper keeps it visible with `--include-untimed`, but it intentionally does not create Google Calendar events unless a precise start and end time is published.

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

Untimed `Patinage artistique` activities are intentionally not included in calendar sync planning because they do not have precise start and end times.

## Calendar Sync

After Google OAuth is configured, run:

```bash
python3 src/main.py --sync-calendar
```

On the first run, the app creates Google Calendar events and saves their Google event IDs in SQLite. On the second run with the same Loisirs data, those same rows become `keep` actions instead of duplicate events.

The sync only considers future timed windows. Saved past events are not deleted just because they are no longer future windows.

Historical note: earlier versions synced public-skate events too. The current app does not. The first sync after this change will delete old app-managed public-skate events from the calendar and keep the calendar reserved for timed `Patinage artistique` windows.

## GitHub Actions

The repository includes an hourly workflow:

```text
.github/workflows/sync-skating.yml
```

It runs:

```bash
python src/main.py --search "patinage artistique" --sync-calendar --state-backend calendar
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

## Operating Notes

- GitHub Actions runs hourly at minute `17`.
- If Loisirs has no timed `Patinage artistique` windows, the calendar should remain empty.
- When timed `Patinage artistique` windows are published, the next scheduled run should add them automatically.
- Manual runs are still available from GitHub Actions via **Run workflow**.
