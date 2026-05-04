# Proposal: Shared Workspace Directory for Workers

**Author:** eshulman2
**Date:** 2026-05-04
**Status:** Draft

## Summary

Replace per-worker ephemeral workspaces with a shared workspace directory so that all workers processing the same ticket operate on the same on-disk state, eliminating the need for pull-before-push workarounds and making `.forge/` state visible across workers.

## Motivation

### Problem Statement

Each worker creates its own local clone of the repository for a given ticket. When a second worker picks up the same ticket (e.g. after a retry, or when `implement_review` runs after `attempt_ci_fix`), it either reuses the stale local workspace or recreates it from scratch. Two failure modes arise:

1. **Stale workspace → non-fast-forward push.** If the branch was pushed forward externally (by another worker or a manual push) since the workspace was last used, the worker's push is rejected. The current fix (`pull_rebase` in `prepare_workspace`) handles this for sequential workers but is a workaround, not a solution.

2. **`.forge/` state is not shared.** Each worker writes task files, CI failure reports, and review plans to its own `.forge/` directory. A second worker starting on the same ticket cannot see what the first one wrote. This makes multi-worker pipelines fragile and forces redundant re-fetching of information.

### Current Workaround

`prepare_workspace()` in `workspace_setup.py` calls `pull_rebase()` before any implementation work. This solves the push-rejection problem for sequential workers but does nothing for concurrent workers or for `.forge/` visibility.

## Proposal

### Overview

Maintain a single canonical workspace directory per ticket on a shared filesystem accessible to all workers. Workers look up the workspace path by ticket key, use it directly if it exists, or create it on first use. No worker ever has an exclusive local copy.

### Detailed Design

#### Workspace Location

A configurable base path (e.g. `FORGE_WORKSPACE_BASE=/var/forge/workspaces`) holds one directory per ticket:

```
/var/forge/workspaces/
  AISOS-525/
    openstack-resource-controller/   ← git repo
    .forge/                          ← task state, shared across all workers
```

On a single-host deployment this is just a directory on local disk. On a multi-host deployment it must be a shared volume (NFS, Ceph, or a cloud file store).

#### Worker Coordination and Locking

Shared state introduces concurrent-write risk. Two workers must not commit and push simultaneously. A file-based or Redis-based lock per ticket controls access to the git operations (commit, push, rebase):

```
/var/forge/workspaces/AISOS-525/.forge/workspace.lock
```

Workers acquire the lock before any mutating git operation and release it after push. Read-only operations (container analysis, log fetching) do not require the lock.

#### WorkspaceManager Changes

`WorkspaceManager.create_workspace()` becomes `WorkspaceManager.get_or_create_workspace()`:
- If the workspace directory exists: return it as-is (caller calls `pull_rebase` to align)
- If not: clone, add fork remote, checkout branch, create `.forge/`

`teardown_workspace()` is removed from the normal workflow. Workspaces are cleaned up by a separate scheduled job (e.g. 7 days after last modification).

#### `.forge/` as Shared State

Because `.forge/` is on a shared filesystem, all workers see each other's output:
- `ci-failures.md` written by the CI evaluator is immediately readable by the fix container
- `review-plan.md` written by the analysis container is immediately readable by the implementation container
- No re-fetching, no redundant API calls

### Deployment Modes

| Mode | Shared FS | Locking | Notes |
|------|-----------|---------|-------|
| Single host | Local disk | File lock | Default; no infrastructure change |
| Multi-host | NFS / cloud volume | Redis lock | Required for horizontal scaling |

### Migration

1. Add `FORGE_WORKSPACE_BASE` config option (defaults to current ephemeral temp dir for backwards compatibility)
2. Implement `get_or_create_workspace()` alongside existing `create_workspace()`
3. Update `prepare_workspace()` to use the new method
4. Remove `teardown_workspace()` from workflow graphs; add a cleanup job
5. Switch default to shared base path once stable

## Relationship to Current Fix

The `pull_rebase` fix in `prepare_workspace()` (shipped in `fix/workspace-sync`) is the right pragmatic solution for now. It handles the common case — sequential workers on the same ticket — safely and with no infrastructure requirements. The shared workspace proposal becomes worth pursuing when:

- Concurrent workers operating on the same ticket simultaneously are needed
- `.forge/` state sharing between workers is actively blocking a feature
- A multi-host deployment is being considered

The `pull_rebase` call remains correct and necessary even with a shared workspace (to handle external pushes from outside Forge), so the current fix is not wasted work.

## Alternatives Considered

| Alternative | Pros | Cons | Why Not |
|-------------|------|------|---------|
| Keep per-worker workspaces + pull_rebase | No infrastructure change | `.forge/` not shared; concurrent workers still race | Current state; acceptable short-term |
| Object storage for `.forge/` only | Lightweight | Doesn't fix push-rejection; adds S3/GCS dependency | Solves half the problem |
| Git for `.forge/` state | Auditable, replicable | Extremely complex; merge conflicts on every task | Over-engineered |
| Single-worker-per-ticket guarantee | Eliminates all races | Limits throughput; hard to enforce across restarts | Architecture constraint, not a solution |

## Open Questions

- [ ] Should workspace cleanup be time-based (e.g. 7 days) or event-based (PR merged/closed)?
- [ ] Should the lock be per-ticket or per-workspace-path (same thing for now, but matters if one ticket spans multiple repos)?
- [ ] On multi-host: Redis lock with TTL, or a proper distributed lock (Redlock)?
- [ ] Should `.forge/` be excluded from the shared workspace and kept per-worker (simpler), or shared (more powerful)?

## References

- Current workaround: `src/forge/workflow/nodes/workspace_setup.py` (`prepare_workspace`)
- Git operations: `src/forge/workspace/git_ops.py` (`pull_rebase`)
- Workspace manager: `src/forge/workspace/manager.py`
