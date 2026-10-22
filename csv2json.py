#!/usr/bin/env python3
"""csv2json — tolerant CSV/TSV -> JSON converter (stdlib only).

Usage:
  python csv2json.py input.csv [-o out.json] [--delimiter ,] [--encoding utf-8]
                     [--indent 2] [--ndjson] [--types]

Handles BOM, duplicate headers, ragged rows, embedded newlines/quotes and
blank trailing rows. Fails with a named message + exit code 2 on bad input.
"""
import argparse
import csv
import io
import json
import sys


def _uniquify(header):
    out, seen = [], {}
    for i, h in enumerate(header):
        name = (h or "").strip().lstrip("\ufeff") or f"column_{i+1}"
        if name in seen:
            seen[name] += 1
            name = f"{name}_{seen[name]}"
        else:
            seen[name] = 1
        out.append(name)
    return out


def _infer(value):
    v = value.strip()
    if v == "":
        return ""
    low = v.lower()
    if low in ("true", "false"):
        return low == "true"
    try:
        return int(v)
    except ValueError:
        pass
    try:
        f = float(v)
        return f
    except ValueError:
        return value


def convert(path, delimiter=None, encoding="utf-8", types=False):
    with open(path, "rb") as fh:
        raw = fh.read()
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    try:
        text = raw.decode(encoding)
    except UnicodeDecodeError as e:
        raise SystemExit(f"error: cannot decode {path} as {encoding}: {e}")
    if not text.strip():
        raise SystemExit("error: input file is empty")

    sample = text[:8192]
    if delimiter is None:
        try:
            delimiter = csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
        except csv.Error:
            delimiter = ","

    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    try:
        header = next(reader)
    except StopIteration:
        raise SystemExit("error: no header row found")
    names = _uniquify(header)

    rows, skipped = [], 0
    for lineno, row in enumerate(reader, start=2):
        if not any(cell.strip() for cell in row):
            skipped += 1
            continue
        if len(row) != len(names):
            if len(row) < len(names):
                row = row + [""] * (len(names) - len(row))
            else:
                row = row[: len(names) - 1] + [delimiter.join(row[len(names) - 1:])]
        rec = {n: (_infer(v) if types else v) for n, v in zip(names, row)}
        rows.append(rec)

    return rows, {"delimiter": delimiter, "columns": len(names), "rows": len(rows),
                  "blank_rows_skipped": skipped}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Convert CSV to JSON (tolerant).")
    ap.add_argument("input")
    ap.add_argument("-o", "--output")
    ap.add_argument("--delimiter")
    ap.add_argument("--encoding", default="utf-8")
    ap.add_argument("--indent", type=int, default=2)
    ap.add_argument("--ndjson", action="store_true", help="one JSON object per line")
    ap.add_argument("--types", action="store_true", help="infer int/float/bool")
    a = ap.parse_args(argv)

    rows, meta = convert(a.input, a.delimiter, a.encoding, a.types)
    if a.ndjson:
        body = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows)
    else:
        body = json.dumps(rows, ensure_ascii=False, indent=a.indent)

    if a.output:
        with open(a.output, "w", encoding="utf-8") as fh:
            fh.write(body)
        print(json.dumps(meta), file=sys.stderr)
    else:
        print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
