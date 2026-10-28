"""Explicit one-battle test harness with the real native Stop button visible."""
from pathlib import Path
import sys
import time
import tkinter as tk
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from coc_advisor.native import NativeApp


def main():
    if '--execute-approved-once' not in sys.argv:
        raise SystemExit('Live run disabled; explicit approval and --execute-approved-once required.')
    root=tk.Tk(); app=NativeApp(root); app.attack_max_inputs=39; app.connect(); started=time.monotonic()
    log=(Path(__file__).resolve().parents[1]/'output/native/native-diagnostic.log').open('w',encoding='utf-8')
    state={'capturing':False,'launched':False,'last_status':None}
    def poll():
        text=app.status.get()
        if text!=state['last_status']:
            log.write(f'{time.monotonic()-started:.3f} {text}\n');log.flush();state['last_status']=text
        if not state['capturing'] and app.serial.get() and not app.busy:
            app.start_capture();state['capturing']=True
        if state['capturing'] and not state['launched'] and app.live_stream and app.live_stream.latest():
            app.start_attack();state['launched']=True
        if time.monotonic()-started>260 and app.attack_worker and app.attack_worker.is_alive():app.stop_capture()
        root.after(100,poll)
    root.after(100,poll)
    try:root.mainloop()
    finally:log.close()


if __name__=='__main__':main()
