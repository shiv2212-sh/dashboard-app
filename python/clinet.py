import requests
import datetime
import platform
import os
import uuid
import sqlite3
import psutil

SERVER_URL = "https://dashboard-app1.onrender.com/api/report"
DB_FILE = "client_data.db"
CLIENT_ID_FILE = "client_id.txt"


# ----------------------------
# Client identity
# ----------------------------
def get_or_create_client_uuid():
    if os.path.exists(CLIENT_ID_FILE):
        return open(CLIENT_ID_FILE).read().strip()

    new_id = str(uuid.uuid4())
    with open(CLIENT_ID_FILE, "w") as f:
        f.write(new_id)
    return new_id


def get_mac_address():
    return hex(uuid.getnode())


# ----------------------------
# Database (local fallback)
# ----------------------------
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


# ----------------------------
# Installed applications (simple)
# ----------------------------
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
                            install_date = raw_date if raw_date else "-"
                            apps.append(f"{name}|{version}|{install_date}|-")
                        except:
                            pass
                except:
                    pass
        except:
            pass

    if not apps:
        apps = ["No apps found|-|-|-"]

    return "\n".join(apps)


# ----------------------------
# Hardware
# ----------------------------
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


# ----------------------------
# Main
# ----------------------------
def start_client():
    print("\n========== CLIENT STARTED ==========\n")

    init_db()

    client_uuid = get_or_create_client_uuid()
    mac = get_mac_address()
    hostname = platform.node()
    apps = get_installed_apps()
    hw = get_hardware_info()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    payload = {
        "uuid": client_uuid,
        "mac": mac,
        "hostname": hostname,
        "timestamp": timestamp,
        "hardware": hw,
        "apps": apps
    }

    print("DATA BEING SENT TO SERVER:\n")
    for k, v in payload.items():
        print(f"{k}: {v}\n")

    upsert_snapshot(client_uuid, mac, hostname, timestamp, hw, apps)

    try:
        print(f"Connecting to {SERVER_URL} ...")
        r = requests.post(SERVER_URL, json=payload, timeout=10)

        if r.status_code == 200:
            print("Server replied:", r.json())
            print("Data sent successfully")
        else:
            print("Server error:", r.status_code, r.text)

    except Exception as e:
        print("Server not available:", e)

    print("\n========== CLIENT FINISHED ==========\n")


if __name__ == "__main__":
    start_client()
    input("\nPress ENTER to close the terminal...")
