import tkinter as tk
import os
from tkinter.filedialog import askopenfile, asksaveasfile
from tkinter.messagebox import showinfo, showerror, askyesnocancel
import socket

HOST = "127.0.0.1"
PORT = 3467

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(b"Hello, server!")
    data = s.recv(1024)

print(f"Received {data!r} from server")

user_filepath = ""
backup_filepath = ""
autosave_fails = 0
autosave_job = None
font = "Arial"
current_mode = "Dark"
partymode = False
light_color = "#E4E4E4"
dark_color = "#303030"

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

def setWindowName(name: str):
    title = f"{name} | Text Party"
    root.title(title)

def newFile():
    if partymode:
        showerror("New File Disabled", "You cannot create a new file while in a party. Please leave the party first.")
        return
    global backup_filepath, user_filepath, autosave_fails
    if text.get("1.0", "end-1c").strip() != "" and not isFileSaved():
        continue_forward = askUserToSave()
        if not continue_forward:
            return
    setWindowName("Untitled")
    backup_filepath = ""
    text.edit_reset()
    user_filepath = ""
    text.delete("1.0", tk.END)
    autosave_fails = 0
    cancelAutosave()

def openFile():
    global user_filepath, backup_filepath, autosave_fails
    if partymode:
        showerror("Open File Disabled", "You cannot open a file while in a party. Please leave the party first.")
        return
    if text.get("1.0", "end-1c").strip() != "" and not isFileSaved():
        continue_forward = askUserToSave()
        if not continue_forward:
            return
    f = askopenfile(mode='r', encoding='utf-8', filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
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
        text.config(bg=light_color, fg=dark_color)
    if change_to == "Dark":
        text.config(fg=light_color, bg=dark_color) 
    current_mode = change_to

def about():
    showinfo(title="About", message="This is Text Party, a simple text editor where you can join your friends or colleagues to collaborate in one single file. Text Party does not store any of your data on its servers, except the bare minimum required to connect you to your party members..\n\nCreated by: Osaidii (Muhammad Osaid Hassan)\nVersion: 1.0\n\nFor more information, visit: https://github.com/Osaidii/text-party")

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
        showerror("In Party", "You cannot close the program while in a party. Please leave the party first.")
        return
    if text.get("1.0", "end-1c").strip() != "":
        if not isFileSaved():
            if not askUserToSave():
                return
    root.destroy()


# # # # #     Party Functions

def aboutParty():
    showinfo(title="About Party", message="A Party can be described as a group or a room which when used, can allow other joined members to edit and update the same text file.")

def createParty():
    global partymode
    if partymode:
        showerror("Already in Party", "You are already in a party. Please leave the current party first.")
        return
    partymode = True
    


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
    f = asksaveasfile(mode='w', defaultextension=".txt", initialdir=save_folder, encoding="utf-8")
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
        text.after_cancel(autosave_job)
        autosave_job = None

def scheduleAutosave():
    global autosave_job
    cancelAutosave()
    autosave_job = text.after(120000, autosave)
    
def autosave():
    global user_filepath, autosave_fails, autosave_job, backup_filepath
    autosave_job = None
    if user_filepath == "" or not root.winfo_exists():
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
            return
        showerror("Autosave Failed", str(e))
    try:
        with open(backup_filepath, "w", encoding="utf-8") as b:
            b.write(t)
    except (OSError, UnicodeEncodeError) as e:
        showerror("Backup Failed", "A backup has failed. Your save file has been saved.", detail=str(e))
    autosave_job = text.after(120000, autosave)
    
def askUserToSave():
    answer = askyesnocancel("Save File", "Do you want to save the file? It is currently unsaved.")
    match answer:
        case True:
            return saveFile()
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
text.bind("<Control-Shift-S>", lambda event: saveAs())
text.bind("<Control-n>", lambda event: newFile())
text.bind("<Control-o>", lambda event: openFile())
text.bind("<Control-0>", lambda event: changeFontSize(default_font_size))
text.bind("<Control-8>", zoomIn)
text.bind("<Control-9>", zoomOut)

menubar = tk.Menu(root, font=("Arial"))
filemenu = tk.Menu(menubar, bg="#FFFFFF", fg="#303030", activebackground="#555555", activeforeground="#FFFFFF", tearoff=0, font=("Arial", int(screen_width / 200)))
filemenu.add_command(label="New", command=newFile) 
filemenu.add_command(label="Open", command=openFile)
filemenu.add_command(label="Save", command=saveFile)
filemenu.add_command(label="Save As...", command=saveAs)
filemenu.add_separator()
filemenu.add_command(label="Quit", command=onClose)
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
partymenu.add_command(label="About", command=aboutParty) 
partymenu.add_separator()
partymenu.add_command(label="Start Party", command=None)
partymenu.add_command(label="Stop Party", command=None)
partymenu.add_command(label="Remove", command=None)
partymenu.add_command(label="Join", command=None)
partymenu.add_command(label="Leave", command=None)
partymenu.add_command(label="See Members", command=None)
menubar.add_cascade(label="Party", menu=partymenu)
fontmenu = tk.Menu(menubar, bg="#FFFFFF", fg="#303030", activebackground="#555555", activeforeground="#FFFFFF", tearoff=0, font=("Arial", int(screen_width / 200)))
for font_name in ("Arial", "Times New Roman", "Courier New", "Verdana", "Tahoma", "Georgia", "Trebuchet MS", "Comic Sans MS", "Impact", "Calibri", "Consolas", "Segoe UI"):
    fontmenu.add_command(label=font_name, command=lambda f=font_name: changeFont(f))
menubar.add_cascade(label="Font", menu=fontmenu)
sizemenu = tk.Menu(menubar, bg="#FFFFFF", fg="#303030", activebackground="#555555", activeforeground="#FFFFFF", tearoff=0, font=("Arial", int(screen_width / 200)))
for size in (8, 10, 12, 14, 16, 18, 20, 24, 32, 40, 48, 56, 70):
    sizemenu.add_command(label=size, command=lambda s=size: changeFontSize(s))
menubar.add_cascade(label="Font Size", menu=sizemenu)
viewmenu = tk.Menu(menubar, bg="#FFFFFF", fg="#303030", activebackground="#555555", activeforeground="#FFFFFF", tearoff=0, font=("Arial", int(screen_width / 200)))
viewmenu.add_command(label="Zoom In", command=zoomIn)
viewmenu.add_command(label="Zoom Out", command=zoomOut)
viewmenu.add_command(label="Reset Zoom", command=lambda: changeFontSize(default_font_size))
viewmenu.add_separator()
viewmenu.add_command(label="Light Mode", command=lambda: changeMode("Light"))
viewmenu.add_command(label="Dark Mode", command=lambda: changeMode("Dark"))
menubar.add_cascade(label="View", menu=viewmenu) 
aboutmenu = tk.Menu(menubar, bg="#FFFFFF", fg="#303030", activebackground="#555555", activeforeground="#FFFFFF", tearoff=0, font=("Arial", int(screen_width / 200)))
aboutmenu.add_command(label="About", command=about)
aboutmenu.add_separator()
aboutmenu.add_command(label="Shortcuts", command=shortcuts)
menubar.add_cascade(label="Help", menu=aboutmenu)
root.config(menu=menubar)

root.mainloop()

# Searching and Replacing, Word Count can be added in the future updates.