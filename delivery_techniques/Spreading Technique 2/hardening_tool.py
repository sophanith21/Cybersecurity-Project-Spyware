import psutil
import subprocess
import socket
import time
import json
import os

LOG_DIR = r"C:\HardeningTool"
LOG_FILE = os.path.join(LOG_DIR, "hardening_log.json")

TELEGRAM_API_HOST = "api.telegram.org"

# Telegram Bot API IP ranges (known official ranges)
TELEGRAM_IP_RANGES = [
    "149.154.",
    "91.108."
]

# -------------------------------------------------
# Ensure log directory exists
# -------------------------------------------------
os.makedirs(LOG_DIR, exist_ok=True)


def write_log(event_type, details):
    entry = {
        "event": event_type,
        "details": details,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

    print("[LOG]", entry)


# -------------------------------------------------
# Detect Python processes 
# -------------------------------------------------
def detect_python_processes():
    suspicious = []

    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            if proc.info['name'] and "python" in proc.info['name'].lower():
                cmd = " ".join(proc.info['cmdline']) if proc.info['cmdline'] else ""
                suspicious.append(cmd)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    if suspicious:
        write_log("PYTHON_PROCESS_DETECTED", suspicious)

    return suspicious


# -------------------------------------------------
# Detect outbound connections to Telegram API
# -------------------------------------------------
def detect_telegram_connections():
    connections = psutil.net_connections(kind='inet')

    hits = []
    for conn in connections:
        if conn.raddr:
            ip = conn.raddr.ip

            if any(ip.startswith(prefix) for prefix in TELEGRAM_IP_RANGES):
                hits.append(ip)

    if hits:
        write_log("TELEGRAM_CONNECTION_DETECTED", hits)

    return hits


# -------------------------------------------------
# Resolve Telegram domain to IP & detect DNS-based communication
# -------------------------------------------------
def detect_telegram_dns_resolution():
    try:
        telegram_ip = socket.gethostbyname(TELEGRAM_API_HOST)
        write_log("TELEGRAM_DNS_RESOLUTION", telegram_ip)
        return telegram_ip
    except socket.gaierror:
        return None


# -------------------------------------------------
# Optional Firewall Blocking (Windows)
# -------------------------------------------------
def block_telegram_api(ip):
    try:
        command = [
            "netsh", "advfirewall", "firewall", "add",
            "rule", f"name=Block_Telegram_{ip}",
            "dir=out", "action=block", f"remoteip={ip}"
        ]
        subprocess.run(command, capture_output=True, text=True)

        write_log("FIREWALL_BLOCK_APPLIED", ip)
    except Exception as e:
        write_log("FIREWALL_BLOCK_FAILED", str(e))


# -------------------------------------------------
# Main Hardening Flow
# -------------------------------------------------
def main():
    write_log("HARDENING_TOOL_START", "Python-based hardening tool is active.")

    # 1. Detect Python processes
    detect_python_processes()

    # 2. Detect outbound Telegram connections
    telegram_ips = detect_telegram_connections()

    # 3. Detect DNS resolution attempts
    resolved_ip = detect_telegram_dns_resolution()

    # 4. Auto-block Telegram API if detected
    if resolved_ip:
        for prefix in TELEGRAM_IP_RANGES:
            if resolved_ip.startswith(prefix):
                block_telegram_api(resolved_ip)

    write_log("HARDENING_TOOL_FINISHED", "Scan complete.")


if __name__ == "__main__":
    main()
