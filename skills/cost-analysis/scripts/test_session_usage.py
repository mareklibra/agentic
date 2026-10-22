"""Tests for session-usage.py. Run: python3 -I skills/cost-analysis/scripts/test_session_usage.py"""
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

    def test_last_record_of_a_message_id_wins(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "s.jsonl"
            p.write_text("\n".join([record("a", 5), record("a", 9)]))
            t, _ = su.totals(su.read_usage(p))
        self.assertEqual(t["out"], 9)

    def test_weighted_uses_the_documented_ratios(self):
        t = {"in": 10, "cw": 10, "cr": 100, "out": 2}
        self.assertEqual(su.weighted(t), 10 + 12.5 + 10 + 10)

    def test_label_survives_bad_meta_and_strips_control_chars(self):
        with tempfile.TemporaryDirectory() as d:
            sub = Path(d) / "agent-x.jsonl"
            sub.write_text("")
            self.assertEqual(su.label_of(sub), "agent-x")  # no .meta.json
            sub.with_suffix(".meta.json").write_text("[1, 2]")  # not a dict
            self.assertEqual(su.label_of(sub), "agent-x")
            sub.with_suffix(".meta.json").write_text(
                json.dumps({"description": "a\x1b[31mb", "spawnDepth": 2})
            )
            self.assertEqual(su.label_of(sub), "a [31mb (d2)")

    def test_main_counts_nested_subagents_and_needs_a_project_value(self):
        import contextlib
        import io

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "sess1.jsonl").write_text(record("m1", 1))
            nested = root / "sess1" / "subagents" / "deeper"
            nested.mkdir(parents=True)
            (nested / "agent-n.jsonl").write_text(record("n1", 2))
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                su.main(["sess1", "--project", str(root)])
            text = out.getvalue()
            self.assertIn("agent-n", text)
            self.assertIn("TOTAL", text)
            with self.assertRaises(SystemExit):
                su.main(["sess1", "--project"])

    def test_clean_strips_c1_and_bidi_controls(self):
        self.assertEqual(su.clean("a\x9bb‮c\x1bd"), "a b c d")

    def test_glob_characters_in_the_prefix_are_literal(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "ab[1]x.jsonl").write_text("")
            (Path(d) / "ab1x.jsonl").write_text("")
            found = su.find_transcript(Path("ab[1]"), Path(d))
        self.assertEqual(found.name, "ab[1]x.jsonl")

    def test_unknown_prefix_exits(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(SystemExit):
                su.find_transcript(Path("zzz"), Path(d))


if __name__ == "__main__":
    unittest.main()
