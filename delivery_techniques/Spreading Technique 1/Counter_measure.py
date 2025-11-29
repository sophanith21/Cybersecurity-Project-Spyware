import socket
import json
import os
import datetime

HOST = ""
PORT = 6000

SAVE_FOLDER = "received_messages"
os.makedirs(SAVE_FOLDER, exist_ok=True)

SUSPICIOUS_EXTENSIONS = [
    ".exe", ".bat", ".cmd", ".scr", ".js", ".vbs"
]

FAKE_DOC_EXTENSIONS = [
    ".pdf.exe", ".docx.exe", ".xlsx.exe"
]

scan_log = []

print("=== Receiver Active (with Auto-Delete Defense) ===")
print(f"Listening on port {PORT}...\n")


def is_suspicious(filename):
    fn = filename.lower()
    reasons = []

    # double extensions
    if any(fn.endswith(ext) for ext in FAKE_DOC_EXTENSIONS):
        reasons.append("Double extension (fake document).")

    # known malicious extensions
    if any(fn.endswith(ext) for ext in SUSPICIOUS_EXTENSIONS):
        reasons.append("Suspicious executable attachment.")

    # multiple dots (disguise)
    if fn.count(".") >= 2:
        reasons.append("Multiple extensions (possible disguise).")

    return reasons


def start_receiver():
    s = socket.socket()
    s.bind((HOST, PORT))
    s.listen(5)

    while True:
        conn, addr = s.accept()
        print(f"[+] Incoming message from {addr[0]}")

        # Receive metadata length
        meta_len = int(conn.recv(16).decode().strip())

        # Receive metadata
        metadata = json.loads(conn.recv(meta_len).decode())

        print(f"From: {metadata['from']}")
        print(f"Subject: {metadata['subject']}")

        # Receive file size
        file_size = int(conn.recv(16).decode().strip())

        # Save attachment
        attachment_name = metadata["attachment"]
        save_path = os.path.join(SAVE_FOLDER, attachment_name)

        with open(save_path, "wb") as f:
            received = 0
            while received < file_size:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                f.write(chunk)
                received += len(chunk)

        print(f"[✓] Saved attachment: {save_path}")

        # Scan attachment
        issues = is_suspicious(attachment_name)

        log_entry = {
            "timestamp": str(datetime.datetime.now()),
            "sender": metadata["from"],
            "subject": metadata["subject"],
            "attachment": attachment_name,
            "issues_detected": issues
        }
        scan_log.append(log_entry)

        # Auto-delete if suspicious
        if issues:
            print("[!] Suspicious file detected:")
            for issue in issues:
                print("   -", issue)

            try:
                os.remove(save_path)
                print(f"[⚠] Suspicious file deleted: {save_path}")
            except Exception as e:
                print(f"[ERROR] Failed to delete file: {e}")
        else:
            print("[✓] File appears safe.")

        print("----------------------------------------------------")
        conn.close()


start_receiver()
