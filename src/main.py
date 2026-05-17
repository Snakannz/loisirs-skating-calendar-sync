import argparse
import json
from datetime import datetime
from zoneinfo import ZoneInfo

from calendar_client import GoogleCalendarClient, build_smoke_test_window
from config import (
    DEFAULT_CALENDAR_NAME,
    DEFAULT_TIME_ZONE,
    env_path,
    env_str,
    load_env_file,
    resolve_repo_path,
)
from loisirs_client import LoisirsClient
from parser import (
    FIGURE_SKATING,
    OTHER_SKATING,
    PUBLIC_SKATE,
    parse_skating_windows,
    parse_untimed_activities,
)


KIND_ALIASES = {
    "all": None,
    "figure": FIGURE_SKATING,
    "figure_skating": FIGURE_SKATING,
    "public": PUBLIC_SKATE,
    "public_skate": PUBLIC_SKATE,
    "other": OTHER_SKATING,
    "other_skating": OTHER_SKATING,
}


def main() -> None:
    load_env_file()
    args = parse_args()

    if args.calendar_smoke_test:
        run_calendar_smoke_test(args)
        return

    run_fetch(args)


def run_fetch(args: argparse.Namespace) -> None:
    client = LoisirsClient()
    response = client.search_activities(
        search_string=args.search,
        expertise_field_ids=args.expertise_field_id,
        limit=args.limit,
    )
    windows = parse_skating_windows(response)
    untimed_activities = parse_untimed_activities(response)
    windows = filter_items_by_kind(windows, args.kind)
    untimed_activities = filter_items_by_kind(untimed_activities, args.kind)
    windows = sorted(windows, key=lambda window: window.start)

    if args.future_only or args.next:
        windows = filter_future_windows(windows, args.time_zone)

    if args.next:
        windows = windows[:1]

    if args.json:
        output = {"windows": [window.to_dict() for window in windows]}
        if args.include_untimed:
            output["untimed_activities"] = [activity.to_dict() for activity in untimed_activities]
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    print(f"{len(windows)} timed skating windows from {response.get('recordCount', 0)} activities")
    for window in windows:
        start_date, start_time = window.start.split("T")
        end_time = window.end.split("T")[1][:8]
        print(
            f"{start_date} {start_time[:8]}-{end_time} | {window.importance} | "
            f"{window.kind} | {window.site_name} | {window.title} | {window.status}"
        )

    if args.include_untimed and untimed_activities:
        print("")
        print(f"{len(untimed_activities)} untimed skating activities")
        for activity in untimed_activities:
            print(
                f"{activity.start_date} to {activity.end_date} | {activity.importance} | "
                f"{activity.kind} | {activity.site_name} | {activity.title} | {activity.status}"
            )


def filter_items_by_kind(items: list, kind_arg: str) -> list:
    kind = KIND_ALIASES[kind_arg]
    if kind is None:
        return items
    return [item for item in items if item.kind == kind]


def filter_future_windows(windows: list, time_zone: str) -> list:
    now = datetime.now(ZoneInfo(time_zone))
    return [window for window in windows if datetime.fromisoformat(window.start) >= now]


def run_calendar_smoke_test(args: argparse.Namespace) -> None:
    client = GoogleCalendarClient(
        credentials_path=args.google_credentials_file,
        token_path=args.google_token_file,
        time_zone=args.time_zone,
    )
    calendar_id = client.get_or_create_calendar(args.calendar_name)
    window = build_smoke_test_window(args.time_zone)
    event = client.create_event(calendar_id, window)

    print(f"Calendar: {args.calendar_name} ({calendar_id})")
    print(f"Created event: {event['id']}")
    if event.get("htmlLink"):
        print(f"Link: {event['htmlLink']}")

    if args.delete_smoke_event:
        client.delete_event(calendar_id, event["id"])
        print("Deleted smoke-test event.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch skating windows from Loisirs Montréal.")
    parser.add_argument("--search", default=env_str("LOISIRS_SEARCH_STRING", "patin"), help="Free-text search string.")
    parser.add_argument(
        "--expertise-field-id",
        default=env_str("LOISIRS_EXPERTISE_FIELD_IDS", "361"),
        help="Loisirs expertise category id.",
    )
    parser.add_argument("--limit", type=int, default=100, help="Maximum activities to fetch.")
    parser.add_argument(
        "--kind",
        choices=sorted(KIND_ALIASES.keys()),
        default="all",
        help="Filter skating windows by kind.",
    )
    parser.add_argument("--future-only", action="store_true", help="Only show windows that have not started yet.")
    parser.add_argument("--next", action="store_true", help="Only show the next matching timed skating window.")
    parser.add_argument(
        "--include-untimed",
        action="store_true",
        help="Also show matching activities that have no time schedule in the API response.",
    )
    parser.add_argument("--json", action="store_true", help="Print normalized windows as JSON.")
    parser.add_argument(
        "--calendar-smoke-test",
        action="store_true",
        help="Create a hardcoded test event in the dedicated Google Calendar.",
    )
    parser.add_argument(
        "--delete-smoke-event",
        action="store_true",
        help="Delete the smoke-test event immediately after creating it.",
    )
    parser.add_argument(
        "--calendar-name",
        default=env_str("GOOGLE_CALENDAR_NAME", DEFAULT_CALENDAR_NAME),
        help="Dedicated Google Calendar name.",
    )
    parser.add_argument(
        "--google-credentials-file",
        default=env_path("GOOGLE_CREDENTIALS_FILE", "credentials.json"),
        type=env_path_arg,
        help="Path to Google OAuth client secrets JSON.",
    )
    parser.add_argument(
        "--google-token-file",
        default=env_path("GOOGLE_TOKEN_FILE", "token.json"),
        type=env_path_arg,
        help="Path where the user OAuth token should be stored.",
    )
    parser.add_argument(
        "--time-zone",
        default=DEFAULT_TIME_ZONE,
        help="Calendar event time zone.",
    )
    return parser.parse_args()


def env_path_arg(value: str):
    return resolve_repo_path(value)


if __name__ == "__main__":
    main()
