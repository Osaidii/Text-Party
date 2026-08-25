import tkinter as tk
import os
from tkinter.filedialog import askopenfile, asksaveasfile
from tkinter.messagebox import showinfo, showerror, askyesnocancel
from tkinter import simpledialog
from datetime import datetime
import json
import socket
import time

filename = None
user_filepath = None
backup_filename = None
backup_filepath = None
server_filepath = None
party_mode = False
font = "Arial"
current_mode = "dark"
light_color = "#E4E4E4"
dark_color = "#303030"

party_name = None
party_password = None

conn = None

save_folder = os.path.join(os.path.expanduser("~"), "Documents", "Text Party Saves")
os.makedirs(save_folder, exist_ok=True)

root = tk.Tk()

screen_height = root.winfo_screenheight()
font_size = int(screen_height / 80)

text = tk.Text(root, width=400, height=400, bg=dark_color, fg=light_color, font=(font, font_size), undo=True, autoseparators=True, maxundo=-1)
text.pack()
text.edit_separator()



# # # # #     Editor Functions

def is_file_saved():
    if filename is None or filename == "Untitled" or backup_filepath is None:
        return False
    try:
        if not os.path.exists(backup_filepath):
            return False
        with open(backup_filepath, "r") as f:
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

def server_file_and_path():
    pass

def new_file():
    global backup_filepath
    global user_filepath
    if text.get("1.0", "end-1c").strip() != "" and is_file_saved() == False:
        continue_forward = save_file_popup()
        if continue_forward:
            pass
        else:
            return
    global filename
    set_window_name("Untitled")
    filename = "Untitled"
    backup_filepath = None
    user_filepath = None
    text.delete(0.0, tk.END)

new_file()
set_window_name("Untitled")

def open_file():
    global filename
    global user_filepath
    global backup_filepath
    if text.get("1.0", "end-1c").strip() != "" and not is_file_saved():
        continue_forward = save_file_popup()
        if not continue_forward:
            return
    f = askopenfile(mode='r')
    if f:
        with f:
            t = f.read()
            text.delete(0.0, tk.END)
            text.insert(0.0, t)     
            user_filepath = f.name
            filename = os.path.basename(f.name)
            set_window_name(os.path.basename(f.name))
            backup_filepath = os.path.join(save_folder, f"{filename} {datetime.now().strftime('%H-%M-%S %m-%d-%y')}")
            try:
                with open(backup_filepath, 'w') as backup_file:
                    backup_file.write(t)
            except OSError:
                showerror("Backup Failed", "Could not create backup file!")

def save_file():
    global filename
    global backup_filepath
    global backup_filename
    global user_filepath
    if user_filepath is None:
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
    if user_filepath is not None:
        save_file()
    root.after(120000, autosave)

def save_as(): 
    global filename
    global backup_filepath
    global user_filepath
    global backup_filename
    f = asksaveasfile(mode='w', defaultextension=".txt", initialdir=save_folder)
    if f is None:
        return False
    t = text.get(0.0, "end-1c")
    try:
        f.write(t)
        f.close()
    except:
        showerror(title="Oops!", message="Unable to save file...")
        return False
    if f:
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

def change_mode_to_light():
    global current_mode
    if "Light" == current_mode:
        return
    text.config(bg=light_color, fg=dark_color)
    current_mode = "Light"

def change_mode_to_dark():
    global current_mode
    if "Dark" == current_mode:
        return
    text.config(fg=light_color, bg=dark_color) 
    current_mode = "Dark"

def about():
    showinfo(title="About", message="This is Text Party, a simple text editor where you can invite your friends or colleagues to collaborate in one single file.\n\nCreated by: Osaidii (Muhammad Osaid Hassan)\nVersion: 1.0\n\nFor more information, visit: https://github.com/Osaidii/text-party")

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
        ("Invite", "Ctrl + I"),
        ("Remove", "Ctrl + R"),
        ("Join", "Ctrl + J"),
        ("Leave", "Ctrl + L"),
    ]
    for row, (action, shortcut) in enumerate(shortcuts, start = 1):
        tk.Label(window, text=action, font=("Arial", 12)).grid(row=row, column=0, padx=20, pady=5)
        tk.Label(window, text=shortcut, font=("Arial", 12)).grid(row=row, column=1, padx=20, pady=5)

def on_close():
    if text.get("1.0", "end-1c").strip() != "":
        if not is_file_saved():
            if not save_file_popup():
                return
    root.destroy()



# # # # #     Party Functions

def about_party():
    showinfo(title="About Party", message="A Party can be described as a group or a room which when used, can allow other invited members to edit and update the same text file.")

def start_party():
    global party_mode
    global party_name
    global party_password
    global conn
    party_name = simpledialog.askstring(title="Party Name",prompt="Enter a unique name for Party?:", parent=root)
    if party_name == None:
        return
    party_password = ""
    if party_name is not None:
        party_password = simpledialog.askstring(title="Party Password",prompt="Enter password for Party?:", parent=root)
        if party_password == None:
                return
        if party_password != "":
            party_mode = True
    try:
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect(("text-party.osaidii.hackclub.app", 3467))
    except OSError as e:
        showerror("Connection Failed", f"Couldn't reach the party server:\n{e}")
        conn = None
        return
    request = {"action": "create", "partyname": party_name, "partypassword": party_password,"text": text.get("1.0", "end-1c")}
    conn.sendall(json.dumps(request).encode())  

def stop_party():
    global party_mode
    global conn
    if conn is None:
        party_mode = False
        return
    try:
        request = {"action": "destroy", "partyname": party_name, "partypassword": party_password}
        conn.sendall(json.dumps(request).encode())
    except OSError:
        pass
    conn.close()
    conn = None
    party_mode = False

def invite():
    pass

def remove():
    pass

def join():
    pass

def leave():
    pass

def update_text():
    text.edit_modified(False)
    global conn
    if conn is None or not party_mode:
        return
    try:
        request = {"action": "update", "partyname": party_name, "partypassword": party_password, "text": text.get("1.0", "end-1c")}
        conn.sendall(json.dumps(request).encode())
    except OSError:
        showerror("Connection Lost", "Disconnected from the party server.")
        conn = None



# # # # #     Software Loop

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

root.minsize(width=400, height=400)
root.protocol("WM_DELETE_WINDOW", on_close)
root.bind("<Control-s>", lambda event: save_file())
root.bind("<Control-Shift-s>", lambda event: save_as())
root.bind("<Control-n>", lambda event: new_file())
root.bind("<Control-o>", lambda event: open_file())
root.bind("<Control-z>", lambda event: undo())
root.bind("<Control-y>", lambda event: redo())
root.bind("<Control-i>", lambda event: invite())
root.bind("<Control-r>", lambda event: remove())
root.bind("<Control-j>", lambda event: join())
root.bind("<Control-l>", lambda event: leave())
text.bind("<Control-x>", lambda event: text.event_generate("<<Cut>>"))
text.bind("<Control-c>", lambda event: text.event_generate("<<Copy>>"))
text.bind("<Control-v>", lambda event: text.event_generate("<<Paste>>"))
text.bind("<Control-0>", lambda event: text.config(font=(font, font_size)))
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
partymenu.add_separator
partymenu.add_command(label="Start Party", command=start_party)
partymenu.add_command(label="Stop Party", command=stop_party)
partymenu.add_command(label="Invite", command=invite)
partymenu.add_command(label="Remove", command=remove)
partymenu.add_command(label="Join", command=join)
partymenu.add_command(label="Leave", command=leave)
menubar.add_cascade(label="Party", menu=partymenu)
fontmenu = tk.Menu(menubar, bg="#FFFFFF", fg="#303030", activebackground="#555555", activeforeground="#FFFFFF", tearoff=0, font=("Arial", int(screen_width / 200)))
fontmenu.add_command(label="Arial", command=lambda: change_font("Arial"))
fontmenu.add_command(label="Times New Roman", command=lambda: change_font("Times New Roman"))
fontmenu.add_command(label="Courier New", command=lambda: change_font("Courier New"))
fontmenu.add_command(label="Verdana", command=lambda: change_font("Verdana"))
fontmenu.add_command(label="Tahoma", command=lambda: change_font("Tahoma"))
fontmenu.add_command(label="Georgia", command=lambda: change_font("Georgia"))
fontmenu.add_command(label="Trebuchet MS", command=lambda: change_font("Trebuchet MS"))
fontmenu.add_command(label="Comic Sans MS", command=lambda: change_font("Comic Sans MS"))
fontmenu.add_command(label="Impact", command=lambda: change_font("Impact"))
fontmenu.add_command(label="Calibri", command=lambda: change_font("Calibri"))
fontmenu.add_command(label="Consolas", command=lambda: change_font("Consolas"))
fontmenu.add_command(label="Segoe UI", command=lambda: change_font("Segoe UI"))
menubar.add_cascade(label="Font", menu=fontmenu)
sizemenu = tk.Menu(menubar, bg="#FFFFFF", fg="#303030", activebackground="#555555", activeforeground="#FFFFFF", tearoff=0, font=("Arial", int(screen_width / 200)))
sizemenu.add_command(label="8", command=lambda: change_font_size(8))
sizemenu.add_command(label="10", command=lambda: change_font_size(10))
sizemenu.add_command(label="12", command=lambda: change_font_size(12))
sizemenu.add_command(label="14", command=lambda: change_font_size(14))
sizemenu.add_command(label="16", command=lambda: change_font_size(16))
sizemenu.add_command(label="18", command=lambda: change_font_size(18))
sizemenu.add_command(label="20", command=lambda: change_font_size(20))
sizemenu.add_command(label="24", command=lambda: change_font_size(24))
sizemenu.add_command(label="32", command=lambda: change_font_size(32))
sizemenu.add_command(label="40", command=lambda: change_font_size(40))
sizemenu.add_command(label="48", command=lambda: change_font_size(48))
sizemenu.add_command(label="56", command=lambda: change_font_size(56))
sizemenu.add_command(label="70", command=lambda: change_font_size(70))
menubar.add_cascade(label="Font Size", menu=sizemenu)
viewmenu = tk.Menu(menubar, bg="#FFFFFF", fg="#303030", activebackground="#555555", activeforeground="#FFFFFF", tearoff=0, font=("Arial", int(screen_width / 200)))
viewmenu.add_command(label="Zoom In", command=zoom_in)
viewmenu.add_command(label="Zoom Out", command=zoom_out)
viewmenu.add_command(label="Reset Zoom", command=lambda: text.config(font=(font, font_size)))
viewmenu.add_separator()
viewmenu.add_command(label="Light Mode", command=change_mode_to_light)
viewmenu.add_command(label="Dark Mode", command=change_mode_to_dark)
menubar.add_cascade(label="View", menu=viewmenu) 
aboutmenu = tk.Menu(menubar, bg="#FFFFFF", fg="#303030", activebackground="#555555", activeforeground="#FFFFFF", tearoff=0, font=("Arial", int(screen_width / 200)))
aboutmenu.add_command(label="About", command=about)
aboutmenu.add_separator()
aboutmenu.add_command(label="Shortcuts", command=shortcuts)
menubar.add_cascade(label="Help", menu=aboutmenu)
root.config(menu=menubar)

root.mainloop()

# Bold, Italic, Underline, Alinging, Encoding, Searching and Replacing, Word Count can be added in the future updates.

# Bug with server domain becuase of nest's reverse proxy
