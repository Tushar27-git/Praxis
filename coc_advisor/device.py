"""Native Android transport; never moves or clicks the Windows mouse."""
from dataclasses import dataclass
import io
import math
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import time

from PIL import Image


GAME_PACKAGE = "com.supercell.clashofclans"


class DeviceError(RuntimeError):
    pass


def find_adb():
    project = Path(__file__).resolve().parents[1]
    candidates = [project / ".tools/platform-tools/adb.exe"]
    for root in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")):
        if root:
            candidates.append(Path(root) / "BlueStacks_nxt/HD-Adb.exe")
    installed = shutil.which("adb")
    if installed:
        candidates.append(Path(installed))
    return next((path for path in candidates if path.is_file()), None)


def _serial(value):
    if not isinstance(value, str) or len(value) > 40:
        raise DeviceError("Select a local emulator, not a physical or remote device.")
    match = re.fullmatch(r"(?:127\.0\.0\.1:|emulator-)(\d{1,5})", value)
    if not match or not 1 <= int(match.group(1)) <= 65535:
        raise DeviceError("Select a local emulator serial or 127.0.0.1:port.")
    return value


def normalized_pixel(x, y, width, height):
    if type(width) is not int or type(height) is not int or width < 1 or height < 1:
        raise DeviceError("No valid device frame dimensions.")
    for value in (x, y):
        if type(value) not in (int, float) or not 0 <= value <= 1 or not math.isfinite(value):
            raise DeviceError("Input coordinates must be finite and inside the device frame.")
    return min(width-1, int(x*width)), min(height-1, int(y*height))


@dataclass(frozen=True)
class Frame:
    serial: str
    image: Image.Image
    png: bytes
    requested_at: float
    received_at: float

    @property
    def capture_ms(self):
        return (self.received_at-self.requested_at)*1000


class AdbClient:
    def __init__(self, executable, runner=subprocess.run):
        self.executable = str(executable)
        self.runner = runner

    def _run(self, args, serial=None, timeout=5):
        command = [self.executable]
        if serial is not None:
            command += ["-s", _serial(serial)]
        command += args
        try:
            result = self.runner(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 timeout=timeout, check=False,
                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise DeviceError(f"Android connection failed: {exc}") from exc
        if result.returncode:
            detail = result.stderr.decode("utf-8", errors="replace").strip()[-240:]
            raise DeviceError(detail or "ADB command failed. Check the emulator connection.")
        return result.stdout

    def devices(self):
        devices = []
        for line in self._run(["devices"]).decode("utf-8", errors="replace").splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                try:
                    devices.append(_serial(parts[0]))
                except DeviceError:
                    continue
        return devices

    def connect(self, endpoint):
        _serial(endpoint)
        if not endpoint.startswith("127.0.0.1:"):
            raise DeviceError("Enter the local 127.0.0.1:port shown by the emulator.")
        return self._run(["connect", endpoint]).decode("utf-8", errors="replace").strip()

    def capture(self, serial):
        started = time.monotonic()
        raw = self._run(["exec-out", "screencap"], serial=serial)
        received = time.monotonic()
        if not 12 <= len(raw) <= 96_000_016:
            raise DeviceError("The emulator did not return a valid raw frame.")
        width,height,pixel_format = struct.unpack_from("<III",raw)
        if not width or not height or width*height > 24_000_000 or pixel_format != 1:
            raise DeviceError("Unsupported Android frame size or pixel format; RGBA_8888 is required.")
        header_size = len(raw)-width*height*4
        if header_size not in (12,16):
            raise DeviceError("Truncated or unsupported Android raw frame.")
        image = Image.frombytes("RGB",(width,height),raw[header_size:],"raw","RGBX")
        output = io.BytesIO()
        # Android PNG compression blocked capture for seconds; encode on the PC instead.
        image.save(output,format="PNG",compress_level=1)
        return Frame(_serial(serial), image, output.getvalue(), started, received)

    def foreground_package(self, serial):
        text = self._run(["shell", "dumpsys", "activity", "activities"], serial=serial).decode("utf-8", errors="replace")
        for line in text.splitlines():
            if re.search(r"\b(?:topResumedActivity|mResumedActivity|ResumedActivity)\b", line):
                match = re.search(r"\b([a-zA-Z0-9_.]+)/[a-zA-Z0-9_.$]+", line)
                if match:
                    return match.group(1)
        return None

    def launch_game(self, serial):
        text = self._run(["shell", "cmd", "package", "resolve-activity", "--brief", GAME_PACKAGE], serial=serial).decode("utf-8", errors="replace")
        component = next((line.strip() for line in text.splitlines()
                          if re.fullmatch(re.escape(GAME_PACKAGE)+r"/[A-Za-z0-9_.$]+", line.strip())), None)
        if not component:
            raise DeviceError("Clash of Clans is not installed in the selected emulator. Install it from Google Play first.")
        self._run(["shell", "am", "start", "-n", component], serial=serial)

    def display_size(self, serial):
        text=self._run(['shell','wm','size'],serial=serial).decode(errors='replace')
        matches=re.findall(r'(?:Physical|Override) size:\s*(\d+)x(\d+)',text)
        if not matches: raise DeviceError('Cannot verify Android display dimensions.')
        return tuple(map(int,matches[-1]))

    @staticmethod
    def _ready(frame, stop):
        if stop.is_set():
            raise DeviceError("Stopped; pending game input was cancelled.")
        if frame.requested_at is None:
            raise DeviceError("Source frame freshness is unknown; game input blocked.")
        if hasattr(frame,'freshness_verified') and not frame.freshness_verified:
            raise DeviceError('Unverified stream timing; game input blocked.')
        if not 0 <= time.monotonic()-frame.requested_at <= .75:
            raise DeviceError("Frame is stale; get a fresh observation before game input.")

    def tap(self, frame, x, y, stop):
        self._ready(frame, stop)
        size=getattr(frame,'device_size',None) or frame.image.size
        px, py = normalized_pixel(x, y, *size)
        if self.foreground_package(frame.serial) != GAME_PACKAGE:
            raise DeviceError("Game input blocked: Clash of Clans is not the active Android app.")
        if getattr(frame,'device_size',None) and self.display_size(frame.serial)!=size:
            raise DeviceError('Android display changed; invalidate frame geometry.')
        self._ready(frame, stop)
        self._run(["shell", "input", "tap", str(px), str(py)], serial=frame.serial)

    def tap_latest(self, source, x, y, stop, validate, hold_ms=0):
        if stop.is_set(): raise DeviceError('Stopped before input validation.')
        first=source.latest()
        if first is None: raise DeviceError('No live frame.')
        if self.foreground_package(first.serial)!=GAME_PACKAGE: raise DeviceError('Clash is not the active Android app.')
        size=self.display_size(first.serial)
        # Blocking package/geometry probes must not make an otherwise live stream stale.
        frame=source.latest()
        if frame is None or getattr(frame,'device_size',None)!=size: raise DeviceError('Display geometry changed.')
        self._ready(frame,stop)
        if not validate(frame): raise DeviceError('Observed action target changed.')
        px,py=normalized_pixel(x,y,*size)
        self._ready(frame,stop)
        if type(hold_ms) is not int or not 0<=hold_ms<=500: raise DeviceError('Deployment hold exceeds 500ms bound.')
        args=['shell','input','tap',str(px),str(py)] if not hold_ms else ['shell','input','swipe',str(px),str(py),str(px),str(py),str(hold_ms)]
        self._run(args,serial=frame.serial)
        return frame
