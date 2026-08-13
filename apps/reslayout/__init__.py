from flask import Blueprint, render_template, request, Response
import httpx
from urllib.parse import urlparse, urljoin
import re

reslayout_bp = Blueprint("reslayout", __name__, url_prefix="/reslayout")

DEVICES = [
    {"name": "iPhone SE", "width": 375, "height": 667, "icon": "fa-mobile-alt"},
    {"name": "iPhone 14 Pro", "width": 393, "height": 852, "icon": "fa-mobile-alt"},
    {"name": "Samsung Galaxy S23", "width": 360, "height": 780, "icon": "fa-mobile-alt"},
    {"name": "iPad Mini", "width": 768, "height": 1024, "icon": "fa-tablet-alt"},
    {"name": "iPad Pro", "width": 1024, "height": 1366, "icon": "fa-tablet-alt"},
    {"name": "Laptop 13\"", "width": 1280, "height": 800, "icon": "fa-laptop"},
    {"name": "Desktop HD", "width": 1920, "height": 1080, "icon": "fa-desktop"},
    {"name": "Custom", "width": 0, "height": 0, "icon": "fa-expand"},
]

# Headers to strip from proxied responses so the page renders inside an iframe
_STRIP_HEADERS = {
    "x-frame-options",
    "content-security-policy",
    "content-security-policy-report-only",
    "cross-origin-opener-policy",
    "cross-origin-embedder-policy",
    "cross-origin-resource-policy",
    "transfer-encoding",
}

@reslayout_bp.route("/")
def index():
    return render_template("reslayout/index.html", devices=DEVICES)

@reslayout_bp.route("/proxy")
def proxy():
    url = request.args.get("url", "").strip()
    if not url:
        return "No URL provided", 400
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        resp = httpx.get(
            url,
            follow_redirects=True,
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"},
        )
    except Exception as e:
        error_html = f"""<!DOCTYPE html><html><body style="font-family:sans-serif;padding:32px;color:#f87171;background:#0d0d0d;">
        <h2>Could not load page</h2><p>{e}</p></body></html>"""
        return Response(error_html, status=200, content_type="text/html")

    content_type = resp.headers.get("content-type", "text/html")

    # Only rewrite HTML responses
    if "text/html" in content_type:
        content = resp.text
        # Inject a <base> tag so relative URLs resolve against the real origin
        final_url = str(resp.url)
        parsed = urlparse(final_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}/"
        base_tag = f'<base href="{base_url}">'
        # Insert after <head> if present, otherwise prepend
        if re.search(r"<head[^>]*>", content, re.IGNORECASE):
            content = re.sub(r"(<head[^>]*>)", r"\1" + base_tag, content, count=1, flags=re.IGNORECASE)
        else:
            content = base_tag + content
        body = content.encode("utf-8", errors="replace")
    else:
        body = resp.content

    headers = {
        k: v for k, v in resp.headers.items()
        if k.lower() not in _STRIP_HEADERS
    }
    headers["Content-Type"] = content_type

    return Response(body, status=resp.status_code, headers=headers)
