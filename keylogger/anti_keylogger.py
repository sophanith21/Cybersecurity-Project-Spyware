import psutil
import os
import time
import shutil

# ==============================
# Quarantine utility
# ==============================
QUARANTINE_DIR = "quarantine"


def quarantine_script(script_path):
    os.makedirs(QUARANTINE_DIR, exist_ok=True)
    new_path = os.path.join(QUARANTINE_DIR, os.path.basename(script_path))
    shutil.copy2(script_path, new_path)
    for _ in range(5):
        try:
            os.remove(script_path)
            print(f"QUARANTINED: {script_path}")
            break
        except PermissionError:
            time.sleep(0.3)
        print(
            f'Failed to remove the suspicious file, please check this Directory "{script_path}"'
        )

    return new_path


# ==============================
# Main Monitor
# ==============================
SUSPICIOUS_MODULES = ["keyboard", "pynput", "requests", "subprocess"]
SAFE_SCRIPTS = ["anti_keylogger.py"]


def scan_processes():
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            if proc.info["name"] and "python" in proc.info["name"].lower():
                cmdline = proc.info["cmdline"]
                if cmdline and len(cmdline) > 1:
                    script = None
                    for part in cmdline:
                        if part.lower().endswith(".py"):
                            script = part
                            break
                    if script is not None:
                        with open(script, "r", encoding="latin-1") as f:
                            data = f.read()
                            score = sum(mod in data for mod in SUSPICIOUS_MODULES)
                            if score >= 1:
                                if not any(s in script for s in SAFE_SCRIPTS):
                                    print(
                                        "⚠ Suspicious Python Script Detected:", script
                                    )
                                    proc.terminate()
                                    try:
                                        proc.wait(
                                            timeout=5
                                        )  # waits until process exits or timeout
                                    except psutil.TimeoutExpired:
                                        proc.kill()
                                    quarantine_script(script)
                                    continue
        except Exception:
            pass


def main():
    print("Anti-Keylogger is now monitoring...\n")
    while True:
        scan_processes()
        time.sleep(2)  # Poll interval


if __name__ == "__main__":
    main()
