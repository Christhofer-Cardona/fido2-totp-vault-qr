# Security

Report suspected vulnerabilities through this repository's private GitHub
vulnerability reporting channel. Please use synthetic enrollment data in
reproductions and omit PINs, passwords, and real account details.

The program reads a local image, decodes one QR code, validates a standard
TOTP URI, and writes a new entry to the existing vault only after `--apply`.
The image and decoded seed remain sensitive until your own retention process
removes them. This companion does not alter the vault's encryption or security
key implementation. It is not a sandbox for untrusted image files.
