# Automatic Version Bumping

The repository is configured to automatically bump the version number on every commit.

## How It Works

A git **pre-commit hook** runs before each commit and:

1. Reads the current version from `pyobd_dashboard/src/version.py`
2. Increments the patch version (e.g., `2.0.0` → `2.0.1`)
3. Updates `version.py` with the new version
4. Auto-stages the version file change

## Example Flow

```bash
# You make changes and try to commit
git commit -m "Add new feature"

# Output shows:
# ✓ Version bumped to 2.0.1

# The commit now includes both your changes AND the version bump
```

## Version Format

```
VERSION = "MAJOR.MINOR.PATCH"
BUILD = "Descriptive text"
```

- **MAJOR**: Breaking changes (bump manually if needed)
- **MINOR**: New features (bump manually if needed)
- **PATCH**: Bug fixes and updates (auto-bumped on every commit)

## Manual Version Update

To manually set the version for major/minor releases:

1. Edit `pyobd_dashboard/src/version.py`
2. Update VERSION and BUILD strings
3. Commit with a message like "Release v2.1.0"

The hook will still bump the patch number after your manual update.

## Disabling the Hook (Not Recommended)

If you need to commit without bumping the version:

```bash
git commit --no-verify -m "your message"
```

## Troubleshooting

If the hook doesn't run:
- Verify it's executable: `chmod +x .git/hooks/pre-commit`
- Check the hook exists: `ls -l .git/hooks/pre-commit`
- Make sure `pyobd_dashboard/src/version.py` exists
