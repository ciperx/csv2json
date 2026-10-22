import json, os, tempfile, unittest
import json2csv

def tmp(text, name):
    p = os.path.join(tempfile.mkdtemp(), name)
    open(p, "w", encoding="utf-8").write(text)
    return p

class T(unittest.TestCase):
    def test_union_of_keys(self):
        p = tmp('[{"a":1},{"b":2,"a":3}]', "u.json")
        cols, rows = json2csv.convert(json2csv.load(p))
        self.assertEqual(cols, ["a", "b"])
        self.assertEqual(rows[1], ["3", "2"])

    def test_nested_flatten(self):
        p = tmp('[{"id":1,"user":{"name":"x","tags":["a","b"]}}]', "n.json")
        cols, rows = json2csv.convert(json2csv.load(p))
        self.assertIn("user.name", cols)
        self.assertIn("user.tags", cols)

    def test_quoting_survives(self):
        p = tmp('[{"t":"a,b","q":"he said \\"hi\\"","n":"line1\\nline2"}]', "q.json")
        cols, rows = json2csv.convert(json2csv.load(p))
        import csv, io
        buf = io.StringIO(); w = csv.writer(buf); w.writerow(cols); w.writerows(rows)
        back = list(csv.reader(io.StringIO(buf.getvalue())))
        self.assertEqual(back[1][0], "a,b")
        self.assertIn("line1\nline2", back[1][2])

    def test_ndjson(self):
        p = tmp('{"a":1}\n{"a":2}\n', "n.ndjson")
        cols, rows = json2csv.convert(json2csv.load(p))
        self.assertEqual(len(rows), 2)

    def test_null_and_bool(self):
        p = tmp('[{"a":null,"b":true}]', "x.json")
        cols, rows = json2csv.convert(json2csv.load(p))
        self.assertEqual(rows[0], ["", "true"])

if __name__ == "__main__":
    unittest.main()
