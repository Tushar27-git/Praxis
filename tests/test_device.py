import io
import subprocess
import struct
import threading
import time
import unittest

from PIL import Image
from coc_advisor.device import AdbClient, DeviceError, Frame, normalized_pixel


def png():
    output = io.BytesIO()
    Image.new("RGB", (200, 100), "#204060").save(output, format="PNG")
    return output.getvalue()


def raw_frame(width=2, height=1, header_size=16):
    header = struct.pack("<III", width, height, 1)
    if header_size == 16:
        header += struct.pack("<I", 0)
    return header + bytes([20, 40, 60, 255])*width*height


class Runner:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def __call__(self, args, **kwargs):
        self.calls.append(args)
        return subprocess.CompletedProcess(args, 0, next(self.responses), b"")


def frame(age=0, serial="127.0.0.1:5555"):
    return Frame(serial, Image.new("RGB", (200, 100)), png(), time.monotonic()-age, time.monotonic())


class DeviceTests(unittest.TestCase):
    def test_lists_only_ready_local_emulators(self):
        runner = Runner([b"List of devices attached\nemulator-5554\tdevice\n127.0.0.1:5555\tdevice\nphone123\tdevice\n127.0.0.1:5556\toffline\n10.0.0.2:5555\tdevice\n"])
        self.assertEqual(AdbClient("adb.exe", runner).devices(), ["emulator-5554", "127.0.0.1:5555"])

    def test_capture_decodes_binary_and_always_scopes_to_serial(self):
        runner = Runner([raw_frame()])
        result = AdbClient("adb.exe", runner).capture("127.0.0.1:5555")
        self.assertEqual(result.image.size, (2,1))
        self.assertEqual(result.image.getpixel((0,0)), (20,40,60))
        self.assertTrue(result.png.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertEqual(runner.calls[0], ["adb.exe", "-s", "127.0.0.1:5555", "exec-out", "screencap"])
        self.assertGreaterEqual(result.capture_ms, 0)

    def test_older_android_raw_header_is_supported(self):
        result = AdbClient("adb.exe", Runner([raw_frame(header_size=12)])).capture("emulator-5554")
        self.assertEqual(result.image.getpixel((1,0)), (20,40,60))

    def test_rejects_truncated_or_unsupported_raw_frames(self):
        wrong_format = struct.pack("<IIII",2,1,4,0)+bytes(8)
        oversized = struct.pack("<IIII",999999,999999,1,0)
        for raw in [raw_frame()[:-1],wrong_format,oversized]:
            with self.subTest(raw=raw[:16]), self.assertRaises(DeviceError):
                AdbClient("adb.exe",Runner([raw])).capture("emulator-5554")

    def test_bad_frame_is_an_error_not_a_fake_live_image(self):
        with self.assertRaises(DeviceError):
            AdbClient("adb.exe", Runner([b"device offline"])).capture("emulator-5554")

    def test_rejects_remote_and_non_emulator_targets(self):
        for target in ["192.168.1.2:5555", "phone123", "127.0.0.1:70000", "127.0.0.1:5555; rm x", ""]:
            with self.subTest(target=target), self.assertRaises(DeviceError):
                AdbClient("adb.exe", Runner([])).capture(target)

    def test_background_tap_targets_android_pixels_not_desktop_coordinates(self):
        runner = Runner([b"mResumedActivity: ActivityRecord{a u0 com.supercell.clashofclans/.GameApp t1}", b""])
        AdbClient("adb.exe", runner).tap(frame(), 1, .5, threading.Event())
        self.assertEqual(runner.calls[-1], ["adb.exe", "-s", "127.0.0.1:5555", "shell", "input", "tap", "199", "50"])

    def test_no_tap_on_stale_frame(self):
        runner = Runner([])
        with self.assertRaises(DeviceError):
            AdbClient("adb.exe", runner).tap(frame(age=30), .5, .5, threading.Event())
        self.assertEqual(runner.calls, [])

    def test_no_tap_outside_clash(self):
        runner = Runner([b"mResumedActivity: ActivityRecord{b u0 com.android.vending/.Login t2}"])
        with self.assertRaises(DeviceError):
            AdbClient("adb.exe", runner).tap(frame(), .5, .5, threading.Event())
        self.assertEqual(len(runner.calls), 1)

    def test_stop_during_focus_check_prevents_queued_tap(self):
        stop = threading.Event()
        calls = []
        def runner(args, **kwargs):
            calls.append(args)
            stop.set()
            return subprocess.CompletedProcess(args, 0, b"mResumedActivity: ActivityRecord{a u0 com.supercell.clashofclans/.GameApp t1}", b"")
        with self.assertRaises(DeviceError):
            AdbClient("adb.exe", runner).tap(frame(), .5, .5, stop)
        self.assertEqual(len(calls), 1)

    def test_coordinate_validation(self):
        for x in [True, float("nan"), -1, 1.01, "0.5"]:
            with self.subTest(x=x), self.assertRaises(DeviceError):
                normalized_pixel(x, .5, 200, 100)
        self.assertEqual(normalized_pixel(0, 0, 200,100), (0,0))

    def test_resolves_game_activity_instead_of_guessing(self):
        runner = Runner([b"com.supercell.clashofclans/com.supercell.titan.GameApp\n", b"Starting"])
        AdbClient("adb.exe", runner).launch_game("emulator-5554")
        self.assertEqual(runner.calls[-1][-5:], ["shell", "am", "start", "-n", "com.supercell.clashofclans/com.supercell.titan.GameApp"])


if __name__ == "__main__":
    unittest.main()
