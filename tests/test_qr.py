"""Synthetic, offline QR and KDBX acceptance tests."""

import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from PIL import Image
from pykeepass import PyKeePass, create_database
import zxingcpp

from fido2_totp_vault_qr.cli import decode_image, import_spec, main, QrImportError

PUBLIC_URI = (
    "otpauth://totp/Example:alice?secret=JBSWY3DPEHPK3PXP&issuer=Example"
)


class QrTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="vault-qr-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.image = self.root / "enrollment.png"
        self.make_qr(PUBLIC_URI)

    def make_qr(self, value):
        barcode = zxingcpp.create_barcode(value, zxingcpp.BarcodeFormat.QRCode)
        Image.fromarray(barcode.to_image(scale=5)).save(self.image)

    def test_preview_is_offline_and_never_prints_seed(self):
        out, err = StringIO(), StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            self.assertEqual(main([str(self.image)]), 0)
        self.assertIn("Example:alice", out.getvalue())
        self.assertIn("No vault change", out.getvalue())
        self.assertNotIn("JBSWY3", out.getvalue() + err.getvalue())

    def test_rejects_non_totp_and_symlink(self):
        self.make_qr("https://example.com/login")
        with self.assertRaisesRegex(QrImportError, "not a supported TOTP"):
            decode_image(self.image)
        if os.name != "nt":
            link = self.root / "link.png"
            link.symlink_to(self.image)
            with self.assertRaisesRegex(QrImportError, "regular file"):
                decode_image(link)

    @unittest.skipIf(os.name == "nt", "native Windows ACL fixture is separate")
    def test_apply_persists_one_entry_and_rejects_duplicate(self):
        vault_root = self.root / "vault-data"
        vault_root.mkdir(mode=0o700)
        vault = vault_root / "totp.vault"
        vault.write_text("[Key 1]\n", encoding="utf-8")
        vault.chmod(0o600)
        database = vault_root / "totp.kdbx"
        create_database(str(database), password="synthetic-password")
        database.chmod(0o600)
        fake = self.root / "fake-fidovault"
        fake.write_text("#!/bin/sh\nprintf 'synthetic-password\\n'\n")
        fake.chmod(0o700)
        with patch.dict(os.environ, {
            "FIDO2_TOTP_VAULT_HOME": str(vault_root),
            "FIDO2_TOTP_VAULT_FIDOVAULT": str(fake),
        }):
            out, err = StringIO(), StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                self.assertEqual(main([str(self.image), "--apply"]), 0, err.getvalue())
            stored = PyKeePass(str(database), password="synthetic-password")
            self.assertEqual(len(stored.entries), 1)
            self.assertEqual(database.stat().st_mode & 0o777, 0o600)
            self.assertEqual(stored.entries[0].title, "Example:alice")
            self.assertIn("otpauth://totp/", stored.entries[0].otp)
            self.assertNotIn("JBSWY3", out.getvalue() + err.getvalue())
            with redirect_stdout(out), redirect_stderr(err):
                self.assertEqual(main([str(self.image), "--apply"]), 1)
            stored = PyKeePass(str(database), password="synthetic-password")
            self.assertEqual(len(stored.entries), 1)
            self.assertNotIn("JBSWY3", out.getvalue() + err.getvalue())


if __name__ == "__main__":
    unittest.main()
