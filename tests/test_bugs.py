from datetime import datetime, timezone
from types import SimpleNamespace

from src.ingestion.bugs import serialize_resource


def test_serialize_resource_converts_datetime():
    created = datetime(2025, 1, 10, 12, 30, tzinfo=timezone.utc)

    resource = SimpleNamespace(
        lp_attributes=["id", "title", "date_created"],
        id=123,
        title="Test bug",
        date_created=created,
    )

    result = serialize_resource(resource)

    assert result["id"] == 123
    assert result["title"] == "Test bug"
    assert result["date_created"] == created.isoformat()
    assert isinstance(result["date_created"], str)


from src.ingestion.bugs import fetch_bug_and_task


def test_fetch_bug_and_task_loads_and_prepares_records():
    bug = SimpleNamespace(
        lp_attributes=["id", "title"],
        id=123,
        title="Test bug",
    )

    task = {
        "bug_link": "https://api.launchpad.net/1.0/ubuntu/+bug/123",
        "status": "New",
        "importance": "High",
    }

    class FakeLaunchpad:
        def __init__(self):
            self.loaded_url = None

        def load(self, url):
            self.loaded_url = url
            return bug

    lp = FakeLaunchpad()

    result = fetch_bug_and_task(lp, task)

    assert lp.loaded_url == task["bug_link"]
    assert result["bug"]["id"] == 123
    assert result["bug"]["title"] == "Test bug"
    assert result["task"]["bug_id"] == 123
    assert result["task"]["status"] == "New"
    assert result["task"]["importance"] == "High"


from src.ingestion.bugs import fetch_one_new_bug


def test_fetch_one_new_bug_discovers_and_loads_bug():
    bug = SimpleNamespace(
        lp_attributes=["id", "title"],
        id=456,
        title="New Ubuntu bug",
    )

    task = SimpleNamespace(
        lp_attributes=["bug_link", "status", "importance"],
        bug_link="https://api.launchpad.net/1.0/ubuntu/+bug/456",
        status="New",
        importance="High",
    )

    class FakeProject:
        def searchTasks(self, status):
            assert status == "New"
            return iter([task])

    class FakeLaunchpad:
        projects = {"ubuntu": FakeProject()}

        def __init__(self):
            self.loaded_url = None

        def load(self, url):
            self.loaded_url = url
            return bug

    lp = FakeLaunchpad()

    result = fetch_one_new_bug(lp)

    assert lp.loaded_url == task.bug_link
    assert result["bug"]["id"] == 456
    assert result["bug"]["title"] == "New Ubuntu bug"
    assert result["task"]["bug_id"] == 456
    assert result["task"]["status"] == "New"
    assert result["task"]["importance"] == "High"


def test_fetch_one_new_bug_returns_none_when_no_tasks():
    class FakeProject:
        def searchTasks(self, status):
            return iter([])

    class FakeLaunchpad:
        projects = {"ubuntu": FakeProject()}

    result = fetch_one_new_bug(FakeLaunchpad())

    assert result is None
