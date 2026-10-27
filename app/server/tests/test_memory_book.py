import atexit
import io
import os
import shutil
import sys
import tempfile
import unittest

TEST_DIR = tempfile.mkdtemp(prefix="memory-book-api-test-")
atexit.register(shutil.rmtree, TEST_DIR, True)
os.environ["MEMORY_DATABASE_PATH"] = os.path.join(TEST_DIR, "memory_book.db")
os.environ["MEMORY_UPLOAD_DIR"] = os.path.join(TEST_DIR, "uploads")
os.environ["SECRET_KEY"] = "unit-test-key-not-for-production"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import BookSettings, GiftSettings, Memory, MemoryPhoto

from PIL import Image

png_buffer = io.BytesIO()
Image.new("RGB", (2, 2), (150, 80, 40)).save(png_buffer, format="PNG")
PNG_BYTES = png_buffer.getvalue()
TEST_PASSWORD = "temporary-test-key"


class MemoryBookApiTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["MIN_PASSWORD_LENGTH"] = 4
        os.environ.pop("PUBLIC_DEPLOYMENT", None)
        with app.app_context():
            db.drop_all()
            db.create_all()
        if os.path.isdir(os.environ["MEMORY_UPLOAD_DIR"]):
            shutil.rmtree(os.environ["MEMORY_UPLOAD_DIR"])
        os.makedirs(os.environ["MEMORY_UPLOAD_DIR"])
        self.client = app.test_client()
        status = self.client.get("/api/auth/status").get_json()
        self.csrf = status["csrf_token"]
        response = self.client.post(
            "/api/auth/setup",
            json={"password": TEST_PASSWORD, "confirmation": TEST_PASSWORD},
            headers=self.csrf_headers,
        )
        self.assertEqual(response.status_code, 200)
        self.csrf = self.client.get("/api/auth/status").get_json()["csrf_token"]

    @property
    def csrf_headers(self):
        return {"X-CSRF-Token": self.csrf}

    def test_password_is_hashed_and_memory_apis_require_authentication(self):
        with app.app_context():
            settings = db.session.get(BookSettings, 1)
            self.assertNotEqual(settings.password_hash, TEST_PASSWORD)

        self.client.post("/api/auth/logout", headers=self.csrf_headers)
        self.csrf = self.client.get("/api/auth/status").get_json()["csrf_token"]
        self.assertEqual(self.client.get("/api/memories").status_code, 401)
        self.assertEqual(self.client.get("/api/media/1").status_code, 401)

        response = self.client.post(
            "/api/auth/login",
            json={"password": TEST_PASSWORD},
            headers=self.csrf_headers,
        )
        self.assertEqual(response.status_code, 200)

    def test_memory_validates_uploads_and_deletes_photo_files(self):
        invalid = self.client.post(
            "/api/memories",
            data={
                "title": "ليلة صيف",
                "story": "جلسنا تحت النجوم.",
                "photos": (io.BytesIO(b"not an image"), "invalid.png"),
            },
            headers=self.csrf_headers,
            content_type="multipart/form-data",
        )
        self.assertEqual(invalid.status_code, 400)
        self.assertIn("صورة صالحة", invalid.get_json()["error"])
        with app.app_context():
            self.assertEqual(Memory.query.count(), 0)

        created = self.client.post(
            "/api/memories",
            data={
                "title": "ليلة صيف",
                "story": "جلسنا تحت النجوم.",
                "happened_on": "2025-08-16",
                "photos": (io.BytesIO(PNG_BYTES), "memory.png"),
            },
            headers=self.csrf_headers,
            content_type="multipart/form-data",
        )
        self.assertEqual(created.status_code, 201)
        memory_id = created.get_json()["id"]
        memory = self.client.get("/api/memories").get_json()[0]
        self.assertEqual(memory["title"], "ليلة صيف")
        self.assertEqual(memory["happened_on"], "2025-08-16")
        self.assertEqual(len(memory["photos"]), 1)

        photo_response = self.client.get(memory["photos"][0]["url"])
        self.assertEqual(photo_response.status_code, 200)
        self.assertEqual(photo_response.data, PNG_BYTES)
        self.assertEqual(photo_response.headers["Cache-Control"], "private, no-store")
        photo_response.close()

        with app.app_context():
            photo = db.session.get(MemoryPhoto, memory["photos"][0]["id"])
            photo_path = os.path.join(os.environ["MEMORY_UPLOAD_DIR"], photo.filename)
            self.assertTrue(os.path.isfile(photo_path))
        deleted = self.client.delete(f"/api/memories/{memory_id}", headers=self.csrf_headers)
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(self.client.get("/api/memories").get_json(), [])
        self.assertFalse(os.path.exists(photo_path))

    def test_password_change_invalidates_old_password(self):
        response = self.client.post(
            "/api/auth/password",
            json={
                "current": TEST_PASSWORD,
                "password": "another-test-key",
                "confirmation": "another-test-key",
            },
            headers=self.csrf_headers,
        )
        self.assertEqual(response.status_code, 200)
        self.client.post("/api/auth/logout", headers=self.csrf_headers)
        status = self.client.get("/api/auth/status").get_json()
        self.csrf = status["csrf_token"]
        old_password = self.client.post(
            "/api/auth/login",
            json={"password": TEST_PASSWORD},
            headers=self.csrf_headers,
        )
        self.assertEqual(old_password.status_code, 401)
        status = self.client.get("/api/auth/status").get_json()
        self.csrf = status["csrf_token"]
        new_password = self.client.post(
            "/api/auth/login",
            json={"password": "another-test-key"},
            headers=self.csrf_headers,
        )
        self.assertEqual(new_password.status_code, 200)

    def test_password_minimum_is_configurable_for_public_deployment(self):
        app.config["MIN_PASSWORD_LENGTH"] = 12
        response = self.client.post(
            "/api/auth/password",
            json={
                "current": TEST_PASSWORD,
                "password": "short-pass",
                "confirmation": "short-pass",
            },
            headers=self.csrf_headers,
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("12", response.get_json()["error"])
        status = self.client.get("/api/auth/status").get_json()
        self.assertEqual(status["password_min_length"], 12)
        self.assertTrue(status["public_deployment"] is False)
        os.environ["PUBLIC_DEPLOYMENT"] = "true"
        os.environ["EPHEMERAL_STORAGE"] = "true"
        status = self.client.get("/api/auth/status").get_json()
        self.assertTrue(status["public_deployment"])
        self.assertTrue(status["ephemeral_storage"])

    def test_gift_password_grants_read_only_memory_and_photo_access(self):
        created = self.client.post(
            "/api/memories",
            data={
                "title": "ليلة صيف",
                "story": "جلسنا تحت النجوم.",
                "photos": (io.BytesIO(PNG_BYTES), "memory.png"),
            },
            headers=self.csrf_headers,
            content_type="multipart/form-data",
        )
        self.assertEqual(created.status_code, 201)
        same_as_owner = self.client.post(
            "/api/gift/settings",
            json={"password": TEST_PASSWORD, "confirmation": TEST_PASSWORD},
            headers=self.csrf_headers,
        )
        self.assertEqual(same_as_owner.status_code, 400)
        settings = self.client.post(
            "/api/gift/settings",
            json={"password": "gift-pass", "confirmation": "gift-pass"},
            headers=self.csrf_headers,
        )
        self.assertEqual(settings.status_code, 200)
        self.assertTrue(settings.get_json()["enabled"])
        with app.app_context():
            gift_settings = db.session.get(GiftSettings, 1)
            self.assertNotEqual(gift_settings.password_hash, "gift-pass")

        self.client.post("/api/auth/logout", headers=self.csrf_headers)
        status = self.client.get("/api/gift/status").get_json()
        self.assertTrue(status["enabled"])
        self.assertFalse(status["authenticated"])
        self.assertEqual(self.client.get("/api/gift/memories").status_code, 401)
        self.assertEqual(
            self.client.post(
                "/api/gift/login",
                json={"password": "wrong"},
                headers={"X-CSRF-Token": status["csrf_token"]},
            ).status_code,
            401,
        )

        response = self.client.post(
            "/api/gift/login",
            json={"password": "gift-pass"},
            headers={"X-CSRF-Token": status["csrf_token"]},
        )
        self.assertEqual(response.status_code, 200)
        memories = self.client.get("/api/gift/memories")
        self.assertEqual(memories.status_code, 200)
        memory = memories.get_json()[0]
        self.assertEqual(memory["title"], "ليلة صيف")
        gift_photo = self.client.get(memory["photos"][0]["url"])
        self.assertEqual(gift_photo.data, PNG_BYTES)
        gift_photo.close()
        self.assertEqual(
            self.client.post(
                "/api/memories",
                data={"title": "تعديل", "story": "لا يسمح"},
                headers={"X-CSRF-Token": self.client.get("/api/gift/status").get_json()["csrf_token"]},
            ).status_code,
            401,
        )
        self.assertEqual(self.client.get("/api/gift/settings").status_code, 401)

        owner = app.test_client()
        owner_status = owner.get("/api/auth/status").get_json()
        owner_login = owner.post(
            "/api/auth/login",
            json={"password": TEST_PASSWORD},
            headers={"X-CSRF-Token": owner_status["csrf_token"]},
        )
        self.assertEqual(owner_login.status_code, 200)
        owner_csrf = owner.get("/api/auth/status").get_json()["csrf_token"]
        rotated = owner.post(
            "/api/gift/settings",
            json={"password": "new-gift-pass", "confirmation": "new-gift-pass"},
            headers={"X-CSRF-Token": owner_csrf},
        )
        self.assertEqual(rotated.status_code, 200)
        self.assertEqual(self.client.get("/api/gift/memories").status_code, 401)
        self.assertEqual(self.client.get(memory["photos"][0]["url"]).status_code, 401)

    def test_login_is_throttled_after_five_incorrect_passwords(self):
        self.client.post("/api/auth/logout", headers=self.csrf_headers)
        statuses = []
        for _ in range(5):
            status = self.client.get("/api/auth/status").get_json()
            self.csrf = status["csrf_token"]
            response = self.client.post(
                "/api/auth/login",
                json={"password": "incorrect"},
                headers=self.csrf_headers,
            )
            statuses.append(response.status_code)
        self.assertEqual(statuses, [401, 401, 401, 401, 429])
        blocked = self.client.post(
            "/api/auth/login",
            json={"password": TEST_PASSWORD},
            headers=self.csrf_headers,
        )
        self.assertEqual(blocked.status_code, 429)

    def tearDown(self):
        with app.app_context():
            db.session.remove()


if __name__ == "__main__":
    unittest.main()
