from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from detoxbench.core.yaml_loader import load_yaml


@dataclass(frozen=True)
class CohortManifest:
    path: Path
    name: str
    version: str
    members: list[dict[str, Any]]
    targets: list[dict[str, Any]]
    raw: dict[str, Any]


def load_cohort_manifest(path: Path) -> CohortManifest:
    manifest_path = path.resolve()
    raw = load_yaml(manifest_path)
    if not isinstance(raw, dict):
        raise ValueError(f"{manifest_path} must contain a mapping")
    name = raw.get("name")
    if not isinstance(name, str) or not name:
        raise ValueError(f"{manifest_path} requires non-empty name")
    version = str(raw.get("version", "1"))
    members = raw.get("members")
    targets = raw.get("targets")
    if not isinstance(members, list) or not members:
        raise ValueError(f"{manifest_path} requires non-empty members")
    if not isinstance(targets, list) or not targets:
        raise ValueError(f"{manifest_path} requires non-empty targets")
    _validate_members(members, manifest_path)
    _validate_targets(targets, manifest_path)
    return CohortManifest(
        path=manifest_path,
        name=name,
        version=version,
        members=members,
        targets=targets,
        raw=raw,
    )


def cohort_fingerprint(manifest: CohortManifest) -> dict[str, Any]:
    hasher = sha256()
    hasher.update(manifest.path.read_bytes())
    manifest_dir = manifest.path.parent
    target_fingerprints = []
    for target in manifest.targets:
        target_dir = _resolve_path(manifest_dir, target["target_dir"])
        contract_path = _resolve_path(target_dir, target.get("contract", "contract.dsl.yaml"))
        contract_sha = sha256(contract_path.read_bytes()).hexdigest() if contract_path.exists() else None
        if contract_sha:
            hasher.update(contract_sha.encode("utf-8"))
        target_fingerprints.append(
            {
                "target_dir": str(target_dir),
                "contract": str(contract_path),
                "contract_sha256": contract_sha,
            }
        )
    return {
        "name": manifest.name,
        "version": manifest.version,
        "manifest": str(manifest.path),
        "manifest_sha256": sha256(manifest.path.read_bytes()).hexdigest(),
        "cohort_sha256": hasher.hexdigest(),
        "member_count": len(manifest.members),
        "target_count": len(manifest.targets),
        "targets": target_fingerprints,
    }


def _validate_members(members: list[Any], manifest_path: Path) -> None:
    seen: set[str] = set()
    for member in members:
        if not isinstance(member, dict):
            raise ValueError(f"{manifest_path} members entries must be mappings")
        member_id = member.get("id")
        if not isinstance(member_id, str) or not member_id:
            raise ValueError(f"{manifest_path} member requires non-empty id")
        if member_id in seen:
            raise ValueError(f"{manifest_path} duplicate member id {member_id!r}")
        seen.add(member_id)
        model = member.get("model")
        if not isinstance(model, str) or not model:
            raise ValueError(f"{manifest_path} member {member_id!r} requires model")


def _validate_targets(targets: list[Any], manifest_path: Path) -> None:
    for target in targets:
        if not isinstance(target, dict):
            raise ValueError(f"{manifest_path} targets entries must be mappings")
        target_dir = target.get("target_dir")
        if not isinstance(target_dir, str) or not target_dir:
            raise ValueError(f"{manifest_path} target requires target_dir")


def _resolve_path(base: Path, value: str | Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = base / path
    return path.resolve()
