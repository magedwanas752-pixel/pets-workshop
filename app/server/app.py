from __future__ import annotations

import hashlib
import hmac
import io
import os
import secrets
import warnings
from datetime import date, datetime, timedelta

from flask import Flask, abort, jsonify, request, send_from_directory, session
from PIL import Image, UnidentifiedImageError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix

from models import BookSettings, GiftSettings, LoginAttempt, Memory, MemoryPhoto, db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.umask(0o077)
MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_PHOTOS = 8
ALLOWED_IMAGE_FORMATS = {
    "JPEG": ("jpg", "image/jpeg"),
    "PNG": ("png", "image/png"),
    "WEBP": ("webp", "image/webp"),
    "GIF": ("gif", "image/gif"),
}


def _secret_key(instance_path: str) -> str:
    configured = os.environ.get("SECRET_KEY")
    if configured:
        return configured

    key_path = os.path.join(instance_path, "session.key")
    os.makedirs(instance_path, exist_ok=True)
    try:
        descriptor = os.open(key_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(descriptor, "w", encoding="ascii") as key_file:
            key_file.write(secrets.token_hex(32))
    except FileExistsError:
        pass
    with open(key_path, "r", encoding="ascii") as key_file:
        return key_file.read().strip()


app = Flask(__name__, instance_path=os.path.join(BASE_DIR, "instance"))
os.makedirs(app.instance_path, mode=0o700, exist_ok=True)
os.chmod(app.instance_path, 0o700)
app.config.update(
    SECRET_KEY=_secret_key(app.instance_path),
    SQLALCHEMY_DATABASE_URI="sqlite:///" + os.environ.get(
        "MEMORY_DATABASE_PATH",
        os.environ.get("DATABASE_PATH", os.path.join(app.instance_path, "memory_book.db")),
    ),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    MAX_CONTENT_LENGTH=84 * 1024 * 1024,
    SESSION_COOKIE_NAME="memory_book_session",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "").lower() == "true",
    PERMANENT_SESSION_LIFETIME=timedelta(days=14),
    MIN_PASSWORD_LENGTH=int(os.environ.get("MIN_PASSWORD_LENGTH", "4")),
)
UPLOAD_DIR = os.environ.get("MEMORY_UPLOAD_DIR", os.path.join(app.instance_path, "uploads"))
os.makedirs(UPLOAD_DIR, mode=0o700, exist_ok=True)
os.chmod(UPLOAD_DIR, 0o700)

db.init_app(app)
with app.app_context():
    db.create_all()

if os.environ.get("TRUST_PROXY", "").lower() == "true":
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    if "Cache-Control" not in response.headers:
        response.headers["Cache-Control"] = "no-store"
    return response


@app.errorhandler(413)
def request_too_large(_error):
    return jsonify({"error": "حجم الطلب أكبر من الحد المسموح به."}), 413


def _error(message: str, status: int):
    return jsonify({"error": message}), status


def _json_payload():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def _csrf_token() -> str:
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


def _check_csrf() -> bool:
    expected = session.get("csrf_token")
    provided = request.headers.get("X-CSRF-Token", "")
    return bool(expected and provided and hmac.compare_digest(expected, provided))


def _authenticated():
    if not session.get("book_unlocked"):
        return _error("افتحي الدفتر بكلمة السر أولاً.", 401)
    if not _check_csrf():
        return _error("انتهت صلاحية الجلسة. حدّثي الصفحة وحاولي مرة أخرى.", 403)
    return None


def _gift_access_allowed() -> bool:
    settings = db.session.get(GiftSettings, 1)
    return bool(
        settings
        and session.get("gift_session_key")
        and hmac.compare_digest(session["gift_session_key"], settings.session_key)
    )


def _rate_limit_key(scope: str = "owner") -> str:
    return hmac.new(
        app.config["SECRET_KEY"].encode("utf-8"),
        f"{scope}:{request.remote_addr or 'unknown'}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


@app.get("/api/auth/status")
def auth_status():
    return jsonify({
        "configured": db.session.get(BookSettings, 1) is not None,
        "authenticated": bool(session.get("book_unlocked")),
        "csrf_token": _csrf_token(),
        "password_min_length": app.config["MIN_PASSWORD_LENGTH"],
        "public_deployment": os.environ.get("PUBLIC_DEPLOYMENT", "").lower() == "true",
        "ephemeral_storage": os.environ.get("EPHEMERAL_STORAGE", "").lower() == "true",
    })


@app.get("/api/health")
def health_check():
    return jsonify({"status": "ok"})


@app.get("/api/gift/status")
def gift_status():
    settings = db.session.get(GiftSettings, 1)
    return jsonify({
        "enabled": settings is not None,
        "authenticated": bool(session.get("book_unlocked") or _gift_access_allowed()),
        "csrf_token": _csrf_token(),
        "password_min_length": app.config["MIN_PASSWORD_LENGTH"],
    })


@app.post("/api/gift/login")
def gift_login():
    if not _check_csrf():
        return _error("حدّثي الصفحة ثم حاولي مرة أخرى.", 403)
    settings = db.session.get(GiftSettings, 1)
    if settings is None:
        return _error("لم تُجهّز هذه الهدية للمشاركة بعد.", 404)

    key = _rate_limit_key("gift")
    now = datetime.utcnow()
    attempt = db.session.get(LoginAttempt, key)
    if attempt and attempt.locked_until and attempt.locked_until > now:
        response, status = _error("محاولات كثيرة. انتظري قليلاً ثم حاولي مجدداً.", 429)
        response.headers["Retry-After"] = str(max(1, int((attempt.locked_until - now).total_seconds())))
        return response, status

    password = _json_payload().get("password", "")
    if not isinstance(password, str) or len(password) > 128 or not check_password_hash(
        settings.password_hash, password
    ):
        if attempt is None:
            attempt = LoginAttempt(key=key, failures=0)
            db.session.add(attempt)
        if attempt.locked_until and attempt.locked_until <= now:
            attempt.failures = 0
            attempt.locked_until = None
        attempt.failures += 1
        if attempt.failures >= 5:
            attempt.failures = 0
            attempt.locked_until = now + timedelta(minutes=15)
        db.session.commit()
        if attempt.locked_until:
            response, status = _error("محاولات كثيرة. انتظري 15 دقيقة ثم حاولي مجدداً.", 429)
            response.headers["Retry-After"] = "900"
            return response, status
        return _error("كلمة السر غير صحيحة.", 401)

    if attempt:
        db.session.delete(attempt)
        db.session.commit()
    session.clear()
    session["gift_session_key"] = settings.session_key
    session.permanent = True
    _csrf_token()
    return jsonify({"authenticated": True})


@app.get("/api/gift/settings")
def gift_settings():
    auth_error = _authenticated()
    if auth_error:
        return auth_error
    return jsonify({"enabled": db.session.get(GiftSettings, 1) is not None})


@app.post("/api/gift/settings")
def update_gift_settings():
    auth_error = _authenticated()
    if auth_error:
        return auth_error
    data = _json_payload()
    password = data.get("password", "")
    confirmation = data.get("confirmation", "")
    if (
        not isinstance(password, str)
        or not app.config["MIN_PASSWORD_LENGTH"] <= len(password) <= 128
    ):
        return _error(
            f"اختاري كلمة سر من {app.config['MIN_PASSWORD_LENGTH']} إلى 128 خانة.",
            400,
        )
    if password != confirmation:
        return _error("كلمتا السر غير متطابقتين.", 400)
    owner_settings = db.session.get(BookSettings, 1)
    if owner_settings and check_password_hash(owner_settings.password_hash, password):
        return _error("يجب أن تختلف كلمة سر الهدية عن كلمة سر الدفتر.", 400)

    settings = db.session.get(GiftSettings, 1)
    if settings is None:
        settings = GiftSettings(id=1, password_hash="")
        db.session.add(settings)
    settings.password_hash = generate_password_hash(password, method="pbkdf2:sha256:600000")
    settings.session_key = secrets.token_hex(32)
    db.session.commit()
    return jsonify({"enabled": True})


@app.post("/api/auth/setup")
def setup_password():
    if not _check_csrf():
        return _error("حدّثي الصفحة ثم حاولي مرة أخرى.", 403)
    if db.session.get(BookSettings, 1) is not None:
        return _error("تم إعداد كلمة السر بالفعل.", 409)

    data = _json_payload()
    password = data.get("password", "")
    confirmation = data.get("confirmation", "")
    if not isinstance(password, str) or not app.config["MIN_PASSWORD_LENGTH"] <= len(password) <= 128:
        return _error(
            f"اختاري كلمة سر من {app.config['MIN_PASSWORD_LENGTH']} إلى 128 خانة.",
            400,
        )
    if password != confirmation:
        return _error("كلمتا السر غير متطابقتين.", 400)

    db.session.add(BookSettings(
        id=1,
        password_hash=generate_password_hash(password, method="pbkdf2:sha256:600000"),
    ))
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("تم إعداد كلمة السر بالفعل.", 409)
    session.clear()
    session["book_unlocked"] = True
    session.permanent = True
    _csrf_token()
    return jsonify({"authenticated": True})


@app.post("/api/auth/login")
def login():
    if not _check_csrf():
        return _error("حدّثي الصفحة ثم حاولي مرة أخرى.", 403)
    settings = db.session.get(BookSettings, 1)
    if settings is None:
        return _error("ابدئي بإعداد كلمة سر الدفتر.", 409)

    key = _rate_limit_key()
    now = datetime.utcnow()
    attempt = db.session.get(LoginAttempt, key)
    if attempt and attempt.locked_until and attempt.locked_until > now:
        seconds = max(1, int((attempt.locked_until - now).total_seconds()))
        response, status = _error("محاولات كثيرة. انتظري قليلاً ثم حاولي مجدداً.", 429)
        response.headers["Retry-After"] = str(seconds)
        return response, status

    data = _json_payload()
    password = data.get("password", "")
    if (
        not isinstance(password, str)
        or len(password) > 128
        or not check_password_hash(settings.password_hash, password)
    ):
        if attempt is None:
            attempt = LoginAttempt(key=key, failures=0)
            db.session.add(attempt)
        if attempt.locked_until and attempt.locked_until <= now:
            attempt.failures = 0
            attempt.locked_until = None
        attempt.failures += 1
        if attempt.failures >= 5:
            attempt.failures = 0
            attempt.locked_until = now + timedelta(minutes=15)
        db.session.commit()
        if attempt.locked_until:
            response, status = _error("محاولات كثيرة. انتظري 15 دقيقة ثم حاولي مجدداً.", 429)
            response.headers["Retry-After"] = "900"
            return response, status
        return _error("كلمة السر غير صحيحة.", 401)

    if attempt:
        db.session.delete(attempt)
        db.session.commit()
    session.clear()
    session["book_unlocked"] = True
    session.permanent = True
    _csrf_token()
    return jsonify({"authenticated": True})


@app.post("/api/auth/logout")
def logout():
    if not _check_csrf():
        return _error("حدّثي الصفحة ثم حاولي مرة أخرى.", 403)
    session.clear()
    return jsonify({"authenticated": False})


@app.post("/api/auth/password")
def change_password():
    auth_error = _authenticated()
    if auth_error:
        return auth_error
    settings = db.session.get(BookSettings, 1)
    data = _json_payload()
    current = data.get("current", "")
    new_password = data.get("password", "")
    confirmation = data.get("confirmation", "")
    if not isinstance(current, str) or not check_password_hash(settings.password_hash, current):
        return _error("كلمة السر الحالية غير صحيحة.", 401)
    if (
        not isinstance(new_password, str)
        or not app.config["MIN_PASSWORD_LENGTH"] <= len(new_password) <= 128
    ):
        return _error(
            f"اختاري كلمة سر من {app.config['MIN_PASSWORD_LENGTH']} إلى 128 خانة.",
            400,
        )
    if new_password != confirmation:
        return _error("كلمتا السر الجديدتان غير متطابقتين.", 400)
    settings.password_hash = generate_password_hash(
        new_password,
        method="pbkdf2:sha256:600000",
    )
    db.session.commit()
    return jsonify({"updated": True})


@app.get("/api/memories")
def list_memories():
    if not session.get("book_unlocked"):
        return _error("افتحي الدفتر بكلمة السر أولاً.", 401)
    memories = Memory.query.order_by(Memory.happened_on.desc(), Memory.created_at.desc()).all()
    return jsonify([
        {
            "id": memory.id,
            "title": memory.title,
            "story": memory.story,
            "happened_on": memory.happened_on.isoformat() if memory.happened_on else None,
            "photos": [
                {"id": photo.id, "url": f"/api/media/{photo.id}"}
                for photo in memory.photos
            ],
        }
        for memory in memories
    ])


@app.get("/api/gift/memories")
def list_gift_memories():
    if not (session.get("book_unlocked") or _gift_access_allowed()):
        return _error("افتحي الهدية بكلمة السر أولاً.", 401)
    return jsonify([
        {
            "id": memory.id,
            "title": memory.title,
            "story": memory.story,
            "happened_on": memory.happened_on.isoformat() if memory.happened_on else None,
            "photos": [
                {"id": photo.id, "url": f"/api/gift/media/{photo.id}"}
                for photo in memory.photos
            ],
        }
        for memory in Memory.query.order_by(Memory.happened_on.desc(), Memory.created_at.desc()).all()
    ])


def _validated_photo(upload):
    content = upload.stream.read(MAX_IMAGE_BYTES + 1)
    if len(content) > MAX_IMAGE_BYTES:
        raise ValueError("يجب ألا يتجاوز حجم الصورة الواحدة 10 ميجابايت.")
    if not content:
        raise ValueError("تعذّر قراءة إحدى الصور.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            image = Image.open(io.BytesIO(content))
            image.verify()
            image_format = image.format
            width, height = image.size
    except (
        UnidentifiedImageError,
        OSError,
        SyntaxError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ):
        raise ValueError("أحد الملفات ليس صورة صالحة.")
    if image_format not in ALLOWED_IMAGE_FORMATS:
        raise ValueError("الصور المدعومة: JPG وPNG وWEBP وGIF.")
    if width * height > 25_000_000:
        raise ValueError("دقة الصورة كبيرة جداً.")
    extension, mime_type = ALLOWED_IMAGE_FORMATS[image_format]
    return content, extension, mime_type


@app.post("/api/memories")
def add_memory():
    auth_error = _authenticated()
    if auth_error:
        return auth_error
    title = request.form.get("title", "").strip()
    story = request.form.get("story", "").strip()
    happened_on_text = request.form.get("happened_on", "").strip()
    uploads = [photo for photo in request.files.getlist("photos") if photo.filename]

    if not title or len(title) > 160:
        return _error("اكتبي عنواناً للذكرى لا يتجاوز 160 حرفاً.", 400)
    if not story:
        return _error("اكتبي حكاية صغيرة عن الذكرى.", 400)
    if len(story) > 10_000:
        return _error("اختصري الحكاية إلى 10,000 حرف كحد أقصى.", 400)
    if len(uploads) > MAX_PHOTOS:
        return _error("يمكنك إضافة 8 صور كحد أقصى للذكرى الواحدة.", 400)
    happened_on = None
    if happened_on_text:
        try:
            happened_on = date.fromisoformat(happened_on_text)
        except ValueError:
            return _error("اختاري تاريخاً صحيحاً للذكرى.", 400)

    photo_data = []
    try:
        for upload in uploads:
            photo_data.append(_validated_photo(upload))
    except ValueError as exc:
        return _error(str(exc), 400)

    saved_files = []
    try:
        memory = Memory(title=title, story=story, happened_on=happened_on)
        db.session.add(memory)
        db.session.flush()
        for content, extension, mime_type in photo_data:
            filename = f"{secrets.token_hex(20)}.{extension}"
            with open(os.path.join(UPLOAD_DIR, filename), "xb") as photo_file:
                photo_file.write(content)
            saved_files.append(filename)
            db.session.add(MemoryPhoto(
                memory_id=memory.id,
                filename=filename,
                mime_type=mime_type,
            ))
        db.session.commit()
    except (OSError, SQLAlchemyError):
        db.session.rollback()
        for filename in saved_files:
            path = os.path.join(UPLOAD_DIR, filename)
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    app.logger.exception("Could not clean up an incomplete memory upload.")
        return _error("تعذّر حفظ الذكرى. تأكدي من وجود مساحة كافية ثم حاولي مرة أخرى.", 500)

    return jsonify({"id": memory.id}), 201


@app.delete("/api/memories/<int:memory_id>")
def delete_memory(memory_id: int):
    auth_error = _authenticated()
    if auth_error:
        return auth_error
    memory = db.session.get(Memory, memory_id)
    if memory is None:
        return _error("لم نعثر على هذه الذكرى.", 404)

    filenames = [photo.filename for photo in memory.photos]
    db.session.delete(memory)
    db.session.commit()
    for filename in filenames:
        path = os.path.join(UPLOAD_DIR, filename)
        if os.path.isfile(path):
            try:
                os.remove(path)
            except OSError:
                app.logger.exception("Memory deleted, but a photo file could not be removed.")
                return _error("حُذفت الذكرى، لكن تعذّر حذف إحدى صورها من مساحة التخزين.", 500)
    return jsonify({"deleted": True})


@app.get("/api/media/<int:photo_id>")
def get_photo(photo_id: int):
    if not session.get("book_unlocked"):
        return _error("افتحي الدفتر بكلمة السر أولاً.", 401)
    photo = db.session.get(MemoryPhoto, photo_id)
    if photo is None:
        abort(404)
    response = send_from_directory(
        UPLOAD_DIR,
        photo.filename,
        mimetype=photo.mime_type,
        conditional=False,
        max_age=0,
    )
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["Content-Disposition"] = "inline"
    return response


@app.get("/api/gift/media/<int:photo_id>")
def get_gift_photo(photo_id: int):
    if not (session.get("book_unlocked") or _gift_access_allowed()):
        return _error("افتحي الهدية بكلمة السر أولاً.", 401)
    photo = db.session.get(MemoryPhoto, photo_id)
    if photo is None:
        abort(404)
    response = send_from_directory(
        UPLOAD_DIR,
        photo.filename,
        mimetype=photo.mime_type,
        conditional=False,
        max_age=0,
    )
    response.headers["Cache-Control"] = "private, no-store"
    return response


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("FLASK_PORT", "5100")),
        debug=os.environ.get("FLASK_DEBUG", "").lower() == "true",
    )
