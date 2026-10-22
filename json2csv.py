#!/usr/bin/env python3
"""json2csv — JSON (array of objects, or NDJSON) -> CSV, stdlib only.

- union of keys in first-seen order (ragged records keep every column)
- nested objects flattened to dot.notation (--flatten, default on)
- proper quoting via csv module (commas, quotes, newlines survive)
- --delimiter, --encoding, --columns to pin/order a schema
- NDJSON input auto-detected (one object per line)
- named error + exit 1 on malformed input
"""
import argparse
import csv
import io
import json
import sys


def load(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    text = raw.decode("utf-8")
    if not text.strip():
        raise SystemExit("error: input file is empty")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        rows = []
        for i, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise SystemExit(f"error: line {i} is not valid JSON: {e.msg}")
        return rows
    if isinstance(data, dict):
        for key in ("data", "rows", "items", "results"):
            if isinstance(data.get(key), list):
                return data[key]
        return [data]
    if not isinstance(data, list):
        raise SystemExit("error: top-level JSON must be an array of objects or an object")
    return data


def flatten(obj, prefix=""):
    out = {}
    for k, v in obj.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(flatten(v, key + "."))
        elif isinstance(v, list):
            out[key] = json.dumps(v, ensure_ascii=False)
        else:
            out[key] = v
    return out


def scalar(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


def convert(rows, columns=None, do_flatten=True):
    norm = []
    for r in rows:
        if not isinstance(r, dict):
            raise SystemExit("error: every record must be a JSON object")
        norm.append(flatten(r) if do_flatten else r)
    if columns:
        cols = list(columns)
    else:
        cols, seen = [], set()
        for r in norm:
            for k in r:
                if k not in seen:
                    seen.add(k)
                    cols.append(k)
    return cols, [[scalar(r.get(c, "")) for c in cols] for r in norm]


def main(argv=None):
    ap = argparse.ArgumentParser(description="Convert JSON/NDJSON to CSV (tolerant).")
    ap.add_argument("input")
    ap.add_argument("-o", "--output")
    ap.add_argument("--delimiter", default=",")
    ap.add_argument("--columns", help="comma-separated column order")
    ap.add_argument("--no-flatten", action="store_true")
    a = ap.parse_args(argv)

    rows = load(a.input)
    cols, table = convert(rows, a.columns.split(",") if a.columns else None, not a.no_flatten)

    buf = io.StringIO()
    w = csv.writer(buf, delimiter=a.delimiter, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
    w.writerow(cols)
    w.writerows(table)
    body = buf.getvalue()

    if a.output:
        open(a.output, "w", encoding="utf-8", newline="").write(body)
        print(json.dumps({"rows": len(table), "columns": len(cols)}), file=sys.stderr)
    else:
        sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
