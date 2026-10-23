"""Read exactly one standard TOTP QR image and import it without echoing its seed."""

from __future__ import annotations

import argparse
import os
import stat
import sys
from pathlib import Path

from PIL import Image, UnidentifiedImageError
import zxingcpp

from fido2_totp_vault.otp import InvalidOtp, OtpSpec, parse_uri
from fido2_totp_vault.store import Store, StoreError

MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_IMAGE_PIXELS = 24_000_000
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS


class QrImportError(ValueError):
    """A QR image cannot be imported safely."""


def decode_image(path: Path) -> OtpSpec:
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_FILE_BYTES:
        raise QrImportError("image must be a regular file of at most 16 MiB")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
    fd = os.open(path, flags)
    with os.fdopen(fd, "rb") as handle:
        opened = os.fstat(handle.fileno())
        if not stat.S_ISREG(opened.st_mode) or opened.st_size > MAX_FILE_BYTES:
            raise QrImportError("image must be a regular file of at most 16 MiB")
        if (info.st_dev, info.st_ino) != (opened.st_dev, opened.st_ino):
            raise QrImportError("image changed while opening")
        with Image.open(handle) as image:
            if image.width * image.height > MAX_IMAGE_PIXELS:
                raise QrImportError("image exceeds the 24 megapixel limit")
            image.load()
            symbols = zxingcpp.read_barcodes(
                image.convert("RGB"), formats=zxingcpp.BarcodeFormat.QRCode
            )
    if len(symbols) != 1:
        raise QrImportError("image must contain exactly one readable QR code")
    try:
        return parse_uri(symbols[0].text)
    except InvalidOtp as exc:
        raise QrImportError("QR code is not a supported TOTP enrollment URI") from exc


def import_spec(store: Store, name: str, spec: OtpSpec) -> None:
    if not 1 <= len(name) <= 100 or not name.isprintable():
        raise QrImportError("entry name must be 1–100 printable characters")
    with store.locked():
        database = store.open_database()
        for entry in database.entries:
            if (entry.title or "").casefold() == name.casefold():
                raise QrImportError("entry name already exists")
            if not entry.otp:
                continue
            old = parse_uri(entry.otp)
            if old.secret == spec.secret:
                raise QrImportError("TOTP seed is already stored")
            if (old.issuer.casefold(), old.account.casefold()) == (
                spec.issuer.casefold(), spec.account.casefold()
            ):
                raise QrImportError("issuer and account are already stored")
        entry = database.add_entry(database.root_group, name, spec.account, "")
        entry.otp = spec.uri()
        entry.notes = f"Issuer: {spec.issuer}. Imported from a local QR image."
        store.save_database(database)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fido2-totp-qr",
        description="Import one local TOTP QR image into FIDO2 TOTP Vault.",
    )
    parser.add_argument("image", type=Path, help="local image containing one QR code")
    parser.add_argument("--name", help="vault entry name (default: issuer:account)")
    parser.add_argument(
        "--apply", action="store_true", help="unlock the hardware key and store the entry"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    # PyKeePass creates a temporary file during save. Match the parent CLI's
    # private umask before any possible write, including on a user's first run.
    if os.name == "posix":
        os.umask(0o077)
    try:
        spec = decode_image(args.image)
        name = args.name or f"{spec.issuer}:{spec.account}"
        if not 1 <= len(name) <= 100 or not name.isprintable():
            raise QrImportError("entry name must be 1–100 printable characters")
        if not args.apply:
            print("One supported TOTP QR code found. No vault change made.")
            print(f"Proposed entry: {name}")
            print("Run again with --apply to import it using your security key.")
            return 0
        import_spec(Store(), name, spec)
        print(f"Imported {name}.")
        return 0
    except (
        QrImportError,
        StoreError,
        InvalidOtp,
        FileNotFoundError,
        PermissionError,
        UnidentifiedImageError,
        Image.DecompressionBombError,
        OSError,
    ) as exc:
        # Image-decoder exception text can include decoded content. Never print it.
        if isinstance(exc, (QrImportError, StoreError, InvalidOtp)):
            print(f"Error: {exc}", file=sys.stderr)
        else:
            print("Error: could not safely read or decode the image", file=sys.stderr)
        return 1
    except Exception:
        print("Error: unexpected QR import failure", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
