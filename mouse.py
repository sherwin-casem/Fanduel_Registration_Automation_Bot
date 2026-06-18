import tkinter as tk
import pyautogui

root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)
label = tk.Label(root, text="", bg="yellow", font=("Arial", 12))
label.pack()

def update():
    x, y = pyautogui.position()
    label.config(text=f"{x}, {y}")
    root.geometry(f"+{x+15}+{y+15}")
    root.after(50, update)

update()
root.mainloop()