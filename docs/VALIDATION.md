# Validation record

Recorded 2026-10-23 on Fedora Linux, Python 3.14.7, against the published
`fido2-totp-vault==0.2.0` wheel.

- Three offline tests passed: preview redaction, unsupported QR and symlink
  rejection, and encrypted KDBX import with duplicate rejection. The import
  test used a public synthetic seed and fake FidoVault unlock.
- The installed console command printed its help and a standard wheel built.
- Wheel metadata declares the vault package as a runtime dependency and names
  Christhofer Cardona as author and maintainer.

The QR decoder and KDBX write were exercised locally. No physical key was
used in this companion's tests. Native Windows and macOS runs are pending.
The parent vault's [release validation](https://github.com/Christhofer-Cardona/fido2-totp-vault/blob/main/docs/VALIDATION.md)
records its own platform and physical-key results.
