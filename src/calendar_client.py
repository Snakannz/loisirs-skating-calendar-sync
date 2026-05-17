from __future__ import annotations

from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from config import DEFAULT_CALENDAR_NAME, DEFAULT_TIME_ZONE
from models import SkatingWindow


SCOPES = ["https://www.googleapis.com/auth/calendar"]


class GoogleCalendarClient:
    def __init__(
        self,
        credentials_path: Path,
        token_path: Path,
        time_zone: str = DEFAULT_TIME_ZONE,
        service: Any | None = None,
    ) -> None:
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.time_zone = time_zone
        self._service = service

    @property
    def service(self) -> Any:
        if self._service is None:
            self._service = self._build_service()
        return self._service

    def get_or_create_calendar(self, name: str = DEFAULT_CALENDAR_NAME) -> str:
        page_token = None
        while True:
            response = self.service.calendarList().list(pageToken=page_token).execute()
            for calendar in response.get("items", []):
                if calendar.get("summary") == name:
                    return calendar["id"]
            page_token = response.get("nextPageToken")
            if not page_token:
                break

        created = (
            self.service.calendars()
            .insert(body={"summary": name, "timeZone": self.time_zone})
            .execute()
        )
        return created["id"]

    def create_event(self, calendar_id: str, window: SkatingWindow) -> dict:
        return (
            self.service.events()
            .insert(calendarId=calendar_id, body=window_to_event(window, self.time_zone))
            .execute()
        )

    def update_event(self, calendar_id: str, event_id: str, window: SkatingWindow) -> dict:
        return (
            self.service.events()
            .update(calendarId=calendar_id, eventId=event_id, body=window_to_event(window, self.time_zone))
            .execute()
        )

    def delete_event(self, calendar_id: str, event_id: str) -> None:
        self.service.events().delete(calendarId=calendar_id, eventId=event_id).execute()

    def _build_service(self) -> Any:
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise RuntimeError(
                "Google Calendar dependencies are missing. Run: python3 -m pip install -r requirements.txt"
            ) from exc

        credentials = None
        if self.token_path.exists():
            credentials = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)

        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                if not self.credentials_path.exists():
                    raise FileNotFoundError(
                        f"Missing Google OAuth client secrets file: {self.credentials_path}"
                    )
                flow = InstalledAppFlow.from_client_secrets_file(str(self.credentials_path), SCOPES)
                credentials = flow.run_local_server(port=0)

            self.token_path.write_text(credentials.to_json(), encoding="utf-8")

        return build("calendar", "v3", credentials=credentials)


def window_to_event(window: SkatingWindow, time_zone: str = DEFAULT_TIME_ZONE) -> dict:
    return {
        "summary": window.title,
        "location": window.location,
        "description": window.description,
        "start": {
            "dateTime": window.start,
            "timeZone": time_zone,
        },
        "end": {
            "dateTime": window.end,
            "timeZone": time_zone,
        },
        "source": {
            "title": "Loisirs Montréal",
            "url": window.url,
        },
        "extendedProperties": {
            "private": {
                "source": "loisirs-montreal",
                "source_key": window.source_key,
                "content_hash": window.content_hash(),
                "kind": window.kind,
                "importance": window.importance,
            }
        },
    }


def build_smoke_test_window(time_zone: str = DEFAULT_TIME_ZONE) -> SkatingWindow:
    tz = ZoneInfo(time_zone)
    tomorrow = datetime.now(tz).date() + timedelta(days=1)
    start = datetime.combine(tomorrow, time(12, 0), tz)
    end = datetime.combine(tomorrow, time(13, 0), tz)
    day = date.isoformat(tomorrow)
    source_key = f"loisirs-mtl|smoke-test|{day}|12:00:00|13:00:00|Test Arena"

    return SkatingWindow(
        source_key=source_key,
        title="Test - Patinage Montréal sync",
        kind="figure_skating",
        importance="primary",
        start=start.isoformat(),
        end=end.isoformat(),
        location="Test Arena, Montréal",
        description="Temporary smoke-test event created by loisirs-skating-calendar-sync.",
        url="https://loisirs.montreal.ca/IC3/",
        activity_id=0,
        status="Test",
        site_name="Test Arena",
        facility_name="Test Arena",
    )
