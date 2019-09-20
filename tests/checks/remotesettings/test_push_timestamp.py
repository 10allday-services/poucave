import json
from contextlib import asynccontextmanager
from unittest import mock
from checks.remotesettings.push_timestamp import run, get_push_timestamp, BROADCAST_ID

from tests.utils import patch_async


async def test_positive(mock_responses):
    url = "http://server.local/v1/buckets/monitor/collections/changes/records"
    mock_responses.head(url, status=200, headers={"ETag": "abc"})

    module = "checks.remotesettings.push_timestamp"
    with patch_async(f"{module}.get_push_timestamp", return_value="abc"):
        status, data = await run(
            remotesettings_server="http://server.local/v1", push_server=""
        )

    assert status is True
    assert data == {"remotesettings": "abc", "push": "abc"}


async def test_negative(mock_responses):
    url = "http://server.local/v1/buckets/monitor/collections/changes/records"
    mock_responses.head(url, status=200, headers={"ETag": "abc"})

    module = "checks.remotesettings.push_timestamp"
    with patch_async(f"{module}.get_push_timestamp", return_value="def"):
        status, data = await run(
            remotesettings_server="http://server.local/v1", push_server=""
        )

    assert status is False
    assert data == {"remotesettings": "abc", "push": "def"}


async def test_get_push_timestamp():
    class FakeConnection:
        async def send(self, value):
            self.sent = value

        async def recv(self):
            return json.dumps({"broadcasts": {BROADCAST_ID: '"42"'}})

    fake_connection = FakeConnection()

    @asynccontextmanager
    async def fake_connect(url):
        yield fake_connection

    with mock.patch("checks.remotesettings.push_timestamp.websockets") as mocked:
        mocked.connect = fake_connect

        result = await get_push_timestamp("ws://fake")

    assert json.loads(fake_connection.sent) == {
        "messageType": "hello",
        "broadcasts": {BROADCAST_ID: "v0"},
        "use_webpush": True,
    }
    assert result == "42"
