import json
from urllib.request import Request, urlopen


SEARCH_URL = "https://loisirs.montreal.ca/IC3/api/U5200/public/search/"
SEARCH_INIT_URL = "https://loisirs.montreal.ca/IC3/api/U5200/public/search/init/"
ACTIVITY_VIEW_URL = "https://loisirs.montreal.ca/IC3/api/U5200/public/view/"


DEFAULT_ACTIVITY_STATUSES = {
    "lblStatusFinish": "Terminé",
    "lblStatusFull": "Complet",
    "lblStatusInProgress": "En cours",
    "lblStatusNotAvailable": "Non disponible",
    "lblStatusOfflineOnly": "Hors ligne seulement",
    "lblStatusToComeUp": "À venir",
    "lblStatusWaitingList": "Liste d’attente",
}


class LoisirsClient:
    def __init__(self, timeout: int = 30) -> None:
        self.timeout = timeout

    def search_activities(
        self,
        search_string: str | None = "patin artistique",
        expertise_field_ids: str | None = "365",
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        payload = {
            "limit": limit,
            "offset": offset,
            "sortColumn": "description",
            "isSortOrderAsc": True,
            "searchString": search_string,
            "age": None,
            "dates": [],
            "dayOfWeekId": None,
            "expertiseFieldIds": expertise_field_ids,
            "boroughIds": None,
            "memberCategoryId": None,
            "sessionId": None,
            "partnerId": None,
            "siteId": None,
            "canRegisterStatuses": None,
            "activityStatuses": DEFAULT_ACTIVITY_STATUSES,
        }
        return self._post_json(SEARCH_URL, payload)

    def get_search_init(self) -> dict:
        return self._get_json(SEARCH_INIT_URL)

    def get_activity(self, activity_id: int) -> dict:
        return self._get_json(f"{ACTIVITY_VIEW_URL}?id={activity_id}")

    def _get_json(self, url: str) -> dict:
        request = Request(url, headers=self._headers())
        return self._open_json(request)

    def _post_json(self, url: str, payload: dict) -> dict:
        body = json.dumps(payload).encode("utf-8")
        headers = self._headers()
        headers["Content-Type"] = "application/json;charset=UTF-8"
        request = Request(url, data=body, headers=headers, method="POST")
        return self._open_json(request)

    def _open_json(self, request: Request) -> dict:
        with urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8-sig"))

    def _headers(self) -> dict:
        return {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "fr",
            "Origin": "https://loisirs.montreal.ca",
            "Referer": "https://loisirs.montreal.ca/IC3/",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36"
            ),
        }
