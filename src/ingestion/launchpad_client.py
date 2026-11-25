import json
from urllib.request import urlopen
from urllib.parse import urlencode
import time
from urllib.error import HTTPError

def open_with_retry(url, timeout=30, max_attempts=4):
    if max_attempts < 1:
        raise ValueError("max_attempts must be atleast 1")
    for attempt in range(max_attempts):
        try:
            return urlopen(url, timeout=timeout)

        except HTTPError as error:
            if error.code != 503 or attempt == max_attempts - 1:
                raise

            delay = 2 ** attempt

            print(
                f"Launchpad returned HTTP 503. "
                f"Retrying in {delay} seconds "
                f"(attempt {attempt + 2}/{max_attempts})..."
            )

            error.close()
            time.sleep(delay)

def get_launchpad():
    from launchpadlib.launchpad import Launchpad

    return Launchpad.login_anonymously(
        "ubuntu-launchpad-pipeline",
        "production",
    )


def fetch_new_tasks(limit, created_since=None):
    if limit <= 0:
        raise ValueError("limit must be greater than zero")

    params = {
        "status": '"New"',
        "ws.op": "searchTasks",
        "ws.size": 75,
        "memo": 75,
        "ws.start": 0,
    }

    if created_since:
         params["created_since"] = created_since

    url = (
        "https://api.launchpad.net/1.0/ubuntu?"
        + urlencode(params)
    )

    tasks = []

    while url and len(tasks) < limit:
        with open_with_retry(url, timeout=30) as response:
            page = json.load(response)

        remaining = limit - len(tasks)
        tasks.extend(page["entries"][:remaining])

        url = page.get("next_collection_link")

    return tasks
