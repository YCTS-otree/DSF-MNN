"""Preserve a named research commit and its declared artifacts without changing originals.

Only published runtime/dependency paths and previously declared synthetic artifacts
are read. No environment dump, user config, credential directory or key file is read.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import platform
import shutil
import sqlite3
import subprocess
import sys
from uuid import uuid4
import zipfile
from zoneinfo import ZoneInfo

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "29d7de6b3fcb2e909ea8f49436640de77db09f6d"
TAG = "research-baseline-29d7de6"
RUNS = ["20261024T131935+0800-ad043dfdbc", "20261024T132006+0800-62f4c67863",
        "20261024T132038+0800-d61aba89f9", "20261024T132204+0800-9245f92d0d",
        "release-20261024T132259-49ba45f15e"]
BLOCKED_SUFFIXES = {".key", ".pem", ".pfx", ".p12", ".der"}
BLOCKED_NAMES = {".env", ".npmrc", ".pypirc", "id_rsa", "id_ed25519", "id_ecdsa", "credentials", "direct_url.json"}


def json_write(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as output:
        json.dump(value, output, ensure_ascii=False, indent=2)
        output.write("\n")


def sha(path):
    result = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def git(*args, binary=False):
    return subprocess.run(["git", "-c", "safe.directory=" + ROOT.as_posix(), *args], cwd=ROOT,
                          check=True, capture_output=True, text=not binary).stdout


def safe_file(path, boundary):
    original = Path(path)
    original.resolve().relative_to(boundary.resolve())
    current = original
    while current != boundary:
        info = current.lstat()
        if current.is_symlink() or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("reparse-point-not-archived")
        current = current.parent
    if any(p.lower() in BLOCKED_NAMES for p in original.parts) or original.suffix.lower() in BLOCKED_SUFFIXES:
        raise ValueError("credential-or-key-path-excluded")
    return original


def archive_files(destination, files):
    entries = []
    with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=3) as output:
        for name, (path, boundary) in sorted(files.items()):
            safe_file(path, boundary)
            before = sha(path)
            output.write(path, name)
            if sha(path) != before:
                raise ValueError("source-changed-during-freeze")
            entries.append({"path": name, "bytes": path.stat().st_size, "sha256": before})
    return entries


def verify(folder):
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    checked = 0
    for name, expected in manifest["files"].items():
        path = safe_file(folder / name, folder)
        if sha(path) != expected["sha256"] or path.stat().st_size != expected["bytes"]:
            raise ValueError("frozen-file-integrity-failed: " + name)
    for archive, inventory in manifest["archives"].items():
        entries = json.loads((folder / inventory).read_text(encoding="utf-8"))
        with zipfile.ZipFile(folder / archive) as source:
            if len(source.namelist()) != len(entries):
                raise ValueError("archive-inventory-length-mismatch")
            for expected in entries:
                result = hashlib.sha256()
                with source.open(expected["path"]) as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        result.update(chunk)
                if result.hexdigest() != expected["sha256"] or source.getinfo(expected["path"]).file_size != expected["bytes"]:
                    raise ValueError("archive-entry-integrity-failed")
                checked += 1
    return {"verified": True, "commit": manifest["commit"], "archive_members_verified": checked, "files_verified": len(manifest["files"])}


def experiment_files():
    files, provenance = {}, []
    for run in RUNS:
        directory = ROOT / "experiments" / run
        index = json.loads((directory / "artifacts.json").read_text(encoding="utf-8"))
        for relative, expected in index.items():
            source = safe_file(directory / relative, directory)
            if sha(source) != expected["sha256"] or source.stat().st_size != expected["bytes"]:
                raise ValueError("original-artifact-integrity-failed")
            files["experiments/" + run + "/" + relative] = (source, directory)
        for name in ("manifest.json", "artifacts.json"):
            files["experiments/" + run + "/" + name] = (directory / name, directory)
        data = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        provenance.append({"run": run, "original_git_revision": data.get("git_revision"), "original_git_dirty": data.get("git_dirty"),
                           "source_tree_sha256": data.get("source_tree_sha256"), "success": data.get("success", data.get("validation", {}).get("passed")),
                           "recorder_failure": data.get("recorder_failure")})
    initial = ROOT / "experiments/retained-initial"
    data = json.loads((initial / "provenance.json").read_text(encoding="utf-8"))
    for row in data["artifacts"]:
        source = safe_file(initial / row["retained"], initial)
        if sha(source) != row["sha256"] or source.stat().st_size != row["bytes"]:
            raise ValueError("retrospective-artifact-integrity-failed")
        files["experiments/retained-initial/" + row["retained"]] = (source, initial)
    for name in ("provenance.json", "baseline-v1.0.0.json", "results-v1.0.0.json"):
        files["experiments/retained-initial/" + name] = (initial / name, initial)
    for name in ("DSF-MNN-v1.0.0-research-source.zip", "manifest.json"):
        files["Release/v1.0.0/" + name] = (ROOT / "Release/v1.0.0" / name, ROOT / "Release/v1.0.0")
    return files, provenance


def python_files(extra_packages=()):
    prefix = Path(sys.base_prefix).resolve()
    files, packages = {}, {}
    for pattern in ("python*.exe", "python*.dll", "vcruntime*.dll", "LICENSE*"):
        for source in prefix.glob(pattern):
            if source.is_file():
                files["python/" + source.name] = (source, prefix)
    for directory in (prefix / "Lib", prefix / "DLLs"):
        for parent, dirs, names in os.walk(directory, followlinks=False):
            dirs[:] = [d for d in dirs if d.lower() not in {"site-packages", "test", "tests", "fixtures", "__pycache__", "ensurepip"}
                       and not (Path(parent) / d).is_symlink() and not (getattr((Path(parent) / d).lstat(), "st_file_attributes", 0) & 0x400)]
            for name in names:
                path = Path(parent) / name
                if path.suffix.lower() in {".py", ".pyd", ".dll"} and name not in {"sitecustomize.py", "usercustomize.py"}:
                    files["python/" + path.relative_to(prefix).as_posix()] = (path, prefix)
    plugins = [{"entry_point": ep.name, "module": ep.value, "distribution": ep.dist.metadata["Name"], "version": ep.dist.version}
               for ep in metadata.entry_points(group="pytest11")]
    todo = ["pytest", "tzdata", "packaging", *extra_packages] + [p["distribution"] for p in plugins]
    while todo:
        distribution = metadata.distribution(todo.pop())
        name = canonicalize_name(distribution.metadata["Name"])
        if name in packages:
            continue
        packages[name] = {"name": distribution.metadata["Name"], "version": distribution.version}
        for requirement in distribution.requires or []:
            parsed = Requirement(requirement)
            if parsed.marker is None or parsed.marker.evaluate({"extra": ""}):
                todo.append(parsed.name)
        for member in distribution.files or []:
            source = Path(distribution.locate_file(member)).resolve()
            if not source.is_relative_to(prefix / "Lib/site-packages") or not source.is_file():
                continue
            if source.suffix.lower() in BLOCKED_SUFFIXES or source.name.lower() in BLOCKED_NAMES:
                continue
            if {"test", "tests", "fixtures", "__pycache__"} & set(source.parts) or source.suffix == ".pyc":
                continue
            files["python/" + source.relative_to(prefix).as_posix()] = (source, prefix)
    return files, sorted(packages.values(), key=lambda p: p["name"].lower()), plugins


def node_files(modules, root_names=("dsh-compaction-basic", "cordis")):
    modules = modules.resolve()
    files, seen, todo = {}, {}, [modules / "@deepseek-ai" / name for name in root_names]
    def resolve(parent, name):
        for directory in (parent, *parent.parents):
            candidate = directory / "node_modules" / name
            if candidate.resolve().is_relative_to(modules) and (candidate / "package.json").is_file():
                return candidate.resolve()
        return None
    while todo:
        package = todo.pop()
        relative = package.relative_to(modules).as_posix()
        if relative in seen:
            continue
        description = json.loads((package / "package.json").read_text(encoding="utf-8"))
        seen[relative] = {"name": description["name"], "version": description["version"], "relative_path": relative,
                          "dependencies": description.get("dependencies", {}), "peerDependencies": description.get("peerDependencies", {})}
        for name in set(description.get("dependencies", {})) | set(description.get("peerDependencies", {})):
            dependency = resolve(package, name)
            if dependency:
                todo.append(dependency)
            elif name not in description.get("optionalDependencies", {}) and not description.get("peerDependenciesMeta", {}).get(name, {}).get("optional"):
                raise ValueError("required-npm-dependency-unavailable")
        for parent, dirs, names in os.walk(package, followlinks=False):
            dirs[:] = [d for d in dirs if d.lower() not in {"node_modules", "test", "tests", "fixtures", ".git"}
                       and not d.startswith(".") and not (Path(parent) / d).is_symlink()
                       and not (getattr((Path(parent) / d).lstat(), "st_file_attributes", 0) & 0x400)]
            for name in names:
                source = Path(parent) / name
                if source.suffix.lower() in {".js", ".mjs", ".cjs", ".json", ".node", ".wasm", ".ts", ".map", ".md", ".txt", ".yaml", ".yml"} or name.upper().startswith(("LICENSE", "NOTICE")):
                    if source.name.lower() not in BLOCKED_NAMES and not source.is_symlink():
                        files["node/node_modules/" + source.relative_to(modules).as_posix()] = (source, modules)
    node = Path(shutil.which("node")).resolve()
    files["node/bin/" + node.name.lower()] = (node, node.parent)
    return files, sorted(seen.values(), key=lambda p: p["relative_path"])


def create(modules):
    if git("rev-parse", TAG + "^{commit}").strip() != COMMIT:
        raise ValueError("baseline-tag-does-not-match")
    root = ROOT / "baselines"
    target = root / "research-29d7de6"
    if target.exists():
        raise ValueError("baseline-already-exists-no-overwrite")
    staging = root / (".freeze-" + uuid4().hex)
    staging.mkdir(parents=True)
    artifacts = staging / "artifacts"
    artifacts.mkdir()
    git("archive", "--format=zip", "--output=" + str(artifacts / "source-29d7de6.zip"), COMMIT)
    git("bundle", "create", str(artifacts / "repository.bundle"), TAG)
    archive_inventory = []
    with zipfile.ZipFile(artifacts / "source-29d7de6.zip") as source:
        for info in source.infolist():
            if not info.is_dir():
                archive_inventory.append({"path": info.filename, "bytes": info.file_size, "sha256": hashlib.sha256(source.read(info)).hexdigest()})
    json_write(staging / "source-files.json", archive_inventory)
    experiments, provenance = experiment_files()
    experiment_index = archive_files(artifacts / "experiments.zip", experiments)
    json_write(staging / "experiment-files.json", experiment_index)
    json_write(staging / "provenance.json", {"historical_runs": provenance, "policy": "Original run revisions, dirty states, failures and missing historical records are preserved; not relabeled as exact-commit results."})
    py, packages, plugins = python_files()
    node, npm = node_files(modules)
    environment_index = archive_files(artifacts / "environment-windows.zip", {**py, **node})
    json_write(staging / "environment-files.json", environment_index)
    historical = json.loads((ROOT / "experiments" / RUNS[3] / "manifest.json").read_text(encoding="utf-8"))
    environment = {"python": sys.version, "sqlite": sqlite3.sqlite_version, "node": subprocess.run([shutil.which("node"), "--version"], capture_output=True, text=True, check=True).stdout.strip(),
                   "platform": platform.platform(), "python_packages": packages, "pytest_plugins": plugins, "npm_packages": npm,
                   "historically_recorded": {k: historical[k] for k in ("python", "sqlite", "node", "platform", "pytest", "dsh_packages")},
                   "capture_scope": "Windows runtime files and installed pytest/plugin/tzdata dependency closure; OS image, environment secrets, user configuration and keys excluded.",
                   "historical_limit": "Full historical environment variables and transitive package hashes were not recorded then; this is a present-day preservation snapshot with matching recorded runtime versions."}
    json_write(staging / "environment-lock.json", environment)
    with (staging / "requirements-frozen.txt").open("x", encoding="utf-8", newline="\n") as output:
        output.write("# Reference pins; offline runtime copies are in environment-windows.zip.\n")
        output.writelines(p["name"] + "==" + p["version"] + "\n" for p in packages)
    manifest = {"schema": "dsf-mnn-research-freeze/1", "commit": COMMIT, "tag": TAG, "runtime_version": "1.0.0",
                "frozen_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(), "original_data_bytes": sum(p["bytes"] for p in experiment_index),
                "archives": {"artifacts/experiments.zip": "experiment-files.json", "artifacts/environment-windows.zip": "environment-files.json"},
                "source_archive": "artifacts/source-29d7de6.zip", "source_inventory": "source-files.json", "files": {},
                "policy": "Never overwrite, clean, move this tag or relabel historical runs. Reproduce in a fresh directory and record a new experiment."}
    for file in sorted(staging.rglob("*")):
        if file.is_file():
            manifest["files"][file.relative_to(staging).as_posix()] = {"bytes": file.stat().st_size, "sha256": sha(file)}
    json_write(staging / "manifest.json", manifest)
    result = verify(staging)
    json_write(staging / "integrity-report.json", result)
    with (staging / "SHA256SUMS").open("x", encoding="utf-8", newline="\n") as output:
        for file in sorted(staging.rglob("*")):
            if file.is_file() and file.name != "SHA256SUMS":
                output.write(sha(file) + "  " + file.relative_to(staging).as_posix() + "\n")
    staging.resolve().relative_to(root.resolve())
    target.resolve().relative_to(root.resolve())
    staging.rename(target)
    print(json.dumps({"baseline": str(target), **result, "original_data_bytes": manifest["original_data_bytes"], "python_distributions": len(packages), "npm_packages": len(npm)}, ensure_ascii=False))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", type=Path)
    parser.add_argument("--dsh-node-modules", type=Path)
    args = parser.parse_args()
    if args.verify:
        print(json.dumps(verify(args.verify), ensure_ascii=False))
    elif args.dsh_node_modules:
        create(args.dsh_node_modules)
    else:
        parser.error("--verify or --dsh-node-modules is required")


if __name__ == "__main__":
    main()
