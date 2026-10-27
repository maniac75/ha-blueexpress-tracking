"""Public read-only Blue Express web-tracking client.

Uses the publicly accessible tracking endpoints behind blue.cl's tracking page.
These endpoints are undocumented and can change without notice.
No account credentials, address, telephone, or recipient identity are collected.
"""

import asyncio
import base64
from datetime import datetime
import json
import secrets
import re
from zoneinfo import ZoneInfo

import aiohttp

API_URL = "https://www.blue.cl/api"
SITE_URL = "https://www.blue.cl"
TIMEZONE = ZoneInfo("America/Santiago")
TRACKING_RE = re.compile(r"^[0-9]{8,10}$")
MAX_HISTORY = 70
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36"
)


class BlueExpressError(Exception):
    """Tracking provider returned invalid, incomplete, or unavailable data."""


def valid_tracking_number(number: str) -> bool:
    """Blue Express's public tracking form accepts eight to ten digits."""
    return bool(TRACKING_RE.fullmatch(str(number).strip()))


def _text(value, maximum: int = 160) -> str | None:
    if isinstance(value, str):
        return value.strip()[:maximum] or None
    return None


def _date(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value, "%d-%m-%Y").date().isoformat()
    except ValueError:
        return None


def _datetime(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value, "%d-%m-%Y %H:%M:%S").replace(
            tzinfo=TIMEZONE
        ).isoformat()
    except ValueError:
        return None


def parse_tracking(number: str, summary: dict, history: dict) -> dict:
    """Extract only non-personal, user-meaningful fields from provider responses."""
    if not valid_tracking_number(number):
        raise BlueExpressError("Invalid tracking number")

    data = summary.get("data") if isinstance(summary, dict) else None
    if not isinstance(summary, dict) or summary.get("status") != "ok" or not isinstance(data, dict):
        raise BlueExpressError("Invalid summary response")
    macro = data.get("macroState", {}).get("data", {})
    info = data.get("generalInfo", {}).get("data", {})
    trace = macro.get("traceMacrostates", {}) if isinstance(macro, dict) else {}
    if not isinstance(trace, dict) or not isinstance(info, dict):
        raise BlueExpressError("Incomplete tracking response")
    if str(trace.get("orderId", "")) != number:
        raise BlueExpressError("Unexpected tracking number")
    stages = trace.get("macrostates", [])
    if not isinstance(stages, list):
        raise BlueExpressError("Invalid stages")
    current = next(
        (
            stage for stage in stages
            if isinstance(stage, dict) and stage.get("isActive") is True
        ),
        None,
    )
    if not current:
        raise BlueExpressError("No active tracking stage")

    hist_data = history.get("data") if isinstance(history, dict) else None
    if not isinstance(history, dict) or history.get("status") != "ok" or not isinstance(hist_data, dict):
        raise BlueExpressError("Invalid history response")
    trace_history = hist_data.get("traceMicrostates", {})
    if not isinstance(trace_history, dict) or str(trace_history.get("orderId")) != number:
        raise BlueExpressError("History tracking number mismatch")
    groups = trace_history.get("microstates", [])
    if not isinstance(groups, list):
        raise BlueExpressError("Invalid movement history")

    events: list[dict] = []
    # Provider may return internal events with null title: do not show or invent them.
    for group in groups[:35]:
        if not isinstance(group, dict):
            continue
        day = _text(group.get("rawDate"), 20)
        if not day:
            continue
        raw_events = group.get("events", [])
        if not isinstance(raw_events, list):
            continue
        for event in raw_events[:40]:
            if not isinstance(event, dict) or not (title := _text(event.get("title"), 140)):
                continue
            time_str = _text(event.get("time"), 12)
            stamp = _datetime(f"{day} {time_str}") if time_str else None
            if not stamp:
                continue
            events.append(
                {
                    "time": stamp,
                    "title": title,
                    "location": _text(event.get("displayLocationName"), 80),
                }
            )
    events.sort(key=lambda event: event["time"], reverse=True)
    events = events[:MAX_HISTORY]

    return {
        "tracking_number": number,
        "status": _text(current.get("title"), 80) or "Estado desconocido",
        "status_code": _text(current.get("id"), 60),
        "promise_date": _date(info.get("promiseDate")),
        "last_movement": _datetime(info.get("lastDateMovement")),
        "event_count": len(events),
        "events": events,
        "source_url": f"{SITE_URL}/enviar/seguimiento?n_seguimiento={number}",
    }


class BlueExpressClient:
    """Async, low-rate, public website data client without account credentials."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def _post(self, path: str, number: str, signed: bool = False) -> dict:
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Origin": SITE_URL,
            "Referer": f"{SITE_URL}/enviar/seguimiento?n_seguimiento={number}",
        }
        if signed:
            payload = json.dumps(
                {
                    "nonce": secrets.token_urlsafe(18),
                    "userAgent": USER_AGENT[:100],
                },
                separators=(",", ":"),
            )
            headers["X-Security-Token"] = base64.b64encode(payload.encode()).decode()

        try:
            async with self._session.post(
                API_URL + path,
                json={"os": number},
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15),
                allow_redirects=False,
            ) as response:
                if response.status != 200:
                    raise BlueExpressError(f"Provider HTTP {response.status}")
                if "json" not in response.headers.get("Content-Type", ""):
                    raise BlueExpressError("Provider returned non-JSON data")
                data = await response.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise BlueExpressError("Provider request failed") from err
        if not isinstance(data, dict):
            raise BlueExpressError("Provider returned malformed data")
        return data

    async def fetch(self, number: str) -> dict:
        if not valid_tracking_number(number):
            raise BlueExpressError("Invalid tracking number")
        summary = await self._post("/tracking", number, signed=True)
        await asyncio.sleep(0.35)
        history = await self._post("/tracking/microestado", number)
        return parse_tracking(number, summary, history)
