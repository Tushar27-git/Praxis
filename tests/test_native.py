import tkinter as tk
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from coc_advisor.native import NativeApp
from coc_advisor.device import DeviceError
from test_device import frame


class NativeUiTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = NativeApp(self.root)

    def tearDown(self):
        self.app.close()

    def test_device_discovery_populates_explicit_emulator_selection(self):
        self.app.messages.put(("devices",["127.0.0.1:5555"]))
        self.app.poll()
        self.assertEqual(self.app.serial.get(),"127.0.0.1:5555")
        self.assertIn("connected",self.app.status.get())

    def test_compact_overlay_is_narrower_and_can_restore_preview(self):
        self.app.compact.set(True)
        self.app.toggle_compact()
        self.root.update_idletasks()
        self.assertLessEqual(int(self.root.geometry().split("x")[0]),560)
        self.assertEqual(self.app.preview.winfo_manager(),"")
        self.app.compact.set(False)
        self.app.toggle_compact()
        self.assertEqual(self.app.preview.winfo_manager(),"pack")

    def test_stop_completion_clears_stopping_status(self):
        self.app.stop_capture()
        self.app.messages.put(("stopped",None))
        self.app.poll()
        self.assertTrue(self.app.stop.is_set())
        self.assertTrue(self.app.status.get().startswith("Stopped"))
        self.assertEqual(str(self.app.record_button["state"]),"disabled")

    def test_basic_attack_requires_live_stream_and_stop_cancels_it(self):
        self.assertEqual(str(self.app.attack_button['state']),'disabled')
        self.app.start_attack()
        self.assertIsNone(self.app.attack_worker)
        self.app.stop_capture()
        self.assertTrue(self.app.attack_stop.is_set())

    def test_stop_keeps_attack_disabled_during_capture_shutdown(self):
        self.app.live_stream=object()
        self.app.attack_button.configure(state='normal')
        self.app.stop_capture()
        self.assertEqual(str(self.app.attack_button['state']),'disabled')
        self.app.poll()
        self.assertEqual(str(self.app.attack_button['state']),'disabled')

    def test_learning_owner_is_reused_across_native_runs(self):
        root=Path(__file__).resolve().parents[1]/'tmp'
        temp=tempfile.TemporaryDirectory(dir=root); self.addCleanup(temp.cleanup)
        calls=[]
        class Runtime:
            def __init__(self,*args):calls.append(args[-2:])
            def run(self,timeout):pass
        with patch('coc_advisor.native.ROOT',Path(temp.name)),patch('coc_advisor.runtime.AttackRuntime',Runtime):
            self.app.live_stream=SimpleNamespace(latest=lambda:frame())
            self.app.start_attack(); self.app.attack_worker.join()
            self.app.start_attack(); self.app.attack_worker.join()
        self.assertIs(calls[0][0],calls[1][0]); self.assertIs(calls[0][1],calls[1][1])

    def test_attack_rejects_missing_stale_unknown_and_failed_stream_frames(self):
        unknown=SimpleNamespace(requested_at=None)
        unverified=SimpleNamespace(requested_at=0,freshness_verified=False)
        for value in (None,frame(age=5),unknown,unverified):
            with self.subTest(value=value),patch('coc_advisor.runtime.AttackRuntime') as runtime:
                self.app.live_stream=SimpleNamespace(latest=lambda:value)
                self.app.start_attack()
                runtime.assert_not_called()
                self.assertIsNone(self.app.attack_worker)
                self.assertIn('Restart live capture',self.app.status.get())
        def disconnected():raise DeviceError('Video stream closed')
        self.app.live_stream=SimpleNamespace(latest=disconnected)
        self.app.start_attack()
        self.assertIsNone(self.app.attack_worker)
        self.assertIn('Video stream closed',self.app.status.get())

    def test_recorder_close_error_cannot_strand_capture_state(self):
        class BrokenRecorder:
            def close(self):
                raise OSError("disk flush failed")
        class DisconnectedDevice:
            def foreground_package(self, serial):
                return "com.supercell.clashofclans"
            def capture(self, serial):
                raise DeviceError("disconnected")
        self.app.recorder = BrokenRecorder()
        self.app.record_requested.set()
        self.app.capture_loop(DisconnectedDevice(),"emulator-5554")
        events = []
        while not self.app.messages.empty():
            events.append(self.app.messages.get_nowait()[0])
        self.assertIn("stopped",events)
        self.assertFalse(self.app.record_requested.is_set())

    def test_transition_from_another_app_does_not_record_its_frame(self):
        class SwitchingDevice:
            def __init__(self):
                self.package = "com.android.vending"
                self.count = 0
            def foreground_package(self, serial):
                return self.package
            def capture(self, serial):
                self.count += 1
                if self.count > 1:
                    raise DeviceError("end of test stream")
                self.package = "com.supercell.clashofclans"
                return frame(serial=serial)
        workspace_tmp = Path(__file__).resolve().parents[1]/"tmp"
        workspace_tmp.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=workspace_tmp) as temp:
            self.assertTrue(Path(temp).resolve().is_relative_to(workspace_tmp.resolve()))
            self.app.record_requested.set()
            with patch("coc_advisor.native.ROOT",Path(temp)):
                self.app.capture_loop(SwitchingDevice(),"emulator-5554")
            self.assertEqual(list(Path(temp).rglob("*.png")),[])


if __name__ == "__main__":
    unittest.main()
