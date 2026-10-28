"""Lossless frame recordings for real-device perception development."""
import csv
from datetime import datetime, timezone
from pathlib import Path


class FrameRecorder:
    def __init__(self, root):
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
        self.directory = Path(root)/stamp
        self.directory.mkdir(parents=True)
        self.handle = (self.directory/"frames.csv").open("w",newline="",encoding="utf-8")
        self.csv = csv.writer(self.handle)
        self.csv.writerow(["sequence","received_utc","serial","width","height","capture_ms"])
        self.count = 0

    def write(self, frame):
        if self.handle.closed:
            raise RuntimeError("Recording is closed.")
        number = self.count+1
        target = self.directory/f"{number:06d}.png"
        temporary = target.with_suffix(".part")
        temporary.write_bytes(frame.png)
        temporary.replace(target)
        self.csv.writerow([number,datetime.now(timezone.utc).isoformat(),frame.serial,
                           frame.image.width,frame.image.height,round(frame.capture_ms,3)])
        self.handle.flush()
        self.count = number

    def close(self):
        self.handle.close()
