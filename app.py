import os
import logging
from flask import Flask, render_template
from werkzeug.middleware.proxy_fix import ProxyFix
from models import db

logging.basicConfig(level=logging.DEBUG)

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(basedir, 'data.db')}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024
    app.config["UPLOAD_FOLDER"] = os.path.join(basedir, "static", "uploads")
    app.config["SCREENSHOT_FOLDER"] = os.path.join(basedir, "static", "screenshots")

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["SCREENSHOT_FOLDER"], exist_ok=True)

    db.init_app(app)

    from apps.admin import admin_bp
    from apps.rename import rename_bp
    from apps.programcheat import programcheat_bp
    from apps.ndagen import ndagen_bp
    from apps.reslayout import reslayout_bp
    from apps.webscreen import webscreen_bp

    app.register_blueprint(admin_bp)
    app.register_blueprint(rename_bp)
    app.register_blueprint(programcheat_bp)
    app.register_blueprint(ndagen_bp)
    app.register_blueprint(reslayout_bp)
    app.register_blueprint(webscreen_bp)

    @app.route("/")
    def index():
        return render_template("index.html")

    with app.app_context():
        db.create_all()
        from models import Setting
        defaults = {
            "GROQ_API_KEY": "",
            "ADMIN_PASSWORD": "admin123",
            "APP_NAME": "DevTools Suite",
            "THEME": "dark",
        }
        for key, val in defaults.items():
            if not Setting.query.filter_by(key=key).first():
                db.session.add(Setting(key=key, value=val))
        db.session.commit()

    return app

app = create_app()
