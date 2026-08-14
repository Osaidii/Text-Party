import tkinter as tk
import os
from tkinter.filedialog import askopenfile, asksaveasfile
from tkinter.messagebox import showinfo, showerror, askyesnocancel

filename = None
filepath = None
last_saved_filename = None
change_name_to = None
font = "Arial"

current_mode = "dark"

light_color = "#E4E4E4"
dark_color = "#303030"

root = tk.Tk()

screen_height = root.winfo_screenheight()
font_size = screen_height / 80

text = tk.Text(root, width=400, height=400, bg=dark_color, fg=light_color, font=(font, font_size), undo=True, autoseparators=True, maxundo=-1)
text.pack()
text.edit_separator()











def is_file_saved(): ###########
    global filename
    if filename is None or filename == "Untitled":
        return False
    try:
        with open(filename, "r") as f:
            saved_text = f.read()
        current_text = text.get("1.0", tk.END)
        return current_text == saved_text
    except (FileNotFoundError, OSError):
        return False

def save_file_popup(): ###########
    answer = askyesnocancel("Save File", "Do you want to save the file? It is currently unsaved.")
    match answer:
        case True:
            save_as()
            save_file()
            return True
        case False:
            return True
        case None:
            return False

def new_file(): ############
    if (not is_file_saved()) and text.get("1.0", tk.END).strip():
        continue_forward = save_file_popup()
        if continue_forward:
            pass
        else:
            return
    global filename
    global last_saved_filename
    filename = "Untitled"
    last_saved_filename = filename
    text.delete(0.0, tk.END)

new_file()

def open_file():
    global filename
    if not is_file_saved() and text.get("1.0", tk.END).strip():
        continue_forward = save_file_popup()
        if continue_forward:
            pass
        else:
            return
    
    try:
        f = askopenfile(mode='r')
    except:
        showerror(title = "Failed", message = "Failed to Open File, maybe the file was altered, or maybe just try again")
        return
    filename = None
    if f:
        t = f.read()
        f.close()
        text.delete(0.0, tk.END)
        text.insert(0.0, t)     
        filename = f.name   

def save_file():
    global filename
    global last_saved_filename
    t = text.get(0.0, tk.END)
    f = open(last_saved_filename, 'w')
    f.write(t)
    f.close()
    if filename != last_saved_filename:
        os.rename(last_saved_filename, filename)
    
def save_as():
    global filename
    f = asksaveasfile(mode='w', defaultextension=".txt")
    t = text.get(0.0, tk.END)
    try:
        f.write(t.rstrip())
    except:
        showerror(title="Oops!", message="Unable to save file...")
    if f:
        filename = f.name






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
    window.geometry("250x475")
    window.resizable(False, False)
    tk.Label(window, text="Actions", font=("Arial", 12)).grid(row=0, column=0, padx=20, pady=10)
    tk.Label(window, text="Shortcuts", font=("Arial", 12)).grid(row=0, column=1, padx=20, pady=10)
    shortcuts = [
        ("------------", "------------"),
        ("New File", "Ctrl + N"),
        ("Open File", "Ctrl + O"),
        ("Save File", "Ctrl + S"),
        ("Undo", "Ctrl + Z"),
        ("Redo", "Ctrl + Y"),
        ("Cut", "Ctrl + X"),
        ("Copy", "Ctrl + C"),
        ("Paste", "Ctrl + V"),
        ("Zoom In", "Ctrl + 8"),
        ("Zoom Out", "Ctrl + 9"),
        ("Reset Zoom", "Ctrl + 0"),
    ]
    for row, (action, shortcut) in enumerate(shortcuts, start = 1):
        tk.Label(window, text=action, font=("Arial", 12)).grid(row=row, column=0, padx=20, pady=5)
        tk.Label(window, text=shortcut, font=("Arial", 12)).grid(row=row, column=1, padx=20, pady=5)

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

root.title("Text Editor")
root.minsize(width=400, height=400)
root.maxsize(width=2560, height=1440)
root.bind("<Control-s>", lambda event: save_file())
root.bind("<Control-n>", lambda event: new_file())
root.bind("<Control-o>", lambda event: open_file())
root.bind("<Control-z>", lambda event: undo())
root.bind("<Control-y>", lambda event: redo())
root.bind("<Control-x>", lambda event: text.event_generate("<<Cut>>"))
root.bind("<Control-c>", lambda event: text.event_generate("<<Copy>>"))
root.bind("<Control-v>", lambda event: text.event_generate("<<Paste>>"))
root.bind("<Control-0>", lambda event: text.config(font=(font, font_size)))
root.bind("<Control-8>", zoom_in)
root.bind("<Control-9>", zoom_out)

menubar = tk.Menu(root, font=("Arial", int(screen_width / 10)))
filemenu = tk.Menu(menubar, bg="#FFFFFF", fg="#303030", activebackground="#555555", activeforeground="#FFFFFF", tearoff=0, font=("Arial", int(screen_width / 200)))
filemenu.add_command(label="New", command=new_file) 
filemenu.add_command(label="Open", command=open_file)
filemenu.add_command(label="Save", command=save_file)
filemenu.add_command(label="Save As...", command=save_as)
filemenu.add_separator()
filemenu.add_command(label="Quit", command=root.quit)
menubar.add_cascade(label="File", menu=filemenu)
editmenu = tk.Menu(menubar, bg="#FFFFFF", fg="#303030", activebackground="#555555", activeforeground="#FFFFFF", tearoff=0, font=("Arial", int(screen_width / 200)))
editmenu.add_command(label="Undo", command=undo) 
editmenu.add_command(label="Redo", command=redo)
editmenu.add_separator()
editmenu.add_command(label="Cut", command=lambda: text.event_generate("<<Cut>>"))
editmenu.add_command(label="Copy", command=lambda: text.event_generate("<<Copy>>"))
editmenu.add_command(label="Paste", command=lambda: text.event_generate("<<Paste>>"))
menubar.add_cascade(label="Edit", menu=editmenu)
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

# Save confirmation before new and open file, Auto Save, Dynamic Window name is in progress,

# Bold, Italic, Underline, Alinging, Encoding, Searching and Replacing, Word Count can be added in the future updates.