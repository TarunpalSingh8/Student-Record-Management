"""Task Manager REST API - Flask + SQLite.

Run:  python app.py
Auth: send header  X-API-Key: <your key>  (set API_KEY env var; default 'dev-secret-key')
"""
import hmac
import os
from functools import wraps

from flask import Flask, jsonify, request

import db
from validation import ALLOWED_FIELDS, validate_task


def error(message, status, details=None):
    body = {"error": message}
    if details:
        body["details"] = details
    return jsonify(body), status


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        DATABASE=os.environ.get("DATABASE", "tasks.db"),
        API_KEY=os.environ.get("API_KEY", "dev-secret-key"),
    )
    if config:
        app.config.update(config)
    db.init_app(app)

    # ---------- authentication ----------
    def require_api_key(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            supplied = request.headers.get("X-API-Key", "").encode()
            expected = app.config["API_KEY"].encode()
            if not hmac.compare_digest(supplied, expected):  # constant-time compare
                return error("Unauthorized: missing or invalid X-API-Key header", 401)
            return view(*args, **kwargs)
        return wrapper

    # ---------- helpers ----------
    def row_to_dict(row):
        return dict(row)

    def get_task_or_none(task_id):
        return db.get_db().execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()

    def read_json():
        data = request.get_json(silent=True)
        if data is None:
            return None, error("Request body must be valid JSON", 400)
        return data, None

    # ---------- public routes ----------
    @app.get("/")
    def index():
        return jsonify({
            "name": "Task Manager API",
            "version": "1.0",
            "auth": "Send header X-API-Key on all /api/* requests",
            "endpoints": {
                "GET /health": "Health check (public)",
                "GET /api/tasks": "List tasks (?status=, ?page=, ?per_page=)",
                "POST /api/tasks": "Create a task",
                "GET /api/tasks/<id>": "Get one task",
                "PUT /api/tasks/<id>": "Replace a task",
                "PATCH /api/tasks/<id>": "Update some fields",
                "DELETE /api/tasks/<id>": "Delete a task",
            },
        })

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    # ---------- CRUD ----------
    @app.get("/api/tasks")
    @require_api_key
    def list_tasks():
        status = request.args.get("status")
        try:
            page = int(request.args.get("page", 1))
            per_page = int(request.args.get("per_page", 10))
        except ValueError:
            return error("page and per_page must be integers", 400)
        if page < 1 or not 1 <= per_page <= 100:
            return error("page must be >= 1 and per_page between 1 and 100", 400)

        where, params = "", []
        if status:
            where, params = "WHERE status = ?", [status]
        conn = db.get_db()
        total = conn.execute(f"SELECT COUNT(*) FROM tasks {where}", params).fetchone()[0]
        rows = conn.execute(
            f"SELECT * FROM tasks {where} ORDER BY id LIMIT ? OFFSET ?",
            params + [per_page, (page - 1) * per_page],
        ).fetchall()
        return jsonify({
            "data": [row_to_dict(r) for r in rows],
            "page": page, "per_page": per_page, "total": total,
        })

    @app.post("/api/tasks")
    @require_api_key
    def create_task():
        data, err = read_json()
        if err:
            return err
        problems = validate_task(data)
        if problems:
            return error("Validation failed", 422, problems)

        conn = db.get_db()
        cur = conn.execute(
            "INSERT INTO tasks (title, description, status, priority) VALUES (?, ?, ?, ?)",
            (data["title"].strip(), data.get("description", ""),
             data.get("status", "todo"), data.get("priority", 2)),
        )
        conn.commit()
        task = row_to_dict(get_task_or_none(cur.lastrowid))
        resp = jsonify(task)
        resp.status_code = 201
        resp.headers["Location"] = f"/api/tasks/{task['id']}"
        return resp

    @app.get("/api/tasks/<int:task_id>")
    @require_api_key
    def get_task(task_id):
        task = get_task_or_none(task_id)
        if task is None:
            return error(f"Task {task_id} not found", 404)
        return jsonify(row_to_dict(task))

    def update_task(task_id, partial):
        if get_task_or_none(task_id) is None:
            return error(f"Task {task_id} not found", 404)
        data, err = read_json()
        if err:
            return err
        problems = validate_task(data, partial=partial)
        if problems:
            return error("Validation failed", 422, problems)

        if not partial:  # PUT replaces the whole resource: apply defaults
            data = {"description": "", "status": "todo", "priority": 2, **data}
        fields = [f for f in data if f in ALLOWED_FIELDS]
        if not fields:
            return error("No fields to update", 400)
        values = [data[f].strip() if f == "title" else data[f] for f in fields]
        assignments = ", ".join(f"{f} = ?" for f in fields)  # fields come from an allow-list

        conn = db.get_db()
        conn.execute(
            f"UPDATE tasks SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            values + [task_id],
        )
        conn.commit()
        return jsonify(row_to_dict(get_task_or_none(task_id)))

    @app.put("/api/tasks/<int:task_id>")
    @require_api_key
    def replace_task(task_id):
        return update_task(task_id, partial=False)

    @app.patch("/api/tasks/<int:task_id>")
    @require_api_key
    def patch_task(task_id):
        return update_task(task_id, partial=True)

    @app.delete("/api/tasks/<int:task_id>")
    @require_api_key
    def delete_task(task_id):
        if get_task_or_none(task_id) is None:
            return error(f"Task {task_id} not found", 404)
        conn = db.get_db()
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        return "", 204

    # ---------- JSON error handlers ----------
    @app.errorhandler(404)
    def not_found(_):
        return error("Resource not found", 404)

    @app.errorhandler(405)
    def method_not_allowed(_):
        return error("Method not allowed", 405)

    @app.errorhandler(500)
    def server_error(_):
        return error("Internal server error", 500)

    return app


if __name__ == "__main__":
    create_app().run(debug=True)