"""Pinned scrcpy 3.3.3 H.264 client. One pending decoded frame, no PNG hot path."""
from dataclasses import dataclass
from fractions import Fraction
from functools import cached_property
import io
from pathlib import Path
import secrets
import socket
import struct
import subprocess
import threading
import time

from .device import DeviceError, _serial

VERSION = '3.3.3'
SERVER = Path(__file__).resolve().parents[1]/'.tools/scrcpy'/f'scrcpy-server-v{VERSION}'


def read_exact(sock, count):
    result = bytearray()
    while len(result)<count:
        part = sock.recv(count-len(result))
        if not part: raise DeviceError('Video stream closed or truncated.')
        result.extend(part)
    return bytes(result)


def read_packet(sock):
    flags,size = struct.unpack('>QI',read_exact(sock,12))
    if not 0<size<=16*1024*1024: raise DeviceError('Invalid video packet size.')
    return flags,read_exact(sock,size)


def decode_packet(decoder,flags,data):
    if flags&(1<<63):
        decoder.extradata=data
        return []
    import av
    pts=flags&((1<<62)-1)
    packet=av.Packet(data); packet.pts=pts; packet.dts=pts; packet.time_base=Fraction(1,1000000)
    return decoder.decode(packet)


class LatestFrame:
    def __init__(self): self._frame=None; self._lock=threading.Lock()
    def publish(self, frame):
        with self._lock: self._frame=frame
    def latest(self):
        with self._lock: return self._frame


@dataclass(frozen=True)
class ClockMap:
    host_before: float
    device_uptime: float
    host_after: float

    def lower_bound(self, pts_us, received):
        # Conditional on matching monotonic epochs; reject an incompatible clock.
        lower=self.host_before + pts_us/1e6-self.device_uptime-.02
        age=received-lower
        if self.host_after-self.host_before>.5 or not 0<=age<5: return None
        return lower


class CausalClock:
    """A lower bound anchored before the server can start its first capture.

    Pinned Server.java starts capture only after DesktopConnection accepts the
    control socket. No assumption about the absolute encoder/uptime epoch.
    A1000ppm drift allowance and monotonic/future checks fail closed.
    """
    def __init__(self,barrier_at):
        self.barrier_at=barrier_at; self.first_pts=None; self.last_pts=None; self.invalid=False
    def lower_bound(self,pts,received):
        if self.invalid:return None
        if self.first_pts is None:self.first_pts=pts
        if self.last_pts is not None and pts<self.last_pts:self.invalid=True;return None
        self.last_pts=pts; elapsed=(pts-self.first_pts)/1e6
        bound=self.barrier_at+elapsed-max(0.,elapsed)*.001
        if bound>received or received-self.barrier_at>300:self.invalid=True;return None
        return bound


@dataclass(frozen=True)
class LiveFrame:
    serial: str
    image: object
    sequence: int
    source_pts_us: int
    received_at: float
    decoded_at: float
    requested_at: float | None
    device_size: tuple | None = None
    freshness_verified: bool = False

    @property
    def capture_ms(self): return (self.decoded_at-self.received_at)*1000

    @cached_property
    def png(self):
        output=io.BytesIO(); self.image.save(output,format='PNG',compress_level=1)
        return output.getvalue()


class VideoStream:
    def __init__(self, client, serial, max_size=960, max_fps=30):
        self.client=client; self.serial=_serial(serial)
        self.max_size=max_size; self.max_fps=max_fps
        self.slot=LatestFrame(); self.error=None; self.count=0
        self.stop_event=threading.Event(); self.sock=None; self.process=None
        self.port=None; self.thread=None; self.logs=[]; self.clock=None
        self.control_sock=None; self.timing=None

    def start(self):
        import av
        if not SERVER.is_file(): raise DeviceError('Pinned scrcpy server is missing under .tools/scrcpy/.')
        try:
            clocks=[]
            for _ in range(3):
                before=time.monotonic()
                uptime=float(self.client._run(['shell','cat','/proc/uptime'],serial=self.serial).split()[0])
                clocks.append(ClockMap(before,uptime,time.monotonic()))
            self.clock=min(clocks,key=lambda c:c.host_after-c.host_before)
            self.device_size=self.client.display_size(self.serial)
            self.client._run(['push',str(SERVER),'/data/local/tmp/coc-scrcpy.jar'],serial=self.serial)
            scid=f'{secrets.randbelow(0x7fffffff):08x}'; name='scrcpy_'+scid
            self.port=int(self.client._run(['forward','tcp:0','localabstract:'+name],serial=self.serial).strip())
            args=[self.client.executable,'-s',self.serial,'shell',
                  'CLASSPATH=/data/local/tmp/coc-scrcpy.jar','app_process','/',
                  'com.genymobile.scrcpy.Server',VERSION,'scid='+scid,
                  'tunnel_forward=true','audio=false','control=true','power_on=false','clipboard_autosync=false',
                  'send_device_meta=false','video_codec=h264',f'max_size={self.max_size}',
                  f'max_fps={self.max_fps}','video_bit_rate=2000000']
            self.process=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            threading.Thread(target=self._drain_logs,daemon=True).start()
            deadline=time.monotonic()+10
            while True:
                try:
                    self.sock=socket.create_connection(('127.0.0.1',self.port),timeout=.5)
                    if read_exact(self.sock,1)!=b'\0': raise DeviceError('Invalid video handshake.')
                    break
                except (OSError,DeviceError):
                    if self.sock: self.sock.close(); self.sock=None
                    if time.monotonic()>deadline: raise DeviceError('Video startup failed: '+' '.join(self.logs[-3:]))
                    time.sleep(.1)
            self.sock.settimeout(3)
            # The server is blocked accepting this second socket: capture cannot
            # predate the host call that opens it (pinned3.3.3startup ordering).
            barrier_at=time.monotonic()
            self.control_sock=socket.create_connection(('127.0.0.1',self.port),timeout=2)
            self.timing=CausalClock(barrier_at)
            codec,w,h=struct.unpack('>III',read_exact(self.sock,12))
            if codec!=0x68323634 or not 0<w*h<=24_000_000: raise DeviceError('Unsupported video codec/size.')
            self.decoder=av.CodecContext.create('h264','r'); self.decoder.thread_count=1
            self.thread=threading.Thread(target=self._read_loop,daemon=True); self.thread.start()
        except Exception:
            self.stop(); raise
        return self

    def _drain_logs(self):
        for line in iter(self.process.stdout.readline,b''):
            self.logs.append(line.decode(errors='replace').strip())
            self.logs[:]=self.logs[-20:]

    def _read_loop(self):
        import av
        try:
            while not self.stop_event.is_set():
                flags,data=read_packet(self.sock); received=time.monotonic()
                for decoded in decode_packet(self.decoder,flags,data):
                    if self.stop_event.is_set(): break
                    actual_pts=decoded.pts
                    if actual_pts is None: raise DeviceError('Decoder lost source timestamps.')
                    if decoded.time_base: actual_pts=round(actual_pts*float(decoded.time_base)*1e6)
                    image=decoded.to_image(); now=time.monotonic(); self.count+=1
                    bound=self.timing.lower_bound(actual_pts,received)
                    self.slot.publish(LiveFrame(self.serial,image,self.count,actual_pts,received,now,bound,self.device_size,bound is not None))
        except Exception as exc:
            if not self.stop_event.is_set(): self.error=str(exc)
        finally:
            self.stop_event.set()

    def latest(self):
        if self.error: raise DeviceError(self.error)
        return self.slot.latest()

    def stop(self):
        self.stop_event.set()
        if self.control_sock:
            self.control_sock.close(); self.control_sock=None
        if self.sock:
            try: self.sock.shutdown(socket.SHUT_RDWR)
            except OSError: pass
            self.sock.close(); self.sock=None
        if self.process:
            if self.process.poll() is None:
                self.process.terminate()
                try: self.process.wait(timeout=2)
                except subprocess.TimeoutExpired: self.process.kill(); self.process.wait(timeout=2)
            if self.process.stdout: self.process.stdout.close()
        if self.thread and self.thread is not threading.current_thread(): self.thread.join(timeout=2)
        if self.port:
            try: self.client._run(['forward','--remove',f'tcp:{self.port}'],serial=self.serial)
            except DeviceError: pass
            self.port=None
