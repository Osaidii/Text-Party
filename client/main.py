import tkinter as tk
import os
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter.messagebox import showinfo, showerror, askyesnocancel
import socket
import secrets
import threading
import base64

VERSION = "1.0"
SERVER_HOST = "bore.pub"
LOCK_HOST = "127.0.0.1"
SERVER_PORT = 28625
LOCK_PORT = 3468
LIGHTCOLOR = "#E4E4E4"
DARKCOLOR = "#303030"

instance_lock_socket = None

user_filepath = ""
backup_filepath = ""
autosave_fails = 0
autosave_job = None
partymode = False
party_socket = None
party_code = 0
party_password = ""
party_name = ""
party_channel = None
updates_failed = 0
last_synced_text = ""
backspace_count = 0
backspace_job = None
is_host = False
font = "Arial"
current_mode = "Dark"

save_folder = os.path.join(os.path.expanduser("~"), "Documents", "Text Party Saves")
os.makedirs(save_folder, exist_ok=True)

def acquireInstanceLock():
    global instance_lock_socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind((LOCK_HOST, LOCK_PORT))
        s.listen(1)
        instance_lock_socket = s
        return True
    except OSError:
        try: s.close()
        except OSError: pass
        return False

if not acquireInstanceLock():
    import sys
    _r = tk.Tk(); _r.withdraw()
    showerror("Text Party", "Text Party is already running.\n""Only one instance can run at a time.")
    _r.destroy()
    sys.exit(0)

root = tk.Tk()

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

font_size = int(screen_height / 80)
default_font_size = font_size
text = tk.Text(root, width=400, height=400, bg=DARKCOLOR, fg=LIGHTCOLOR, font=(font, font_size), undo=True, autoseparators=False, maxundo=1000, padx=10, pady=10, wrap=tk.WORD)
text.tag_configure("margins", rmargin=15)
text.tag_add("margins", "1.0", "end")
text.pack()
text.edit_separator()


# # # # #     Editor Functions

def setWindowName(name: str):
    title = f"{name} | Text Party"
    root.title(title)

def newFile():
    if partymode:
        showerror("In Party Mode", "You cannot create a new file while in a party, please leave the party first.")
        return
    global backup_filepath, user_filepath, autosave_fails
    if text.get("1.0", "end-1c").strip() != "" and not isFileSaved():
        continue_forward = askUserToSave()
        if not continue_forward:
            return
    setWindowName("Untitled")
    backup_filepath = ""
    text.delete("1.0", tk.END)
    text.edit_reset()
    user_filepath = ""
    autosave_fails = 0
    cancelAutosave()

def openFile():
    global user_filepath, backup_filepath, autosave_fails
    if partymode:
        showerror("In Party Mode", "You cannot open a file while in a party, please leave the party first.")
        return
    if text.get("1.0", "end-1c").strip() != "" and not isFileSaved():
        continue_forward = askUserToSave()
        if not continue_forward:
            return
    path = askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    if not path:
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            t = f.read()
    except UnicodeDecodeError as e:
        showerror("Open Failed", "Could not open file, please ensure it is a valid text file.")
        return
    except OSError as e:
        showerror("Open Failed", str(e))
        return
    text.delete("1.0", tk.END)
    text.insert("1.0", t)     
    user_filepath = path
    backup_filepath = os.path.join(save_folder, os.path.basename(user_filepath))
    text.edit_reset()
    autosave_fails = 0
    setWindowName(os.path.basename(path))
    scheduleAutosave()
    
def changeFont(changed_font):
    global font
    font = changed_font
    text.config(font=(font, font_size))

def changeFontSize(changed_font_size):
    global font_size
    font_size = changed_font_size
    text.config(font=(font, font_size))

def zoomIn(event=None):
    global font_size
    font_size = min(font_size + max(2, int(font_size / 10)), 100)
    text.config(font=(font, font_size))

def zoomOut(event=None):
    global font_size
    font_size = max(font_size - max(2, int(font_size / 10)), 8)
    text.config(font=(font, font_size))

def zoomReset(event=None):
    global font_size
    font_size = default_font_size
    text.config(font=(font, font_size))

def undo():
    try:
        text.edit_undo()
    except tk.TclError:
        pass

def redo():
    try:
        text.edit_redo() 
    except tk.TclError:
        pass

def changeMode(change_to):
    global current_mode
    if change_to == current_mode:
        return
    if change_to == "Light":
        text.config(bg=LIGHTCOLOR, fg=DARKCOLOR)
    if change_to == "Dark":
        text.config(fg=LIGHTCOLOR, bg=DARKCOLOR) 
    current_mode = change_to

def about():
    showinfo(title="About", message="This is Text Party, a simple text editor where you can join your friends or colleagues to collaborate in one single file. Text Party does not store any of your data on its servers, except the bare minimum required to connect you to your party members.\n\nCreated by: Osaidii (Muhammad Osaid Hassan)\nVersion: 1.0\n\nFor more information, visit: https://github.com/Osaidii/Text-Party")

def shortcuts():
    window = tk.Toplevel(root)
    window.title("Shortcuts")
    window.geometry("275x635")
    window.resizable(False, False)
    tk.Label(window, text="Actions", font=("Arial", 12)).grid(row=0, column=0, padx=20, pady=10)
    tk.Label(window, text="Shortcuts", font=("Arial", 12)).grid(row=0, column=1, padx=20, pady=10)
    shortcuts = [
        ("------------", "------------"),
        ("New File", "Ctrl + N"),
        ("Open File", "Ctrl + O"),
        ("Save File", "Ctrl + S"),
        ("Save As", "Ctrl + Shift + S"),
        ("Undo", "Ctrl + Z"),
        ("Redo", "Ctrl + Y"),
        ("Cut", "Ctrl + X"),
        ("Copy", "Ctrl + C"),
        ("Paste", "Ctrl + V"),
        ("Zoom In", "Ctrl + 8"),
        ("Zoom Out", "Ctrl + 9"),
        ("Reset Zoom", "Ctrl + 0")
    ]
    for row, (action, shortcut) in enumerate(shortcuts, start = 1):
        tk.Label(window, text=action, font=("Arial", 12)).grid(row=row, column=0, padx=20, pady=5)
        tk.Label(window, text=shortcut, font=("Arial", 12)).grid(row=row, column=1, padx=20, pady=5)

def onClose():
    if partymode:
        answer = askyesnocancel("Confirmation", "Are you sure you want to leave the party?")
        if answer == False or answer == None:
            return
        leaveParty(True)
    if text.get("1.0", "end-1c").strip() != "":
        if not isFileSaved():
            if not askUserToSave():
                return
    root.destroy()

def _undo_separator_on_key(event):
    if event.char and event.char.isprintable() and not (event.state & 0x4):
        text.edit_separator()
    elif event.keysym in ("Return", "KP_Enter", "BackSpace", "Delete", "Tab"):
        text.edit_separator()
    return None



# # # # #     Party Functions

def aboutParty():
    showinfo(title="About Party", message="A party can be described as a group or a room which when used, can allow other joined members to edit and update the same text file.")

def createParty():
    global partymode, party_code, party_socket, party_password, party_name, is_host, last_synced_text, backspace_job, backspace_count
    if partymode:
        showerror("In Party Mode", "You are already in a party, please leave the current party first.")
        return
    try:
        party_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        party_socket.connect((SERVER_HOST, SERVER_PORT))
        party_socket.settimeout(5.0)
        party_socket.sendall(f"handshake:{VERSION}\n".encode())
        try:
            data = party_socket.recv(1024)
            if data == b"Invalid Request":
                showerror("Failed to Connect", "The client failed to connect to the server, please try again later or report to the developer.")
                party_socket.close()
                party_socket = None
                return
        except socket.timeout:
            party_socket.close()
            party_socket = None
            showerror("Connection Failed", "Server did not respond in time.")
            return
        if data == b"Wrong Version":
            showerror("Wrong Version", "Please update to the latest version to use all party functions.")
            party_socket.close()
            party_socket = None
            return
        if not data == b"Hello":
            showerror("Something went Wrong", "Please check your internet or try again later.")
            party_socket.close()
            party_socket = None
            return
    except (ConnectionRefusedError, socket.timeout, OSError):
        party_socket.close()
        party_socket = None
        showerror("Connection Failed", "Could not connect to the server, please try later or report to the developer.")
        return
    win = tk.Toplevel(root)
    win.title("Create Party")
    win.geometry("300x200")
    win.resizable(False, False)
    win.transient(root)
    win.grab_set()
    party_code = f"{secrets.randbelow(1_000_000):06d}"
    tk.Label(win, text=f"Join Code: {party_code}", font=("Arial", 16)).grid(row=0, columnspan=2, padx=10, pady=(15, 10))
    tk.Label(win, text="Password:", font=("Arial", 14)).grid(row=2, column=0, padx=10, pady=5, sticky="e")
    pw_var = tk.StringVar()
    tk.Entry(win, textvariable=pw_var, show="*", width=25).grid(row=2, column=1, padx=10, pady=5)
    tk.Label(win, text="Name:", font=("Arial", 14)).grid(row=3, column=0, padx=10, pady=(15, 5), sticky="e")
    name_var = tk.StringVar()
    tk.Entry(win, textvariable=name_var, width=25).grid(row=3, column=1, padx=10, pady=(15, 5))
    def submit(event=None):
        global party_password, party_name
        n = name_var.get().strip()
        p = pw_var.get()
        if not p:
            showerror("Missing", "Please enter a password.", parent=win)
            return
        if not n:
            showerror("Missing", "Please enter a name.", parent=win)
            return
        win.destroy()
        party_password = p
        party_name = n
    tk.Button(win, text="Create Party", command=submit, width=30, relief="solid", borderwidth=1, bd=1).grid(row=4, column=0, columnspan=2, pady=15, padx=15)
    win.bind("<Return>", submit)
    win.bind("<Escape>", lambda e: win.destroy())
    name_var.set("")
    win.wait_window()
    if party_name is None:
        party_socket.close()
        party_socket = None
        return
    for i in [party_code, party_password, party_name]:
        if ':' in i:
            showerror("Unallowed Character Used", "You cannot use a colon ':' inside any of the fields, please retry with a different entry.")
            party_socket.close()
            party_socket = None
            return
    party_socket.sendall(f"create:{party_code}:{party_password}:{party_name}\n".encode("utf-8"))
    try:
        data = party_socket.recv(1024)
    except socket.timeout:
        party_socket.close(); party_socket = None
        showerror("Connection Failed", "Server did not respond in time.")
        return
    if data == b"Code Taken":
        showerror("Party Creation Failed", "Party code collision, please try again.")
        party_socket.close()
        is_host = False
        party_socket = None
        return
    if data == b"Party Created":
        partymode = True
        is_host = True
        setWindowName(f"Party {party_code} | Text Party")
        showinfo("Party Created", f"Your party has been created successfully.\n\nJoin Code: {party_code}\nPassword: {party_password}")
        last_synced_text = ""
        backspace_job = None
        backspace_count = 0
        askForUpdate()
        syncText()
        party_socket.close()
        party_socket = None
    else:
        showerror("Party Creation Failed", f"Could not create party. Server replied: {data.decode('utf-8')}")
        party_socket.close()
        party_socket = None
        is_host = False
        return

def destroyParty():
    global partymode, party_socket, party_code, party_password, party_name, is_host, party_channel
    if not partymode:
        showerror("Not in Party Mode", "You are not currently in a party.")
        return
    win = tk.Toplevel(root)
    win.title("Destroy Party")
    win.geometry("300x160")
    win.resizable(False, False)
    win.transient(root)
    win.grab_set()
    tk.Label(win, text=f"Join Code: {party_code}", font=("Arial", 16)).grid(row=0, columnspan=2, padx=10, pady=(15, 10))
    tk.Label(win, text="Password:", font=("Arial", 14)).grid(row=2, column=0, padx=10, pady=5, sticky="e")
    pw_var = tk.StringVar()
    tk.Entry(win, textvariable=pw_var, show="*", width=25).grid(row=2, column=1, padx=10, pady=5)
    result = {"password": None}
    def submit(event=None):
        global party_password, party_name
        p = pw_var.get()
        if not p:
            showerror("Missing", "Please enter a password.", parent=win)
            return
        result["password"] = p
        win.destroy()
    tk.Button(win, text="Destroy Party", command=submit, width=30, relief="solid", borderwidth=1, bd=1).grid(row=4, column=0, columnspan=2, pady=15, padx=15)
    win.bind("<Return>", submit)
    win.bind("<Escape>", lambda e: win.destroy())
    win.wait_window()
    for i in [party_code, party_password, party_name]:
        if ':' in i:
            showerror("Unexpected Error Encountered", "There might be a problem in your software files, please redownload the software if you keep encountering this error.")
            party_socket.close()
            party_socket = None
            if party_channel is not None:
                party_channel.close()
                party_channel = None
            return
    try:
        if result["password"] != party_password:
            return
        askyesnocancel_result = askyesnocancel("Confirm Destruction", "Are you sure you want to destroy the party? This action cannot be undone. Members will also be kicked")
        if not askyesnocancel_result:
            return
        party_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        party_socket.settimeout(5.0)
        party_socket.connect((SERVER_HOST, SERVER_PORT))
        party_socket.sendall(f"destroy:{party_code}:{result['password']}:{party_name}\n".encode("utf-8"))
        try:
            data = party_socket.recv(1024)
        except socket.timeout:
            party_socket.close(); 
            party_socket = None
            if party_channel is not None:
                party_channel.close()
                party_channel = None
            showerror("Connection Failed", "Server did not respond in time.")
            return
        if data == b"Party Destroyed":
            partymode = False
            setWindowName("Untitled | Text Party")
            showinfo("Party Destroyed", "Your party has been destroyed successfully.")
            party_socket.close()
            party_socket = None
            if party_channel is not None:
                party_channel.close()
                party_channel = None
            party_code = 0
            party_password = ""
            party_name = ""
            is_host = False
        elif data == b"Invalid Request":
            showerror("Party Destruction Failed", "You must be the host of a working party to destroy it. Only the host can destroy the party.")
        else:
            showerror("Party Destruction Failed", f"Could not destroy party. Server replied: {data.decode('utf-8')}")
    except Exception as e:
        showerror("Party Destruction Failed", f"Could not destroy party. Error: {str(e)}")

def joinParty():
    global partymode, party_socket, party_code, party_password, party_name, is_host, last_synced_text, backspace_job, backspace_count
    if partymode:
        showerror("In Party Mode", "You are already in a party. Leave the current party first before joining another.")
        return
    is_host = False
    try:
        party_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        party_socket.connect((SERVER_HOST, SERVER_PORT))
        party_socket.settimeout(5.0)
        party_socket.sendall(f"handshake:{VERSION}\n".encode())
        try:
            data = party_socket.recv(1024)
        except socket.timeout:
            party_socket.close(); party_socket = None
            showerror("Connection Failed", "Server did not respond in time.")
            return
        if data == b"Wrong Version":
            showerror("Wrong Version", "Please update to the latest version to use all party functions.")
            party_socket.close()
            party_socket = None
            return
        if not data == b"Hello":
            showerror("Something went Wrong", "Please check your internet or try again later.")
            party_socket.close()
            party_socket = None
            return
    except (ConnectionRefusedError, socket.timeout, OSError):
        party_socket.close()
        party_socket = None
        showerror("Connection Failed", "Could not connect to the server, please try later or report to the developer.")
        return
    win = tk.Toplevel(root)
    win.title("Join Party")
    win.geometry("300x200")
    win.resizable(False, False)
    win.transient(root)
    win.grab_set()
    tk.Label(win, text="Party Code:", font=("Arial", 14)).grid(row=1, column=0, padx=10, pady=(15, 5), sticky="e")
    pc_var = tk.StringVar()
    tk.Entry(win, textvariable=pc_var, width=25).grid(row=1, column=1, padx=10, pady=5)
    tk.Label(win, text="Password:", font=("Arial", 14)).grid(row=2, column=0, padx=10, pady=5, sticky="e")
    pw_var = tk.StringVar()
    tk.Entry(win, textvariable=pw_var, show="*", width=25).grid(row=2, column=1, padx=10, pady=5)
    tk.Label(win, text="Name:", font=("Arial", 14)).grid(row=3, column=0, padx=10, pady=(15, 5), sticky="e")
    name_var = tk.StringVar()
    tk.Entry(win, textvariable=name_var, width=25).grid(row=3, column=1, padx=10, pady=(15, 5))
    result = {"code": None, "password": None, "name": None}
    def submit(event=None):
        global party_password, party_name
        n = name_var.get().strip()
        p = pw_var.get()
        c = pc_var.get().strip()
        if not c:
            showerror("Missing", "Please enter a party code.", parent=win)
            return
        if not p:
            showerror("Missing", "Please enter a password.", parent=win)
            return
        if not n:
            showerror("Missing", "Please enter a name.", parent=win)
            return
        result["code"] = c
        result["password"] = p
        result["name"] = n
        win.destroy()
    tk.Button(win, text="Join Party", command=submit, width=30, relief="solid", borderwidth=1, bd=1).grid(row=4, column=0, columnspan=2, pady=15, padx=15)
    win.bind("<Return>", submit)
    win.bind("<Escape>", lambda e: win.destroy())
    win.wait_window()   
    if result["code"] is None:
        party_socket.close()
        party_socket = None
        return
    for i in [result["code"], result["password"], result["name"]]:
        if ':' in i:
            showerror("Unallowed Character Used", "You cannot use a colon ':' inside any of the fields, please retry with a different entry.")
            party_socket.close()
            party_socket = None
            return
    try:
        party_socket.sendall(f"join:{result['code']}:{result['password']}:{result['name']}\n".encode("utf-8"))
        try:
            data = party_socket.recv(1024)
        except socket.timeout:
            party_socket.close(); party_socket = None
            showerror("Connection Failed", "Server did not respond in time.")
            return
        if data == b"Joined Party":
            partymode = True
            setWindowName(f"{result['name']} | Text Party")
            showinfo("Joined Party", "You have joined the party successfully.")
            party_code = result["code"]
            party_password = result["password"]
            party_name = result["name"]
            last_synced_text = ""
            backspace_job = None
            backspace_count = 0
            askForUpdate()
        elif data == b"Wrong Password" or data == b"Invalid Request":
            showerror("Join Party Failed", "The party code or password is incorrect.")
            party_socket.close()
            party_socket = None
        elif data == b"Invalid Code":
            showerror("Join Party Failed", "The party code you entered does not exist, please try with correct party code.")
            party_socket.close()
            party_socket = None
        elif data == b"Name Already Exists":
            showerror("Join Party Failed", "The name you have selected is already used by someone in the party.")
            party_socket.close()
            party_socket = None
        else:
            showerror("Join Party Failed", f"Could not join party. Server replied: {data.decode('utf-8')}")
            party_socket.close()
            party_socket = None
    except Exception as e:
        showerror("Join Party Failed", f"Could not join party. Error: {str(e)}")
        party_socket.close()
        party_socket = None

def leaveParty(silent=False):
    global partymode, party_socket, party_code, party_name, party_password, party_channel, is_host
    if not partymode:
        if not silent:
            showerror("Not in Party Mode", "You are not currently in a party.")
        return
    for i in [party_code, party_password, party_name]:
        if ':' in i:
            showerror("Unexpected Error Encountered", "There might be a problem in your software files, please redownload the software if you keep encountering this error.")
            party_socket.close()
            party_socket = None
            return
    if is_host:
        answer = askyesnocancel("Host", "You are the host of this party. If you leave, the role of host will be transferred to the person who joined the earliest. Confirm Leaving?")
        if answer == False or answer == None:
            return
    try:
        party_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        party_socket.settimeout(5.0)
        party_socket.connect((SERVER_HOST, SERVER_PORT))
        party_socket.sendall(f"leave:{party_code}:{party_password}:{party_name}\n".encode("utf-8"))
        try:
            data = party_socket.recv(1024)
        except socket.timeout:
            party_socket.close(); 
            party_socket = None
            if party_channel is not None:
                party_channel.close()
                party_channel = None
            if not silent:
                showerror("Connection Failed", "Server did not respond in time.")
            return
        if data == b"Left Party":
            partymode = False
            if not silent:
                setWindowName("Untitled | Text Party")
                showinfo("Left Party", "You have left the party successfully.")
            party_socket.close()
            party_socket = None
            if party_channel is not None:
                party_channel.close()
                party_channel = None
            party_code = 0
            is_host = False
            party_name = ""
        else:
            if not silent:
                showerror("Leave Party Failed", f"Could not leave party. Server replied: {data.decode('utf-8')}")
            party_socket.close()
            party_socket = None
            if party_channel is not None:
                party_channel.close()
                party_channel = None
    except Exception as e:
        print(repr(e))
        if not silent:
            showerror("Leave Party Failed", f"Could not leave party. Error: {str(e)}")

def askForUpdate():
    global partymode, party_channel, party_code, party_name, is_host, updates_failed
    if not partymode:
        return
    if party_channel is not None:
        return
    try:
        party_channel = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        party_channel.settimeout(2.0)
        party_channel.connect((SERVER_HOST, SERVER_PORT))
        party_channel.sendall(f"update:{party_code}:{party_name}\n".encode('utf-8'))
    except (socket.timeout, OSError):
        party_channel = None
        updates_failed += 1
        if updates_failed >= 3:
            updates_failed = 0
            showerror("Connection Failed", "The client cannot establish a connection with the server, please restart client or try again later.")
            partymode = False
        return
    buffer = b""
    got_status = False
    try:
        while not got_status:
            chunk = party_channel.recv(4096)
            if not chunk:
                party_channel = None
                partymode = False
                return
            buffer += chunk
            while b"\n" in buffer:
                line_bytes, buffer = buffer.split(b"\n", 1)
                line = line_bytes.decode("utf-8").strip()
                if not line:
                    continue
                if line.startswith("text:"):
                    apply_text_snapshot(line[5:])
                elif line == "Destroyed":
                    showerror("Party Destroyed", "This party has been destroyed by the host or does not exist at all.")
                    party_channel.close()
                    party_channel = None
                    partymode = False
                    return
                elif line == "New Host":
                    if not is_host:
                        showinfo("Selected as Host", "Since the original host has left, you have been selected as the new one.")
                        is_host = True
                    got_status = True
                elif line == "Alive":
                    got_status = True
    except (socket.timeout, OSError):
        party_channel.close()
        party_channel = None
        return
    party_channel.settimeout(None)
    threading.Thread(target=readChannel, daemon=True).start()

def readChannel():
    buffer = b""
    while True:
        try:
            data = party_channel.recv(4096)
        except OSError:
            break
        if not data:
            break
        buffer += data
        while b"\n" in buffer:
            line_bytes, buffer = buffer.split(b"\n", 1)
            line = line_bytes.decode("utf-8").strip()
            if not line:
                continue
            parts = line.split(":", 3)
            if parts[0] == "edit" and len(parts) >= 4:
                if parts[1] == "add":
                    root.after(0, apply_add, int(parts[2]), parts[3])
                elif parts[1] == "remove":
                    root.after(0, apply_remove, int(parts[2]), int(parts[3]))
            else:
                print(line)

def syncText():
    global last_synced_text
    print(f"syncText called: partymode={partymode}, channel={party_channel}, last={repr(last_synced_text)}, current={repr(text.get('1.0', 'end-1c'))}")
    if not partymode or party_channel is None:
        return
    current = text.get("1.0", "end-1c")
    if current == last_synced_text:
        return
    i = 0
    while i < len(current) and i < len(last_synced_text) and current[i] == last_synced_text[i]:
        i += 1
    remove_count = len(last_synced_text) - i
    if remove_count > 0:
        try: party_channel.sendall(f"edit:remove:{i}:{remove_count}\n".encode())
        except OSError: pass
    insert_text = current[i:]
    if insert_text:
        payload = base64.b64encode(insert_text.encode()).decode()
        try: party_channel.sendall(f"edit:add:{i}:{payload}\n".encode())
        except OSError: pass
    last_synced_text = current

def apply_add(index, b64):
    global last_synced_text
    new = base64.b64decode(b64).decode()
    text.insert(text.index(f"1.0 + {index} chars"), new)
    last_synced_text = text.get("1.0", "end-1c")

def apply_remove(index, count):
    global last_synced_text
    start = text.index(f"1.0 + {index} chars")
    end = text.index(f"1.0 + {index + count} chars")
    text.delete(start, end)
    last_synced_text = text.get("1.0", "end-1c")

def apply_text_snapshot(b64):
    global last_synced_text
    if not b64:
        return
    t = base64.b64decode(b64).decode("utf-8")
    if not t:
        return
    if t == text.get("1.0", "end-1c"):
        last_synced_text = t
        return
    text.delete("1.0", "end")
    text.insert("1.0", t)
    last_synced_text = t

def on_space(event=None):
    print("on_space fired")
    if not partymode:
        return
    syncText()

def on_backspace(event=None):
    global backspace_count, backspace_job
    if not partymode:
        return
    backspace_count += 1
    if backspace_job is not None:
        try:
            text.after_cancel(backspace_job)
        except (ValueError, tk.TclError):
            pass
    backspace_job = text.after(1000, on_backspace_idle)

def on_backspace_idle():
    global backspace_count, backspace_job
    backspace_job = None
    backspace_count = 0
    if not partymode:
        return
    syncText()

def showPartyInfo():
    global party_code, party_password, party_name
    if not partymode:
        showerror("Not in Party Mode", "You are not currently in a party.")
        return
    win = tk.Toplevel(root)
    win.title("Party Information")
    win.geometry("200x180")
    win.resizable(False, False)
    win.transient(root)
    win.grab_set()
    tk.Label(win, text=f"Join Code: {party_code}", font=("Arial", 14)).grid(row=0, columnspan=2, padx=10, pady=(15, 10))
    tk.Label(win, text=f"Password: {party_password}", font=("Arial", 14)).grid(row=1, columnspan=2, padx=10, pady=(15, 10))
    tk.Label(win, text=f"Name: {party_name}", font=("Arial", 14)).grid(row=2, columnspan=2, padx=10, pady=(15, 10))
    win.bind("<Escape>", lambda e: win.destroy())
    win.wait_window()
    

# # # # #     Save Functions 

def saveFile():
    global backup_filepath, user_filepath, autosave_fails
    if user_filepath == "":
        return saveAs()
    t = text.get("1.0", "end-1c")
    try:
        with open(user_filepath, "w", encoding="utf-8") as f:
            f.write(t)
    except (OSError, UnicodeEncodeError) as e:
        showerror("Save Failed", str(e))
        return False
    try:
        with open(backup_filepath, "w", encoding="utf-8") as b:
            b.write(t)
    except (OSError, UnicodeEncodeError) as e:
        showerror("Backup Failed", "The backup has failed. Your save file has been saved.", detail=str(e))
    autosave_fails = 0
    scheduleAutosave()
    return True

def saveAs():
    global backup_filepath, user_filepath, autosave_fails
    path = asksaveasfilename(defaultextension=".txt", initialdir=save_folder, filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    if not path:
        return False
    t = text.get("1.0", "end-1c")
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(t)
    except (OSError, UnicodeEncodeError) as e:
        showerror(title="Oops!", message="Unable to save file...", detail=str(e))
        return False
    user_filepath = path
    backup_filepath = os.path.join(save_folder, os.path.basename(user_filepath))
    setWindowName(os.path.basename(path))
    autosave_fails = 0
    scheduleAutosave()
    try:
        with open(backup_filepath, "w", encoding="utf-8") as b:
            b.write(t)
    except (OSError, UnicodeEncodeError) as e:
        showerror("Backup Failed", "The backup has failed. Your personal save file has still been saved.", detail=str(e))
    return True

def cancelAutosave():
    global autosave_job
    if autosave_job is not None:
        try:
            text.after_cancel(autosave_job)
        except tk.TclError:
            pass
        autosave_job = None

def scheduleAutosave():
    global autosave_job
    cancelAutosave()
    if user_filepath == "":
        return
    try:
        autosave_job = text.after(120000, autosave)
    except tk.TclError:
        autosave_job = None
 
def autosave():
    global user_filepath, autosave_fails, autosave_job, backup_filepath
    if not root.winfo_exists() or user_filepath == "":
        autosave_job = None
        return
    try:
        autosave_job = text.after(120000, autosave)
    except tk.TclError:
        autosave_job = None
        return
    if isFileSaved():
        return
    t = text.get("1.0", "end-1c")
    try:
        with open(user_filepath, "w", encoding="utf-8") as f:
            f.write(t)
        autosave_fails = 0
    except (OSError, UnicodeEncodeError) as e:
        autosave_fails += 1
        if autosave_fails >= 3:
            showerror("Autosave Failed", "Autosave has failed 3 times and is suspended. A restart or manual save will resume autosave functionality.", detail=str(e))
            autosave_job = None
            return
        showerror("Autosave Failed", str(e))
    try:
        with open(backup_filepath, "w", encoding="utf-8") as b:
            b.write(t)
    except (OSError, UnicodeEncodeError) as e:
        showerror("Backup Failed", "A backup has failed. Your personal save file has still been saved.", detail=str(e))
    
def askUserToSave():
    answer = askyesnocancel("Save File", "Do you want to save the file? It is currently unsaved.")
    match answer:
        case True:
            match isFileSaved():
                case True:
                    return saveFile()
                case False:
                    return saveAs()
        case False:
            return True
        case None:
            return False

def isFileSaved():
    global user_filepath
    if user_filepath == "":
        return False
    try:
        if not os.path.exists(user_filepath):
            return False
        with open(user_filepath, "r", encoding="utf-8") as f:
            saved_text = f.read()
        current_text = text.get("1.0", "end-1c")
        return current_text == saved_text
    except (FileNotFoundError, OSError, TypeError, UnicodeDecodeError):
        return False


# # # # #     Software Loop

newFile()

root.minsize(width=400, height=400)
root.protocol("WM_DELETE_WINDOW", onClose)
text.bind("<Control-s>", lambda event: saveFile())
text.bind("<Control-S>", lambda event: saveFile())
text.bind("<Control-Shift-S>", lambda event: saveAs())
text.bind("<Control-Shift-s>", lambda event: saveAs())
text.bind("<Control-n>", lambda event: newFile())
text.bind("<Control-N>", lambda event: newFile())
text.bind("<Control-o>", lambda event: openFile())
text.bind("<Control-O>", lambda event: openFile())
text.bind("<Control-0>", lambda event: changeFontSize(default_font_size))
text.bind("<Control-8>", zoomIn)
text.bind("<Control-9>", zoomOut)
text.bind("<KeyRelease-space>", on_space)
text.bind("<KeyRelease-BackSpace>", on_backspace)
text.bind("<Key>", _undo_separator_on_key)

menubar = tk.Menu(root, font=("Arial"))
filemenu = tk.Menu(menubar, bg="#FFFFFF", fg="#303030", activebackground="#555555", activeforeground="#FFFFFF", tearoff=0, font=("Arial", int(screen_width / 150)))
filemenu.add_command(label="New", command=newFile) 
filemenu.add_command(label="Open", command=openFile)
filemenu.add_command(label="Save", command=saveFile)
filemenu.add_command(label="Save As...", command=saveAs)
filemenu.add_separator()
filemenu.add_command(label="Quit", command=onClose)
menubar.add_cascade(label="File", menu=filemenu)
editmenu = tk.Menu(menubar, bg="#FFFFFF", fg="#303030", activebackground="#555555", activeforeground="#FFFFFF", tearoff=0, font=("Arial", int(screen_width / 150)))
editmenu.add_command(label="Undo", command=undo) 
editmenu.add_command(label="Redo", command=redo)
editmenu.add_separator()
editmenu.add_command(label="Cut", command=lambda: text.event_generate("<<Cut>>"))
editmenu.add_command(label="Copy", command=lambda: text.event_generate("<<Copy>>"))
editmenu.add_command(label="Paste", command=lambda: text.event_generate("<<Paste>>"))
menubar.add_cascade(label="Edit", menu=editmenu)
partymenu = tk.Menu(menubar, bg="#FFFFFF", fg="#303030", activebackground="#555555", activeforeground="#FFFFFF", tearoff=0, font=("Arial", int(screen_width / 150)))
partymenu.add_command(label="About", command=aboutParty) 
partymenu.add_separator()
partymenu.add_command(label="Create Party", command=createParty)
partymenu.add_command(label="Destroy Party", command=destroyParty)
partymenu.add_command(label="Join Party", command=joinParty)
partymenu.add_command(label="Leave Party", command=leaveParty)
partymenu.add_separator()
partymenu.add_command(label="About Current Party", command=showPartyInfo)
menubar.add_cascade(label="Party", menu=partymenu)
fontmenu = tk.Menu(menubar, bg="#FFFFFF", fg="#303030", activebackground="#555555", activeforeground="#FFFFFF", tearoff=0, font=("Arial", int(screen_width / 150)))
for font_name in ("Arial", "Times New Roman", "Courier New", "Verdana", "Tahoma", "Georgia", "Trebuchet MS", "Comic Sans MS", "Impact", "Calibri", "Consolas", "Segoe UI"):
    fontmenu.add_command(label=font_name, command=lambda f=font_name: changeFont(f))
menubar.add_cascade(label="Font", menu=fontmenu)
viewmenu = tk.Menu(menubar, bg="#FFFFFF", fg="#303030", activebackground="#555555", activeforeground="#FFFFFF", tearoff=0, font=("Arial", int(screen_width / 150)))
viewmenu.add_command(label="Zoom In", command=zoomIn)
viewmenu.add_command(label="Zoom Out", command=zoomOut)
viewmenu.add_command(label="Reset Zoom", command=lambda: zoomReset())
viewmenu.add_separator()
viewmenu.add_command(label="Light Mode", command=lambda: changeMode("Light"))
viewmenu.add_command(label="Dark Mode", command=lambda: changeMode("Dark"))
menubar.add_cascade(label="View", menu=viewmenu) 
aboutmenu = tk.Menu(menubar, bg="#FFFFFF", fg="#303030", activebackground="#555555", activeforeground="#FFFFFF", tearoff=0, font=("Arial", int(screen_width / 150)))
aboutmenu.add_command(label="About", command=about)
aboutmenu.add_separator()
aboutmenu.add_command(label="Shortcuts", command=shortcuts)
menubar.add_cascade(label="Help", menu=aboutmenu)
root.config(menu=menubar)

root.mainloop()