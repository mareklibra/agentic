"""Tests for session-usage.py. Run: python3 -I scripts/test_session_usage.py"""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "session_usage", Path(__file__).with_name("session-usage.py")
)
su = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(su)


def record(mid, out, model="m"):
    usage = {
        "input_tokens": 1,
        "cache_creation_input_tokens": 10,
        "cache_read_input_tokens": 100,
        "output_tokens": out,
    }
    return json.dumps({"message": {"id": mid, "model": model, "usage": usage}})


class SessionUsage(unittest.TestCase):
    def test_same_message_id_is_counted_once(self):
        # The harness repeats a usage block once per content block.
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "s.jsonl"
            p.write_text("\n".join([record("a", 5), record("a", 5), record("b", 7)]))
            t, by_model = su.totals(su.read_usage(p))
        self.assertEqual(t["msgs"], 2)
        self.assertEqual(t["out"], 12)
        self.assertEqual(t["cr"], 200)
        self.assertEqual(set(by_model), {"m"})

    def test_garbage_and_usage_free_lines_are_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "s.jsonl"
            p.write_text("not json\n{}\n" + json.dumps({"message": {"id": "x"}}) + "\n")
            self.assertEqual(su.read_usage(p), {})

    def test_find_transcript_in_project_dir(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "abc123.jsonl").write_text("")
            found = su.find_transcript(Path("abc"), Path(d))
        self.assertEqual(found.name, "abc123.jsonl")

    def test_ambiguous_prefix_exits(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "abc1.jsonl").write_text("")
            (Path(d) / "abc2.jsonl").write_text("")
            with self.assertRaises(SystemExit) as cm:
                su.find_transcript(Path("abc"), Path(d))
        self.assertIn("ambiguous", str(cm.exception))

    def test_unknown_prefix_exits(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(SystemExit):
                su.find_transcript(Path("zzz"), Path(d))


if __name__ == "__main__":
    unittest.main()
