"""Create and verify SHA-256 release manifests without external dependencies."""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path

FORMAT = "release-notary-v1"

def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()

def build_manifest(paths: list[Path]) -> dict:
    if not paths:
        raise ValueError("at least one artifact is required")
    names = set()
    artifacts = []
    for path in paths:
        if not path.is_file():
            raise ValueError(f"not a regular file: {path}")
        if path.name in names:
            raise ValueError(f"duplicate artifact name: {path.name}")
        names.add(path.name)
        artifacts.append({"name": path.name, "size": path.stat().st_size, "sha256": digest(path)})
    return {"format": FORMAT, "artifacts": sorted(artifacts, key=lambda item: item["name"])}

def verify_manifest(manifest: dict, directory: Path) -> dict:
    if not isinstance(manifest, dict) or manifest.get("format") != FORMAT or not isinstance(manifest.get("artifacts"), list):
        raise ValueError("invalid manifest format")
    results = []
    seen = set()
    for item in manifest["artifacts"]:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str) or not isinstance(item.get("sha256"), str) or not isinstance(item.get("size"), int):
            raise ValueError("invalid artifact entry")
        name = item["name"]
        if not name or name in {".", ".."} or Path(name).name != name or "/" in name or "\\" in name or name in seen:
            raise ValueError("invalid or duplicate artifact name")
        if len(item["sha256"]) != 64 or any(ch not in "0123456789abcdef" for ch in item["sha256"]):
            raise ValueError("invalid SHA-256 digest")
        seen.add(name)
        path = directory / name
        if not path.is_file():
            status = "missing"
        elif path.stat().st_size != item["size"] or digest(path) != item["sha256"]:
            status = "mismatch"
        else:
            status = "ok"
        results.append({"name": name, "status": status})
    return {"ok": all(r["status"] == "ok" for r in results), "results": results}

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Create or verify SHA-256 release manifests")
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create", help="Create manifest from release files")
    create.add_argument("artifacts", nargs="+", type=Path)
    create.add_argument("--output", required=True, type=Path)
    verify = commands.add_parser("verify", help="Verify files against manifest")
    verify.add_argument("manifest", type=Path)
    verify.add_argument("--directory", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    try:
        if args.command == "create":
            output = args.output.resolve()
            if any(p.resolve() == output for p in args.artifacts):
                raise ValueError("manifest output must not be one of the artifacts")
            manifest = build_manifest(args.artifacts)
            args.output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            print(f"Created {args.output} ({len(manifest['artifacts'])} artifacts)")
            return 0
        report = verify_manifest(json.loads(args.manifest.read_text(encoding="utf-8")), args.directory)
        print(json.dumps(report, indent=2))
        return 0 if report["ok"] else 1
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"release-notary: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
