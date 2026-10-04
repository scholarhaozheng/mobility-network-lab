#!/usr/bin/env python3
"""Check the single declared computational download against public source bytes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import zipfile

ARCHIVE = "docs/downloads/computational-checkout.zip"
MANIFEST = "docs/downloads/computational-checkout.manifest.json"
ALLOWED_SUFFIXES = {".cff", ".cjs", ".css", ".csv", ".geojson", ".html", ".js", ".json", ".lock", ".md", ".npz", ".png", ".py", ".sql", ".svg", ".txt", ".yaml", ".yml"}
EXTENSIONLESS = {".gitattributes", "LICENSE", "algorithms/origin_based_algorithm_b/LICENSE"}
FORBIDDEN_PARTS = {".git", ".venv", "__pycache__", "external_data", "private_data", "private_audit", "conversation_exports", "cache", "release", "paper", "manuscript", "results", "outputs"}


def safe_member(name: str) -> bool:
    path = PurePosixPath(name)
    return (bool(name) and not path.is_absolute() and "\\" not in name and ":" not in name
            and all(part not in {"", ".", ".."} for part in name.split("/"))
            and not any(part.lower() in FORBIDDEN_PARTS for part in path.parts)
            and (path.suffix.lower() in ALLOWED_SUFFIXES or name in EXTENSIONLESS))


def validate(root: Path) -> dict:
    archive, manifest = root / ARCHIVE, root / MANIFEST
    errors: list[str] = []
    checks = 0
    if not archive.exists() and not manifest.exists():
        return {"status": "NOT_PRESENT", "checks": 0, "errors": [], "allowed_archives": []}
    if not archive.is_file() or not manifest.is_file():
        return {"status": "FAIL", "checks": 1, "errors": ["Computational download and manifest must both exist"], "allowed_archives": []}
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        if data.get("schema") != "mcl_public_computational_archive_v1" or data.get("archive") != archive.name:
            errors.append("Computational archive manifest identity differs")
        if archive.stat().st_size > 100 * 1024 * 1024:
            errors.append("Computational archive exceeds the 100 MiB safety limit")
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        if digest != data.get("sha256") or archive.stat().st_size != data.get("bytes"):
            errors.append("Computational archive SHA-256 or byte count differs")
        release_id = data.get("releaseId", "")
        expected_revision = "reproduction-" + release_id[:4] + "-" + release_id[4:6] + "-" + release_id[6:]
        if data.get("sourceRevision") != expected_revision:
            errors.append("Computational archive source revision does not match its release ID")
        download_index = root / "docs/downloads/downloads.json"
        if download_index.is_file():
            index = json.loads(download_index.read_text(encoding="utf-8"))
            if index.get("releaseId") != release_id or index.get("sourceRevision") != expected_revision:
                errors.append("Download index release identity differs from the archive manifest")
        checks += 2
        declared = data.get("files", [])
        if not declared or len(declared) > 10000:
            errors.append("Computational archive member count is invalid")
        names = [item.get("path", "") for item in declared]
        if len(names) != len(set(name.casefold() for name in names)):
            errors.append("Duplicate computational archive member")
        checks += 4
        with zipfile.ZipFile(archive) as bundle:
            actual = bundle.infolist()
            if sorted(item.filename for item in actual) != sorted(names):
                errors.append("Computational archive member set differs from its exact manifest")
            if sum(item.file_size for item in actual) > 512 * 1024 * 1024:
                errors.append("Computational archive expanded size exceeds 512 MiB")
            checks += 2
            for item in declared:
                name = item.get("path", "")
                if not safe_member(name) or item.get("source") != name:
                    errors.append(f"Unsafe computational archive source/member: {name}")
                    continue
                path = root / name
                if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
                    errors.append(f"Missing or unsafe computational source: {name}")
                    continue
                entry = bundle.getinfo(name)
                if entry.is_dir() or stat.S_ISLNK(entry.external_attr >> 16) or entry.flag_bits & 1:
                    errors.append(f"Non-regular or encrypted computational member: {name}")
                    continue
                content = bundle.read(name)
                digest = hashlib.sha256(content).hexdigest()
                if digest != item.get("sha256") or len(content) != item.get("bytes"):
                    errors.append(f"Computational member hash or size differs: {name}")
                if content != path.read_bytes():
                    errors.append(f"Computational member differs from public repository source: {name}")
                checks += 4
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as exc:
        errors.append(f"Invalid computational archive: {exc}")
    return {"status": "PASS" if not errors else "FAIL", "checks": checks, "errors": errors,
            "allowed_archives": [ARCHIVE] if not errors else []}


if __name__ == "__main__":
    report = validate(Path(__file__).resolve().parents[1])
    print(json.dumps(report, indent=2))
    raise SystemExit(bool(report["errors"]))
