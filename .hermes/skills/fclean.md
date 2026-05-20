---
name: fclean
description: File organization CLI tool — organize, stats, rename, dupes, batch rename, undo
version: 0.4.0
---

# fclean Agent Skill

fclean is a safe, colorful CLI tool for organizing messy folders by file type. All commands support `--json` output for AI Agent consumption.

## Commands

### organize — Sort files by type into categorized subdirectories

```bash
# Dry-run preview (default, safe)
fclean /path/to/dir
fclean organize /path/to/dir

# Execute organization
fclean organize /path/to/dir --execute

# With exclusions
fclean /path/to/dir --exclude '*.tmp' --exclude-dir node_modules

# JSON output for AI Agent
fclean --json /path/to/dir
```

### stats — View directory file statistics

```bash
fclean stats /path/to/dir
fclean stats --json /path/to/dir
```

### rename — Batch rename files with template patterns

Template variables: `{n}` (sequence number), `{n:03d}` (zero-padded), `{date}` (modification date), `{ext}` (extension).

```bash
# Preview rename
fclean rename "*.jpg" --pattern "vacation_{n:03d}"

# Execute rename
fclean rename "*.jpg" --pattern "vacation_{n:03d}" --execute

# JSON output
fclean rename "*.jpg" --pattern "vacation_{n:03d}" --json
```

### dupes — Find and safely remove duplicate files (SHA-256)

```bash
# Scan for duplicates (dry-run)
fclean dupes /path/to/dir

# Skip small files
fclean dupes /path/to/dir --min-size 1MB

# Delete duplicates (keep newest by default)
fclean dupes /path/to/dir --delete

# Custom keep strategy
fclean dupes /path/to/dir --delete --strategy oldest

# JSON output
fclean dupes --json /path/to/dir
```

### config — View current configuration

```bash
fclean config
```

### init — Generate .fcleanrc configuration file

```bash
fclean init
fclean init --global  # ~/.fcleanrc
```

### Undo / History

```bash
fclean --undo        # Rollback last operation
fclean --history     # View undo log
fclean --json --undo # JSON rollback result
```

## JSON Output

Every command supports `--json` / `-j` flag for structured output.

```json
{
  "tool": "fclean",
  "command": "organize",
  "timestamp": "2026-05-20T14:30:00Z",
  "path": "/home/user/Downloads",
  "status": "dry_run",
  "files_scanned": 42,
  "files_moved": 38,
  "categories_found": {
    "images": {"count": 10, "size_bytes": 5242880}
  },
  "changes": [
    {"from": "photo.jpg", "to": "images/photo.jpg", "category": "images", "size": 1048576}
  ],
  "summary": "42 files scanned, 38 files organized into 3 categories"
}
```

## Tips for AI Agents

1. **Always use `--json`** for machine-parseable output instead of parsing color tables.
2. **Start with dry-run** (`fclean dupes /path --json`) before destructive operations.
3. **Use `--execute`** to actually perform organization after reviewing the plan.
4. **Combine with `jq`** to filter results: `fclean --json ~/Downloads | jq '.summary'`
5. **Check undo history** before operating: `fclean --json --history`
