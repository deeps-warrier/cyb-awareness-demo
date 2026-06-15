from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime
from user_agents import parse

app = Flask(__name__)

DB_NAME = "awareness.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS visits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        ip_address TEXT,
        device TEXT,
        browser TEXT,
        os TEXT,
        camera_permission TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()


@app.route("/")
def index():

    ua_string = request.headers.get("User-Agent", "")
    ua = parse(ua_string)

    ip = request.headers.get(
        "X-Forwarded-For",
        request.remote_addr
    )

    if "," in str(ip):
        ip = ip.split(",")[0].strip()

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO visits
    (
        timestamp,
        ip_address,
        device,
        browser,
        os,
        camera_permission
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ip,
        ua.device.family,
        ua.browser.family,
        ua.os.family,
        "Pending"
    ))

    visit_id = cur.lastrowid

    conn.commit()
    conn.close()

    return render_template(
        "index.html",
        visit_id=visit_id
    )


@app.route("/permission", methods=["POST"])
def permission():

    data = request.get_json()

    visit_id = data.get("visit_id")
    status = data.get("status")

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    UPDATE visits
    SET camera_permission = ?
    WHERE id = ?
    """, (
        status,
        visit_id
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True
    })


@app.route("/dashboard")
def dashboard():

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    rows = cur.execute("""
    SELECT *
    FROM visits
    ORDER BY id DESC
    """).fetchall()

    total = len(rows)

    granted = sum(
        1 for r in rows
        if r[6] == "Granted"
    )

    denied = sum(
        1 for r in rows
        if r[6] == "Denied"
    )

    pending = sum(
        1 for r in rows
        if r[6] == "Pending"
    )

    conn.close()

    return render_template(
        "dashboard.html",
        rows=rows,
        total=total,
        granted=granted,
        denied=denied,
        pending=pending
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5555)