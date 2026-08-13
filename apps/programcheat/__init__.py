from flask import Blueprint, render_template, request, jsonify
from models import db, Setting, CheatSheet
import json

programcheat_bp = Blueprint("programcheat", __name__, url_prefix="/programcheat")

LANGUAGES = [
    "Python", "JavaScript", "TypeScript", "Go", "Rust", "Java", "C++", "C#",
    "PHP", "Ruby", "Swift", "Kotlin", "Dart/Flutter", "React", "Vue.js",
    "Node.js", "Django", "Flask", "FastAPI", "SQL", "Bash/Shell", "Docker",
    "Git", "CSS/Tailwind", "HTML5"
]

def get_groq_key():
    s = Setting.query.filter_by(key="GROQ_API_KEY").first()
    return s.value if s else ""

def generate_cheatsheet_ai(language, topic):
    from groq import Groq
    client = Groq(api_key=get_groq_key())
    prompt = f"""Create a comprehensive, well-structured cheatsheet for {language}{' focusing on ' + topic if topic else ''}.

Format with clear sections using markdown:
- Key syntax examples
- Common operations/methods
- Best practices
- Quick reference tables

Make it concise, printable, and practical. Use code blocks for examples."""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000
    )
    return response.choices[0].message.content

@programcheat_bp.route("/")
def index():
    recent = CheatSheet.query.order_by(CheatSheet.created_at.desc()).limit(5).all()
    return render_template("programcheat/index.html", languages=LANGUAGES, recent=recent)

@programcheat_bp.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    language = data.get("language", "")
    topic = data.get("topic", "")

    if not language:
        return jsonify({"error": "Please select a language"}), 400

    key = get_groq_key()
    if not key:
        return jsonify({"error": "Groq API key not configured. Please set it in the Admin Panel."}), 400

    try:
        content = generate_cheatsheet_ai(language, topic)
        sheet = CheatSheet(language=language, content=content)
        db.session.add(sheet)
        db.session.commit()
        return jsonify({"success": True, "content": content, "id": sheet.id, "language": language})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@programcheat_bp.route("/get/<int:sheet_id>")
def get_sheet(sheet_id):
    sheet = CheatSheet.query.get_or_404(sheet_id)
    return jsonify({"content": sheet.content, "language": sheet.language})
