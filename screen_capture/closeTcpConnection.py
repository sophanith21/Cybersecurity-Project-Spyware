import psutil
import time
import socket

def is_py_script(cmdline):
    """
    Returns True if the process is running a .py file
    """
    for arg in cmdline:
        arg = arg.lower()
        if arg.endswith(".py") or ".py" in arg:
            return True
    return False


def monitor_python_connections():
    print("[Anti‑malware] Monitoring all running .py scripts...\n")

    seen_connections = set()

    while True:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmd = proc.cmdline()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

            # Only detect Python scripts (.py)
            if not is_py_script(cmd):
                continue

            try:
                conns = proc.net_connections(kind='inet')
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

            for c in conns:
                if not c.raddr:
                    continue
                if c.type != socket.SOCK_STREAM:
                    continue

                pid = proc.pid
                lip, lport = c.laddr.ip, c.laddr.port
                rip, rport = c.raddr.ip, c.raddr.port

                conn_key = (pid, lip, lport, rip, rport)

                # Detect new TCP connection
                if conn_key not in seen_connections:
                    seen_connections.add(conn_key)

                    print("\n[ALERT] Python script detected making a TCP connection!")
                    print(f" Script: {cmd}")
                    print(f" PID = {pid}")
                    print(f" {lip}:{lport} → {rip}:{rport}")
                    print(" SUSPENDING process to block activity...")

                    try:
                        proc.suspend()
                        print("[ACTION] Process suspended (NOT terminated).")
                        print("[INFO] The user must decide what to do next.\n")

                    except psutil.AccessDenied:
                        print("[ERROR] Access denied: cannot suspend this process.\n")

                    except Exception as e:
                        print(f"[ERROR] Failed to suspend process: {e}\n")

        time.sleep(0.5)


if __name__ == "__main__":
    monitor_python_connections()
