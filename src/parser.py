from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from models import SkatingWindow


MONTREAL = ZoneInfo("America/Montreal")
SOURCE_URL = "https://loisirs.montreal.ca/IC3/#/U5200/view/{activity_id}"


def parse_skating_windows(search_response: dict) -> list[SkatingWindow]:
    windows: list[SkatingWindow] = []
    for activity in search_response.get("results", []):
        windows.extend(parse_activity(activity))
    return windows


def parse_activity(activity: dict) -> list[SkatingWindow]:
    windows: list[SkatingWindow] = []
    activity_id = activity["id"]
    activity_date = _local_date(activity["startDate"])

    for schedule in activity.get("activitySchedules") or []:
        start_time = schedule.get("startTime")
        end_time = schedule.get("endTime")
        if not start_time or not end_time:
            continue

        site_name = _site_name(activity, schedule)
        facility_name = ((schedule.get("facility") or {}).get("name")) or site_name
        location = _location(site_name, facility_name)
        start = _combine(activity_date, start_time)
        end = _combine(activity_date, end_time)
        status = ((activity.get("status") or {}).get("name")) or ""
        title = f"{activity['description']} - {site_name}"
        url = SOURCE_URL.format(activity_id=activity_id)

        windows.append(
            SkatingWindow(
                source_key=_source_key(activity_id, activity_date, start_time, end_time, site_name),
                title=title,
                start=start.isoformat(),
                end=end.isoformat(),
                location=location,
                description=_description(activity, status, url),
                url=url,
                activity_id=activity_id,
                status=status,
                site_name=site_name,
                facility_name=facility_name,
            )
        )

    return windows


def _local_date(value: str) -> date:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(MONTREAL).date()


def _combine(day: date, value: str) -> datetime:
    return datetime.combine(day, time.fromisoformat(value), MONTREAL)


def _site_name(activity: dict, schedule: dict) -> str:
    main_site = activity.get("mainSite") or {}
    if main_site.get("name"):
        return main_site["name"]

    facility = schedule.get("facility") or {}
    site = facility.get("site") or {}
    return site.get("name") or facility.get("name") or "Lieu à confirmer"


def _location(site_name: str, facility_name: str) -> str:
    if facility_name and facility_name != site_name:
        return f"{facility_name}, {site_name}, Montréal"
    return f"{site_name}, Montréal"


def _description(activity: dict, status: str, url: str) -> str:
    lines = [
        "Source: Loisirs Montréal",
        f"Activity ID: {activity['id']}",
        f"Activity: {activity['description']}",
    ]
    if status:
        lines.append(f"Status: {status}")
    if activity.get("basePriceWithTaxes") is not None:
        lines.append(f"Price: {activity['basePriceWithTaxes']}")
    lines.append(f"URL: {url}")
    return "\n".join(lines)


def _source_key(activity_id: int, day: date, start_time: str, end_time: str, venue: str) -> str:
    safe_venue = venue.replace("|", " ").strip()
    return f"loisirs-mtl|{activity_id}|{day.isoformat()}|{start_time}|{end_time}|{safe_venue}"

