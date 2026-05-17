from datetime import date, datetime, timedelta, time
from zoneinfo import ZoneInfo

from models import SkatingActivity, SkatingWindow


MONTREAL = ZoneInfo("America/Montreal")
SOURCE_URL = "https://loisirs.montreal.ca/IC3/#/U5200/view/{activity_id}"
FIGURE_SKATING = "figure_skating"
PUBLIC_SKATE = "public_skate"
OTHER_SKATING = "other_skating"
PRIMARY = "primary"
SECONDARY = "secondary"
OTHER = "other"


def parse_skating_windows(search_response: dict) -> list[SkatingWindow]:
    windows: list[SkatingWindow] = []
    for activity in search_response.get("results", []):
        windows.extend(parse_activity(activity))
    return windows


def parse_untimed_activities(search_response: dict) -> list[SkatingActivity]:
    activities: list[SkatingActivity] = []
    for activity in search_response.get("results", []):
        if _has_timed_schedule(activity):
            continue
        activities.append(parse_activity_summary(activity, has_timed_schedules=False))
    return activities


def parse_activity_summary(activity: dict, has_timed_schedules: bool) -> SkatingActivity:
    activity_id = activity["id"]
    start_date = _local_date(activity["startDate"])
    end_date = _local_date(activity.get("endDate") or activity["startDate"])
    site_name = ((activity.get("mainSite") or {}).get("name")) or "Lieu à confirmer"
    status = ((activity.get("status") or {}).get("name")) or ""
    kind = classify_activity(activity.get("description", ""))
    importance = importance_for_kind(kind)
    url = SOURCE_URL.format(activity_id=activity_id)

    return SkatingActivity(
        source_key=f"loisirs-mtl|activity|{activity_id}|{start_date.isoformat()}|{end_date.isoformat()}",
        kind=kind,
        importance=importance,
        title=activity["description"],
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        site_name=site_name,
        status=status,
        url=url,
        activity_id=activity_id,
        has_timed_schedules=has_timed_schedules,
    )


def parse_activity(activity: dict) -> list[SkatingWindow]:
    windows: list[SkatingWindow] = []
    activity_id = activity["id"]
    kind = classify_activity(activity.get("description", ""))
    importance = importance_for_kind(kind)

    for schedule in activity.get("activitySchedules") or []:
        start_time = schedule.get("startTime")
        end_time = schedule.get("endTime")
        if not start_time or not end_time:
            continue

        site_name = _site_name(activity, schedule)
        facility_name = ((schedule.get("facility") or {}).get("name")) or site_name
        location = _location(site_name, facility_name)
        status = ((activity.get("status") or {}).get("name")) or ""
        title = f"{activity['description']} - {site_name}"
        url = SOURCE_URL.format(activity_id=activity_id)

        for activity_date in _activity_dates(activity, schedule):
            start = _combine(activity_date, start_time)
            end = _combine(activity_date, end_time)

            windows.append(
                SkatingWindow(
                    source_key=_source_key(activity_id, activity_date, start_time, end_time, site_name),
                    kind=kind,
                    importance=importance,
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


def classify_activity(description: str) -> str:
    normalized = description.casefold()
    if "patinage artistique" in normalized or "patin artistique" in normalized:
        return FIGURE_SKATING
    if "patin libre" in normalized or "patinage libre" in normalized:
        return PUBLIC_SKATE
    return OTHER_SKATING


def importance_for_kind(kind: str) -> str:
    if kind == FIGURE_SKATING:
        return PRIMARY
    if kind == PUBLIC_SKATE:
        return SECONDARY
    return OTHER


def _local_date(value: str) -> date:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(MONTREAL).date()


def _activity_dates(activity: dict, schedule: dict) -> list[date]:
    start_date = _local_date(activity["startDate"])
    end_date = _local_date(activity.get("endDate") or activity["startDate"])
    day_of_week_id = ((schedule.get("dayOfWeek") or {}).get("id"))

    if start_date == end_date or day_of_week_id is None:
        return [start_date]

    dates = []
    current = start_date
    while current <= end_date:
        if current.isoweekday() == day_of_week_id:
            dates.append(current)
        current += timedelta(days=1)
    return dates or [start_date]


def _combine(day: date, value: str) -> datetime:
    return datetime.combine(day, time.fromisoformat(value), MONTREAL)


def _has_timed_schedule(activity: dict) -> bool:
    for schedule in activity.get("activitySchedules") or []:
        if schedule.get("startTime") and schedule.get("endTime"):
            return True
    return False


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
