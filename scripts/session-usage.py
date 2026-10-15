#!/usr/bin/env python3
"""Token usage of one Claude Code session, from its transcripts.

Usage: session-usage.py <session-id-or-jsonl-path> [--project DIR]

Reads the main transcript plus every subagent transcript below the session
directory (nested agents included), de-duplicates by message.id (the same
usage block is repeated once per content block, a naive sum double-counts),
and prints raw and price-weighted tokens per transcript and per model.

Weights are a ratio model, not a bill: cache read 0.1x, cache write 1.25x,
output 5x of a base input token.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

W = {"in": 1.0, "cw": 1.25, "cr": 0.1, "out": 5.0}


def read_usage(path):
    """Return {message.id: (model, usage dict)}, last record per id wins."""
    seen = {}
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            msg = rec.get("message") if isinstance(rec, dict) else None
            if not isinstance(msg, dict) or not isinstance(msg.get("usage"), dict):
                continue
            mid = msg.get("id") or rec.get("uuid")
            if mid:
                seen[mid] = (msg.get("model") or "?", msg["usage"])
    return seen


def totals(seen):
    t = defaultdict(float)
    by_model = defaultdict(lambda: defaultdict(float))
    for model, u in seen.values():
        row = {
            "in": u.get("input_tokens", 0),
            "cw": u.get("cache_creation_input_tokens", 0),
            "cr": u.get("cache_read_input_tokens", 0),
            "out": u.get("output_tokens", 0),
        }
        for k, v in row.items():
            t[k] += v
            by_model[model][k] += v
        t["msgs"] += 1
        by_model[model]["msgs"] += 1
    return t, by_model


def weighted(t):
    return sum(t[k] * w for k, w in W.items())


def fmt(label, t):
    return (
        f"{label:<40} msgs={int(t['msgs']):>4} in={int(t['in']):>8} "
        f"cw={int(t['cw']):>9} cr={int(t['cr']):>11} out={int(t['out']):>8} "
        f"weighted={int(weighted(t)):>10}"
    )


def find_transcript(arg, project=None):
    """Resolve a .jsonl path or a session-id prefix to one main transcript.

    `project` is one project directory (it holds <session>.jsonl directly);
    without it every project below ~/.claude/projects is searched. The nested
    subagent files never match because they are named agent-*.jsonl and live
    one level deeper.
    """
    if arg.suffix == ".jsonl":
        return arg
    if project:
        hits = list(project.glob(f"{arg.name}*.jsonl"))
        where = project
    else:
        where = Path.home() / ".claude" / "projects"
        hits = list(where.glob(f"*/{arg.name}*.jsonl"))
    if not hits:
        sys.exit(f"no transcript for session {arg.name} under {where}")
    if len(hits) > 1:
        # A wrong session would silently give wrong numbers: make the user pick.
        names = "\n  ".join(str(h) for h in sorted(hits))
        sys.exit(f"session prefix {arg.name} is ambiguous:\n  {names}")
    return hits[0]


def main(argv):
    if not argv:
        sys.exit(__doc__)
    project = None
    if "--project" in argv:
        i = argv.index("--project")
        project = Path(argv[i + 1]).expanduser()
        del argv[i : i + 2]
    main_jsonl = find_transcript(Path(argv[0]).expanduser(), project)
    session_dir = main_jsonl.with_suffix("")

    rows = [("main session", read_usage(main_jsonl))]
    for sub in sorted(session_dir.glob("**/agent-*.jsonl")):
        label = sub.stem
        meta = sub.with_suffix(".meta.json")
        try:
            m = json.loads(meta.read_text())
            label = f"{m.get('description') or sub.stem} (d{m.get('spawnDepth', '?')})"
        except (OSError, ValueError):
            pass  # a missing .meta.json only loses the label
        rows.append((label[:40], read_usage(sub)))

    grand = defaultdict(float)
    models = defaultdict(lambda: defaultdict(float))
    for label, seen in rows:
        t, by_model = totals(seen)
        print(fmt(label, t))
        for k, v in t.items():
            grand[k] += v
        for model, mt in by_model.items():
            for k, v in mt.items():
                models[model][k] += v
    print("-" * 40)
    print(fmt("TOTAL", grand))
    main_w = weighted(totals(rows[0][1])[0])
    if weighted(grand):
        print(f"main session share (weighted): {main_w / weighted(grand):.0%}")
        print(f"cache-read share of raw tokens: {grand['cr'] / max(1, grand['in'] + grand['cw'] + grand['cr'] + grand['out']):.0%}")
    for model, mt in sorted(models.items()):
        print(fmt(f"model {model}", mt))


if __name__ == "__main__":
    main(sys.argv[1:])
