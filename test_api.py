"""API endpoint tests. Run from the project root:  python -m unittest discover -s tests -v"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app  # noqa: E402

HEADERS = {"X-API-Key": "test-key"}


class TaskApiTests(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.app = create_app({"DATABASE": self.db_path, "API_KEY": "test-key", "TESTING": True})
        self.client = self.app.test_client()

    def tearDown(self):
        os.remove(self.db_path)

    def create(self, **payload):
        payload.setdefault("title", "Sample task")
        return self.client.post("/api/tasks", json=payload, headers=HEADERS)

    # ----- public + auth -----
    def test_health_is_public(self):
        self.assertEqual(self.client.get("/health").status_code, 200)

    def test_missing_api_key_rejected(self):
        self.assertEqual(self.client.get("/api/tasks").status_code, 401)

    def test_wrong_api_key_rejected(self):
        r = self.client.get("/api/tasks", headers={"X-API-Key": "nope"})
        self.assertEqual(r.status_code, 401)

    # ----- create + validation -----
    def test_create_task(self):
        r = self.create(title="  Learn Flask ", priority=1)
        self.assertEqual(r.status_code, 201)
        body = r.get_json()
        self.assertEqual(body["title"], "Learn Flask")
        self.assertEqual(body["status"], "todo")
        self.assertEqual(r.headers["Location"], f"/api/tasks/{body['id']}")

    def test_create_requires_title(self):
        r = self.client.post("/api/tasks", json={"priority": 1}, headers=HEADERS)
        self.assertEqual(r.status_code, 422)
        self.assertIn("title", r.get_json()["details"])

    def test_create_rejects_bad_values(self):
        for bad in ({"status": "finished"}, {"priority": 9}, {"priority": True},
                    {"priority": "high"}, {"title": ""}, {"extra": 1}):
            with self.subTest(bad=bad):
                self.assertEqual(self.create(**bad).status_code, 422)

    def test_invalid_json_body(self):
        r = self.client.post("/api/tasks", data="not json", headers=HEADERS,
                             content_type="application/json")
        self.assertEqual(r.status_code, 400)

    # ----- read -----
    def test_get_task_and_404(self):
        task_id = self.create().get_json()["id"]
        self.assertEqual(self.client.get(f"/api/tasks/{task_id}", headers=HEADERS).status_code, 200)
        self.assertEqual(self.client.get("/api/tasks/999", headers=HEADERS).status_code, 404)

    def test_list_filter_and_pagination(self):
        for i in range(5):
            self.create(title=f"Task {i}", status="done" if i % 2 == 0 else "todo")
        r = self.client.get("/api/tasks?status=done", headers=HEADERS).get_json()
        self.assertEqual(r["total"], 3)
        r = self.client.get("/api/tasks?per_page=2&page=2", headers=HEADERS).get_json()
        self.assertEqual(len(r["data"]), 2)
        self.assertEqual(r["total"], 5)

    def test_invalid_pagination(self):
        for q in ("page=0", "per_page=1000", "page=abc"):
            with self.subTest(q=q):
                self.assertEqual(self.client.get(f"/api/tasks?{q}", headers=HEADERS).status_code, 400)

    # ----- update -----
    def test_patch_updates_only_given_fields(self):
        task = self.create(title="Old", priority=3).get_json()
        r = self.client.patch(f"/api/tasks/{task['id']}", json={"status": "done"}, headers=HEADERS)
        body = r.get_json()
        self.assertEqual((body["status"], body["title"], body["priority"]), ("done", "Old", 3))

    def test_put_replaces_task(self):
        task = self.create(title="Old", priority=3).get_json()
        r = self.client.put(f"/api/tasks/{task['id']}", json={"title": "New"}, headers=HEADERS)
        body = r.get_json()
        self.assertEqual((body["title"], body["priority"]), ("New", 2))  # priority reset to default

    def test_put_without_title_fails(self):
        task_id = self.create().get_json()["id"]
        r = self.client.put(f"/api/tasks/{task_id}", json={"status": "done"}, headers=HEADERS)
        self.assertEqual(r.status_code, 422)

    def test_update_missing_task(self):
        r = self.client.patch("/api/tasks/999", json={"status": "done"}, headers=HEADERS)
        self.assertEqual(r.status_code, 404)

    # ----- delete -----
    def test_delete_task(self):
        task_id = self.create().get_json()["id"]
        self.assertEqual(self.client.delete(f"/api/tasks/{task_id}", headers=HEADERS).status_code, 204)
        self.assertEqual(self.client.get(f"/api/tasks/{task_id}", headers=HEADERS).status_code, 404)

    def test_method_not_allowed_is_json(self):
        r = self.client.post("/health")
        self.assertEqual(r.status_code, 405)
        self.assertIn("error", r.get_json())


if __name__ == "__main__":
    unittest.main()