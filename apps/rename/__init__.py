import os
import re
import zipfile
import shutil
from flask import Blueprint, render_template, request, jsonify, send_file, current_app
from models import db, RenameJob
from datetime import datetime

rename_bp = Blueprint("rename", __name__, url_prefix="/rename")

def apply_rules(filename, rules):
    name, ext = os.path.splitext(filename)
    for rule in rules:
        rtype = rule.get("type")
        value = rule.get("value", "")
        replace_with = rule.get("replace_with", "")
        if rtype == "prefix":
            name = value + name
        elif rtype == "suffix":
            name = name + value
        elif rtype == "replace":
            name = name.replace(value, replace_with)
        elif rtype == "lowercase":
            name = name.lower()
        elif rtype == "uppercase":
            name = name.upper()
        elif rtype == "spaces_to_underscores":
            name = name.replace(" ", "_")
        elif rtype == "remove_special":
            name = re.sub(r"[^a-zA-Z0-9_\-]", "", name)
        elif rtype == "numbering":
            pass
    return name + ext

@rename_bp.route("/")
def index():
    jobs = RenameJob.query.order_by(RenameJob.created_at.desc()).limit(20).all()
    return render_template("rename/index.html", jobs=jobs)

@rename_bp.route("/process", methods=["POST"])
def process():
    if "zipfile" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    f = request.files["zipfile"]
    if not f.filename.endswith(".zip"):
        return jsonify({"error": "Please upload a ZIP file"}), 400

    import json
    rules = json.loads(request.form.get("rules", "[]"))

    upload_dir = current_app.config["UPLOAD_FOLDER"]
    timestamp = int(datetime.utcnow().timestamp())
    extract_dir = os.path.join(upload_dir, f"rename_{timestamp}")
    os.makedirs(extract_dir, exist_ok=True)

    zip_path = os.path.join(upload_dir, f"upload_{timestamp}.zip")
    f.save(zip_path)

    renamed_files = []
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(extract_dir)

    output_dir = os.path.join(upload_dir, f"renamed_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)

    counter = 1
    for root, dirs, files in os.walk(extract_dir):
        for fname in files:
            if fname.startswith("."):
                continue
            new_name = apply_rules(fname, rules)
            # Handle numbering rule
            for rule in rules:
                if rule.get("type") == "numbering":
                    n, ext = os.path.splitext(new_name)
                    new_name = f"{n}_{counter:03d}{ext}"
                    counter += 1
            src = os.path.join(root, fname)
            dst = os.path.join(output_dir, new_name)
            shutil.copy2(src, dst)
            renamed_files.append({"original": fname, "renamed": new_name})
            db.session.add(RenameJob(original_name=fname, renamed_to=new_name, rule=str(rules)))

    db.session.commit()

    # Zip the output
    out_zip = os.path.join(upload_dir, f"result_{timestamp}.zip")
    with zipfile.ZipFile(out_zip, "w") as z:
        for root, dirs, files in os.walk(output_dir):
            for fname in files:
                z.write(os.path.join(root, fname), fname)

    # Cleanup
    shutil.rmtree(extract_dir, ignore_errors=True)
    shutil.rmtree(output_dir, ignore_errors=True)
    os.remove(zip_path)

    return jsonify({
        "success": True,
        "renamed": renamed_files,
        "download_url": f"/rename/download/{os.path.basename(out_zip)}"
    })

@rename_bp.route("/download/<filename>")
def download(filename):
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    return send_file(path, as_attachment=True, download_name="renamed_files.zip")
