import tkinter as tk
import time
from tkinter.filedialog import askopenfile, asksaveasfile
from tkinter.messagebox import showinfo, showerror

filename = None
font = "Arial"
font_size_for_screen = 12
font_size = font_size_for_screen

root = tk.Tk()

screen_height = root.winfo_screenheight()

text = tk.Text(root, width=400, height=400, bg="#303030", fg="#E4E4E4", insertbackground="#555555", font=(font, font_size), undo=True, autoseparators=False, maxundo=-1)
text.pack()

def newFile():
    global filename
    filename = "Untitled (Unsaved)"
    global font_size_for_screen
    font_size_for_screen = int(screen_height / 100)
    print("Font size for screen: " + str(font_size_for_screen))
    text.delete(0.0, tk.END)
    text.edit_reset()

newFile()

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

def saveFile():
    global filename
    t = text.get(0.0, tk.END)
    f= open(filename, 'w')
    f.write(t)
    f.close()
    
def saveAs():
    filename = None
    f = asksaveasfile(mode='w', defaultextension=".txt")
    t = text.get(0.0, tk.END)
    try:
        f.write(t.rstrip())
    except:
        showerror(title="Oops!", message="Unable to save file...")

def openFile():
    filename = None
    f = askopenfile(mode='r')
    if f:
        t = f.read()
        f.close()
        text.delete(0.0, tk.END)
        text.insert(0.0, t)
        text.edit_reset()

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
        ("Zoom In", "Ctrl + +"),
        ("Zoom Out", "Ctrl + -"),
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
root.bind("<Control-s>", lambda event: saveFile())
root.bind("<Control-n>", lambda event: newFile())
root.bind("<Control-o>", lambda event: openFile())
root.bind("<Control-z>", lambda event: undo())
root.bind("<Control-y>", lambda event: redo())
root.bind("<Control-x>", lambda event: text.event_generate("<<Cut>>"))
root.bind("<Control-c>", lambda event: text.event_generate("<<Copy>>"))
root.bind("<Control-v>", lambda event: text.event_generate("<<Paste>>"))
root.bind("<Control-0>", lambda event: text.config(font=(font, font_size)))
root.bind("<Control-8>", zoom_in) #########################
root.bind("<Control-9>", zoom_out) ########################

menubar = tk.Menu(root, font=("Arial", int(screen_width / 10)))
filemenu = tk.Menu(menubar, bg="#FFFFFF", fg="#303030", activebackground="#555555", activeforeground="#FFFFFF", tearoff=0, font=("Arial", int(screen_width / 200)))
filemenu.add_command(label="New", command=newFile) 
filemenu.add_command(label="Open", command=openFile)
filemenu.add_command(label="Save", command=saveFile)
filemenu.add_command(label="Save As...", command=saveAs)
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
viewmenu.add_separator()
viewmenu.add_command(label="Reset Zoom", command=lambda: text.config(font=(font, font_size)))
menubar.add_cascade(label="View", menu=viewmenu) 
aboutmenu = tk.Menu(menubar, bg="#FFFFFF", fg="#303030", activebackground="#555555", activeforeground="#FFFFFF", tearoff=0, font=("Arial", int(screen_width / 200)))
aboutmenu.add_command(label="About", command=about)
aboutmenu.add_separator()
aboutmenu.add_command(label="Shortcuts", command=shortcuts)
menubar.add_cascade(label="Help", menu=aboutmenu)
root.config(menu=menubar)

root.mainloop()

# Undo is in progress

# Bold, Italic, Underline, Alinging, Encoding, Searching and Replacing, Word Count, Save confirmation before new and open file, Auto Save, Dark and Light Modes, Window Dynamic Name can be added in the future updates.