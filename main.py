import tkinter as tk
from tkinter.filedialog import askopenfile, asksaveasfile
from tkinter.messagebox import showerror
import math

filename = None

def newFile():
    global filename
    filename = "Untitled (Unsaved)"
    text.delete(0.0, tk.END)
    
def saveFile():
    global filename
    t = text.get(0.0, tk.END)
    f= open(filename, 'w')
    f.write(t)
    f.close()
    
def saveAs():
    f = asksaveasfile(mode='w', defaultextension=".txt")
    t = text.get(0.0, tk.END)
    try:
        f.write(t.rstrip())
    except:
        showerror(title="Oops!", message="Unable to save file...")

def openFile():
    f = askopenfile(mode='r')
    t = f.read()
    text.delete(0.0, tk.END)
    text.insert(0.0, t)

def undo():
    try:
        text.edit_undo()
    except:
        pass

def redo():
    try:
        print("here")
        text.edit_redo()
    except:
        print("he1re")
        pass

root = tk.Tk()

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

root.title("Text Editor")
root.minsize(width=400, height=400)
root.maxsize(width=1920, height=1080)
root.bind("<Control-s>", lambda event: saveFile())
root.bind("<Control-n>", lambda event: newFile())
root.bind("<Control-o>", lambda event: openFile())
root.bind("<Control-z>", lambda event: undo())
root.bind("<Control-y>", lambda event: redo())
root.bind("<Control-x>", lambda event: text.event_generate("<<Cut>>"))
root.bind("<Control-c>", lambda event: text.event_generate("<<Copy>>"))
root.bind("<Control-v>", lambda event: text.event_generate("<<Paste>>"))

text = tk.Text(root, width=400, height=400, bg="#303030", fg="#E4E4E4", insertbackground="#555555", font=("Arial", int(screen_width / 140)))
text.pack()

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
editmenu.add_separator()
editmenu.add_command(label="Font", command=root.quit)
menubar.add_cascade(label="Edit", menu=editmenu)
root.config(menu=menubar)
root.mainloop()


 