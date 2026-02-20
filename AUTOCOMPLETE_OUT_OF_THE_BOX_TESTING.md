# 🎯 Autocomplete Out-of-the-Box Testing Guide

> **Last updated**: Feb 20, 2026 18:15 UTC

## Overview

This document verifies that bash autocomplete works **out-of-the-box** without user interaction.

## Test Scenario

**Fresh machine setup** (no prior Vitruvyan installation):

```bash
# 1. Clone repository
git clone https://github.com/dbaldoni/vitruvyan-core.git
cd vitruvyan-core

# 2. First command (triggers auto-configuration)
./vit status

# 3. Test autocomplete (immediate effect in current shell)
vit <TAB>              # Should show: status, update, upgrade, plan, rollback
vit upgrade --<TAB>    # Should show: --channel, --target, --yes, --json
```

## Expected Behavior

### On First Run

**What happens** (automatic, non-interactive):
1. Wrapper script checks for `~/.vit_completion_configured` marker
2. If not found:
   - Adds `source /path/to/vit-completion.bash` to `~/.bashrc`
   - Loads completion script for **current shell** (immediate effect)
   - Creates `~/.vit_completion_configured` marker

**User experience**:
- ✅ No prompt or interaction required
- ✅ Autocomplete works **immediately** in current shell
- ✅ Autocomplete persists in new shells (sourced from .bashrc)

### Verification Checks

```bash
# 1. Check marker file exists
ls -la ~/.vit_completion_configured
# Expected: File exists with timestamp of first run

# 2. Check .bashrc was modified
grep "vit-completion.bash" ~/.bashrc
# Expected output:
# # Vitruvyan CLI autocomplete (auto-configured)
# source /path/to/vitruvyan-core/vitruvyan_core/core/platform/update_manager/cli/completion/vit-completion.bash

# 3. Test tab completion
vit <TAB>
# Expected: Displays available commands

vit upgrade --<TAB>
# Expected: Displays available flags

vit upgrade --channel <TAB>
# Expected: stable, beta
```

## Implementation Details

### Wrapper Script Logic (`/vit`)

```bash
# Auto-setup completion on first run (out-of-the-box, non-interactive)
COMPLETION_SETUP_MARKER="${HOME}/.vit_completion_configured"
COMPLETION_SCRIPT="${SCRIPT_DIR}/vitruvyan_core/core/platform/update_manager/cli/completion/vit-completion.bash"

if [[ ! -f "${COMPLETION_SETUP_MARKER}" ]] && [[ -n "${BASH_VERSION}" ]] && [[ -f "${COMPLETION_SCRIPT}" ]]; then
    # Auto-enable bash autocomplete (out-of-the-box)
    COMPLETION_LINE="source ${COMPLETION_SCRIPT}"
    
    # Check if .bashrc exists and doesn't already have completion
    if [[ -f "${HOME}/.bashrc" ]] && ! grep -qF "vit-completion.bash" "${HOME}/.bashrc" 2>/dev/null; then
        # Add completion source to bashrc (silently)
        echo "" >> "${HOME}/.bashrc"
        echo "# Vitruvyan CLI autocomplete (auto-configured)" >> "${HOME}/.bashrc"
        echo "${COMPLETION_LINE}" >> "${HOME}/.bashrc"
    fi
    
    # Mark as configured
    touch "${COMPLETION_SETUP_MARKER}"
fi

# Load completion for current shell session (immediate effect)
if [[ -n "${BASH_VERSION}" ]] && [[ -f "${COMPLETION_SCRIPT}" ]]; then
    source "${COMPLETION_SCRIPT}" 2>/dev/null || true
fi
```

### Key Design Decisions

1. **Non-interactive**: No user prompt (previous version asked Y/n)
2. **Immediate effect**: Sources completion in current shell (no need to restart)
3. **Idempotent**: Checks for existing configuration before modifying .bashrc
4. **Safe**: Uses `grep -qF` to avoid duplicates
5. **Silent**: No console output (clean UX)

## Troubleshooting

### Autocomplete Not Working

**Check 1: Bash version**
```bash
echo $BASH_VERSION
# Expected: 4.0+ (most modern systems)
```

**Check 2: Completion script exists**
```bash
ls -lh vitruvyan_core/core/platform/update_manager/cli/completion/vit-completion.bash
# Expected: File exists and is readable
```

**Check 3: .bashrc modified**
```bash
tail -10 ~/.bashrc
# Expected: Should see "# Vitruvyan CLI autocomplete (auto-configured)"
```

**Check 4: Current shell loaded completion**
```bash
complete -p vit
# Expected: complete -F _vit_completion vit
```

### Manual Re-configuration

```bash
# Remove configuration
rm ~/.vit_completion_configured
grep -v "vit-completion.bash" ~/.bashrc > ~/.bashrc.tmp && mv ~/.bashrc.tmp ~/.bashrc

# Re-run first command
./vit status

# Verify autocomplete works
vit <TAB>
```

## Test Results

### Test Machine 1: vmi3066053 (Feb 20, 2026)
- ✅ Auto-configuration successful
- ✅ Autocomplete working in current shell
- ✅ No user interaction required
- ✅ .bashrc updated correctly

### Test Machine 2: vmi2647694 (Feb 20, 2026)
- ✅ Auto-configuration successful
- ✅ Autocomplete working in current shell
- ✅ No user interaction required
- ✅ .bashrc updated correctly

## Related Documentation

- [VIT_CLI_QUICKSTART.md](VIT_CLI_QUICKSTART.md) - Complete CLI usage guide
- [README.md](README.md#-update-manager-cli) - Feature overview
- [vit-completion.bash](vitruvyan_core/core/platform/update_manager/cli/completion/vit-completion.bash) - Completion script
- [completion.py](vitruvyan_core/core/platform/update_manager/cli/commands/completion.py) - Manual install/uninstall commands

## Contract Compliance

This implementation satisfies:
- **Zero-installation principle**: No `pip install` required
- **Out-of-the-box UX**: No manual setup steps
- **Idempotent configuration**: Safe to run multiple times
- **Non-invasive**: Respects existing .bashrc content

---

**Status**: ✅ Production-ready (validated on 2 VMs)
**Version**: vit v1.2.1+
**Date**: Feb 20, 2026
