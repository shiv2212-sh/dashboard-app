# import threading, socket, sqlite3, json, io, csv, datetime, os, tempfile
# from flask import Flask, jsonify, render_template, send_file, request
# from waitress import serve
# from reportlab.lib.pagesizes import A4
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.lib import colors
# import os
# from waitress import serve
# import psutil
#
#
#
# DB_FILE = r"C:\Users\shivs\PyCharmMiscProject\client-dashboard-app\python\server_data.db"
# TEMPLATE_DIR = os.path.join(os.path.dirname(DB_FILE), "templates")
#
# TCP_HOST = "0.0.0.0"
# TCP_PORT = 9002
#
# app = Flask(__name__, template_folder=TEMPLATE_DIR)
# shutdown_flag = threading.Event()
#
# # ---------------- DATABASE ----------------
# def init_db():
#     os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
#     con = sqlite3.connect(DB_FILE)
#     cur = con.cursor()
#
#     cur.execute("""
#     CREATE TABLE IF NOT EXISTS clients (
#         client_uuid TEXT PRIMARY KEY,
#         mac_address TEXT,
#         hostname TEXT,
#         last_seen TEXT,
#         client_ip TEXT,
#         hardware_info TEXT,
#         installed_apps TEXT
#     )""")
#
#     cur.execute("""
#     CREATE TABLE IF NOT EXISTS app_history (
#         client_uuid TEXT,
#         app_name TEXT,
#         version TEXT,
#         status TEXT,
#         time TEXT
#     )""")
#
#     con.commit()
#     con.close()
#
#
# def upsert_client(data, ip):
#     con = sqlite3.connect(DB_FILE)
#     cur = con.cursor()
#
#     cur.execute("""
#     INSERT INTO clients VALUES (?, ?, ?, ?, ?, ?, ?)
#     ON CONFLICT(client_uuid) DO UPDATE SET
#         mac_address=excluded.mac_address,
#         hostname=excluded.hostname,
#         last_seen=excluded.last_seen,
#         client_ip=excluded.client_ip,
#         hardware_info=excluded.hardware_info,
#         installed_apps=excluded.installed_apps
#     """, (data["uuid"], data["mac"], data["hostname"],
#           data["timestamp"], ip, data["hardware"], data["apps"]))
#
#     for line in data["apps"].splitlines():
#         if "|" in line:
#             name, version, install_date, _ = line.split("|", 3)
#             time_val = install_date if install_date != "-" else data["timestamp"]
#             cur.execute("INSERT INTO app_history VALUES (?,?,?,?,?)",
#                         (data["uuid"], name, version, "Installed", time_val))
#
#     con.commit()
#     con.close()
#
#
# # ---------------- TCP SERVER ----------------
# def recv_line(sock):
#     data = b""
#     while not data.endswith(b"\n"):
#         p = sock.recv(1)
#         if not p: return None
#         data += p
#     return data.decode().strip()
#
#
# def recv_exact(sock, n):
#     data = b""
#     while len(data) < n:
#         p = sock.recv(n - len(data))
#         if not p: return None
#         data += p
#     return data
#
#
# def recv_text(sock):
#     l = recv_line(sock)
#     if not l: return None
#     payload = recv_exact(sock, int(l))
#     return payload.decode() if payload else None
#
#
# def parse_text_data(text):
#     lines = text.splitlines()
#     data = {"hardware": "", "apps": ""}
#     mode = None
#     for line in lines:
#         if line.startswith("CLIENT_UUID:"): data["uuid"] = line.split(":",1)[1].strip()
#         elif line.startswith("MAC_ADDRESS:"): data["mac"] = line.split(":",1)[1].strip()
#         elif line.startswith("HOSTNAME:"): data["hostname"] = line.split(":",1)[1].strip()
#         elif line.startswith("TIMESTAMP:"): data["timestamp"] = line.split(":",1)[1].strip()
#         elif line.startswith("=== HARDWARE"): mode="hw"
#         elif line.startswith("=== APPLICATIONS"): mode="apps"
#         elif mode=="hw": data["hardware"] += line + "\n"
#         elif mode=="apps": data["apps"] += line + "\n"
#     return data
#
#
# def handle_client(sock, addr):
#     ip,_ = addr
#     cmd = recv_line(sock)
#     if cmd != "get apps":
#         sock.close()
#         return
#     text = recv_text(sock)
#     data = parse_text_data(text)
#     if "uuid" in data:
#         upsert_client(data, ip)
#     sock.sendall(b"OK\n")
#     sock.close()
#
#
# def tcp_server():
#     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#     s.bind((TCP_HOST, TCP_PORT))
#     s.listen(5)
#     print(f"[+] TCP listening {TCP_HOST}:{TCP_PORT}")
#     while not shutdown_flag.is_set():
#         try:
#             s.settimeout(1)
#             c,addr = s.accept()
#             threading.Thread(target=handle_client, args=(c,addr), daemon=True).start()
#         except socket.timeout:
#             continue
#     s.close()
#
#
# # ---------------- HELPERS ----------------
# def safe_json(v):
#     try:
#         return json.loads(v)
#     except:
#         return v.splitlines()
#
#
# def status_from_last_seen(ts):
#     try:
#         t = datetime.datetime.strptime(ts,"%Y-%m-%d %H:%M:%S")
#         return "Online" if (datetime.datetime.now()-t).seconds<=60 else "Offline"
#     except:
#         return "Offline"
#
#
# # ---------------- FLASK ROUTES ----------------
# @app.route("/")
# def dashboard():
#     return render_template("dashboard.html")
#
#
# @app.route("/api/clients")
# def api_clients():
#     con = sqlite3.connect(DB_FILE)
#     cur = con.cursor()
#     cur.execute("SELECT * FROM clients")
#     rows = cur.fetchall()
#     con.close()
#
#     return jsonify([{
#         "uuid":r[0],
#         "mac":r[1],
#         "hostname":r[2],
#         "last_seen":r[3],
#         "ip":r[4],
#         "status":status_from_last_seen(r[3])
#     } for r in rows])
#
#
# @app.route("/api/client/<uuid>")
# def api_client(uuid):
#     con = sqlite3.connect(DB_FILE)
#     cur = con.cursor()
#     cur.execute("SELECT * FROM clients WHERE client_uuid=?", (uuid,))
#     r = cur.fetchone()
#     con.close()
#
#     return jsonify({
#         "uuid":r[0],
#         "mac":r[1],
#         "hostname":r[2],
#         "last_seen":r[3],
#         "ip":r[4],
#         "hardware":safe_json(r[5]),
#         "apps":safe_json(r[6])
#     })
#
#
# @app.route("/export/pdf/<uuid>")
# def export_pdf(uuid):
#     con = sqlite3.connect(DB_FILE)
#     cur = con.cursor()
#     cur.execute("SELECT * FROM clients WHERE client_uuid=?", (uuid,))
#     r = cur.fetchone()
#     con.close()
#
#     if not r:
#         return "Client not found", 404
#
#     fd, path = tempfile.mkstemp(suffix=".pdf")
#     os.close(fd)
#
#     doc = SimpleDocTemplate(path, pagesize=A4)
#     styles = getSampleStyleSheet()
#     elements = []
#
#     elements.append(Paragraph("Client Report", styles["Title"]))
#     elements.append(Spacer(1, 12))
#
#     info = [["Field","Value"],
#             ["UUID",r[0]],["MAC",r[1]],["Hostname",r[2]],
#             ["Last Seen",r[3]],["IP",r[4]]]
#
#     t1 = Table(info, colWidths=[120,350])
#     t1.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.black),
#                             ('BACKGROUND',(0,0),(-1,0),colors.lightgrey)]))
#     elements.append(t1); elements.append(Spacer(1,20))
#
#     elements.append(Paragraph("Hardware", styles["Heading2"]))
#     hw = [["Component"]] + [[l] for l in safe_json(r[5])]
#     t2 = Table(hw, colWidths=[470])
#     t2.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.black)]))
#     elements.append(t2); elements.append(Spacer(1,20))
#
#     elements.append(Paragraph("Applications", styles["Heading2"]))
#     apps = [["Name","Version","Date","Size"]]
#     for l in safe_json(r[6]):
#         if "|" in l: apps.append(l.split("|",3))
#     t3 = Table(apps, colWidths=[180,90,100,100])
#     t3.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.black),
#                             ('BACKGROUND',(0,0),(-1,0),colors.lightgrey)]))
#     elements.append(t3)
#
#     doc.build(elements)
#
#     return send_file(path, as_attachment=True,
#                      mimetype="application/pdf",
#                      download_name=f"{uuid}.pdf")
#
#
# @app.route("/shutdown", methods=["POST"])
# def shutdown():
#     shutdown_flag.set()
#     os._exit(0)
#
#
# # ---------------- RUN ----------------
#
# if __name__ == "__main__":
#     port = int(os.environ.get("PORT", 9001))
#     serve(app, host="0.0.0.0", port=port)
















# postgre


# import os
# import sqlite3
# import logging
# from flask import Flask, request, jsonify, render_template
#
# app = Flask(__name__)
# logging.basicConfig(level=logging.INFO)
#
# DB_FILE = "dashboard.db"
#
#
# # ----------------------------
# # Database helpers
# # ----------------------------
# def get_db():
#     return sqlite3.connect(DB_FILE, check_same_thread=False)
#
#
# def init_db():
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("""
#         CREATE TABLE IF NOT EXISTS clients (
#             uuid TEXT PRIMARY KEY,
#             mac TEXT,
#             hostname TEXT,
#             timestamp TEXT,
#             hardware TEXT,
#             apps TEXT
#         )
#     """)
#     con.commit()
#     con.close()
#
#
# # ----------------------------
# # Routes
# # ----------------------------
# @app.route("/")
# def dashboard():
#     return render_template("dashboard.html")
#
#
# @app.route("/api/report", methods=["POST"])
# def api_report():
#     try:
#         data = request.get_json(force=True)
#
#         uuid_ = data.get("uuid")
#         mac = data.get("mac")
#         hostname = data.get("hostname")
#         timestamp = data.get("timestamp")
#         hardware = data.get("hardware")
#         apps = data.get("apps")
#
#         if not uuid_:
#             return jsonify({"status": "error", "msg": "Missing uuid"}), 400
#
#         con = get_db()
#         cur = con.cursor()
#
#         cur.execute("""
#             INSERT INTO clients (uuid, mac, hostname, timestamp, hardware, apps)
#             VALUES (?, ?, ?, ?, ?, ?)
#             ON CONFLICT(uuid) DO UPDATE SET
#                 mac=excluded.mac,
#                 hostname=excluded.hostname,
#                 timestamp=excluded.timestamp,
#                 hardware=excluded.hardware,
#                 apps=excluded.apps
#         """, (uuid_, mac, hostname, timestamp, hardware, apps))
#
#         con.commit()
#         con.close()
#
#         return jsonify({"status": "ok"})
#
#     except Exception as e:
#         app.logger.exception("Error in /api/report")
#         return jsonify({"status": "error", "msg": str(e)}), 500
#
#
# @app.route("/api/clients", methods=["GET"])
# def api_clients():
#     try:
#         con = get_db()
#         cur = con.cursor()
#         cur.execute("SELECT * FROM clients")
#         rows = cur.fetchall()
#         con.close()
#
#         result = []
#         for r in rows:
#             result.append({
#                 "uuid": r[0],
#                 "mac": r[1],
#                 "hostname": r[2],
#                 "timestamp": r[3],
#                 "hardware": r[4],
#                 "apps": r[5]
#             })
#
#         return jsonify(result)
#
#     except Exception as e:
#         app.logger.exception("Error in /api/clients")
#         return jsonify({"status": "error", "msg": str(e)}), 500
#
#
# # ----------------------------
# # Startup
# # ----------------------------
# if __name__ == "__main__":
#     init_db()
#     port = int(os.environ.get("PORT", 5000))
#     app.run(host="0.0.0.0", port=port)











# 2nd
import os, psycopg2, datetime
from flask import Flask, jsonify, request, render_template, send_file
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


app = Flask(__name__)
DATABASE_URL = os.environ.get("")

def get_db():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def init_db():
    con = get_db()
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        id SERIAL PRIMARY KEY,
        uuid TEXT UNIQUE,
        mac TEXT,
        hostname TEXT,
        ip TEXT,
        last_seen TIMESTAMPTZ,
        hardware TEXT,
        apps TEXT
    )
    """)
    con.commit()
    con.close()

@app.route("/")
def index():
    return render_template("dashboard.html")

@app.route("/api/report", methods=["POST"])
def api_report():
    data = request.json
    con = get_db()
    cur = con.cursor()
    now = datetime.datetime.now(datetime.UTC)

    cur.execute("""
    INSERT INTO clients (uuid, mac, hostname, ip, last_seen, hardware, apps)
    VALUES (%s,%s,%s,%s,%s,%s,%s)
    ON CONFLICT (uuid) DO UPDATE SET
        mac=EXCLUDED.mac,
        hostname=EXCLUDED.hostname,
        ip=EXCLUDED.ip,
        last_seen=EXCLUDED.last_seen,
        hardware=EXCLUDED.hardware,
        apps=EXCLUDED.apps
    """, (
        data["uuid"], data["mac"], data["hostname"],
        request.remote_addr, now,
        data["hardware"], data["apps"]
    ))

    con.commit()
    con.close()
    return jsonify({"status": "ok"})

@app.route("/api/clients")
def api_clients():
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT uuid, hostname, ip, last_seen FROM clients")
    rows = cur.fetchall()
    now = datetime.datetime.now(datetime.UTC)
    result = []

    for uuid_, hostname, ip, last_seen in rows:
        if last_seen:
            delta = (now - last_seen).total_seconds()
            status = "Online" if delta < 60 else "Offline"
            last_seen_val = last_seen.isoformat()
        else:
            status = "Offline"
            last_seen_val = None

        result.append({
            "uuid": uuid_,
            "hostname": hostname,
            "ip": ip,
            "last_seen": last_seen_val,
            "status": status
        })

    con.close()
    return jsonify(result)

@app.route("/api/client/<uuid>")
def api_client(uuid):
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT hostname, hardware, apps FROM clients WHERE uuid=%s", (uuid,))
    row = cur.fetchone()
    con.close()

    if not row:
        return jsonify({"error": "Not found"}), 404

    hostname, hardware, apps = row
    return jsonify({
        "uuid": uuid,
        "hostname": hostname,
        "hardware": hardware.split("\n") if hardware else [],
        "apps": apps.split("\n") if apps else []
    })

@app.route("/api/client/<uuid>/pdf")
def client_pdf(uuid):
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT hostname, hardware, apps FROM clients WHERE uuid=%s", (uuid,))
    row = cur.fetchone()
    con.close()

    if not row:
        return "Not found", 404

    hostname, hardware, apps = row
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    y = 800
    p.drawString(50, y, f"Client Report: {hostname} ({uuid})")

    y -= 30
    p.drawString(50, y, "Hardware:")
    for line in hardware.split("\n"):
        y -= 15
        p.drawString(60, y, line)

    y -= 30
    p.drawString(50, y, "Installed Apps:")
    for line in apps.split("\n"):
        y -= 15
        p.drawString(60, y, line)

    p.showPage()
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"{hostname}_report.pdf")

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
