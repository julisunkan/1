import os
import shutil
import uuid
from flask import Blueprint, render_template, request, jsonify, send_file, current_app
from models import db, Screenshot

webscreen_bp = Blueprint("webscreen", __name__, url_prefix="/webscreen")

def _find_wkhtmltopdf():
    """Return the wkhtmltopdf binary path, preferring the env var, then PATH, then common locations."""
    env_path = os.environ.get("WKHTMLTOPDF_PATH", "").strip()
    if env_path and os.path.isfile(env_path):
        return env_path
    found = shutil.which("wkhtmltopdf")
    if found:
        return found
    candidates = [
        "/usr/bin/wkhtmltopdf",
        "/usr/local/bin/wkhtmltopdf",
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None

def capture_screenshot(url, width, height):
    try:
        import imgkit
        filename = f"screenshot_{uuid.uuid4().hex[:8]}.jpg"
        out_path = os.path.join(current_app.config["SCREENSHOT_FOLDER"], filename)
        options = {
            "width": str(int(width)),
            "height": str(int(height)),
            "format": "jpg",
            "quality": "85",
            "javascript-delay": "1500",
            "no-stop-slow-scripts": "",
            "quiet": "",
        }
        wk_path = _find_wkhtmltopdf()
        config = imgkit.config(wkhtmltoimage=wk_path) if wk_path else None
        imgkit.from_url(url, out_path, options=options, config=config)
        return filename, None
    except Exception as e:
        return None, str(e)

@webscreen_bp.route("/")
def index():
    shots = Screenshot.query.order_by(Screenshot.created_at.desc()).limit(12).all()
    return render_template("webscreen/index.html", shots=shots)

@webscreen_bp.route("/capture", methods=["POST"])
def capture():
    data = request.get_json()
    url = data.get("url", "").strip()
    width = data.get("width", 1280)
    height = data.get("height", 800)

    if not url:
        return jsonify({"error": "URL is required"}), 400

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    filename, error = capture_screenshot(url, width, height)
    if error:
        return jsonify({"error": f"Screenshot failed: {error}"}), 500

    shot = Screenshot(url=url, filename=filename)
    db.session.add(shot)
    db.session.commit()

    return jsonify({
        "success": True,
        "filename": filename,
        "url": f"/static/screenshots/{filename}",
        "id": shot.id
    })

@webscreen_bp.route("/download/<filename>")
def download(filename):
    path = os.path.join(current_app.config["SCREENSHOT_FOLDER"], filename)
    return send_file(path, as_attachment=True, download_name=filename)

@webscreen_bp.route("/delete/<int:shot_id>", methods=["DELETE"])
def delete(shot_id):
    shot = Screenshot.query.get_or_404(shot_id)
    try:
        path = os.path.join(current_app.config["SCREENSHOT_FOLDER"], shot.filename)
        if os.path.exists(path):
            os.remove(path)
    except:
        pass
    db.session.delete(shot)
    db.session.commit()
    return jsonify({"success": True})
