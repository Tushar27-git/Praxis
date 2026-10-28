import io
import struct
import threading
import time
import unittest
from PIL import Image
from coc_advisor.device import AdbClient, DeviceError
from coc_advisor.stream import read_exact, read_packet, LatestFrame, LiveFrame, ClockMap, CausalClock, decode_packet


class Fragmented:
    def __init__(self, data): self.data = io.BytesIO(data)
    def recv(self, n): return self.data.read(min(2,n))


class StreamTests(unittest.TestCase):
    def test_codec_configuration_is_not_decoded_as_picture(self):
        class Decoder:
            def decode(self, packet): raise AssertionError('Configuration is not a picture')
        decoder=Decoder()
        self.assertEqual(decode_packet(decoder,1<<63,b'codec config'),[])
        self.assertEqual(decoder.extradata,b'codec config')
    def test_fragmented_packet_preserves_pts(self):
        pts, payload = read_packet(Fragmented(struct.pack('>QI',123456,3)+b'abc'))
        self.assertEqual((pts,payload),(123456,b'abc'))

    def test_truncated_and_oversized_packets_fail(self):
        for data in [b'x',struct.pack('>QI',1,100000000),struct.pack('>QI',1,4)+b'a']:
            with self.subTest(data=data), self.assertRaises(DeviceError): read_packet(Fragmented(data))

    def test_latest_slot_replaces_old_frame(self):
        slot = LatestFrame()
        for n in range(100): slot.publish(n)
        self.assertEqual(slot.latest(),99)

    def test_unknown_and_buffered_frame_cannot_be_used_for_input(self):
        for acquired in [None,time.monotonic()-4]:
            frame = LiveFrame('emulator-5554',Image.new('RGB',(2,2)),1,123,time.monotonic(),time.monotonic(),acquired)
            with self.assertRaises(DeviceError): AdbClient._ready(frame,threading.Event())

    def test_scaled_stream_tap_maps_to_android_display(self):
        from test_device import Runner
        r=Runner([b'mResumedActivity: ActivityRecord{x u0 com.supercell.clashofclans/.Game}',
                  b'Physical size: 1600x900\n',b''])
        now=time.monotonic()
        f=LiveFrame('emulator-5554',Image.new('RGB',(960,544)),1,1,now,now,now,(1600,900),True)
        AdbClient('adb',r).tap(f,.5,.5,threading.Event())
        self.assertEqual(r.calls[-1][-2:],['800','450'])

    def test_latest_tap_observes_new_frame_after_slow_checks(self):
        from test_device import Runner
        r=Runner([b'mResumedActivity: ActivityRecord{x u0 com.supercell.clashofclans/.Game}',b'Physical size: 1600x900',b''])
        class Source:
            def latest(self):
                now=time.monotonic()
                return LiveFrame('emulator-5554',Image.new('RGB',(960,544)),1,1,now,now,now,(1600,900),True)
        AdbClient('adb',r).tap_latest(Source(),.5,.5,threading.Event(),lambda f:True)
        self.assertEqual(r.calls[-1][-2:],['800','450'])

    def test_clock_bound_is_conservative_and_bad_epoch_rejected(self):
        clock = ClockMap(1000,10.0,1000.1)
        self.assertAlmostEqual(clock.lower_bound(10_200_000,1000.25),1000.18)
        self.assertIsNone(clock.lower_bound(100,1000.25))

    def test_causal_barrier_not_uptime_epoch_authorizes_frame_age(self):
        clock=CausalClock(100.)
        self.assertEqual(clock.lower_bound(9_000_000,100.2),100.)
        self.assertLessEqual(clock.lower_bound(10_000_000,101.2),101.)
        self.assertIsNone(clock.lower_bound(8_000_000,102.))

    def test_png_is_only_encoded_when_requested(self):
        f=LiveFrame('emulator-5554',Image.new('RGB',(2,2)),1,1,1,1,None)
        self.assertNotIn('_png',f.__dict__)
        self.assertTrue(f.png.startswith(b'\x89PNG'))
