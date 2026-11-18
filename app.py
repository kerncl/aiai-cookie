"""aiai 饼家 — a bilingual Flask catalogue of the biscuits we sell and what goes into them."""

from __future__ import annotations

import json
from pathlib import Path

from flask import Flask, abort, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "cookies.json"
UI_FILE = BASE_DIR / "data" / "ui.json"
COOKIE_IMAGE_DIR = BASE_DIR / "static" / "images" / "cookies"

app = Flask(__name__)

# Serve real Chinese characters in /api/cookies rather than \uXXXX escapes.
app.json.ensure_ascii = False

# Both files are small enough to hold in memory. We key the cache on each file's
# mtime so editing them shows up on refresh without restarting the server.
_cache: dict[Path, tuple[float, dict]] = {}


def load_json(path: Path) -> dict:
    """Read a JSON file, re-reading only when it has changed on disk."""
    mtime = path.stat().st_mtime
    cached = _cache.get(path)
    if cached is None or cached[0] != mtime:
        with path.open(encoding="utf-8") as fh:
            _cache[path] = (mtime, json.load(fh))
    return _cache[path][1]


def load_catalogue() -> dict:
    return load_json(DATA_FILE)


def image_exists(filename: str | None) -> bool:
    """True if a cookie photo has actually been dropped in yet."""
    return bool(filename) and (COOKIE_IMAGE_DIR / filename).is_file()


def matches_search(cookie: dict, needle: str) -> bool:
    """Match on either language, across name, tagline and every ingredient.

    Chinese needs no lowering, but English does, and .lower() leaves CJK
    untouched — so one pass handles both scripts.
    """
    haystack = [
        cookie.get("name_zh", ""),
        cookie.get("name_en", ""),
        cookie.get("tagline_zh", ""),
        cookie.get("tagline_en", ""),
    ]
    for ing in cookie.get("ingredients", []):
        haystack += [ing.get("zh", ""), ing.get("en", "")]
    return any(needle in field.lower() for field in haystack)


@app.template_filter("money")
def money(value: float) -> str:
    # Malaysian retail convention is always two decimals and no space: RM28.90
    symbol = load_catalogue()["shop"].get("currency_symbol", "RM")
    return f"{symbol}{value:.2f}"


@app.context_processor
def inject_globals():
    catalogue = load_catalogue()
    return {
        "shop": catalogue["shop"],
        "allergen_labels": catalogue["allergen_labels"],
        "dietary_labels": catalogue["dietary_labels"],
        "t": load_json(UI_FILE),
        "image_exists": image_exists,
    }


@app.route("/")
def index():
    catalogue = load_catalogue()
    cookies = catalogue["cookies"]

    # Two filters with deliberately opposite senses:
    #   exclude=  removes anything CONTAINING the allergen (keep me safe)
    #   dietary=  keeps only what CARRIES the marker       (show me what I can eat)
    excluded = set(request.args.getlist("exclude"))
    required_diet = set(request.args.getlist("dietary"))
    query = request.args.get("q", "").strip().lower()

    visible = cookies
    if excluded:
        visible = [c for c in visible if not excluded & set(c.get("allergens", []))]
    if required_diet:
        visible = [c for c in visible if required_diet <= set(c.get("dietary", []))]
    if query:
        visible = [c for c in visible if matches_search(c, query)]

    return render_template(
        "index.html",
        cookies=visible,
        total=len(cookies),
        excluded=excluded,
        required_diet=required_diet,
        query=request.args.get("q", ""),
    )


@app.route("/cookie/<slug>")
def cookie_detail(slug: str):
    catalogue = load_catalogue()
    cookie = next((c for c in catalogue["cookies"] if c["slug"] == slug), None)
    if cookie is None:
        abort(404)
    return render_template("cookie.html", cookie=cookie)


@app.route("/api/cookies")
def api_cookies():
    """JSON feed of the catalogue — here for whatever comes next (ordering, an app)."""
    return jsonify(load_catalogue()["cookies"])


@app.route("/healthz")
def healthz():
    """Liveness probe for Azure App Service."""
    return {"status": "ok", "cookies": len(load_catalogue()["cookies"])}


@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True, port=5000)
