# Deploying to PythonAnywhere

## Prerequisites
- A PythonAnywhere account (free Beginner tier works for testing; a paid plan is needed for outbound HTTP calls from the Responsive Layout proxy and Web Screenshot tool).
- Your project files uploaded or cloned into your PythonAnywhere home directory.

---

## Step 1 — Upload the project

**Option A – Git (recommended)**
```bash
# In a PythonAnywhere Bash console:
git clone https://github.com/<you>/<repo>.git ~/devtools
cd ~/devtools
```

**Option B – ZIP upload**  
Use the PythonAnywhere Files tab to upload a ZIP, then unzip it:
```bash
unzip devtools.zip -d ~/devtools
cd ~/devtools
```

---

## Step 2 — Create a virtual environment

```bash
python3.11 -m venv ~/devtools/venv
source ~/devtools/venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Step 3 — Set environment variables

In the PythonAnywhere **Web** tab scroll down to the **Environment variables** section and add:

| Key | Value |
|-----|-------|
| `SESSION_SECRET` | A long random string — run `python -c "import secrets; print(secrets.token_hex(32))"` to generate one |
| `WKHTMLTOPDF_PATH` | `/usr/bin/wkhtmltopdf` (leave blank to auto-detect) |

---

## Step 4 — Configure the Web app

1. Go to the **Web** tab → **Add a new web app**.
2. Choose **Manual configuration** → **Python 3.11**.
3. Set the following fields:

| Field | Value |
|-------|-------|
| Source code | `/home/<username>/devtools` |
| Working directory | `/home/<username>/devtools` |
| WSGI configuration file | click the link → replace the entire contents with the snippet below |
| Virtualenv | `/home/<username>/devtools/venv` |

**WSGI configuration file content:**
```python
import sys, os
project_home = '/home/<username>/devtools'
if project_home not in sys.path:
    sys.path.insert(0, project_home)
from app import app as application
```
Replace `<username>` with your actual PythonAnywhere username.

---

## Step 5 — Configure static files

In the **Web** tab → **Static files** section add:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/<username>/devtools/static` |

---

## Step 6 — Initialise the database

Run this once in a PythonAnywhere Bash console to create `data.db` and seed default settings:

```bash
cd ~/devtools
source venv/bin/activate
python - <<'EOF'
from app import app, db
with app.app_context():
    db.create_all()
    print("Database ready.")
EOF
```

---

## Step 7 — Set your Groq API key

1. Open your deployed app and go to `/admin`.
2. Log in with the default password `admin123`.
3. Go to **Settings** and paste your Groq API key.
4. Change the admin password while you're there.

---

## Step 8 — Reload and test

Click **Reload** in the PythonAnywhere Web tab, then visit:

```
https://<username>.pythonanywhere.com/
```

---

## Notes on specific tools

### NDA Generator — PDF download
The PDF export uses `wkhtmltopdf`. PythonAnywhere has it pre-installed at `/usr/bin/wkhtmltopdf`. The app detects this automatically; set the `WKHTMLTOPDF_PATH` environment variable only if the auto-detection fails.

### Web Screenshot
Also uses `wkhtmltopdf` (via `imgkit`). Same binary, same auto-detection applies.

### Responsive Layout Tester — proxy
The proxy route (`/reslayout/proxy`) makes outbound HTTP requests. **PythonAnywhere free accounts cannot make outbound HTTP calls to arbitrary URLs** — upgrade to a paid plan or whitelist the domains you need in the PythonAnywhere whitelist panel.

### Uploaded / generated files
- File Renamer uploads → `static/uploads/`
- Screenshots → `static/screenshots/`

Both directories are created automatically on first run. They are served through Flask on PythonAnywhere (the static file mapping above covers them).

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `ModuleNotFoundError` | Make sure the virtualenv is set in the Web tab and all packages are installed with `pip install -r requirements.txt` |
| 500 on PDF download | Check the Error log in the Web tab; the most common cause is a missing `wkhtmltopdf` binary. Run `which wkhtmltopdf` in a console to confirm the path, then set `WKHTMLTOPDF_PATH` |
| Screenshots fail | Same `wkhtmltopdf` issue — see above |
| Proxy returns error | Outbound HTTP is restricted on free accounts — upgrade or whitelist the target domain |
| Static files 404 | Confirm the static files URL/directory mapping in the Web tab |
