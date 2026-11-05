# Release Notary

A dependency-free Python CLI for generating and verifying **SHA-256 checksum manifests** for software release artifacts.

## Features

- Stream SHA-256 checksums for large files
- Record artifact filenames and sizes in JSON
- Detect missing, modified, and duplicate artifacts
- Reject path traversal in manifests
- Automate verification with exit codes: 0 (verified), 1 (mismatch/missing), 2 (invalid input)
- Run on Python 3.9+

## Install

```bash
python -m pip install .
```

## Example

```bash
release-notary create dist/app.zip dist/app.tar.gz --output dist/SHA256-manifest.json
release-notary verify dist/SHA256-manifest.json --directory dist
```

Or run `python release_notary.py --help`.

The manifest stores artifact **base filenames**. Artifacts must have unique names, and verification looks for them directly inside the selected directory.

## Security notes

SHA-256 manifests detect accidental or malicious changes **only when the manifest itself is obtained from a trusted source**. This tool does **not** sign files, verify publisher identity, or replace cryptographic signatures or provenance attestations. Do not describe a checksum as proof of authorship.

## Development

```bash
python -m unittest discover -s tests -v
python -m pip install build
python -m build
```

GitHub Actions runs unit tests and builds on Linux and Windows, Python 3.9/3.11/3.13.

## License

MIT.
