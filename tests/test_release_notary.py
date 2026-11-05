import json
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stdout
from io import StringIO
from release_notary import build_manifest, verify_manifest, main

class ReleaseNotaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.dir = Path(self.temp.name)
        self.file = self.dir / "app.zip"
        self.file.write_bytes(b"hello release")
    def tearDown(self):
        self.temp.cleanup()
    def test_round_trip(self):
        report = verify_manifest(build_manifest([self.file]), self.dir)
        self.assertTrue(report["ok"])
    def test_modified(self):
        manifest = build_manifest([self.file])
        self.file.write_bytes(b"tampered")
        self.assertEqual(verify_manifest(manifest, self.dir)["results"][0]["status"], "mismatch")
    def test_missing(self):
        manifest = build_manifest([self.file])
        self.file.unlink()
        self.assertEqual(verify_manifest(manifest, self.dir)["results"][0]["status"], "missing")
    def test_duplicate_name(self):
        with self.assertRaises(ValueError):
            build_manifest([self.file, self.file])
    def test_reject_path_traversal(self):
        manifest = {"format": "release-notary-v1", "artifacts": [{"name": "../secret", "size": 1, "sha256": "a" * 64}]}
        with self.assertRaises(ValueError):
            verify_manifest(manifest, self.dir)
    def test_cli_round_trip(self):
        manifest = self.dir / "SHA256-manifest.json"
        with redirect_stdout(StringIO()):
            self.assertEqual(main(["create", str(self.file), "--output", str(manifest)]), 0)
            self.assertEqual(main(["verify", str(manifest), "--directory", str(self.dir)]), 0)
        self.assertEqual(json.loads(manifest.read_text())["format"], "release-notary-v1")
if __name__ == "__main__":
    unittest.main()
