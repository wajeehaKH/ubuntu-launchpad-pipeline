from urllib.error import HTTPError

from src.ingestion.launchpad_client import open_with_retry
from src.ingestion.launchpad_client import fetch_new_tasks
from urllib.parse import parse_qs, urlparse

import pytest

def test_open_with_retry_retries_after_503(monkeypatch):
    attempts = []
    delays = []

    response = object()

    def fake_urlopen(url, timeout):
        attempts.append(url)

        if len(attempts) == 1:
            raise HTTPError(
                url, 503, "Service Unavailable", None, None
            )

        return response

    monkeypatch.setattr(
        "src.ingestion.launchpad_client.urlopen",
        fake_urlopen,
    )

    monkeypatch.setattr(
        "src.ingestion.launchpad_client.time.sleep",
        lambda delay: delays.append(delay),
    )

    result = open_with_retry("https://example.com", max_attempts=4)

    assert result is response
    assert len(attempts) == 2
    assert delays == [1]


def test_open_with_retry_uses_exponential_backoff(monkeypatch):
    attempts = []
    delays = []

    def fake_urlopen(url, timeout):
        attempts.append(url)
        raise HTTPError(
            url, 503, "Service Unavailable", None, None
        )

    monkeypatch.setattr(
        "src.ingestion.launchpad_client.urlopen",
        fake_urlopen,
    )

    monkeypatch.setattr(
        "src.ingestion.launchpad_client.time.sleep",
        lambda delay: delays.append(delay),
    )

    with pytest.raises(HTTPError) as exc_info:
        open_with_retry(
            "https://example.com",
            max_attempts=4,
        )

    assert exc_info.value.code == 503
    assert len(attempts) == 4
    assert delays == [1, 2, 4]


def test_open_with_retry_does_not_retry_404(monkeypatch):
    attempts = []

    def fake_urlopen(url, timeout):
        attempts.append(url)
        raise HTTPError(
            url, 404, "Not Found", None, None
        )

    monkeypatch.setattr(
        "src.ingestion.launchpad_client.urlopen",
        fake_urlopen,
    )

    with pytest.raises(HTTPError) as exc_info:
        open_with_retry(
            "https://example.com",
            max_attempts=4,
        )

    assert exc_info.value.code == 404
    assert len(attempts) == 1


def test_fetch_new_tasks_follows_pagination_and_respects_limit(monkeypatch):
    responses = [
        {
            "entries": [
                {"id": 1},
                {"id": 2},
            ],
            "next_collection_link": "https://example.com/page2",
        },
        {
            "entries": [
                {"id": 3},
                {"id": 4},
            ],
            "next_collection_link": None,
        },
    ]

    requested_urls = []

    class FakeResponse:
        def __init__(self, page):
            self.page = page

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            pass

    def fake_open(url, timeout):
        requested_urls.append(url)
        return FakeResponse(responses[len(requested_urls) - 1])

    monkeypatch.setattr(
        "src.ingestion.launchpad_client.open_with_retry",
        fake_open,
    )

    monkeypatch.setattr(
        "src.ingestion.launchpad_client.json.load",
        lambda response: response.page,
    )

    tasks = fetch_new_tasks(limit=3)

    assert [task["id"] for task in tasks] == [1, 2, 3]
    assert len(requested_urls) == 2
    assert requested_urls[1] == "https://example.com/page2"


def test_fetch_new_tasks_includes_created_since(monkeypatch):
    requested_urls = []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            pass

    def fake_open(url, timeout):
        requested_urls.append(url)
        return FakeResponse()

    monkeypatch.setattr(
        "src.ingestion.launchpad_client.open_with_retry",
        fake_open,
    )

    monkeypatch.setattr(
        "src.ingestion.launchpad_client.json.load",
        lambda response: {
            "entries": [{"id": 1}],
            "next_collection_link": None,
        },
    )

    fetch_new_tasks(
        limit=10,
        created_since="2025-01-01T00:00:00Z",
    )

    parsed_url = urlparse(requested_urls[0])
    params = parse_qs(parsed_url.query)

    assert params["created_since"] == ["2025-01-01T00:00:00Z"]
    assert params["status"] == ['"New"']
    assert params["ws.op"] == ["searchTasks"]
    assert params["ws.size"] == ["75"]


@pytest.mark.parametrize("limit", [0, -1, -10])
def test_fetch_new_tasks_rejects_invalid_limit(limit):
    with pytest.raises(
        ValueError,
        match="limit must be greater than zero",
    ):
        fetch_new_tasks(limit=limit)
