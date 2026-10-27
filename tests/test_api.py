"""Provider unit tests: synthetic data only, no real shipments or recipients."""

import asyncio
import importlib.util
from pathlib import Path
import unittest


MODULE = Path(__file__).resolve().parents[1] / "custom_components" / "blueexpress_tracking" / "api.py"
spec = importlib.util.spec_from_file_location("blueexpress_api_standalone", MODULE)
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)


def responses(number="12345678"):
    summary = {
        "status": "ok",
        "data": {
            "macroState": {
                "data": {
                    "traceMacrostates": {
                        "orderId": number,
                        "macrostates": [
                            {"id": "IN_PREPARATION", "title": "En preparación", "isActive": False},
                            {"id": "CUSTOMS", "title": "Aduana", "isActive": True},
                        ],
                    }
                }
            },
            "generalInfo": {
                "data": {
                    "promiseDate": "30-10-2026",
                    "lastDateMovement": "27-10-2026 05:30:14",
                    # The provider sends PII; it must never leave parse_tracking:
                    "receiverAddress": "DO NOT LEAK ADDRESS",
                    "receiverEmail": "private@example.invalid",
                    "receiverPhone": "DO NOT LEAK PHONE",
                }
            },
        },
    }
    history = {
        "status": "ok",
        "data": {
            "traceMicrostates": {
                "orderId": number,
                "microstates": [
                    {"rawDate": "27-10-2026", "events": [
                        {"time": "05:30:14", "title": "Liberado por Aduanas", "eventCode": "LI",
                         "displayLocationName": "Santiago", "receiverName": "DO NOT LEAK NAME"},
                        {"time": "05:31:09", "title": None, "eventCode": "EP"},
                    ]},
                    {"rawDate": "23-10-2026", "events": [
                        {"time": "06:00:59", "title": "Viaje internacional",
                         "displayLocationName": "En camino a Chile"}
                    ]},
                ],
            },
        },
    }
    return summary, history


class TestBlueExpressParser(unittest.TestCase):
    def test_valid_numbers(self):
        self.assertTrue(api.valid_tracking_number("12345678"))
        self.assertTrue(api.valid_tracking_number("1234567890"))
        self.assertFalse(api.valid_tracking_number("1234567"))
        self.assertFalse(api.valid_tracking_number("x123456789"))
        self.assertFalse(api.valid_tracking_number("12345678901"))

    def test_summary_and_meaningful_timeline(self):
        summary, history = responses()
        result = api.parse_tracking("12345678", summary, history)
        self.assertEqual(result["status"], "Aduana")
        self.assertEqual(result["promise_date"], "2026-10-30")
        self.assertIn("05:30:14", result["last_movement"])
        self.assertEqual(result["event_count"], 2)
        self.assertEqual(result["events"][0]["title"], "Liberado por Aduanas")
        self.assertEqual(result["events"][1]["title"], "Viaje internacional")
        self.assertNotIn("EP", str(result))
        self.assertNotIn("DO NOT LEAK", str(result))
        self.assertNotIn("private@", str(result))
        self.assertNotIn("receiver", str(result))

    def test_invalid_response_rejected(self):
        summary, history = responses()
        summary["data"]["macroState"]["data"]["traceMacrostates"]["orderId"] = "87654321"
        with self.assertRaises(api.BlueExpressError):
            api.parse_tracking("12345678", summary, history)

    def test_history_mismatch_rejected(self):
        summary, history = responses()
        history["data"]["traceMicrostates"]["orderId"] = "87654321"
        with self.assertRaises(api.BlueExpressError):
            api.parse_tracking("12345678", summary, history)

    def test_missing_active_stage_rejected(self):
        summary, history = responses()
        for stage in summary["data"]["macroState"]["data"]["traceMacrostates"]["macrostates"]:
            stage["isActive"] = False
        with self.assertRaises(api.BlueExpressError):
            api.parse_tracking("12345678", summary, history)


class FakeResponse:
    status = 200
    headers = {"Content-Type": "application/json"}

    def __init__(self, data):
        self._data = data

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def json(self):
        return self._data


class FakeSession:
    def __init__(self, fake_responses):
        self.responses = iter(fake_responses)
        self.calls = []

    def post(self, path, **kwargs):
        self.calls.append((path, kwargs))
        return FakeResponse(next(self.responses))


class TestClient(unittest.IsolatedAsyncioTestCase):
    async def test_public_endpoints_and_security_nonce(self):
        summary, history = responses()
        client_session = FakeSession([summary, history])
        client = api.BlueExpressClient(client_session)
        result = await client.fetch("12345678")
        self.assertEqual(result["status"], "Aduana")
        self.assertEqual(len(client_session.calls), 2)
        first = client_session.calls[0]
        second = client_session.calls[1]
        self.assertTrue(first[0].endswith("/tracking"))
        self.assertTrue(second[0].endswith("/tracking/microestado"))
        self.assertEqual(first[1]["json"], {"os": "12345678"})
        self.assertIn("X-Security-Token", first[1]["headers"])
        self.assertNotIn("X-Security-Token", second[1]["headers"])
        self.assertFalse(first[1]["allow_redirects"])

    async def test_bad_tracking_has_no_network_calls(self):
        client_session = FakeSession([])
        with self.assertRaises(api.BlueExpressError):
            await api.BlueExpressClient(client_session).fetch("invalid")
        self.assertEqual(len(client_session.calls), 0)


if __name__ == "__main__":
    unittest.main()
