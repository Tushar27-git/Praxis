"""Render our own native setup window; does not access or control the game."""
from pathlib import Path
import tkinter as tk

from PIL import ImageGrab
from coc_advisor.native import NativeApp


root=tk.Tk()
app=NativeApp(root)
root.geometry("840x620+80+80")
root.update()
out=Path("output/native")
out.mkdir(parents=True,exist_ok=True)
root.after(400,root.quit)
root.mainloop()
bounds=(root.winfo_rootx(),root.winfo_rooty(),root.winfo_rootx()+root.winfo_width(),root.winfo_rooty()+root.winfo_height())
ImageGrab.grab(bbox=bounds).save(out/"native-setup.png")
app.compact.set(True)
app.toggle_compact()
root.update()
assert root.winfo_width() <= 560
assert app.preview.winfo_manager() == ""
app.close()
print("Native setup window rendered and compact controls verified.")
