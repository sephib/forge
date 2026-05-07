"""CLI handler implementations for the ``forge skills`` subcommands.

Provides the async handler functions that are wired into ``forge.cli`` for the
``forge skills install``, ``forge skills list``, and ``forge skills update``
subcommands.
"""

import argparse
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

from forge.skills.fetcher import CloneError, clone_skill_package
from forge.skills.installer import install_path_mode
from forge.skills.lock import update_lock_file
from forge.skills.models import LockEntry


def _is_git_url(source: str) -> bool:
    """Return True when *source* looks like a Git URL.

    Detects:
    - URLs with a scheme (e.g. ``https://``, ``ssh://``, ``git://``)
    - SCP-style Git URLs (e.g. ``git@github.com:org/repo.git``)

    Args:
        source: The source string to test.

    Returns:
        ``True`` if *source* appears to be a Git URL, ``False`` otherwise.
    """
    return "://" in source or source.startswith("git@")


async def cmd_skills_install(args: argparse.Namespace) -> int:
    """Install a skill package from a Git URL.

    Validates arguments, detects the source type, clones the repository,
    copies skills to the target directory, updates the lock file, and cleans
    up the temporary clone.

    Args:
        args: Parsed CLI arguments with attributes:
            - ``source``: Git URL or local path of the skill package.
            - ``project``: Optional project key (mutually exclusive with
              ``--default``).
            - ``default``: Boolean flag; install to ``skills/default/``.
            - ``ref``: Optional git ref (branch, tag, or commit SHA).

    Returns:
        Exit code – ``0`` on success, ``1`` on clone/install failure,
        ``2`` on invalid argument combinations.
    """
    # ------------------------------------------------------------------
    # 1. Validate argument combinations.
    # ------------------------------------------------------------------
    if not args.project and not args.default:
        print(
            "Error: exactly one of --project or --default must be provided",
            file=sys.stderr,
        )
        return 2

    if args.project and args.default:
        print(
            "Error: --project and --default are mutually exclusive; provide exactly one",
            file=sys.stderr,
        )
        return 2

    source: str = args.source
    ref: str | None = getattr(args, "ref", None)
    project: str | None = args.project
    use_default: bool = args.default

    # ------------------------------------------------------------------
    # 2. Determine the target directory name.
    # ------------------------------------------------------------------
    # project is guaranteed non-None here when use_default is False.
    target_name = "default" if use_default else project  # type: ignore[assignment]

    # ------------------------------------------------------------------
    # 3. Detect source type and route accordingly.
    # ------------------------------------------------------------------
    if _is_git_url(source):
        return await _install_git_url(source, ref, target_name)
    else:
        return _install_local_path(source, target_name)


async def _install_git_url(
    source: str,
    ref: str | None,
    target_name: str,
) -> int:
    """Clone *source* and install skills into ``skills/<target_name>/``.

    Args:
        source: Git URL to clone.
        ref: Optional git ref (branch, tag, or SHA); ``None`` clones the
            default branch.
        target_name: Subdirectory name inside ``skills/`` where skills will
            be installed (e.g. ``"myproj"`` or ``"default"``).

    Returns:
        ``0`` on success, ``1`` on failure.
    """
    # ------------------------------------------------------------------
    # 4. Clone into a temporary directory.
    # ------------------------------------------------------------------
    print(f"Cloning {source!r} …", flush=True)

    try:
        clone_dir = await clone_skill_package(source, ref)
    except CloneError as exc:
        print(f"Error: clone failed – {exc}", file=sys.stderr)
        return 1

    # ------------------------------------------------------------------
    # 5. Determine the skills source directory inside the clone.
    #    Convention: if a ``skills/`` subdirectory exists, use it;
    #    otherwise treat the repo root as the skills container.
    # ------------------------------------------------------------------
    skills_subdir = clone_dir / "skills"
    source_dir = skills_subdir if skills_subdir.is_dir() else clone_dir

    # ------------------------------------------------------------------
    # 6. Resolve the installed-at commit SHA.
    # ------------------------------------------------------------------
    resolved_commit = await _resolve_head_sha(clone_dir)

    # ------------------------------------------------------------------
    # 7. Determine the target installation directory.
    #    Use the current working directory as the skills root.
    # ------------------------------------------------------------------
    skills_root = Path.cwd() / "skills"
    target_dir = skills_root / target_name

    # ------------------------------------------------------------------
    # 8. Copy skills from the clone into the target directory.
    # ------------------------------------------------------------------
    try:
        installed_skills = install_path_mode(source_dir, target_dir)
    except (FileNotFoundError, NotADirectoryError) as exc:
        print(f"Error: could not install skills – {exc}", file=sys.stderr)
        shutil.rmtree(clone_dir, ignore_errors=True)
        return 1
    finally:
        # ------------------------------------------------------------------
        # 9. Clean up the temporary clone directory.
        # ------------------------------------------------------------------
        shutil.rmtree(clone_dir, ignore_errors=True)

    # ------------------------------------------------------------------
    # 10. Update the lock file.
    # ------------------------------------------------------------------
    lock_path = skills_root / "skills.lock"
    lock_entry = LockEntry(
        source=source,
        ref=ref or "",
        resolved_commit=resolved_commit,
        mode="path",
        path=None,
        skill_mapping=None,
        target=target_name,
        skills=installed_skills,
        fetched_at=datetime.now(tz=UTC),
    )
    update_lock_file(lock_path, lock_entry)

    # ------------------------------------------------------------------
    # 11. Report success.
    # ------------------------------------------------------------------
    skill_word = "skill" if len(installed_skills) == 1 else "skills"
    print(
        f"Successfully installed {len(installed_skills)} {skill_word} "
        f"from {source!r} into skills/{target_name}/",
        flush=True,
    )
    if installed_skills:
        for name in installed_skills:
            print(f"  - {name}", flush=True)

    return 0


def _install_local_path(source: str, target_name: str) -> int:
    """Copy a local directory into ``skills/<target_name>/``.

    The entire *source* directory is copied to the target using
    :func:`shutil.copytree`, replacing any existing content.

    Args:
        source: Local path (absolute or relative) to the skills directory.
        target_name: Subdirectory name inside ``skills/`` where skills will
            be installed (e.g. ``"myproj"`` or ``"default"``).

    Returns:
        ``0`` on success, ``1`` on validation failure.
    """
    source_path = Path(source).resolve()

    # ------------------------------------------------------------------
    # Validate that the source path exists and is a directory.
    # ------------------------------------------------------------------
    if not source_path.exists():
        print(
            f"Error: local path {source!r} does not exist",
            file=sys.stderr,
        )
        return 1

    if not source_path.is_dir():
        print(
            f"Error: local path {source!r} is not a directory",
            file=sys.stderr,
        )
        return 1

    # ------------------------------------------------------------------
    # Determine the target installation directory.
    # ------------------------------------------------------------------
    skills_root = Path.cwd() / "skills"
    target_dir = skills_root / target_name

    # ------------------------------------------------------------------
    # Copy the source directory to the target, overwriting existing content.
    # ------------------------------------------------------------------
    if target_dir.exists():
        shutil.rmtree(target_dir)

    shutil.copytree(source_path, target_dir, symlinks=True)

    # Count installed skills (immediate subdirectories).
    installed_skills = [entry.name for entry in sorted(target_dir.iterdir()) if entry.is_dir()]

    # ------------------------------------------------------------------
    # Update the lock file.
    # ------------------------------------------------------------------
    lock_path = skills_root / "skills.lock"
    lock_entry = LockEntry(
        source=str(source_path),
        ref="",
        resolved_commit="",
        mode="path",
        path=None,
        skill_mapping=None,
        target=target_name,
        skills=installed_skills,
        fetched_at=datetime.now(tz=UTC),
    )
    update_lock_file(lock_path, lock_entry)

    # ------------------------------------------------------------------
    # Report success.
    # ------------------------------------------------------------------
    skill_word = "skill" if len(installed_skills) == 1 else "skills"
    print(
        f"Successfully installed {len(installed_skills)} {skill_word} "
        f"from {source!r} into skills/{target_name}/",
        flush=True,
    )
    if installed_skills:
        for name in installed_skills:
            print(f"  - {name}", flush=True)

    return 0


async def _resolve_head_sha(clone_dir: Path) -> str:
    """Return the current HEAD commit SHA of the repository at *clone_dir*.

    Falls back to the empty string when the SHA cannot be resolved (e.g.
    when git is not available or the directory is not a git repository).

    Args:
        clone_dir: Path to the root of the cloned repository.

    Returns:
        40-character commit SHA, or ``""`` on failure.
    """
    import asyncio

    try:
        process = await asyncio.create_subprocess_exec(
            "git",
            "-C",
            str(clone_dir),
            "rev-parse",
            "HEAD",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, _ = await asyncio.wait_for(process.communicate(), timeout=10)
        if process.returncode == 0:
            return stdout_bytes.decode(errors="replace").strip()
    except Exception:  # noqa: BLE001
        pass

    return ""


async def cmd_skills_list(_args: argparse.Namespace) -> int:
    """List installed skills (stub – not yet implemented).

    Args:
        _args: Parsed CLI arguments (unused).

    Returns:
        Always ``0``.
    """
    return 0


async def cmd_skills_update(_args: argparse.Namespace) -> int:
    """Update installed skills (stub – not yet implemented).

    Args:
        _args: Parsed CLI arguments (unused).

    Returns:
        Always ``0``.
    """
    return 0
