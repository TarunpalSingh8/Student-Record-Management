"""Schema validation for task payloads (no external dependencies)."""

VALID_STATUSES = ("todo", "in_progress", "done")
ALLOWED_FIELDS = {"title", "description", "status", "priority"}


def validate_task(data, partial=False):
    """Validate a task payload.

    partial=False -> 'title' is required (POST / PUT)
    partial=True  -> every field optional (PATCH)
    Returns a dict of {field: error message}; empty dict means valid.
    """
    if not isinstance(data, dict):
        return {"body": "must be a JSON object"}

    errors = {field: "unknown field" for field in sorted(set(data) - ALLOWED_FIELDS)}

    if "title" in data:
        title = data["title"]
        if not isinstance(title, str) or not title.strip():
            errors["title"] = "must be a non-empty string"
        elif len(title.strip()) > 100:
            errors["title"] = "must be at most 100 characters"
    elif not partial:
        errors["title"] = "is required"

    if "description" in data:
        desc = data["description"]
        if not isinstance(desc, str):
            errors["description"] = "must be a string"
        elif len(desc) > 500:
            errors["description"] = "must be at most 500 characters"

    if "status" in data and data["status"] not in VALID_STATUSES:
        errors["status"] = f"must be one of {list(VALID_STATUSES)}"

    if "priority" in data:
        p = data["priority"]
        # bool is a subclass of int in Python, so exclude it explicitly
        if isinstance(p, bool) or not isinstance(p, int) or not 1 <= p <= 3:
            errors["priority"] = "must be an integer between 1 and 3"

    return errors