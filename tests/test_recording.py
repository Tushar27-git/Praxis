import csv
import json
from pathlib import Path
import tempfile
import unittest

from coc_advisor.recording import FrameRecorder
from test_device import frame


class RecordingTests(unittest.TestCase):
    def test_records_original_frames_with_dimensions_and_timestamps(self):
        workspace_tmp = Path(__file__).resolve().parents[1]/"tmp"
        workspace_tmp.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=workspace_tmp) as tmp:
            self.assertTrue(Path(tmp).resolve().is_relative_to(workspace_tmp.resolve()))
            recorder = FrameRecorder(Path(tmp))
            sample = frame()
            recorder.write(sample)
            recorder.write(sample)
            recorder.close()
            self.assertEqual((recorder.directory/"000001.png").read_bytes(), sample.png)
            with (recorder.directory/"frames.csv").open(newline="",encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows),2)
            self.assertEqual(rows[0]["width"],"200")
            self.assertEqual(rows[0]["serial"],sample.serial)
            self.assertIn("+00:00",rows[0]["received_utc"])
    def test_optional_metadata_is_paired_with_the_recorded_frame(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'tmp') as tmp:
            recorder=FrameRecorder(tmp)
            try:
                recorder.write(frame(),metadata={'scene':'home','reason':'Paused: own Town Hall level not verified'})
            finally:recorder.close()
            metadata=json.loads((recorder.directory/'000001.json').read_text(encoding='utf-8'))
            self.assertEqual(metadata['scene'],'home')
            self.assertEqual(metadata['reason'],'Paused: own Town Hall level not verified')
            self.assertTrue((recorder.directory/'000001.png').is_file())


if __name__ == "__main__":
    unittest.main()
