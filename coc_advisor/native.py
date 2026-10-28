"""Native device-connection UI. Autonomous combat is not implemented here."""
from pathlib import Path
import queue
import threading
import time
import tkinter as tk
from tkinter import filedialog, ttk
import webbrowser

from PIL import Image, ImageTk

from .device import AdbClient, DeviceError, GAME_PACKAGE, find_adb
from .recording import FrameRecorder
from .stream import VideoStream


ROOT = Path(__file__).resolve().parents[1]


class NativeApp:
    def __init__(self, root):
        self.root = root
        root.title("Clash Controller - native setup")
        root.geometry("840x620")
        root.minsize(480,430)
        self.stop = threading.Event()
        self.worker = None
        self.messages = queue.Queue()
        self.lock = threading.Lock()
        self.latest = None
        self.recorder = None
        self.record_requested = threading.Event()
        self.frame_number = 0
        self.shown_number = -1
        self.photo = None
        self.busy = False
        self.had_error = False
        self.live_stream=None
        self.attack_worker=None
        self.attack_stop=threading.Event()
        self.experience_store=None; self.learning=None
        self.attack_max_inputs=40
        self.adb_path = tk.StringVar(value=str(find_adb() or ""))
        self.endpoint = tk.StringVar(value="127.0.0.1:5555")
        self.serial = tk.StringVar()
        self.capture_mode = tk.StringVar(value='Continuous video')
        self.status = tk.StringVar(value="Install the emulator and game, enable its ADB connection, then connect here.")
        self.stats = tk.StringVar(value="No device frames received.")
        self.floating = tk.BooleanVar(value=True)
        self.compact = tk.BooleanVar(value=False)
        self._build()
        root.attributes("-topmost",True)
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.poll_id = root.after(100,self.poll)

    def _build(self):
        outer = ttk.Frame(self.root,padding=16)
        outer.pack(fill="both",expand=True)
        ttk.Label(outer,text="Clash Controller",font=("Segoe UI",18,"bold")).pack(anchor="w")
        ttk.Label(outer,text="Native connection setup · background Android capture/input").pack(anchor="w",pady=(2,12))
        settings = ttk.LabelFrame(outer,text="Emulator connection",padding=10)
        settings.pack(fill="x")
        settings.columnconfigure(1,weight=1)
        ttk.Label(settings,text="ADB executable").grid(row=0,column=0,sticky="w",padx=(0,10))
        self.path_entry = ttk.Entry(settings,textvariable=self.adb_path)
        self.path_entry.grid(row=0,column=1,sticky="ew")
        ttk.Button(settings,text="Browse",command=self.browse).grid(row=0,column=2,padx=(8,0))
        ttk.Label(settings,text="Local address").grid(row=1,column=0,sticky="w",pady=8)
        ttk.Entry(settings,textvariable=self.endpoint).grid(row=1,column=1,sticky="ew")
        self.connect_button = ttk.Button(settings,text="Connect / refresh",command=self.connect)
        self.connect_button.grid(row=1,column=2,padx=(8,0))
        ttk.Label(settings,text="Device").grid(row=2,column=0,sticky="w")
        self.devices = ttk.Combobox(settings,textvariable=self.serial,state="readonly")
        self.devices.grid(row=2,column=1,columnspan=2,sticky="ew")
        ttk.Combobox(settings,textvariable=self.capture_mode,state='readonly',values=['Continuous video','Raw screenshots (slow fallback)']).grid(row=3,column=1,columnspan=2,sticky='ew',pady=(6,0))
        actions = ttk.Frame(outer)
        actions.pack(fill="x",pady=12)
        self.live_button = ttk.Button(actions,text="Start live capture",command=self.start_capture)
        self.live_button.pack(side="left")
        self.record_button = ttk.Button(actions,text="Record frames",command=self.toggle_record,state="disabled")
        self.record_button.pack(side="left",padx=8)
        self.stop_button = ttk.Button(actions,text="Stop",command=self.stop_capture,state="disabled")
        self.stop_button.pack(side="left")
        self.attack_button=ttk.Button(actions,text='Run one basic-army attack',command=self.start_attack,state='disabled')
        self.attack_button.pack(side='left',padx=8)
        ttk.Checkbutton(actions,text="Float",variable=self.floating,command=lambda:self.root.attributes("-topmost",self.floating.get())).pack(side="right")
        ttk.Checkbutton(actions,text="Compact",variable=self.compact,command=self.toggle_compact).pack(side="right",padx=8)
        ttk.Label(outer,textvariable=self.status,wraplength=770,foreground="#20546b").pack(anchor="w",fill="x")
        ttk.Label(outer,textvariable=self.stats).pack(anchor="w",pady=(6,10))
        self.preview = ttk.Label(outer,text="Connect a running emulator to receive live frames.",anchor="center",relief="sunken")
        self.preview.pack(fill="both",expand=True,pady=(0,12))
        ttk.Label(outer,text="Experimental: verified TH2,10-gold Regular Battle, Barbarians/Archers only. Unknown states pause. No trained outcome model.40-input/4-minute cap; no purchases.",foreground="#9c492d",wraplength=770).pack(anchor="w")
        links = ttk.Frame(outer)
        links.pack(fill="x",pady=(10,0))
        ttk.Button(links,text="Emulator download",command=lambda:webbrowser.open("https://www.bluestacks.com/download.html")).pack(side="left")
        ttk.Button(links,text="ADB setup guide",command=lambda:webbrowser.open("https://support.bluestacks.com/hc/en-us/articles/23925869130381-How-to-enable-Android-Debug-Bridge-on-BlueStacks-5")).pack(side="left",padx=8)

    def browse(self):
        path = filedialog.askopenfilename(title="Select adb.exe or HD-Adb.exe",filetypes=[("ADB executable","*.exe")])
        if path:
            self.adb_path.set(path)

    def client(self):
        path = Path(self.adb_path.get())
        if not path.is_file():
            raise DeviceError("Select an installed ADB executable. The project tools are under .tools/platform-tools/.")
        return AdbClient(path)

    def connect(self):
        if self.busy or (self.worker and self.worker.is_alive()):
            return
        try:
            client = self.client()
        except DeviceError as exc:
            self.status.set(str(exc));return
        endpoint = self.endpoint.get().strip()
        self.busy = True
        self.connect_button.configure(state="disabled")
        self.status.set("Checking local emulator connection…")
        def run():
            try:
                if endpoint:
                    client.connect(endpoint)
                self.messages.put(("devices",client.devices()))
            except DeviceError as exc:
                self.messages.put(("error",str(exc)))
            finally:
                self.messages.put(("ready",None))
        threading.Thread(target=run,daemon=True).start()

    def start_capture(self):
        if self.busy or (self.worker and self.worker.is_alive()):
            return
        try:
            client = self.client()
            serial = self.serial.get()
            if not serial:
                raise DeviceError("Connect and select a local emulator first.")
        except DeviceError as exc:
            self.status.set(str(exc));return
        self.stop.clear()
        self.had_error = False
        self.worker = threading.Thread(target=self.capture_loop,args=(client,serial,self.capture_mode.get()=='Continuous video'),daemon=True)
        self.worker.start()
        self.live_button.configure(state="disabled")
        self.connect_button.configure(state="disabled")
        self.record_button.configure(state="normal")
        self.stop_button.configure(state="normal")
        self.status.set("Receiving live Android frames. No autonomous attack inputs are enabled.")

    def capture_loop(self, client, serial, use_stream=False):
        stream=None; seen=0
        try:
            if use_stream:
                stream=VideoStream(client,serial).start(); self.live_stream=stream
            while not self.stop.is_set():
                before = client.foreground_package(serial) if self.record_requested.is_set() else None
                frame = stream.latest() if stream else client.capture(serial)
                if frame is None or (stream and frame.sequence==seen):
                    self.stop.wait(.01); continue
                if stream: seen=frame.sequence
                if self.stop.is_set():
                    break
                if self.record_requested.is_set():
                    after = client.foreground_package(serial)
                    if before == GAME_PACKAGE and after == GAME_PACKAGE:
                        if not self.stop.is_set() and self.record_requested.is_set():
                            if self.recorder is None:
                                self.recorder = FrameRecorder(ROOT/"recordings")
                                self.messages.put(("recording",str(self.recorder.directory)))
                            self.recorder.write(frame)
                    else:
                        self.messages.put(("record_wait","Recording waits until Clash is the active Android app."))
                elif self.recorder is not None:
                    self.recorder.close();self.recorder=None
                with self.lock:
                    self.latest = frame
                    self.frame_number += 1
                self.stop.wait(.05)
        except (DeviceError,OSError,RuntimeError,ImportError) as exc:
            self.messages.put(("error",str(exc)))
        finally:
            self.live_stream=None
            try:
                if stream: stream.stop()
                if self.recorder:
                    self.recorder.close()
            except OSError as exc:
                self.messages.put(("error",f"Recording could not be finalized: {exc}"))
            finally:
                self.recorder = None
                self.record_requested.clear()
                self.messages.put(("stopped",None))

    def toggle_record(self):
        if self.record_requested.is_set():
            self.record_requested.clear()
            self.record_button.configure(text="Record frames")
            self.status.set("Recording stopped; live capture continues.")
        else:
            self.record_requested.set()
            self.record_button.configure(text="Stop recording")
            self.status.set("Recording game frames only; waiting for the active Clash app.")

    def start_attack(self):
        if self.live_stream is None or (self.attack_worker and self.attack_worker.is_alive()):
            self.status.set('Start continuous live capture before a basic-army diagnostic.');return
        try:
            from .runtime import AttackRuntime
            from .experience import ExperienceStore
            from .training import LearningCoordinator
            client=self.client(); stream=self.live_stream
            if self.experience_store is None:
                self.experience_store=ExperienceStore(ROOT/'recordings/experience')
                self.learning=LearningCoordinator(self.experience_store,ROOT/'recordings/models')
        except (ImportError,DeviceError) as exc:
            self.status.set(str(exc)); return
        self.attack_stop.clear(); self.attack_button.configure(state='disabled')
        self.status.set('Starting one unscored diagnostic battle, up to10gold; no purchases/gems.')
        def run():
            try:
                runtime=AttackRuntime(client,stream,self.attack_stop,lambda value:self.messages.put(('automation',value)),self.attack_max_inputs,self.experience_store,self.learning)
                runtime.run(timeout=240)
            except Exception as exc:self.messages.put(('error','Controller stopped: '+str(exc)))
        self.attack_worker=threading.Thread(target=run,daemon=True); self.attack_worker.start()

    def stop_capture(self):
        self.stop.set()
        self.attack_stop.set()
        self.record_requested.clear()
        self.status.set("Stopping capture. An in-flight ADB request may take up to five seconds to return.")
        self.stop_button.configure(state="disabled")

    def toggle_compact(self):
        if self.compact.get():
            self.preview.pack_forget()
            self.root.geometry("540x390")
            self.root.minsize(480,350)
        else:
            self.preview.pack(fill="both",expand=True,before=self.preview.master.winfo_children()[-2])
            self.root.geometry("840x620")
            self.root.minsize(480,430)

    def poll(self):
        while True:
            try:
                kind,value = self.messages.get_nowait()
            except queue.Empty:
                break
            if kind == "devices":
                self.devices.configure(values=value)
                self.serial.set(value[0] if value else "")
                self.status.set("Emulator connected. Start live capture to verify background frames." if value else "No ready local emulator. Enable its ADB option and check the displayed port.")
            elif kind == "ready":
                self.busy = False
                self.connect_button.configure(state="normal")
            elif kind == "error":
                self.had_error = True
                self.status.set(value)
            elif kind=='automation':self.status.set(value)
            elif kind in {"recording","record_wait"}:
                self.status.set("Recording to "+value if kind == "recording" else value)
            elif kind == "stopped":
                self.live_button.configure(state="normal")
                self.connect_button.configure(state="normal")
                self.record_button.configure(state="disabled",text="Record frames")
                self.stop_button.configure(state="disabled")
                if self.stop.is_set() and not self.had_error:
                    self.status.set("Stopped. No further capture or game inputs will be started.")
                self.stats.set(self.stats.get()+" · stopped")
        with self.lock:
            frame,number = self.latest,self.frame_number
        enabled=self.live_stream is not None and not (self.attack_worker and self.attack_worker.is_alive())
        self.attack_button.configure(state='normal' if enabled else 'disabled')
        if frame and number != self.shown_number:
            self.shown_number = number
            age = f'{(time.monotonic()-frame.requested_at)*1000:.0f} ms' if frame.requested_at is not None else 'unknown'
            label='decode' if hasattr(frame,'source_pts_us') else 'capture'
            self.stats.set(f"{frame.image.width} × {frame.image.height} · {label} {frame.capture_ms:.0f} ms · source age bound {age} · {number} frames")
            if not self.compact.get():
                resized = frame.image.copy()
                resized.thumbnail((max(100,self.preview.winfo_width()-12),max(80,self.preview.winfo_height()-12)),Image.Resampling.LANCZOS)
                self.photo = ImageTk.PhotoImage(resized)
                self.preview.configure(image=self.photo,text="")
        self.poll_id = self.root.after(100,self.poll)

    def close(self):
        self.stop.set()
        self.attack_stop.set()
        if self.learning:self.learning.close()
        if self.experience_store:self.experience_store.close()
        self.record_requested.clear()
        self.root.after_cancel(self.poll_id)
        self.root.destroy()


def main():
    root = tk.Tk()
    NativeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
