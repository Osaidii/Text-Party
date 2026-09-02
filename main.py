import threading
import tkinter as tk
import os
from tkinter.filedialog import askopenfile, asksaveasfile
from tkinter.messagebox import showinfo, showerror, askyesnocancel
from tkinter import simpledialog
from datetime import datetime
import urllib.request
import json
import asyncio
import websockets

filename = ""
user_filepath = ""
backup_filename = ""
backup_filepath = ""
party_mode = False
pending_update = ""
font = "Arial"
current_mode = "Dark"
light_color = "#E4E4E4"
dark_color = "#303030"
party_name = ""
party_password = ""
conn = ""
ip = "" 
user_name = ""

save_folder = os.path.join(os.path.expanduser("~"), "Documents", "Text Party Saves")
os.makedirs(save_folder, exist_ok=True)

root = tk.Tk()

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

font_size = int(screen_height / 80)
default_font_size = font_size
text = tk.Text(root, width=400, height=400, bg=dark_color, fg=light_color, font=(font, font_size), undo=True, autoseparators=True, maxundo=-1)
text.pack()
text.edit_separator()



# # # # #     Editor Functions

def is_file_saved():
    if filename == "" or filename == "Untitled" or user_filepath == "":
        return False
    try:
        if not os.path.exists(user_filepath):
            return False
        with open(user_filepath, "r") as f:
            saved_text = f.read()
        current_text = text.get("1.0", "end-1c")
        return current_text == saved_text
    except (FileNotFoundError, OSError, TypeError):
        return False

def save_file_popup():
    answer = askyesnocancel("Save File", "Do you want to save the file? It is currently unsaved.")
    match answer:
        case True:
            save_file()
            return True
        case False:
            return True
        case None:
            return False

def set_window_name(name: str):
    title = f"{name} | Text Party"
    root.title(title)

def new_file():
    if party_mode:
        showerror("Party Mode Active", "Cannot create a new file while in Party mode. Please leave the party first.")
        return
    global backup_filepath, user_filepath, filename
    if text.get("1.0", "end-1c").strip() != "" and is_file_saved() == False:
        continue_forward = save_file_popup()
        if continue_forward:
            pass
        else:
            return
    set_window_name("Untitled")
    filename = "Untitled"
    backup_filepath = ""
    text.edit_reset()
    user_filepath = ""
    text.delete("1.0", tk.END)

new_file()
set_window_name("Untitled")

def open_file():
    if party_mode:
        showerror("Party Mode Active", "Cannot open a file while in Party mode. Please leave the party first.")
        return
    global filename, user_filepath, backup_filepath
    if text.get("1.0", "end-1c").strip() != "" and not is_file_saved():
        continue_forward = save_file_popup()
        if not continue_forward:
            return
    f = askopenfile(mode='r')
    if f:
        with f:
            t = f.read()
            text.delete("1.0", tk.END)
            text.insert("1.0", t)     
            user_filepath = f.name
            text.edit_reset()
            filename = os.path.basename(f.name)
            set_window_name(os.path.basename(f.name))
            backup_filepath = os.path.join(save_folder, f"{filename} {datetime.now().strftime('%H-%M-%S %m-%d-%y')}")
            try:
                with open(backup_filepath, 'w') as backup_file:
                    backup_file.write(t)
            except OSError:
                showerror("Backup Failed", "Could not create backup file!")

def save_file():
    global filename, backup_filepath, backup_filename, user_filepath
    if user_filepath == "":
        return save_as()
    t = text.get("1.0", "end-1c")
    try:
        with open(user_filepath, "w") as f:
            f.write(t)
    except OSError as e:
        showerror("Save Failed", str(e))
    try:
        with open(backup_filepath, 'w') as backup_file:
            backup_file.write(t)
        current_name = backup_filepath
        backup_filename = f"{filename} {datetime.now().strftime('%H-%M-%S %m-%d-%y')}"
        new_filepath = os.path.join(os.path.dirname(backup_filepath), backup_filename)
        os.rename(current_name, new_filepath)
        backup_filepath = new_filepath
    except OSError as e:
        showerror("Save Failed", str(e))
    
def autosave():
    if not root.winfo_exists():
        return
    if user_filepath != "":
        save_file()
    root.after(120000, autosave)

def save_as(): 
    global filename, backup_filepath, user_filepath, backup_filename
    f = asksaveasfile(mode='w', defaultextension=".txt", initialdir=save_folder)
    if f == "":
        return False
    t = text.get("1.0", "end-1c")
    try:
        f.write(t)
        f.close()
    except:
        showerror(title="Oops!", message="Unable to save file...")
        return False
    user_filepath = f.name
    set_window_name(os.path.basename(f.name))
    filename = os.path.basename(f.name)
    try:
        backup_filepath = os.path.join(save_folder, f"{filename} {datetime.now().strftime('%H-%M-%S %m-%d-%y')}")
        backup_filename = os.path.basename(backup_filepath)
        with open(backup_filepath, 'w') as backup_file:
            backup_file.write(t)
    except OSError:
        showerror(title="Backup Failed", message="Unable to create backup!")
    return True
    
def change_font(changed_font):
    global font
    font = changed_font
    text.config(font=(font, font_size))

def change_font_size(changed_font_size):
    global font_size
    font_size = changed_font_size
    text.config(font=(font, font_size))

def zoom_in(event=None):
    global font_size
    if font_size >= 100:
        return
    font_size += max(2, int(font_size / 10))
    text.config(font=(font, font_size))

def zoom_out(event=None):
    global font_size
    if font_size <= 8:
        return
    font_size -= max(2, int(font_size / 10))
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

def change_mode(change_to):
    global current_mode
    if change_to == current_mode:
        return
    if change_to == "Light":
        text.config(bg=light_color, fg=dark_color)
    if change_to == "Dark":
        text.config(fg=light_color, bg=dark_color) 
    current_mode = change_to

def about():
    showinfo(title="About", message="This is Text Party, a simple text editor where you can join your friends or colleagues to collaborate in one single file.\n\nCreated by: Osaidii (Muhammad Osaid Hassan)\nVersion: 1.0\n\nFor more information, visit: https://github.com/Osaidii/text-party")

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
        ("Reset Zoom", "Ctrl + 0"),
        ("Remove", "Ctrl + R"),
        ("Join", "Ctrl + J"),
        ("Leave", "Ctrl + L"),
    ]
    for row, (action, shortcut) in enumerate(shortcuts, start = 1):
        tk.Label(window, text=action, font=("Arial", 12)).grid(row=row, column=0, padx=20, pady=5)
        tk.Label(window, text=shortcut, font=("Arial", 12)).grid(row=row, column=1, padx=20, pady=5)

def on_close():
    if party_mode:
        stop_party()
    if text.get("1.0", "end-1c").strip() != "":
        if not is_file_saved():
            if not save_file_popup():
                return
    root.destroy()



# # # # #     Party Functions

def about_party():
    showinfo(title="About Party", message="A Party can be described as a group or a room which when used, can allow other joined members to edit and update the same text file.")

def get_public_ip():
    try:
        return urllib.request.urlopen("https://api.ipify.org", timeout=3).read().decode()
    except Exception:
        return "unknown"

def start_party():
    global party_mode, party_name, party_password, conn, user_name
    if party_mode == True:
        showerror("Party Failed", "Party mode is already active.")
        return
    party_name = simpledialog.askstring(title="Party Name",prompt="Enter a unique name for Party?:", parent=root)
    if party_name == "" or party_name is None:
        showerror("Setup Failed", "Name already taken or not entered.")
        return  
    party_password = simpledialog.askstring(title="Party Password",prompt="Enter password for Party?:", parent=root)
    if party_password == "" or party_password is None:
        showerror("Setup Failed", "Password was not entered.")
        party_mode = False
        return False
    user_name = simpledialog.askstring(title="User Name",prompt="Enter your name for this Party?:", parent=root)
    if user_name == "" or user_name is None:
        showerror("Setup Failed", "Name was not entered.")
        party_mode = False
        return False
    party_mode = True
    current_text = text.get("1.0", "end-1c")
    def worker():
        global conn, party_mode
        ip = get_public_ip()
        if ip == "unknown":
            root.after(0, lambda: showerror("Connection Failed", "Couldn't get your public ip."))
            party_mode = False
            return
        request = {"action": "create", "filename": party_name, "partypassword": party_password, "members": {ip: user_name}, "text": current_text}
        try:
            asyncio.run(_send(request))
            conn = True
        except OSError as e:
            root.after(0, lambda: showerror("Connection Failed", f"Couldn't reach the party server:\n{e}"))
            conn = ""
            party_mode = False
    threading.Thread(target=worker, daemon=True).start()

def stop_party():
    global party_mode, conn, pending_update
    if pending_update != "":
        root.after_cancel(pending_update)
        pending_update = ""
    if conn == "" or not party_mode:
        party_mode = False
        return
    try:
        request = {"action": "destroy", "filename": party_name, "partypassword": party_password}
        threading.Thread(target=lambda: asyncio.run(_send(request)), daemon=True).start()
    except OSError:
        pass
    conn = ""
    party_mode = False

def join():
    global party_mode, party_name, party_password, conn, user_name
    if party_mode:
        showerror("Party Failed", "Party mode is already active or already in a party.")
        return
    party_name = simpledialog.askstring(title="Party Name",prompt="Enter Party Name?:", parent=root)
    if party_name == "" or party_name is None:
        showerror("Setup Failed", "Name was not entered.")
        return  
    party_password = simpledialog.askstring(title="Party Password",prompt="Enter Party Password?:", parent=root)
    if party_password == "" or party_password is None:
        showerror("Setup Failed", "Password was not entered.")
        party_mode = False
        return False
    user_name = simpledialog.askstring(title="User Name",prompt="Enter your name for this Party?:", parent=root)
    if user_name == "" or user_name is None:
        showerror("Setup Failed", "Name was not entered.")
        party_mode = False
        return False
    new_file()
    party_mode = True
    def worker():
        global conn, party_mode
        ip = get_public_ip()
        if ip == "unknown":
            root.after(0, lambda: showerror("Connection Failed", "Couldn't get your public ip."))
            party_mode = False
            return
        request = {"action": "join", "filename": party_name, "partypassword": party_password, "ip": ip, "member_name": user_name}
        try:
            asyncio.run(_send(request))
            conn = True
        except OSError as e:
            root.after(0, lambda: showerror("Connection Failed", f"Couldn't reach the party server:\n{e}"))
            conn = ""
            party_mode = False
    threading.Thread(target=worker, daemon=True).start()

def remove():
    pass

def leave():
    global party_mode, conn, pending_update
    if not party_mode:
        party_mode = False
        return
    if pending_update != "":
        root.after_cancel(pending_update)
        pending_update = ""
    ip = get_public_ip()
    def worker():
        global conn, party_mode
        try:
            request = {"action": "leave", "filename": party_name, "partypassword": party_password, "ip": ip, "member_name": user_name}
            asyncio.run(_send(request))
        except OSError:
            pass
        finally:
            conn = ""
            party_mode = False
    threading.Thread(target=worker, daemon=True).start()

def update_text(event=None):
    global conn, pending_update
    text.edit_modified(False)
    if conn == "" or not party_mode:
        return
    if pending_update != "":
        root.after_cancel(pending_update)
    def send():
        global conn
        try:
            request = {"action": "update", "filename": party_name, "partypassword": party_password, "text": text.get("1.0", "end-1c")}
            threading.Thread(target=lambda: asyncio.run(_send(request)), daemon=True).start()
        except OSError:
            showerror("Connection Lost", "Disconnected from the party server.")
            conn = ""
    pending_update = root.after(500, send)

async def _send(request):
    async with websockets.connect("wss://text-party.osaidii.hackclub.app") as ws:
        await ws.send(json.dumps(request))  



# # # # #     Software Loop

root.minsize(width=400, height=400)
root.protocol("WM_DELETE_WINDOW", on_close)
root.bind("<Control-s>", lambda event: save_file())
root.bind("<Control-Shift-s>", lambda event: save_as())
root.bind("<Control-n>", lambda event: new_file())
root.bind("<Control-o>", lambda event: open_file())
root.bind("<Control-z>", lambda event: undo())
root.bind("<Control-y>", lambda event: redo())
root.bind("<Control-r>", lambda event: remove())
root.bind("<Control-j>", lambda event: join())
root.bind("<Control-l>", lambda event: leave())
text.bind("<Control-x>", lambda event: text.event_generate("<<Cut>>"))
text.bind("<Control-c>", lambda event: text.event_generate("<<Copy>>"))
text.bind("<Control-v>", lambda event: text.event_generate("<<Paste>>"))
text.bind("<Control-0>", lambda event: change_font_size(default_font_size))
text.bind("<Control-8>", zoom_in)
text.bind("<Control-9>", zoom_out)
text.bind("<<Modified>>", update_text)
root.after(120000, autosave)

menubar = tk.Menu(root, font=("Arial"))
filemenu = tk.Menu(menubar, bg="#FFFFFF", fg="#303030", activebackground="#555555", activeforeground="#FFFFFF", tearoff=0, font=("Arial", int(screen_width / 200)))
filemenu.add_command(label="New", command=new_file) 
filemenu.add_command(label="Open", command=open_file)
filemenu.add_command(label="Save", command=save_file)
filemenu.add_command(label="Save As...", command=save_as)
filemenu.add_separator()
filemenu.add_command(label="Quit", command=on_close )
menubar.add_cascade(label="File", menu=filemenu)
editmenu = tk.Menu(menubar, bg="#FFFFFF", fg="#303030", activebackground="#555555", activeforeground="#FFFFFF", tearoff=0, font=("Arial", int(screen_width / 200)))
editmenu.add_command(label="Undo", command=undo) 
editmenu.add_command(label="Redo", command=redo)
editmenu.add_separator()
editmenu.add_command(label="Cut", command=lambda: text.event_generate("<<Cut>>"))
editmenu.add_command(label="Copy", command=lambda: text.event_generate("<<Copy>>"))
editmenu.add_command(label="Paste", command=lambda: text.event_generate("<<Paste>>"))
menubar.add_cascade(label="Edit", menu=editmenu)
partymenu = tk.Menu(menubar, bg="#FFFFFF", fg="#303030", activebackground="#555555", activeforeground="#FFFFFF", tearoff=0, font=("Arial", int(screen_width / 200)))
partymenu.add_command(label="About", command=about_party) 
partymenu.add_separator()
partymenu.add_command(label="Start Party", command=start_party)
partymenu.add_command(label="Stop Party", command=stop_party)
partymenu.add_command(label="Remove", command=remove)
partymenu.add_command(label="Join", command=join)
partymenu.add_command(label="Leave", command=leave)
menubar.add_cascade(label="Party", menu=partymenu)
fontmenu = tk.Menu(menubar, bg="#FFFFFF", fg="#303030", activebackground="#555555", activeforeground="#FFFFFF", tearoff=0, font=("Arial", int(screen_width / 200)))
for font_name in ("Arial", "Times New Roman", "Courier New", "Verdana", "Tahoma", "Georgia", "Trebuchet MS", "Comic Sans MS", "Impact", "Calibri", "Consolas", "Segoe UI"):
    fontmenu.add_command(label=font_name, command=lambda f=font_name: change_font(f))
menubar.add_cascade(label="Font", menu=fontmenu)
sizemenu = tk.Menu(menubar, bg="#FFFFFF", fg="#303030", activebackground="#555555", activeforeground="#FFFFFF", tearoff=0, font=("Arial", int(screen_width / 200)))
for size in (8, 10, 12, 14, 16, 18, 20, 24, 32, 40, 48, 56, 70):
    sizemenu.add_command(label=size, command=lambda s=size: change_font_size(s))
menubar.add_cascade(label="Font Size", menu=sizemenu)
viewmenu = tk.Menu(menubar, bg="#FFFFFF", fg="#303030", activebackground="#555555", activeforeground="#FFFFFF", tearoff=0, font=("Arial", int(screen_width / 200)))
viewmenu.add_command(label="Zoom In", command=zoom_in)
viewmenu.add_command(label="Zoom Out", command=zoom_out)
viewmenu.add_command(label="Reset Zoom", command=lambda: change_font_size(default_font_size))
viewmenu.add_separator()
viewmenu.add_command(label="Light Mode", command=lambda: change_mode("Light"))
viewmenu.add_command(label="Dark Mode", command=lambda: change_mode("Dark"))
menubar.add_cascade(label="View", menu=viewmenu) 
aboutmenu = tk.Menu(menubar, bg="#FFFFFF", fg="#303030", activebackground="#555555", activeforeground="#FFFFFF", tearoff=0, font=("Arial", int(screen_width / 200)))
aboutmenu.add_command(label="About", command=about)
aboutmenu.add_separator()
aboutmenu.add_command(label="Shortcuts", command=shortcuts)
menubar.add_cascade(label="Help", menu=aboutmenu)
root.config(menu=menubar)

root.mainloop()

# Change from making a connection every time to making a connection once and keeping it open for the entire time.
# Also look trough how to fix older return packet overwriting the newer one.
# Add Inviting, Removing, Joining and Leaving parties. 
# Make sure party name and user name are unique.
# Add Text Recieving
# Add member menu

# Encoding, Searching and Replacing, Word Count can be added in the future updates.