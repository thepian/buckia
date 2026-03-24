# Sync Features

## Default behaviour

By default, buckia synchronises bidirectionally: files present on remote but absent locally are downloaded, and local files absent from remote are uploaded. Checksums are compared to detect modifications.

```yaml
# .buckia
provider: bunny
bucket_name: my-zone
delete_orphaned: false   # remote-only files are left alone
```

---

## `upload_only` — one-way sync

Set `upload_only: true` to prevent buckia from ever downloading files from remote. All remote → local flow is disabled, regardless of what exists on the remote.

```yaml
provider: bunny
bucket_name: my-zone
upload_only: true
```

Useful when:
- A pipeline writes files locally and pushes them to a CDN; you never want remote state pulled back
- Multiple machines push to the same bucket and local state should not be overwritten

**Note:** `upload_only` does not affect `delete_orphaned`. Setting both `upload_only: true` and `delete_orphaned: true` will still remove remote files that have no local counterpart.

CLI override for a single run:
```bash
buckia sync ./dist --upload-only
```

---

## `create_only_patterns` — immutable file patterns

For files that are written once and never change (e.g. parquet partitions, content-addressed assets), you can declare them as immutable using glob patterns. Buckia will:

- **Upload** the file if it does not yet exist on remote (existence check only)
- **Skip** the file if it already exists on remote, even if checksums differ
- **Never download** files matching these patterns

This is strictly cheaper than the default: no checksum computation is needed for files already present on remote.

```yaml
provider: bunny
bucket_name: my-archive
upload_only: true
create_only_patterns:
  - "archive/**/*.parquet"
  - "snapshots/*.csv.gz"
  - "assets/**"
```

Pattern syntax follows standard glob rules (`*` matches within a path segment, `**` matches across segments).

---

## Local state cache — skip checksum recomputation

For large archives, computing SHA-256 for every local file on every run is expensive even when nothing has changed. The state cache records the checksum, size, and modification time of each synced file. On subsequent runs, files whose `mtime` and `size` match the cache reuse the stored checksum — no disk read required.

The cache is stored as `.buckia_state.json` in the local sync directory by default.

```yaml
provider: bunny
bucket_name: my-archive
# state_file: /custom/path/.buckia_state.json  # optional override
```

### How the cache is invalidated

The cache is ignored when:
- The state file is missing or corrupt — falls back to full checksum scan
- The `bucket` recorded in state doesn't match the current config's `bucket_name`
- `--force-full-sync` is passed on the CLI

### "Fell behind" detection

If remote has files not present in either the local tree or the state cache, buckia logs a warning:

```
Remote has 42 file(s) not in local state — consider running with force_full_sync=True to verify
```

This can happen when another machine pushed files to the same bucket. Run with `--force-full-sync` to do a full comparison and bring state up to date.

```bash
buckia sync ./archive --force-full-sync
```

---

## Performance guidance

| Scenario | Recommended config |
|---|---|
| Small directory, bidirectional | Default (no special config) |
| Upload-only pipeline | `upload_only: true` |
| Large immutable archive (parquets, assets) | `create_only_patterns` + state cache |
| Archive + state cache wiped | `--force-full-sync` once, then normal runs |
| Multiple machines writing to same bucket | `upload_only: true`, no state cache |

The state cache provides the largest benefit when most files are unchanged between runs and the local tree is large. It has no effect on the first run (no prior state) or when `--force-full-sync` is used.
