from datetime import datetime


def serialize_resource(resource):
    """Convert a Launchpad resource into a JSON-compatible dictionary."""
    data = {}

    for field in resource.lp_attributes:
        value = getattr(resource, field)

        if isinstance(value, datetime):
            value = value.isoformat()

        data[field] = value

    return data


def fetch_one_new_bug(lp):
    """Fetch one New Ubuntu bug and its associated task."""
    project = lp.projects["ubuntu"]

    task = next(iter(project.searchTasks(status="New")))

    bug = lp.load(task.bug_link)

    return {
        "bug": serialize_resource(bug),
        "task": {
            **serialize_resource(task),
            "bug_id": bug.id,
        },
    }

def fetch_bug_and_task(lp, task):
    """Fetch a bug and prepare its associated task for storage."""
    bug = lp.load(task["bug_link"])

    return {
        "bug": serialize_resource(bug),
        "task": {
            **task,
            "bug_id": bug.id,
        },
    }
