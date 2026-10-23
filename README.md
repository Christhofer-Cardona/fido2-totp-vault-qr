# FIDO2 TOTP Vault QR Import

Import a TOTP setup QR code from a **local image** into
[FIDO2 TOTP Vault](https://github.com/Christhofer-Cardona/fido2-totp-vault).
The vault CLI intentionally accepts text enrollment URIs; this companion reads
one QR image offline, validates its `otpauth://totp` content using the vault
package, and writes it to the existing FIDO2-gated KDBX database only with
`--apply`. No seed is sent to a QR-decoding website, printed, or passed as a
command-line argument.

## Use

Requires Python 3.11+, a local copy of the QR image, and an initialized vault.
On Windows, macOS, or Linux:

```bash
git clone https://github.com/Christhofer-Cardona/fido2-totp-vault-qr.git
cd fido2-totp-vault-qr
python -m venv .venv
# Activate .venv using your shell's normal command, then:
python -m pip install -e .
fido2-totp-qr path/to/qr.png
fido2-totp-qr path/to/qr.png --apply
```

Preview is the default. It checks for exactly one QR code and shows only the
proposed entry name. `--name` overrides that name. Applying asks FidoVault for
the enrolled security key and its configured PIN or additional password.
Existing names, seeds, and issuer/account pairs are rejected. The decoded
URI stays in process memory; the image is never copied or deleted by this tool.

An enrollment QR image is effectively a password. Keep it private, do not
upload it to issue trackers or cloud QR readers, and remove it using your own
retention process after a successful import. Storage devices may retain copies
or snapshots even after deletion. The local image decoder is
[ZXing-C++](https://github.com/zxing-cpp/zxing-cpp); image loading uses Pillow.
Only standard TOTP QR codes supported by the main vault are accepted, with a
16 MiB file and 24 megapixel image limit. Multiple QR codes are rejected to
avoid choosing the wrong account.

## Development and security

This project is maintained by **Christhofer Cardona**. Security issues can be
reported using GitHub's private vulnerability reporting channel for this
repository. Do not include real enrollment images, seeds, codes, or PINs in
reports. See [SECURITY.md](SECURITY.md) for scope and limitations.

Run `python -m unittest discover -s tests -v` from an environment where this
package is installed. Tests use only a public synthetic seed and fake hardware
unlock; they do not prove physical key compatibility. The parent vault's
[validation record](https://github.com/Christhofer-Cardona/fido2-totp-vault/blob/main/docs/VALIDATION.md)
covers its own hardware and platform testing.
Native Windows and macOS runs of this companion have not yet been recorded;
see [validation](docs/VALIDATION.md) for the exact current checks.

This project is GPL-3.0-or-later because it depends on and integrates with the
GPL-licensed vault package. See [LICENSE](LICENSE).
