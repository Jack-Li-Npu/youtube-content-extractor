import json
import tempfile
import unittest
from pathlib import Path

from workers.local_subtitles import ExtractionError, export, normalize_segments, probe_media, timestamp


class CaptionRegressions(unittest.TestCase):
    def test_clip_offset_and_export_after_one_hour(self):
        raw = [
            {
                "start": 0.125,
                "end": 2.875,
                "text": " First sentence. Second sentence.",
                "words": [
                    {"word": " First", "start": 0.125, "end": 0.5},
                    {"word": " sentence.", "start": 0.5, "end": 1.25},
                    {"word": " Second", "start": 2, "end": 2.5},
                    {"word": " sentence.", "start": 2.5, "end": 2.875},
                ],
            }
        ]
        segments = normalize_segments(raw, offset=3660, duration=3, language="en")
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0]["start"], 3660.125)
        self.assertEqual(segments[0]["duration"], 1.125)
        self.assertEqual(timestamp(3660.125, True), "01:01:00,125")
        with tempfile.TemporaryDirectory() as folder:
            prefix = Path(folder) / "captions"
            export({"metadata": {}, "segments": segments}, prefix)
            srt = Path(str(prefix) + ".srt").read_text()
            md = Path(str(prefix) + ".md").read_text()
            self.assertIn("01:01:00,125 --> 01:01:01,250", srt)
            for segment in segments:
                self.assertIn(segment["text"], srt)
                self.assertIn(segment["text"], md)
            self.assertEqual(json.loads(Path(str(prefix) + ".json").read_text())["segments"], segments)

    def test_empty_asr_is_an_error(self):
        with self.assertRaises(ExtractionError) as error:
            normalize_segments([], offset=0, duration=10, language="en")
        self.assertEqual(error.exception.code, "no_speech")

    def test_bad_timing_is_an_error(self):
        for start, end in ((1, 0.5), (float("nan"), 2), (0, 12)):
            with self.assertRaises(ExtractionError) as error:
                normalize_segments(
                    [{"text": "Speech", "start": start, "end": end}], offset=0, duration=10, language="en"
                )
            self.assertEqual(error.exception.code, "timing_invalid")

    def test_bad_word_alignment_keeps_complete_native_text(self):
        raw = [
            {
                "start": 0,
                "end": 2,
                "text": "Keep all this text.",
                "words": [
                    {"word": " Keep", "start": 0, "end": 0},
                ],
            }
        ]
        segment = normalize_segments(raw, offset=0, duration=3, language="en")[0]
        self.assertEqual(segment["text"], raw[0]["text"])
        self.assertIn("word_alignment_fallback", segment["quality_flags"])

    def test_missing_file_is_distinct(self):
        with self.assertRaises(ExtractionError) as error:
            probe_media(Path(tempfile.gettempdir()) / "missing-subtitle-regression-video.mp4")
        self.assertEqual(error.exception.code, "file_missing")


if __name__ == "__main__":
    unittest.main()
