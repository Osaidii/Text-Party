import tkinter as tk
import os
from tkinter.filedialog import askopenfile, asksaveasfile
from tkinter.messagebox import showinfo, showerror, askyesnocancel
import socket
import secrets

VERSION = 1.0
HOST = "127.0.0.1"
PORT = 3467
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
is_host = False
font = "Arial"
current_mode = "Dark"

save_folder = os.path.join(os.path.expanduser("~"), "Documents", "Text Party Saves")
os.makedirs(save_folder, exist_ok=True)

def acquireInstanceLock():
    global instance_lock_socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((HOST, LOCK_PORT))
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
        showerror("In Party Mode", "You cannot create a new file while in a party. Please leave the party first.")
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
        showerror("In Party Mode", "You cannot open a file while in a party. Please leave the party first.")
        return
    if text.get("1.0", "end-1c").strip() != "" and not isFileSaved():
        continue_forward = askUserToSave()
        if not continue_forward:
            return
    f = askopenfile(mode='r', filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    if f is None:
        return
    try:
        with f:
            t = f.read()
    except UnicodeDecodeError as e:
        showerror("Open Failed", "Could not open file. Please ensure it is a valid text file.")
        return
    except OSError as e:
        showerror("Open Failed", str(e))
        return
    text.delete("1.0", tk.END)
    text.insert("1.0", t)     
    user_filepath = f.name
    backup_filepath = os.path.join(save_folder, os.path.basename(user_filepath))
    text.edit_reset()
    autosave_fails = 0
    setWindowName(os.path.basename(f.name))
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
    text.edit_separator()
    return None



# # # # #     Party Functions

def aboutParty():
    showinfo(title="About Party", message="A Party can be described as a group or a room which when used, can allow other joined members to edit and update the same text file.")

def createParty():
    global partymode, party_code, party_socket, party_password, party_name, is_host
    if partymode:
        showerror("In Party Mode", "You are already in a party. Please leave the current party first.")
        return
    party_code = None
    party_password = None
    party_name = None
    try:
        party_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        party_socket.connect((HOST, PORT))
        party_socket.settimeout(5.0)
        party_socket.sendall(f"handshake:{VERSION}")
        try:
            data = party_socket.recv(1024)
            if data == b"Invalid Request":
                showerror("Failed to connect", "The client failed to connect to the server, please try agan later or report to the developer.")
        except socket.timeout:
            party_socket.close(); party_socket = None
            showerror("Connection Failed", "Server did not respond in time.")
            return
        if data == b"Wrong Version":
            showerror("Wrong Verion", "Please update to the latest version to use all party functions.")
            party_socket.close()
            party_socket = None
            return
    except ConnectionRefusedError:
        party_socket.close()
        party_socket = None
        showerror("Connection Failed", "Could not connect to the server. Please try later or report to the developer.")
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
    result = {"password": None, "name": None}
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
        party_password = p
        party_name = n
        win.destroy()
        if ':' in party_password:
            showerror("Character not allowed", """The character ":" cannot be used inside the party password.""")
    tk.Button(win, text="Create Party", command=submit, width=30, relief="solid", borderwidth=1, bd=1).grid(row=4, column=0, columnspan=2, pady=15, padx=15)
    win.bind("<Return>", submit)
    win.bind("<Escape>", lambda e: win.destroy())
    name_var.set("")
    win.wait_window()
    if party_name is None:
        party_socket.close()
        party_socket = None
        return
    party_socket.sendall(f"create:{party_code}:{party_password}:{party_name}".encode("utf-8"))
    try:
        data = party_socket.recv(1024)
    except socket.timeout:
        party_socket.close(); party_socket = None
        showerror("Connection Failed", "Server did not respond in time.")
        return
    if data == b"Code Taken":
        showerror("Party Creation Failed", "Party code collision. Please try again.")
        party_socket.close()
        is_host = False
        party_socket = None
        return
    if data == b"Party Created":
        partymode = True
        is_host = True
        setWindowName(f"Party {party_code} | Text Party")
        showinfo("Party Created", f"Your party has been created successfully.\n\nJoin Code: {party_code}\nPassword: {party_password}")
    else:
        showerror("Party Creation Failed", f"Could not create party. Server replied: {data.decode('utf-8')}")
        party_socket.close()
        party_socket = None
        is_host = False
        return

def destroyParty():
    global partymode, party_socket, party_code, party_password, party_name, is_host
    if not partymode or party_socket is None:
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
    try:
        if result["password"] != party_password:
            return
        askyesnocancel_result = askyesnocancel("Confirm Destruction", "Are you sure you want to destroy the party? This action cannot be undone. Memebers will also be kicked")
        if askyesnocancel_result is None:
            return
        party_socket.sendall(f"destroy:{party_code}:{result['password']}:{party_name}".encode("utf-8"))
        try:
            data = party_socket.recv(1024)
        except socket.timeout:
            party_socket.close(); party_socket = None
            showerror("Connection Failed", "Server did not respond in time.")
            return
        if data == b"Party Destroyed":
            partymode = False
            setWindowName("Untitled | Text Party")
            showinfo("Party Destroyed", "Your party has been destroyed successfully.")
            party_socket.close()
            party_socket = None
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

def removeMember():
    global partymode, party_socket, party_code, party_password, party_name
    if not partymode or party_socket is None:
        showerror("Not in Party Mode", "You are currently not in a party. You must be the host of a party to remove a member.")
        return
    if not is_host:
        showerror("Not Host", "Only the host can remove members.")
        return
    win = tk.Toplevel(root)
    win.title("Remove Member")
    win.geometry("300x200")
    win.resizable(False, False)
    win.transient(root)
    win.grab_set()
    tk.Label(win, text="Remove Member:", font=("Arial", 14)).grid(row=1, column=0, padx=10, pady=(15, 5), sticky="e")
    name_var = tk.StringVar()
    tk.Entry(win, textvariable=name_var, width=25).grid(row=1, column=1, padx=10, pady=5)
    result = {"target": None}
    def submit(event=None):
        global party_password, party_name
        n = name_var.get().strip()
        if not n:
            showerror("Missing", "Please enter a name.", parent=win)
            return
        result["target"] = n
        win.destroy()
    tk.Button(win, text="Remove Member", command=submit, width=30, relief="solid", borderwidth=1, bd=1).grid(row=4, column=0, columnspan=2, pady=15, padx=15)
    win.bind("<Return>", submit)
    win.bind("<Escape>", lambda e: win.destroy())
    win.wait_window()   
    try:
        party_socket.sendall(f"remove:{party_code}:{party_password}:{party_name}:{result['target']}".encode("utf-8"))
        try:
            data = party_socket.recv(1024)
        except socket.timeout:
            party_socket.close(); party_socket = None
            showerror("Connection Failed", "Server did not respond in time.")
            return
        if data == b"Removed Member":
            showinfo("Player Removed Succesfully", "The removed member will not be able to or get any update.")
        elif data == b"Is not Host":
            showerror("Remove Member Failed", "You are not the host of this party.")
        else:
            showerror("Remove Member Failed", f"Could not Remove Member. Server replied: {data.decode('utf-8')}")
    except Exception as e:
        showerror("Remove Member Failed", f"Error: {str(e)}")

def joinParty():
    global partymode, party_socket, party_code, party_password, party_name, is_host
    if partymode:
        showerror("In Party Mode", "You already currently in a party. Leave the current party first before joining another.")
        return
    party_code = None
    party_password = None
    party_name = None
    is_host = False
    try:
        party_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        party_socket.connect((HOST, PORT))
        party_socket.settimeout(5.0)
        party_socket.sendall(f"handshake:{VERSION}")
        try:
            data = party_socket.recv(1024)
        except socket.timeout:
            party_socket.close(); party_socket = None
            showerror("Connection Failed", "Server did not respond in time.")
            return
        if data == b"Wrong Version":
            showerror("Wrong Verion", "Please update to the latest version to use all party functions.")
            party_socket.close()
            party_socket = None
            return
    except ConnectionRefusedError:
        party_socket.close()
        party_socket = None
        showerror("Connection Failed", "Could not connect to the server. Please try later or report to the developer.")
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
    try:
        party_socket.sendall(f"join:{result['code']}:{result['password']}:{result['name']}".encode("utf-8"))
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
        elif data == b"Wrong Password" or data == b"Invalid Request":
            showerror("Join Party Failed", "The party code or password is incorrect.")
            party_socket.close()
            party_socket = None
        elif data == b"Invalid Code":
            showerror("Join Party Failed", "The party code you entered does not exist. Please try with correct party code.")
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
    global partymode, party_socket, party_code, party_name
    if not partymode or party_socket is None:
        showerror("Not in Party Mode", "You are not currently in a party.")
        return
    if is_host:
        answer = askyesnocancel("Host", "You are the host of this party. If you leave, the role of host will be transferred to the person who joined the earliest. Confirm Leaving?")
        if answer == False or answer == None:
            return
    try:
        party_socket.sendall(f"leave:{party_code}:{party_name}".encode("utf-8"))
        try:
            data = party_socket.recv(1024)
        except socket.timeout:
            party_socket.close(); party_socket = None
            showerror("Connection Failed", "Server did not respond in time.")
            return
        if data == b"Left Party":
            partymode = False
            if not silent:
                setWindowName("Untitled | Text Party")
                showinfo("Left Party", "You have left the party successfully.")
            party_socket.close()
            party_socket = None
            party_code = 0
            is_host = False
            party_name = ""
        else:
            showerror("Leave Party Failed", f"Could not leave party. Server replied: {data.decode('utf-8')}")
            party_socket.close()
            party_socket = None
    except Exception as e:
        showerror("Leave Party Failed", f"Could not leave party. Error: {str(e)}")

def showPartyInfo():
    global party_code, party_password, party_name
    if not partymode or party_socket is None:
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
        showerror("Backup Failed", "A backup has failed. Your save file has been saved.", detail=str(e))
    autosave_fails = 0
    scheduleAutosave()
    return True

def saveAs():
    global backup_filepath, user_filepath, autosave_fails
    f = asksaveasfile(mode='w', defaultextension=".txt", initialdir=save_folder, filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    if f == None:
        return False
    t = text.get("1.0", "end-1c")
    user_filepath = f.name
    backup_filepath = os.path.join(save_folder, os.path.basename(user_filepath))
    try:
        with f:
            f.write(t)
        setWindowName(os.path.basename(f.name))
        autosave_fails = 0
        scheduleAutosave()
    except (OSError, UnicodeEncodeError) as e:
        showerror(title="Oops!", message="Unable to save file...", detail=str(e))
        return False
    try:
        with open(backup_filepath, "w", encoding="utf-8") as b:
            b.write(t)
    except (OSError, UnicodeEncodeError) as e:
        showerror("Backup Failed", "A backup has failed. Your save file has been saved.", detail=str(e))
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
        showerror("Backup Failed", "A backup has failed. Your save file has been saved.", detail=str(e))
    
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
partymenu.add_command(label="Remove Member", command=removeMember)
partymenu.add_separator()
partymenu.add_command(label="See Party Info", command=showPartyInfo)
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

# Supporting Multiple OSes and Updating, Leaving, Joining, Kicking, Kicking after Destroying Logic left.

# Searching and Replacing, Word Count, Drag and Drop Text can be added in the future updates