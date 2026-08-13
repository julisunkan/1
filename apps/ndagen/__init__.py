from flask import Blueprint, render_template, request, jsonify, Response
from models import db, Setting, NDADocument, ContentReport
from datetime import datetime
import pdfkit
import shutil
import os

ndagen_bp = Blueprint("ndagen", __name__, url_prefix="/ndagen")

def _find_wkhtmltopdf():
    """Return the wkhtmltopdf binary path, preferring the env var, then PATH, then common locations."""
    env_path = os.environ.get("WKHTMLTOPDF_PATH", "").strip()
    if env_path and os.path.isfile(env_path):
        return env_path
    found = shutil.which("wkhtmltopdf")
    if found:
        return found
    candidates = [
        "/usr/bin/wkhtmltopdf",           # PythonAnywhere / Debian/Ubuntu
        "/usr/local/bin/wkhtmltopdf",     # Homebrew / manual installs
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None  # let pdfkit use its own default

def get_groq_key():
    s = Setting.query.filter_by(key="GROQ_API_KEY").first()
    return s.value if s else ""

def generate_nda_ai(party_a, party_b, purpose, duration, jurisdiction):
    from groq import Groq
    client = Groq(api_key=get_groq_key())
    prompt = f"""Generate a professional, legally sound Non-Disclosure Agreement (NDA) with the following details:

- Party A (Disclosing Party): {party_a}
- Party B (Receiving Party): {party_b}
- Purpose: {purpose}
- Duration: {duration}
- Jurisdiction: {jurisdiction}

Include all standard NDA clauses:
1. Definition of Confidential Information
2. Obligations of Receiving Party
3. Exclusions from Confidential Information
4. Term and Termination
5. Return of Information
6. Remedies
7. Governing Law
8. Entire Agreement
9. Signature blocks

Format it as a proper legal document with section numbers."""

    from groq import Groq
    client = Groq(api_key=get_groq_key())
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=3000
    )
    return response.choices[0].message.content

@ndagen_bp.route("/")
def index():
    docs = NDADocument.query.order_by(NDADocument.created_at.desc()).limit(10).all()
    return render_template("ndagen/index.html", docs=docs)

@ndagen_bp.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    party_a = data.get("party_a", "")
    party_b = data.get("party_b", "")
    purpose = data.get("purpose", "")
    duration = data.get("duration", "2 years")
    jurisdiction = data.get("jurisdiction", "")

    if not party_a or not party_b or not purpose:
        return jsonify({"error": "Party names and purpose are required"}), 400

    key = get_groq_key()
    if not key:
        return jsonify({"error": "Groq API key not configured. Please set it in the Admin Panel."}), 400

    try:
        content = generate_nda_ai(party_a, party_b, purpose, duration, jurisdiction)
        doc = NDADocument(party_a=party_a, party_b=party_b, content=content)
        db.session.add(doc)
        db.session.commit()
        return jsonify({"success": True, "content": content, "id": doc.id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@ndagen_bp.route("/sign/<int:doc_id>", methods=["POST"])
def sign(doc_id):
    doc = NDADocument.query.get_or_404(doc_id)
    data = request.get_json()
    party = data.get("party")
    sig = data.get("signature")
    if party == "a":
        doc.signature_a = sig
    elif party == "b":
        doc.signature_b = sig
    if doc.signature_a and doc.signature_b:
        doc.signed_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"success": True, "fully_signed": bool(doc.signed_at)})

@ndagen_bp.route("/report", methods=["POST"])
def report_content():
    data = request.get_json(silent=True) or {}
    try:
        doc_id = int(data.get("document_id", 0))
    except (TypeError, ValueError):
        doc_id = 0
    reason = (data.get("reason") or "").strip()
    details = (data.get("details") or "").strip()
    allowed_reasons = {
        "inaccurate": "Inaccurate or misleading",
        "unsafe": "Unsafe or inappropriate",
        "missing": "Missing important information",
        "other": "Other concern",
    }

    if not doc_id or not NDADocument.query.get(doc_id):
        return jsonify({"error": "That NDA could not be found."}), 404
    if reason not in allowed_reasons:
        return jsonify({"error": "Please choose a valid report reason."}), 400
    if len(details) > 2000:
        return jsonify({"error": "Additional details must be 2,000 characters or fewer."}), 400

    report = ContentReport(
        document_id=doc_id,
        reason=allowed_reasons[reason],
        details=details,
    )
    db.session.add(report)
    db.session.commit()
    return jsonify({"success": True, "message": "Thanks — your report was sent to an administrator for review."})

@ndagen_bp.route("/get/<int:doc_id>")
def get_doc(doc_id):
    doc = NDADocument.query.get_or_404(doc_id)
    return jsonify({
        "content": doc.content,
        "party_a": doc.party_a,
        "party_b": doc.party_b,
        "signature_a": doc.signature_a,
        "signature_b": doc.signature_b,
        "signed_at": doc.signed_at.isoformat() if doc.signed_at else None
    })

@ndagen_bp.route("/txt/<int:doc_id>")
def download_txt(doc_id):
    doc = NDADocument.query.get_or_404(doc_id)
    filename = f"NDA_{doc.party_a}_{doc.party_b}_{doc_id}.txt".replace(" ", "_")
    return Response(
        doc.content,
        mimetype="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@ndagen_bp.route("/pdf/<int:doc_id>")
def download_pdf(doc_id):
    doc = NDADocument.query.get_or_404(doc_id)

    signed_date = doc.signed_at.strftime("%B %d, %Y") if doc.signed_at else None
    created_date = doc.created_at.strftime("%B %d, %Y")

    # Build signature blocks HTML
    def sig_block(label, sig_data, party_name):
        img_tag = (
            f'<img src="{sig_data}" style="max-height:64px;max-width:260px;display:block;margin-bottom:4px;">'
            if sig_data else
            '<div style="height:64px;border-bottom:1px solid #333;margin-bottom:4px;"></div>'
        )
        return f"""
        <div style="flex:1;min-width:220px;">
          <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#555;margin-bottom:6px;">{label}</div>
          {img_tag}
          <div style="font-size:13px;font-weight:700;color:#111;">{party_name}</div>
          <div style="font-size:11px;color:#555;margin-top:2px;">{'Signed · ' + signed_date if signed_date else 'Signature pending'}</div>
        </div>"""

    # Convert plain-text NDA to basic HTML paragraphs
    import html as html_mod
    paragraphs = ""
    for line in doc.content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        escaped = html_mod.escape(stripped)
        # Section headings: lines starting with a digit and a dot, or ALL CAPS short lines
        if (stripped[:2].rstrip('.').isdigit() or
                (stripped.isupper() and len(stripped) < 80 and len(stripped) > 3)):
            paragraphs += f'<h3 style="font-size:13px;font-weight:700;letter-spacing:.03em;margin:22px 0 6px;color:#111;font-family:\'Georgia\',serif;">{escaped}</h3>\n'
        else:
            paragraphs += f'<p style="margin:0 0 10px;">{escaped}</p>\n'

    sig_html = f"""
    <div style="display:flex;gap:48px;flex-wrap:wrap;margin-top:12px;padding-top:24px;border-top:1px solid #ccc;">
      {sig_block("Party A — Disclosing Party", doc.signature_a, doc.party_a)}
      {sig_block("Party B — Receiving Party", doc.signature_b, doc.party_b)}
    </div>"""

    executed_banner = ""
    if doc.signed_at:
        executed_banner = f"""
        <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:6px;padding:14px 20px;margin-bottom:32px;display:flex;align-items:center;gap:12px;">
          <span style="font-size:20px;">✅</span>
          <div>
            <div style="font-weight:700;color:#15803d;font-size:13px;">NDA Fully Executed</div>
            <div style="font-size:12px;color:#166534;margin-top:2px;">Both parties signed on {signed_date}</div>
          </div>
        </div>"""

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=EB+Garamond:wght@400;600;700&family=Inter:wght@400;600;700&display=swap');
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Georgia', 'Times New Roman', serif;
    font-size: 14px;
    line-height: 1.9;
    color: #1a1a1a;
    background: #fff;
    padding: 64px 80px;
  }}
  .header {{
    text-align: center;
    margin-bottom: 40px;
    padding-bottom: 24px;
    border-bottom: 2px solid #1a1a1a;
  }}
  .header h1 {{
    font-size: 22px;
    font-weight: 700;
    letter-spacing: .06em;
    text-transform: uppercase;
    margin-bottom: 6px;
    font-family: 'Georgia', serif;
  }}
  .header .meta {{
    font-size: 12px;
    color: #555;
    font-family: Arial, sans-serif;
  }}
  .body-text {{
    font-size: 14px;
    line-height: 1.9;
    color: #1a1a1a;
  }}
  .signatures {{
    margin-top: 48px;
    page-break-inside: avoid;
  }}
</style>
</head>
<body>
<div class="header">
  <h1>Non-Disclosure Agreement</h1>
  <div class="meta">
    Between <strong>{html_mod.escape(doc.party_a)}</strong> and <strong>{html_mod.escape(doc.party_b)}</strong>
    &nbsp;·&nbsp; Prepared {created_date}
  </div>
</div>
{executed_banner}
<div class="body-text">
{paragraphs}
</div>
<div class="signatures">
  {sig_html}
</div>
</body>
</html>"""

    wk_path = _find_wkhtmltopdf()
    config = pdfkit.configuration(wkhtmltopdf=wk_path) if wk_path else pdfkit.configuration()
    options = {
        "page-size": "A4",
        "margin-top": "0",
        "margin-right": "0",
        "margin-bottom": "0",
        "margin-left": "0",
        "encoding": "UTF-8",
        "enable-local-file-access": "",
        "quiet": "",
    }
    pdf_bytes = pdfkit.from_string(html_content, False, configuration=config, options=options)

    filename = f"NDA_{doc.party_a}_{doc.party_b}_{doc_id}.pdf".replace(" ", "_")
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
