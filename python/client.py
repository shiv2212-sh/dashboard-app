
# # # after implementing app size
#
# import socket
# import datetime
# import platform
# import os
# import uuid
# import sqlite3
# import psutil
# import subprocess
#
# TCP_HOST = "10.0.5.28"
# TCP_PORT = 9002
# DB_FILE = "client_data.db"
# CLIENT_ID_FILE = "client_id.txt"
#
#
# # ----------------------------
# # Date helpers
# # ----------------------------
# def format_yyyymmdd(raw):
#     try:
#         return datetime.datetime.strptime(raw, "%Y%m%d").strftime("%Y-%m-%d")
#     except Exception:
#         return "-"
#
#
# # ----------------------------
# # Client identity
# # ----------------------------
# def get_or_create_client_uuid():
#     if os.path.exists(CLIENT_ID_FILE):
#         return open(CLIENT_ID_FILE).read().strip()
#
#     new_id = str(uuid.uuid4())
#     with open(CLIENT_ID_FILE, "w") as f:
#         f.write(new_id)
#     return new_id
#
#
# def get_mac_address():
#     return hex(uuid.getnode())
#
#
# # ----------------------------
# # Database (local fallback)
# # ----------------------------
# def init_db():
#     conn = sqlite3.connect(DB_FILE)
#     cur = conn.cursor()
#     cur.execute("""
#         CREATE TABLE IF NOT EXISTS system_snapshot (
#             client_uuid TEXT PRIMARY KEY,
#             mac_address TEXT,
#             hostname TEXT,
#             timestamp TEXT,
#             hardware_info TEXT,
#             installed_apps TEXT
#         )
#     """)
#     conn.commit()
#     conn.close()
#
#
# def upsert_snapshot(client_uuid, mac, hostname, timestamp, hw, apps):
#     conn = sqlite3.connect(DB_FILE)
#     cur = conn.cursor()
#     cur.execute("""
#         INSERT INTO system_snapshot
#         VALUES (?, ?, ?, ?, ?, ?)
#         ON CONFLICT(client_uuid) DO UPDATE SET
#             mac_address=excluded.mac_address,
#             hostname=excluded.hostname,
#             timestamp=excluded.timestamp,
#             hardware_info=excluded.hardware_info,
#             installed_apps=excluded.installed_apps
#     """, (client_uuid, mac, hostname, timestamp, hw, apps))
#     conn.commit()
#     conn.close()
#
#
# # ----------------------------
# # Utils
# # ----------------------------
# def get_folder_size_mb(path):
#     total = 0
#     try:
#         for root, dirs, files in os.walk(path):
#             for f in files:
#                 try:
#                     fp = os.path.join(root, f)
#                     total += os.path.getsize(fp)
#                 except:
#                     pass
#     except:
#         pass
#     return round(total / (1024 * 1024), 2)
#
#
# # ----------------------------
# # Installed applications (WITH SIZE)
# # ----------------------------
# def get_installed_apps():
#     apps = []
#     if platform.system() == "Windows":
#         try:
#             import winreg
#             paths = [
#                 r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall",
#                 r"SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall"
#             ]
#             for path in paths:
#                 try:
#                     key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
#                     for i in range(winreg.QueryInfoKey(key)[0]):
#                         sub = winreg.OpenKey(key, winreg.EnumKey(key, i))
#                         try:
#                             name = winreg.QueryValueEx(sub, "DisplayName")[0]
#                             version = winreg.QueryValueEx(sub, "DisplayVersion")[0]
#                             raw_date = winreg.QueryValueEx(sub, "InstallDate")[0]
#                             install_date = format_yyyymmdd(raw_date)
#
#                             size_mb = "-"
#                             # Try InstallLocation folder size
#                             try:
#                                 loc = winreg.QueryValueEx(sub, "InstallLocation")[0]
#                                 if loc and os.path.exists(loc):
#                                     size_mb = get_folder_size_mb(loc)
#                             except:
#                                 pass
#
#                             # Fallback to EstimatedSize (KB → MB)
#                             if size_mb == "-":
#                                 try:
#                                     est_kb = winreg.QueryValueEx(sub, "EstimatedSize")[0]
#                                     size_mb = round(est_kb / 1024, 2)
#                                 except:
#                                     pass
#
#                             apps.append({
#                                 "name": name,
#                                 "version": version,
#                                 "install_date": install_date,
#                                 "size": size_mb
#                             })
#                         except:
#                             pass
#                 except:
#                     pass
#         except:
#             pass
#
#     if not apps:
#         apps = [{"name": "No apps found", "version": "-", "install_date": "-", "size": "-"}]
#
#     return apps
#
#
# # ----------------------------
# # Hardware
# # ----------------------------
# def get_hardware_info():
#     disk = psutil.disk_usage('/')
#     return "\n".join([
#         f"OS: {platform.system()} {platform.release()}",
#         f"Architecture: {platform.machine()}",
#         f"Processor: {platform.processor()}",
#         f"CPU Cores: {os.cpu_count()}",
#         f"Physical RAM: {round(psutil.virtual_memory().total / (1024**3), 2)} GB",
#         f"Available RAM: {round(psutil.virtual_memory().available / (1024**3), 2)} GB",
#         f"Disk Total: {round(disk.total / (1024**3), 2)} GB",
#         f"Disk Used: {round(disk.used / (1024**3), 2)} GB",
#         f"Disk Free: {round(disk.free / (1024**3), 2)} GB",
#         f"Python Version: {platform.python_version()}"
#     ])
#
#
# # ----------------------------
# # Network
# # ----------------------------
# def send_text(sock, text):
#     payload = text.encode()
#     sock.sendall(f"{len(payload)}\n".encode() + payload)
#
#
# # ----------------------------
# # Main
# # ----------------------------
# def start_client():
#     print("\n========== CLIENT STARTED ==========\n")
#
#     init_db()
#
#     client_uuid = get_or_create_client_uuid()
#     mac = get_mac_address()
#     hostname = platform.node()
#     apps_list = get_installed_apps()
#
#     apps = "\n".join(
#         f"{a['name']}|{a['version']}|{a['install_date']}|{a['size']}"
#         for a in apps_list
#     )
#
#     hw = get_hardware_info()
#     timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#
#     text_data = (
#         f"CLIENT_UUID: {client_uuid}\n"
#         f"MAC_ADDRESS: {mac}\n"
#         f"HOSTNAME: {hostname}\n"
#         f"TIMESTAMP: {timestamp}\n\n"
#         f"=== HARDWARE ===\n{hw}\n\n"
#         f"=== APPLICATIONS ===\n{apps}"
#     )
#
#     print("DATA BEING SENT TO SERVER:\n")
#     print(text_data)
#     print("\n====================================\n")
#
#     upsert_snapshot(client_uuid, mac, hostname, timestamp, hw, apps)
#
#     try:
#         print(f"Connecting to {TCP_HOST}:{TCP_PORT} ...")
#         s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         s.settimeout(5)
#         s.connect((TCP_HOST, TCP_PORT))
#
#         s.sendall(b"get apps\n")
#         send_text(s, text_data)
#
#         cmd = s.recv(1024).decode().strip()
#         print("Server replied:", cmd)
#
#         s.close()
#         print("Data sent successfully")
#
#     except Exception as e:
#         print("Server not available:", e)
#
#     print("\n========== CLIENT FINISHED ==========\n")
#
#
# if __name__ == "__main__":
#     start_client()
#     input("\nPress ENTER to close the terminal...")













# import socket
# import datetime
# import platform
# import os
# import uuid
# import sqlite3
# import psutil
#
# TCP_PORT = 9002
# DB_FILE = "client_data.db"
# CLIENT_ID_FILE = "client_id.txt"
#
#
# # ----------------------------
# # Date helpers
# # ----------------------------
# def format_yyyymmdd(raw):
#     try:
#         return datetime.datetime.strptime(raw, "%Y%m%d").strftime("%Y-%m-%d")
#     except Exception:
#         return "-"
#
#
# # ----------------------------
# # Client identity
# # ----------------------------
# def get_or_create_client_uuid():
#     if os.path.exists(CLIENT_ID_FILE):
#         return open(CLIENT_ID_FILE).read().strip()
#
#     new_id = str(uuid.uuid4())
#     with open(CLIENT_ID_FILE, "w") as f:
#         f.write(new_id)
#     return new_id
#
#
# def get_mac_address():
#     return hex(uuid.getnode())
#
#
# # ----------------------------
# # Database (local fallback)
# # ----------------------------
# def init_db():
#     conn = sqlite3.connect(DB_FILE)
#     cur = conn.cursor()
#     cur.execute("""
#         CREATE TABLE IF NOT EXISTS system_snapshot (
#             client_uuid TEXT PRIMARY KEY,
#             mac_address TEXT,
#             hostname TEXT,
#             timestamp TEXT,
#             hardware_info TEXT,
#             installed_apps TEXT
#         )
#     """)
#     conn.commit()
#     conn.close()
#
#
# def upsert_snapshot(client_uuid, mac, hostname, timestamp, hw, apps):
#     conn = sqlite3.connect(DB_FILE)
#     cur = conn.cursor()
#     cur.execute("""
#         INSERT INTO system_snapshot
#         VALUES (?, ?, ?, ?, ?, ?)
#         ON CONFLICT(client_uuid) DO UPDATE SET
#             mac_address=excluded.mac_address,
#             hostname=excluded.hostname,
#             timestamp=excluded.timestamp,
#             hardware_info=excluded.hardware_info,
#             installed_apps=excluded.installed_apps
#     """, (client_uuid, mac, hostname, timestamp, hw, apps))
#     conn.commit()
#     conn.close()
#
#
# # ----------------------------
# # Utils
# # ----------------------------
# def get_folder_size_mb(path):
#     total = 0
#     try:
#         for root, dirs, files in os.walk(path):
#             for f in files:
#                 try:
#                     fp = os.path.join(root, f)
#                     total += os.path.getsize(fp)
#                 except:
#                     pass
#     except:
#         pass
#     return round(total / (1024 * 1024), 2)
#
#
# # ----------------------------
# # Installed applications (WITH SIZE)
# # ----------------------------
# def get_installed_apps():
#     apps = []
#     if platform.system() == "Windows":
#         try:
#             import winreg
#             paths = [
#                 r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall",
#                 r"SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall"
#             ]
#             for path in paths:
#                 try:
#                     key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
#                     for i in range(winreg.QueryInfoKey(key)[0]):
#                         sub = winreg.OpenKey(key, winreg.EnumKey(key, i))
#                         try:
#                             name = winreg.QueryValueEx(sub, "DisplayName")[0]
#                             version = winreg.QueryValueEx(sub, "DisplayVersion")[0]
#                             raw_date = winreg.QueryValueEx(sub, "InstallDate")[0]
#                             install_date = format_yyyymmdd(raw_date)
#
#                             size_mb = "-"
#                             try:
#                                 loc = winreg.QueryValueEx(sub, "InstallLocation")[0]
#                                 if loc and os.path.exists(loc):
#                                     size_mb = get_folder_size_mb(loc)
#                             except:
#                                 pass
#
#                             if size_mb == "-":
#                                 try:
#                                     est_kb = winreg.QueryValueEx(sub, "EstimatedSize")[0]
#                                     size_mb = round(est_kb / 1024, 2)
#                                 except:
#                                     pass
#
#                             apps.append({
#                                 "name": name,
#                                 "version": version,
#                                 "install_date": install_date,
#                                 "size": size_mb
#                             })
#                         except:
#                             pass
#                 except:
#                     pass
#         except:
#             pass
#
#     if not apps:
#         apps = [{"name": "No apps found", "version": "-", "install_date": "-", "size": "-"}]
#
#     return apps
#
#
# # ----------------------------
# # Hardware
# # ----------------------------
# def get_hardware_info():
#     disk = psutil.disk_usage('/')
#     return "\n".join([
#         f"OS: {platform.system()} {platform.release()}",
#         f"Architecture: {platform.machine()}",
#         f"Processor: {platform.processor()}",
#         f"CPU Cores: {os.cpu_count()}",
#         f"Physical RAM: {round(psutil.virtual_memory().total / (1024**3), 2)} GB",
#         f"Available RAM: {round(psutil.virtual_memory().available / (1024**3), 2)} GB",
#         f"Disk Total: {round(disk.total / (1024**3), 2)} GB",
#         f"Disk Used: {round(disk.used / (1024**3), 2)} GB",
#         f"Disk Free: {round(disk.free / (1024**3), 2)} GB",
#         f"Python Version: {platform.python_version()}"
#     ])
#
#
# # ----------------------------
# # Network
# # ----------------------------
# def send_text(sock, text):
#     payload = text.encode()
#     sock.sendall(f"{len(payload)}\n".encode() + payload)
#
#
# # ----------------------------
# # Main
# # ----------------------------
# def start_client():
#     print("\n========== CLIENT STARTED ==========\n")
#
#     server_host = input("Enter Server IP / Domain: ").strip()
#     if not server_host:
#         print("No server entered. Exiting.")
#         return
#
#     init_db()
#
#     client_uuid = get_or_create_client_uuid()
#     mac = get_mac_address()
#     hostname = platform.node()
#     apps_list = get_installed_apps()
#
#     apps = "\n".join(
#         f"{a['name']}|{a['version']}|{a['install_date']}|{a['size']}"
#         for a in apps_list
#     )
#
#     hw = get_hardware_info()
#     timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#
#     text_data = (
#         f"CLIENT_UUID: {client_uuid}\n"
#         f"MAC_ADDRESS: {mac}\n"
#         f"HOSTNAME: {hostname}\n"
#         f"TIMESTAMP: {timestamp}\n\n"
#         f"=== HARDWARE ===\n{hw}\n\n"
#         f"=== APPLICATIONS ===\n{apps}"
#     )
#
#     print("DATA BEING SENT TO SERVER:\n")
#     print(text_data)
#     print("\n====================================\n")
#
#     upsert_snapshot(client_uuid, mac, hostname, timestamp, hw, apps)
#
#     try:
#         print(f"Connecting to {server_host}:{TCP_PORT} ...")
#         s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         s.settimeout(8)
#         s.connect((server_host, TCP_PORT))
#
#         s.sendall(b"get apps\n")
#         send_text(s, text_data)
#
#         cmd = s.recv(1024).decode().strip()
#         print("Server replied:", cmd)
#
#         s.close()
#         print("Data sent successfully")
#
#     except Exception as e:
#         print("Server not available:", e)
#
#     print("\n========== CLIENT FINISHED ==========\n")
#
#
# if __name__ == "__main__":
#     start_client()
#     input("\nPress ENTER to close the terminal...")











# import socket
# import datetime
# import platform
# import os
# import uuid
# import sqlite3
# import psutil
# import subprocess
#
# TCP_PORT = 9002
# DB_FILE = "client_data.db"
# CLIENT_ID_FILE = "client_id.txt"
#
#
# # ----------------------------
# # Date helpers
# # ----------------------------
# def format_yyyymmdd(raw):
#     try:
#         return datetime.datetime.strptime(raw, "%Y%m%d").strftime("%Y-%m-%d")
#     except Exception:
#         return "-"
#
#
# # ----------------------------
# # Client identity
# # ----------------------------
# def get_or_create_client_uuid():
#     if os.path.exists(CLIENT_ID_FILE):
#         return open(CLIENT_ID_FILE).read().strip()
#
#     new_id = str(uuid.uuid4())
#     with open(CLIENT_ID_FILE, "w") as f:
#         f.write(new_id)
#     return new_id
#
#
# def get_mac_address():
#     return hex(uuid.getnode())
#
#
# # ----------------------------
# # Database (local fallback)
# # ----------------------------
# def init_db():
#     conn = sqlite3.connect(DB_FILE)
#     cur = conn.cursor()
#     cur.execute("""
#         CREATE TABLE IF NOT EXISTS system_snapshot (
#             client_uuid TEXT PRIMARY KEY,
#             mac_address TEXT,
#             hostname TEXT,
#             timestamp TEXT,
#             hardware_info TEXT,
#             installed_apps TEXT
#         )
#     """)
#     conn.commit()
#     conn.close()
#
#
# def upsert_snapshot(client_uuid, mac, hostname, timestamp, hw, apps):
#     conn = sqlite3.connect(DB_FILE)
#     cur = conn.cursor()
#     cur.execute("""
#         INSERT INTO system_snapshot
#         VALUES (?, ?, ?, ?, ?, ?)
#         ON CONFLICT(client_uuid) DO UPDATE SET
#             mac_address=excluded.mac_address,
#             hostname=excluded.hostname,
#             timestamp=excluded.timestamp,
#             hardware_info=excluded.hardware_info,
#             installed_apps=excluded.installed_apps
#     """, (client_uuid, mac, hostname, timestamp, hw, apps))
#     conn.commit()
#     conn.close()
#
#
# # ----------------------------
# # Utils
# # ----------------------------
# def get_folder_size_mb(path):
#     total = 0
#     try:
#         for root, dirs, files in os.walk(path):
#             for f in files:
#                 try:
#                     fp = os.path.join(root, f)
#                     total += os.path.getsize(fp)
#                 except:
#                     pass
#     except:
#         pass
#     return round(total / (1024 * 1024), 2)
#
#
# # ----------------------------
# # Installed applications (CROSS-PLATFORM)
# # ----------------------------
# def get_installed_apps():
#     system = platform.system()
#     apps = []
#
#     # -------- Windows --------
#     if system == "Windows":
#         try:
#             import winreg
#             paths = [
#                 r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall",
#                 r"SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall"
#             ]
#             for path in paths:
#                 try:
#                     key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
#                     for i in range(winreg.QueryInfoKey(key)[0]):
#                         sub = winreg.OpenKey(key, winreg.EnumKey(key, i))
#                         try:
#                             name = winreg.QueryValueEx(sub, "DisplayName")[0]
#                             version = winreg.QueryValueEx(sub, "DisplayVersion")[0]
#                             raw_date = winreg.QueryValueEx(sub, "InstallDate")[0]
#                             install_date = format_yyyymmdd(raw_date)
#
#                             size_mb = "-"
#                             try:
#                                 loc = winreg.QueryValueEx(sub, "InstallLocation")[0]
#                                 if loc and os.path.exists(loc):
#                                     size_mb = get_folder_size_mb(loc)
#                             except:
#                                 pass
#
#                             if size_mb == "-":
#                                 try:
#                                     est_kb = winreg.QueryValueEx(sub, "EstimatedSize")[0]
#                                     size_mb = round(est_kb / 1024, 2)
#                                 except:
#                                     pass
#
#                             apps.append({
#                                 "name": name,
#                                 "version": version,
#                                 "install_date": install_date,
#                                 "size": size_mb
#                             })
#                         except:
#                             pass
#                 except:
#                     pass
#         except:
#             pass
#
#     # -------- macOS --------
#     elif system == "Darwin":
#         try:
#             cmd = ["system_profiler", "SPApplicationsDataType"]
#             output = subprocess.check_output(cmd, text=True, errors="ignore")
#             current = {}
#             for line in output.splitlines():
#                 line = line.strip()
#                 if not line:
#                     continue
#                 if not line.startswith("Version:") and ":" in line:
#                     key, val = line.split(":", 1)
#                     key = key.strip()
#                     val = val.strip()
#                     if key == "Location":
#                         current["size"] = "-"
#                         apps.append({
#                             "name": current.get("Name", "Unknown"),
#                             "version": current.get("Version", "-"),
#                             "install_date": "-",
#                             "size": current.get("size", "-")
#                         })
#                         current = {}
#                     else:
#                         current[key] = val
#         except:
#             pass
#
#     # -------- Linux --------
#     elif system == "Linux":
#         try:
#             # dpkg
#             try:
#                 output = subprocess.check_output(["dpkg", "-l"], text=True, errors="ignore")
#                 for line in output.splitlines():
#                     if line.startswith("ii"):
#                         parts = line.split()
#                         name = parts[1]
#                         version = parts[2]
#                         apps.append({
#                             "name": name,
#                             "version": version,
#                             "install_date": "-",
#                             "size": "-"
#                         })
#             except:
#                 pass
#
#             # rpm
#             try:
#                 output = subprocess.check_output(["rpm", "-qa"], text=True, errors="ignore")
#                 for line in output.splitlines():
#                     if "-" in line:
#                         name, version = line.rsplit("-", 1)
#                         apps.append({
#                             "name": name,
#                             "version": version,
#                             "install_date": "-",
#                             "size": "-"
#                         })
#             except:
#                 pass
#
#             # snap
#             try:
#                 output = subprocess.check_output(["snap", "list"], text=True, errors="ignore")
#                 for line in output.splitlines()[1:]:
#                     parts = line.split()
#                     if len(parts) >= 2:
#                         apps.append({
#                             "name": parts[0],
#                             "version": parts[1],
#                             "install_date": "-",
#                             "size": "-"
#                         })
#             except:
#                 pass
#         except:
#             pass
#
#     if not apps:
#         apps = [{"name": "No apps found", "version": "-", "install_date": "-", "size": "-"}]
#
#     return apps
#
#
# # ----------------------------
# # Hardware
# # ----------------------------
# def get_hardware_info():
#     disk = psutil.disk_usage('/')
#     return "\n".join([
#         f"OS: {platform.system()} {platform.release()}",
#         f"Architecture: {platform.machine()}",
#         f"Processor: {platform.processor()}",
#         f"CPU Cores: {os.cpu_count()}",
#         f"Physical RAM: {round(psutil.virtual_memory().total / (1024**3), 2)} GB",
#         f"Available RAM: {round(psutil.virtual_memory().available / (1024**3), 2)} GB",
#         f"Disk Total: {round(disk.total / (1024**3), 2)} GB",
#         f"Disk Used: {round(disk.used / (1024**3), 2)} GB",
#         f"Disk Free: {round(disk.free / (1024**3), 2)} GB",
#         f"Python Version: {platform.python_version()}"
#     ])
#
#
# # ----------------------------
# # Network
# # ----------------------------
# def send_text(sock, text):
#     payload = text.encode()
#     sock.sendall(f"{len(payload)}\n".encode() + payload)
#
#
# # ----------------------------
# # Main
# # ----------------------------
# def start_client():
#     print("\n========== CLIENT STARTED ==========\n")
#
#     server_host = input("Enter Server IP / Domain: ").strip()
#     if not server_host:
#         print("No server entered. Exiting.")
#         return
#
#     init_db()
#
#     client_uuid = get_or_create_client_uuid()
#     mac = get_mac_address()
#     hostname = platform.node()
#     apps_list = get_installed_apps()
#
#     apps = "\n".join(
#         f"{a['name']}|{a['version']}|{a['install_date']}|{a['size']}"
#         for a in apps_list
#     )
#
#     hw = get_hardware_info()
#     timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#
#     text_data = (
#         f"CLIENT_UUID: {client_uuid}\n"
#         f"MAC_ADDRESS: {mac}\n"
#         f"HOSTNAME: {hostname}\n"
#         f"TIMESTAMP: {timestamp}\n\n"
#         f"=== HARDWARE ===\n{hw}\n\n"
#         f"=== APPLICATIONS ===\n{apps}"
#     )
#
#     print("DATA BEING SENT TO SERVER:\n")
#     print(text_data)
#     print("\n====================================\n")
#
#     upsert_snapshot(client_uuid, mac, hostname, timestamp, hw, apps)
#
#     try:
#         print(f"Connecting to {server_host}:{TCP_PORT} ...")
#         s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         s.settimeout(8)
#         s.connect((server_host, TCP_PORT))
#
#         s.sendall(b"get apps\n")
#         send_text(s, text_data)
#
#         cmd = s.recv(1024).decode().strip()
#         print("Server replied:", cmd)
#
#         s.close()
#         print("Data sent successfully")
#
#     except Exception as e:
#         print("Server not available:", e)
#
#     print("\n========== CLIENT FINISHED ==========\n")
#
#
# if __name__ == "__main__":
#     start_client()
#     input("\nPress ENTER to close the terminal...")












import socket
import datetime
import platform
import os
import uuid
import sqlite3
import psutil
import tkinter as tk
from tkinter import simpledialog, messagebox

TCP_PORT = 9002
DB_FILE = "client_data.db"
CLIENT_ID_FILE = "client_id.txt"
SERVER_FILE = "last_server.txt"


# ----------------------------
# Helpers
# ----------------------------
def format_yyyymmdd(raw):
    try:
        return datetime.datetime.strptime(raw, "%Y%m%d").strftime("%Y-%m-%d")
    except Exception:
        return "-"


def get_or_create_client_uuid():
    if os.path.exists(CLIENT_ID_FILE):
        return open(CLIENT_ID_FILE).read().strip()
    new_id = str(uuid.uuid4())
    with open(CLIENT_ID_FILE, "w") as f:
        f.write(new_id)
    return new_id


def get_mac_address():
    return hex(uuid.getnode())


def get_last_server():
    if os.path.exists(SERVER_FILE):
        return open(SERVER_FILE).read().strip()
    return ""


def save_last_server(host):
    with open(SERVER_FILE, "w") as f:
        f.write(host)


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS system_snapshot (
            client_uuid TEXT PRIMARY KEY,
            mac_address TEXT,
            hostname TEXT,
            timestamp TEXT,
            hardware_info TEXT,
            installed_apps TEXT
        )
    """)
    conn.commit()
    conn.close()


def upsert_snapshot(client_uuid, mac, hostname, timestamp, hw, apps):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO system_snapshot
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(client_uuid) DO UPDATE SET
            mac_address=excluded.mac_address,
            hostname=excluded.hostname,
            timestamp=excluded.timestamp,
            hardware_info=excluded.hardware_info,
            installed_apps=excluded.installed_apps
    """, (client_uuid, mac, hostname, timestamp, hw, apps))
    conn.commit()
    conn.close()


def get_folder_size_mb(path):
    total = 0
    try:
        for root, dirs, files in os.walk(path):
            for f in files:
                try:
                    fp = os.path.join(root, f)
                    total += os.path.getsize(fp)
                except:
                    pass
    except:
        pass
    return round(total / (1024 * 1024), 2)


def get_installed_apps():
    apps = []
    if platform.system() == "Windows":
        try:
            import winreg
            paths = [
                r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall",
                r"SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall"
            ]
            for path in paths:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        sub = winreg.OpenKey(key, winreg.EnumKey(key, i))
                        try:
                            name = winreg.QueryValueEx(sub, "DisplayName")[0]
                            version = winreg.QueryValueEx(sub, "DisplayVersion")[0]
                            raw_date = winreg.QueryValueEx(sub, "InstallDate")[0]
                            install_date = format_yyyymmdd(raw_date)

                            size_mb = "-"
                            try:
                                loc = winreg.QueryValueEx(sub, "InstallLocation")[0]
                                if loc and os.path.exists(loc):
                                    size_mb = get_folder_size_mb(loc)
                            except:
                                pass

                            if size_mb == "-":
                                try:
                                    est_kb = winreg.QueryValueEx(sub, "EstimatedSize")[0]
                                    size_mb = round(est_kb / 1024, 2)
                                except:
                                    pass

                            apps.append({
                                "name": name,
                                "version": version,
                                "install_date": install_date,
                                "size": size_mb
                            })
                        except:
                            pass
                except:
                    pass
        except:
            pass

    if not apps:
        apps = [{"name": "No apps found", "version": "-", "install_date": "-", "size": "-"}]

    return apps


def get_hardware_info():
    disk = psutil.disk_usage('/')
    return "\n".join([
        f"OS: {platform.system()} {platform.release()}",
        f"Architecture: {platform.machine()}",
        f"Processor: {platform.processor()}",
        f"CPU Cores: {os.cpu_count()}",
        f"Physical RAM: {round(psutil.virtual_memory().total / (1024**3), 2)} GB",
        f"Available RAM: {round(psutil.virtual_memory().available / (1024**3), 2)} GB",
        f"Disk Total: {round(disk.total / (1024**3), 2)} GB",
        f"Disk Used: {round(disk.used / (1024**3), 2)} GB",
        f"Disk Free: {round(disk.free / (1024**3), 2)} GB",
        f"Python Version: {platform.python_version()}"
    ])


def send_text(sock, text):
    payload = text.encode()
    sock.sendall(f"{len(payload)}\n".encode() + payload)


# ----------------------------
# Main with GUI
# ----------------------------
def start_client():
    root = tk.Tk()
    root.withdraw()

    last = get_last_server()
    prompt = "Enter Server IP / Domain:"
    if last:
        prompt += f"\n(Press OK to use: {last})"

    server_host = simpledialog.askstring("Server connection", prompt)

    if not server_host:
        if last:
            server_host = last
        else:
            messagebox.showerror("Error", "No server entered. Exiting.")
            return

    save_last_server(server_host)

    init_db()

    client_uuid = get_or_create_client_uuid()
    mac = get_mac_address()
    hostname = platform.node()
    apps_list = get_installed_apps()

    apps = "\n".join(
        f"{a['name']}|{a['version']}|{a['install_date']}|{a['size']}"
        for a in apps_list
    )

    hw = get_hardware_info()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    text_data = (
        f"CLIENT_UUID: {client_uuid}\n"
        f"MAC_ADDRESS: {mac}\n"
        f"HOSTNAME: {hostname}\n"
        f"TIMESTAMP: {timestamp}\n\n"
        f"=== HARDWARE ===\n{hw}\n\n"
        f"=== APPLICATIONS ===\n{apps}"
    )

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(8)
        s.connect((server_host, TCP_PORT))

        s.sendall(b"get apps\n")
        send_text(s, text_data)

        cmd = s.recv(1024).decode().strip()
        s.close()

        messagebox.showinfo("Success", f"Connected to {server_host}\nServer replied: {cmd}")

    except Exception as e:
        messagebox.showerror("Connection Failed", f"Could not connect to {server_host}\n\n{e}")


if __name__ == "__main__":
    start_client()
