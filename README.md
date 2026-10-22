# csv2json / json2csv

Two tolerant converters, Python 3.8+, stdlib only:

- `csv2json.py` — CSV/TSV → JSON (or NDJSON)
- `json2csv.py` — JSON array / NDJSON → CSV, union of keys, dot.notation flattening

Handles the things naive converters break on:

- BOM (`utf-8-sig`), mixed encodings via `--encoding`
- delimiter sniffing (`,` `;` `\t` `|`) with `--delimiter` override
- embedded newlines and quotes inside fields
- ragged rows (short rows padded, long rows folded into the last column)
- duplicate headers (`x, x` → `x`, `x_2`), blank headers → `column_N`
- blank trailing rows
- optional type inference (`--types`: int / float / bool)
- NDJSON output (`--ndjson`) for streaming pipelines

## Usage

```bash
python csv2json.py input.csv -o out.json
python csv2json.py data.tsv --ndjson --types
python csv2json.py export.csv --encoding latin-1 --delimiter ';'
```

Exit codes: `0` ok, `1` empty/bad input with a named message on stderr.

## Tests

```bash
python -m unittest -v test_csv2json
```

5 tests covering quotes/newlines, BOM+semicolon, ragged/blank rows, duplicate
headers, and type inference.


## json2csv

```bash
python json2csv.py data.json -o out.csv
python json2csv.py events.ndjson --columns id,ts,type
python json2csv.py nested.json --no-flatten
```

Union of keys in first-seen order, nested objects flattened to `a.b`, arrays
serialised as JSON inside one cell, `null` → empty, booleans → `true/false`,
proper CSV quoting. 5 unittest cases (`test_json2csv.py`).
