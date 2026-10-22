import json, os, tempfile, unittest
import csv2json

class T(unittest.TestCase):
    def _f(self, text, name):
        p = os.path.join(tempfile.mkdtemp(), name)
        open(p, "w", encoding="utf-8", newline="").write(text)
        return p

    def test_quotes_and_newlines(self):
        p = self._f('a,b\n"x, y","line1\nline2"\n', "q.csv")
        rows, meta = csv2json.convert(p)
        self.assertEqual(rows[0]["a"], "x, y")
        self.assertIn("\n", rows[0]["b"])

    def test_bom_and_semicolon(self):
        p = self._f('\ufeffid;v\n1;a\n', "b.csv")
        rows, meta = csv2json.convert(p)
        self.assertEqual(meta["delimiter"], ";")
        self.assertEqual(list(rows[0]), ["id", "v"])

    def test_ragged_and_blank(self):
        p = self._f('a,b,c\n1,2\n\n3,4,5,6\n', "r.csv")
        rows, meta = csv2json.convert(p)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["c"], "")
        self.assertEqual(rows[1]["c"], "5,6")

    def test_duplicate_headers(self):
        p = self._f('x,x\n1,2\n', "d.csv")
        rows, _ = csv2json.convert(p)
        self.assertEqual(sorted(rows[0]), ["x", "x_2"])

    def test_types(self):
        p = self._f('n,f,b,s\n1,1.5,true,abc\n', "t.csv")
        rows, _ = csv2json.convert(p, types=True)
        self.assertIsInstance(rows[0]["n"], int)
        self.assertIsInstance(rows[0]["f"], float)
        self.assertIs(rows[0]["b"], True)

if __name__ == "__main__":
    unittest.main()
