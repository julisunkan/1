from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, Setting, RenameJob, CheatSheet, NDADocument, Screenshot

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

def get_setting(key):
    s = Setting.query.filter_by(key=key).first()
    return s.value if s else ""

def require_admin(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin.login"))
        return f(*args, **kwargs)
    return decorated

@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        pwd = request.form.get("password", "")
        correct = get_setting("ADMIN_PASSWORD") or "admin123"
        if pwd == correct:
            session["admin_logged_in"] = True
            return redirect(url_for("admin.dashboard"))
        flash("Invalid password", "error")
    return render_template("admin/login.html")

@admin_bp.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin.login"))

@admin_bp.route("/")
@require_admin
def dashboard():
    stats = {
        "rename_jobs": RenameJob.query.count(),
        "cheatsheets": CheatSheet.query.count(),
        "ndas": NDADocument.query.count(),
        "screenshots": Screenshot.query.count(),
    }
    settings = {s.key: s.value for s in Setting.query.all()}
    return render_template("admin/dashboard.html", stats=stats, settings=settings)

@admin_bp.route("/settings", methods=["GET", "POST"])
@require_admin
def settings():
    if request.method == "POST":
        keys = ["GROQ_API_KEY", "ADMIN_PASSWORD", "APP_NAME", "THEME"]
        for key in keys:
            val = request.form.get(key, "")
            s = Setting.query.filter_by(key=key).first()
            if s:
                s.value = val
            else:
                db.session.add(Setting(key=key, value=val))
        db.session.commit()
        flash("Settings saved successfully!", "success")
        return redirect(url_for("admin.settings"))
    settings_data = {s.key: s.value for s in Setting.query.all()}
    return render_template("admin/settings.html", settings=settings_data)
