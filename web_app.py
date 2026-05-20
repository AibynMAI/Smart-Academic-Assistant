"""
Flask web server for Smart Academic Assistant
Run: python web_app.py
Then open: http://localhost:5000
"""
from flask import Flask, jsonify, request, render_template_string
import json, os

app = Flask(__name__)
DATA_FILE = "data/students.json"

# ── data helpers ──────────────────────────────
def _load():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def _save(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def _find(data, sid):
    for s in data:
        if s["student_id"] == sid:
            return s
    return None

def _avg(subjects):
    total, count = 0, 0
    for g in subjects.values():
        total += sum(g); count += len(g)
    return round(total / count, 2) if count else 0.0

# ── API routes ────────────────────────────────
@app.route("/api/students", methods=["GET"])
def get_students():
    return jsonify(_load())

@app.route("/api/students", methods=["POST"])
def add_student():
    body = request.json
    data = _load()
    if _find(data, body["student_id"]):
        return jsonify({"error": "ID already exists"}), 400
    data.append({"name": body["name"], "student_id": body["student_id"], "subjects": {}})
    _save(data)
    return jsonify({"ok": True})

@app.route("/api/students/<sid>", methods=["DELETE"])
def delete_student(sid):
    data = _load()
    new  = [s for s in data if s["student_id"] != sid]
    if len(new) == len(data):
        return jsonify({"error": "Not found"}), 404
    _save(new)
    return jsonify({"ok": True})

@app.route("/api/grades", methods=["POST"])
def add_grade():
    body = request.json
    data = _load()
    s    = _find(data, body["student_id"])
    if not s:
        return jsonify({"error": "Student not found"}), 404
    s["subjects"].setdefault(body["subject"], []).append(float(body["grade"]))
    _save(data)
    return jsonify({"ok": True, "new_avg": _avg(s["subjects"])})

@app.route("/api/stats", methods=["GET"])
def get_stats():
    data = _load()
    if not data:
        return jsonify({})
    avgs = [_avg(s["subjects"]) for s in data]
    top  = max(data, key=lambda s: _avg(s["subjects"]))
    return jsonify({
        "total":     len(data),
        "group_avg": round(sum(avgs)/len(avgs), 2),
        "highest":   max(avgs),
        "lowest":    min(avgs),
        "top_name":  top["name"],
        "at_risk":   sum(1 for a in avgs if a < 50),
    })

# ── serve frontend ────────────────────────────
@app.route("/")
def index():
    html_path = os.path.join(os.path.dirname(__file__), "web_static", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web_static", "index.html")
    if not os.path.exists(html_path):
        print(f"❌ ERROR: index.html not found at {html_path}")
        print("Make sure web_static/index.html exists!")
    else:
        print(f"✅ Found index.html at {html_path}")
        print("🌐 Web app running at http://localhost:5000")
        app.run(debug=True, port=5000)