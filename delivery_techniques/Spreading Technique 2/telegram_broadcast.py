import requests
import sys
import time

BOT_TOKEN = "8013803485:AAHoQKS8hUblbNlkWDFfqeyBY2O4BhuT33I"
GROUP_ID = -5046759349
MESSAGE = ("[Demo] Cybersecurity training link — do NOT click unless instructed.\n"
           "Demo link: https://example.com/demo\n\n"
           "This is a controlled test. Everyone in this group has consented.")
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

def send_message(group_id, text):
    resp = requests.post(API_URL, data={"chat_id": group_id, "text": text})
    return resp.status_code, resp.text

def main():
    print("Sending demo broadcast...")
    status, text = send_message(GROUP_ID, MESSAGE)
    print("Response:", status)
    if status != 200:
        print("Failed response:", text)
        sys.exit(1)
    print("Message sent successfully.")

if __name__ == "__main__":
    main()
