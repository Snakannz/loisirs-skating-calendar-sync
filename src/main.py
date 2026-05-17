import argparse
import json

from loisirs_client import LoisirsClient
from parser import parse_skating_windows


def main() -> None:
    args = parse_args()
    client = LoisirsClient()
    response = client.search_activities(
        search_string=args.search,
        expertise_field_ids=args.expertise_field_id,
        limit=args.limit,
    )
    windows = parse_skating_windows(response)

    if args.json:
        print(json.dumps([window.to_dict() for window in windows], ensure_ascii=False, indent=2))
        return

    print(f"{len(windows)} timed skating windows from {response.get('recordCount', 0)} activities")
    for window in windows:
        start_date, start_time = window.start.split("T")
        end_time = window.end.split("T")[1][:8]
        print(f"{start_date} {start_time[:8]}-{end_time} | {window.site_name} | {window.title} | {window.status}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch skating windows from Loisirs Montréal.")
    parser.add_argument("--search", default="patin", help="Free-text search string.")
    parser.add_argument("--expertise-field-id", default="361", help="Loisirs expertise category id.")
    parser.add_argument("--limit", type=int, default=100, help="Maximum activities to fetch.")
    parser.add_argument("--json", action="store_true", help="Print normalized windows as JSON.")
    return parser.parse_args()


if __name__ == "__main__":
    main()

