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

# app = Flask(__name__)
# logging.basicConfig(level=logging.INFO)

# DB_FILE = "dashboard.db"


# # ----------------------------
# # Database helpers
# # ----------------------------
# def get_db():
#     return sqlite3.connect(DB_FILE, check_same_thread=False)


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


# # ----------------------------
# # Routes
# # ----------------------------
# @app.route("/")
# def dashboard():
#     return render_template("dashboard.html")


# @app.route("/api/report", methods=["POST"])
# def api_report():
#     try:
#         data = request.get_json(force=True)

#         uuid_ = data.get("uuid")
#         mac = data.get("mac")
#         hostname = data.get("hostname")
#         timestamp = data.get("timestamp")
#         hardware = data.get("hardware")
#         apps = data.get("apps")

#         if not uuid_:
#             return jsonify({"status": "error", "msg": "Missing uuid"}), 400

#         con = get_db()
#         cur = con.cursor()

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

#         con.commit()
#         con.close()

#         return jsonify({"status": "ok"})

#     except Exception as e:
#         app.logger.exception("Error in /api/report")
#         return jsonify({"status": "error", "msg": str(e)}), 500


# @app.route("/api/clients", methods=["GET"])
# def api_clients():
#     try:
#         con = get_db()
#         cur = con.cursor()
#         cur.execute("SELECT * FROM clients")
#         rows = cur.fetchall()
#         con.close()

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

#         return jsonify(result)

#     except Exception as e:
#         app.logger.exception("Error in /api/clients")
#         return jsonify({"status": "error", "msg": str(e)}), 500


# # ----------------------------
# # Startup
# # ----------------------------
# if __name__ == "__main__":
#     init_db()
#     port = int(os.environ.get("PORT", 5000))
#     app.run(host="0.0.0.0", port=port)











# import os, json, datetime, psycopg2, tempfile
# from flask import Flask, jsonify, render_template, send_file, request
# from reportlab.lib.pagesizes import A4
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.lib import colors

# DATABASE_URL = os.environ.get("DATABASE_URL")

# app = Flask(__name__, template_folder="templates")

# # ---------------- DATABASE ----------------
# def get_db():
#     return psycopg2.connect(DATABASE_URL, sslmode="require", connect_timeout=5)

# def init_db():
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("""
#     CREATE TABLE IF NOT EXISTS clients (
#         client_uuid TEXT PRIMARY KEY,
#         mac_address TEXT,
#         hostname TEXT,
#         last_seen TEXT,
#         client_ip TEXT,
#         hardware_info TEXT,
#         installed_apps TEXT
#     )
#     """)
#     con.commit()
#     con.close()

# # ---------------- HELPERS ----------------
# def safe_json(v):
#     try:
#         return json.loads(v)
#     except:
#         return v.splitlines()

# def status_from_last_seen(ts):
#     try:
#         t = datetime.datetime.strptime(ts,"%Y-%m-%d %H:%M:%S")
#         return "Online" if (datetime.datetime.now()-t).seconds<=60 else "Offline"
#     except:
#         return "Offline"

# # ---------------- ROUTES ----------------
# @app.route("/")
# def dashboard():
#     return render_template("dashboard.html")

# @app.route("/api/report", methods=["POST"])
# def api_report():
#     data = request.json
#     ip = request.remote_addr

#     con = get_db()
#     cur = con.cursor()

#     cur.execute("""
#     INSERT INTO clients VALUES (%s,%s,%s,%s,%s,%s,%s)
#     ON CONFLICT(client_uuid) DO UPDATE SET
#         mac_address=EXCLUDED.mac_address,
#         hostname=EXCLUDED.hostname,
#         last_seen=EXCLUDED.last_seen,
#         client_ip=EXCLUDED.client_ip,
#         hardware_info=EXCLUDED.hardware_info,
#         installed_apps=EXCLUDED.installed_apps
#     """, (
#         data["uuid"], data["mac"], data["hostname"],
#         data["timestamp"], ip, data["hardware"], data["apps"]
#     ))

#     con.commit()
#     con.close()
#     return jsonify({"status": "ok"})

# @app.route("/api/clients")
# def api_clients():
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("SELECT * FROM clients")
#     rows = cur.fetchall()
#     con.close()

#     return jsonify([{
#         "uuid":r[0],
#         "mac":r[1],
#         "hostname":r[2],
#         "last_seen":r[3],
#         "ip":r[4],
#         "status":status_from_last_seen(r[3])
#     } for r in rows])

# @app.route("/api/client/<uuid>")
# def api_client(uuid):
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("SELECT * FROM clients WHERE client_uuid=%s", (uuid,))
#     r = cur.fetchone()
#     con.close()

#     return jsonify({
#         "uuid":r[0],
#         "mac":r[1],
#         "hostname":r[2],
#         "last_seen":r[3],
#         "ip":r[4],
#         "hardware":safe_json(r[5]),
#         "apps":safe_json(r[6])
#     })

# @app.route("/export/pdf/<uuid>")
# def export_pdf(uuid):
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("SELECT * FROM clients WHERE client_uuid=%s", (uuid,))
#     r = cur.fetchone()
#     con.close()

#     fd, path = tempfile.mkstemp(suffix=".pdf")
#     os.close(fd)

#     doc = SimpleDocTemplate(path, pagesize=A4)
#     styles = getSampleStyleSheet()
#     elements = []

#     elements.append(Paragraph("Client Report", styles["Title"]))
#     elements.append(Spacer(1, 12))

#     info = [["Field","Value"],
#             ["UUID",r[0]],["MAC",r[1]],["Hostname",r[2]],
#             ["Last Seen",r[3]],["IP",r[4]]]

#     t1 = Table(info, colWidths=[120,350])
#     t1.setStyle(TableStyle([
#         ('GRID',(0,0),(-1,-1),0.5,colors.black),
#         ('BACKGROUND',(0,0),(-1,0),colors.lightgrey)
#     ]))
#     elements.append(t1)

#     doc.build(elements)
#     return send_file(path, as_attachment=True,
#                      mimetype="application/pdf",
#                      download_name=f"{uuid}.pdf")

# # ---------------- RUN ----------------
# if __name__ == "__main__":
#     init_db()
#     app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

# # # 2nd
# import os, json, datetime, psycopg2, tempfile, csv
# from flask import Flask, jsonify, render_template, send_file, request, Response
# from reportlab.lib.pagesizes import A4
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.lib import colors

# DATABASE_URL = os.environ.get("DATABASE_URL")

# app = Flask(__name__, template_folder="templates")

# # ---------------- DATABASE ----------------
# def get_db():
#     return psycopg2.connect(DATABASE_URL, sslmode="require", connect_timeout=5)

# def init_db():
#     con = get_db()
#     cur = con.cursor()

#     cur.execute("""
#     CREATE TABLE IF NOT EXISTS clients (
#         client_uuid TEXT PRIMARY KEY,
#         mac_address TEXT,
#         hostname TEXT,
#         last_seen TEXT,
#         client_ip TEXT,
#         hardware_info TEXT,
#         installed_apps TEXT
#     )
#     """)

#     columns = {
#         "client_uuid": "TEXT",
#         "mac_address": "TEXT",
#         "hostname": "TEXT",
#         "last_seen": "TEXT",
#         "client_ip": "TEXT",
#         "hardware_info": "TEXT",
#         "installed_apps": "TEXT"
#     }

#     for col, coltype in columns.items():
#         cur.execute(f"""
#         DO $$
#         BEGIN
#             IF NOT EXISTS (
#                 SELECT 1 FROM information_schema.columns
#                 WHERE table_name='clients' AND column_name='{col}'
#             ) THEN
#                 ALTER TABLE clients ADD COLUMN {col} {coltype};
#             END IF;
#         END$$;
#         """)

#     con.commit()
#     con.close()

# # ---------------- HELPERS ----------------
# def safe_json(v):
#     try:
#         return json.loads(v)
#     except:
#         return v.splitlines() if isinstance(v, str) else v

# def status_from_last_seen(ts):
#     try:
#         t = datetime.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
#         return "Online" if (datetime.datetime.now() - t).seconds <= 60 else "Offline"
#     except:
#         return "Offline"

# # ---------------- ROUTES ----------------
# @app.route("/")
# def dashboard():
#     return render_template("dashboard.html")

# @app.route("/api/report", methods=["POST"])
# def api_report():
#     data = request.json
#     ip = request.remote_addr

#     con = get_db()
#     cur = con.cursor()

#     cur.execute("""
#     INSERT INTO clients VALUES (%s,%s,%s,%s,%s,%s,%s)
#     ON CONFLICT(client_uuid) DO UPDATE SET
#         mac_address=EXCLUDED.mac_address,
#         hostname=EXCLUDED.hostname,
#         last_seen=EXCLUDED.last_seen,
#         client_ip=EXCLUDED.client_ip,
#         hardware_info=EXCLUDED.hardware_info,
#         installed_apps=EXCLUDED.installed_apps
#     """, (
#         data["uuid"], data["mac"], data["hostname"],
#         data["timestamp"], ip, data["hardware"], data["apps"]
#     ))

#     con.commit()
#     con.close()
#     return jsonify({"status": "ok"})

# @app.route("/api/clients")
# def api_clients():
#     search = request.args.get("search")

#     con = get_db()
#     cur = con.cursor()

#     if search:
#         cur.execute("""
#         SELECT * FROM clients
#         WHERE client_uuid ILIKE %s OR hostname ILIKE %s OR mac_address ILIKE %s
#         """, (f"%{search}%", f"%{search}%", f"%{search}%"))
#     else:
#         cur.execute("SELECT * FROM clients")

#     rows = cur.fetchall()
#     con.close()

#     return jsonify([{
#         "uuid": r[0],
#         "mac": r[1],
#         "hostname": r[2],
#         "last_seen": r[3],
#         "ip": r[4],
#         "status": status_from_last_seen(r[3])
#     } for r in rows])

# @app.route("/api/client/<uuid>")
# def api_client(uuid):
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("SELECT * FROM clients WHERE client_uuid=%s", (uuid,))
#     r = cur.fetchone()
#     con.close()

#     if not r:
#         return jsonify({"error": "Client not found"}), 404

#     return jsonify({
#         "uuid": r[0],
#         "mac": r[1],
#         "hostname": r[2],
#         "last_seen": r[3],
#         "ip": r[4],
#         "hardware": safe_json(r[5]),
#         "apps": safe_json(r[6])
#     })

# @app.route("/export/pdf/<uuid>")
# def export_pdf(uuid):
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("SELECT * FROM clients WHERE client_uuid=%s", (uuid,))
#     r = cur.fetchone()
#     con.close()

#     if not r:
#         return "Client not found", 404

#     fd, path = tempfile.mkstemp(suffix=".pdf")
#     os.close(fd)

#     doc = SimpleDocTemplate(path, pagesize=A4)
#     styles = getSampleStyleSheet()
#     elements = []

#     elements.append(Paragraph("Client Report", styles["Title"]))
#     elements.append(Spacer(1, 12))

#     info = [
#         ["Field", "Value"],
#         ["UUID", r[0]],
#         ["MAC", r[1]],
#         ["Hostname", r[2]],
#         ["Last Seen", r[3]],
#         ["IP", r[4]],
#     ]

#     t1 = Table(info, colWidths=[120, 350])
#     t1.setStyle(TableStyle([
#         ('GRID', (0,0), (-1,-1), 0.5, colors.black),
#         ('BACKGROUND', (0,0), (-1,0), colors.lightgrey)
#     ]))
#     elements.append(t1)

#     doc.build(elements)
#     return send_file(path, as_attachment=True,
#                      mimetype="application/pdf",
#                      download_name=f"{uuid}.pdf")

# @app.route("/export/csv")
# def export_csv():
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("SELECT client_uuid, mac_address, hostname, last_seen, client_ip FROM clients")
#     rows = cur.fetchall()
#     con.close()

#     def generate():
#         data = csv.writer(tempfile.TemporaryFile(mode="w+"))
#         yield "UUID,MAC,Hostname,Last Seen,IP\n"
#         for r in rows:
#             yield f"{r[0]},{r[1]},{r[2]},{r[3]},{r[4]}\n"

#     return Response(generate(), mimetype="text/csv",
#                     headers={"Content-Disposition": "attachment;filename=clients.csv"})

# # ---------------- RUN ----------------
# if __name__ == "__main__":
#     init_db()
#     app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))















import os, json, datetime, psycopg2, tempfile, csv
from flask import Flask, jsonify, render_template, send_file, request, Response
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

DATABASE_URL = os.environ.get("DATABASE_URL")

app = Flask(__name__, template_folder="templates")
@app.route("/ping")
def ping():
    return "SERVER IS RUNNING", 200


# ---------------- DATABASE ----------------
def get_db():
    return psycopg2.connect(DATABASE_URL, sslmode="require", connect_timeout=5)

def init_db():
    con = get_db()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        client_uuid TEXT PRIMARY KEY,
        mac_address TEXT,
        hostname TEXT,
        last_seen TEXT,
        client_ip TEXT,
        hardware_info TEXT,
        installed_apps TEXT
    )
    """)

    columns = {
        "client_uuid": "TEXT",
        "mac_address": "TEXT",
        "hostname": "TEXT",
        "last_seen": "TEXT",
        "client_ip": "TEXT",
        "hardware_info": "TEXT",
        "installed_apps": "TEXT"
    }

    for col, coltype in columns.items():
        cur.execute(f"""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='clients' AND column_name='{col}'
            ) THEN
                ALTER TABLE clients ADD COLUMN {col} {coltype};
            END IF;
        END$$;
        """)

    con.commit()
    con.close()

# ---------------- HELPERS ----------------
def safe_json(v):
    try:
        return json.loads(v)
    except:
        return v.splitlines() if isinstance(v, str) else v

def status_from_last_seen(ts):
    try:
        t = datetime.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
        return "Online" if (datetime.datetime.now() - t).seconds <= 60 else "Offline"
    except:
        return "Offline"

# ---------------- ROUTES ----------------
@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/api/report", methods=["POST"])
def api_report():
    data = request.json
    ip = request.remote_addr

    con = get_db()
    cur = con.cursor()

    cur.execute("""
    INSERT INTO clients
        (client_uuid, mac_address, hostname, last_seen, client_ip, hardware_info, installed_apps)
    VALUES (%s,%s,%s,%s,%s,%s,%s)
    ON CONFLICT(client_uuid) DO UPDATE SET
        mac_address=EXCLUDED.mac_address,
        hostname=EXCLUDED.hostname,
        last_seen=EXCLUDED.last_seen,
        client_ip=EXCLUDED.client_ip,
        hardware_info=EXCLUDED.hardware_info,
        installed_apps=EXCLUDED.installed_apps
    """, (
        data["uuid"], data["mac"], data["hostname"],
        data["timestamp"], ip, data["hardware"], data["apps"]
    ))

    con.commit()
    con.close()
    return jsonify({"status": "ok"})

@app.route("/api/clients")
def api_clients():
    search = request.args.get("search")

    con = get_db()
    cur = con.cursor()

    if search:
        cur.execute("""
        SELECT * FROM clients
        WHERE client_uuid ILIKE %s OR hostname ILIKE %s OR mac_address ILIKE %s
        """, (f"%{search}%", f"%{search}%", f"%{search}%"))
    else:
        cur.execute("SELECT * FROM clients")

    rows = cur.fetchall()
    con.close()

    return jsonify([{
        "uuid": r[0],
        "mac": r[1],
        "hostname": r[2],
        "last_seen": r[3],
        "ip": r[4],
        "status": status_from_last_seen(r[3])
    } for r in rows])

@app.route("/api/client/<uuid>")
def api_client(uuid):
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT * FROM clients WHERE client_uuid=%s", (uuid,))
    r = cur.fetchone()
    con.close()

    if not r:
        return jsonify({"error": "Client not found"}), 404

    return jsonify({
        "uuid": r[0],
        "mac": r[1],
        "hostname": r[2],
        "last_seen": r[3],
        "ip": r[4],
        "hardware": safe_json(r[5]),
        "apps": safe_json(r[6])
    })

@app.route("/export/pdf/<uuid>")
def export_pdf(uuid):
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT * FROM clients WHERE client_uuid=%s", (uuid,))
    r = cur.fetchone()
    con.close()

    if not r:
        return "Client not found", 404

    fd, path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)

    doc = SimpleDocTemplate(path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Client Report", styles["Title"]))
    elements.append(Spacer(1, 12))

    info = [
        ["Field", "Value"],
        ["UUID", r[0]],
        ["MAC", r[1]],
        ["Hostname", r[2]],
        ["Last Seen", r[3]],
        ["IP", r[4]],
    ]

    t1 = Table(info, colWidths=[120, 350])
    t1.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey)
    ]))
    elements.append(t1)

    doc.build(elements)
    return send_file(path, as_attachment=True,
                     mimetype="application/pdf",
                     download_name=f"{uuid}.pdf")

@app.route("/export/csv")
def export_csv():
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT client_uuid, mac_address, hostname, last_seen, client_ip FROM clients")
    rows = cur.fetchall()
    con.close()

    def generate():
        yield "UUID,MAC,Hostname,Last Seen,IP\n"
        for r in rows:
            yield f"{r[0]},{r[1]},{r[2]},{r[3]},{r[4]}\n"

    return Response(generate(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=clients.csv"})

# ---------------- RUN ----------------
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
