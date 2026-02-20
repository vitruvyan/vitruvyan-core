# 🚀 Vitruvyan CLI Quick Start

## Immediate Usage (No Installation Required)

The `vit` command works **out-of-the-box** without any installation:

```bash
cd /path/to/vitruvyan-core
./vit status
```

### ✨ Auto-Configured Features

The `vit` wrapper automatically configures on first run:

1. **PYTHONPATH** — no need for `pip install -e .`
2. **Bash autocomplete** — tab completion enabled automatically
3. **GitHub authentication** — auto-detects `gh auth token` for private repos

**Autocomplete activation** (happens automatically):
```bash
# First run: completion added to ~/.bashrc
./vit status

# Immediate effect in current shell (tab completion works)
vit <TAB>         # → status, update, upgrade, plan, rollback
vit upgrade --<TAB>   # → --channel, --target, --yes, --json
```

**To reload in existing shells**:
```bash
source ~/.bashrc
# or
exec bash
```

### Add to PATH (Optional, Recommended)

To use `vit` from anywhere:

```bash
# Add this line to your ~/.bashrc
export PATH="/path/to/vitruvyan-core:${PATH}"

# Reload shell
source ~/.bashrc
```

Now you can use `vit` from any directory:

```bash
vit status
vit plan
vit update
```

---

## 📋 Essential Commands

### Check Current Version & Updates
```bash
vit status
```

### Plan an Upgrade (Dry-Run)
```bash
vit plan
vit plan --target v1.2.0
```

### Apply Update
```bash
vit update          # Interactive
vit update --yes    # Non-interactive
```

### Apply Upgrade (with Tests)
```bash
vit upgrade         # Interactive with smoke tests
vit upgrade --yes   # Non-interactive
```

### Rollback to Previous Version
```bash
vit rollback
```

---

## ⚡ Autocomplete

**Tab completion is enabled automatically** on first run.

### How It Works
```bash
# First time you run vit
./vit status

# Behind the scenes (automatic, no interaction):
# 1. Adds completion source to ~/.bashrc
# 2. Loads completion for current shell (immediate effect)
# 3. Creates ~/.vit_completion_configured marker

# ✅ No user interaction required
# ✅ Works immediately in current shell
# ✅ Persists across shell restarts
```

### Verify Autocomplete
```bash
# Test tab completion (works immediately after first run)
vit <TAB>              # Shows: update, upgrade, plan, rollback, status, channel
vit upgrade --<TAB>    # Shows: --channel, --target, --yes, --json
vit upgrade --channel <TAB>  # Shows: stable, beta
```

### Troubleshooting

**Autocomplete not working?**
```bash
# 1. Check if .bashrc was modified
grep "vit-completion.bash" ~/.bashrc

# 2. Reload shell configuration
source ~/.bashrc

# 3. Test in new terminal
exec bash

# 4. Verify completion script exists
ls -lh vitruvyan_core/core/platform/update_manager/cli/completion/vit-completion.bash

# 5. Manual load for current shell
source vitruvyan_core/core/platform/update_manager/cli/completion/vit-completion.bash
```

### Manual Control (if needed)
```bash
# Check autocomplete status
ls -la ~/.vit_completion_configured

# Remove autocomplete configuration
vit completion uninstall
rm ~/.vit_completion_configured

# Re-enable autocomplete
rm ~/.vit_completion_configured
./vit status  # Auto-configures again
```

---

## 🎯 First-Time Setup on New Machine

```bash
# 1. Clone the repository
git clone https://github.com/dbaldoni/vitruvyan-core.git
cd vitruvyan-core

# 2. Use vit immediately (no installation needed!)
./vit status

# 3. Add to PATH (optional)
echo 'export PATH="'$(pwd)':${PATH}"' >> ~/.bashrc
source ~/.bashrc

# 4. Test from anywhere
cd ~
vit status
```

---

## 🔧 Update Workflow Example

```bash
# 1. Check current status
vit status
# Output: Current version: v1.1.0

# 2. See what's available
vit plan
# Output: Available: v1.2.0 (8 commits, Update Manager + Pipeline viz)

# 3. Dry-run (preview changes)
vit plan --target v1.2.0

# 4. Apply upgrade (with tests)
vit upgrade
# Pulls updates, runs smoke tests, commits changes

# 5. Verify
vit status
# Output: Current version: v1.2.0

# 6. Rollback if needed
vit rollback
# Output: Rolled back to v1.1.0
```

---

## 📦 No Dependencies Required

The `vit` CLI is designed to work with **only** the dependencies already present in your vitruvyan-core installation:

- ✅ Python 3.10+
- ✅ Git
- ✅ Core Python dependencies (already installed with vitruvyan-core)

**No pip install, no package managers, no extra setup needed!**

---

## 🆘 Troubleshooting

### "Command not found: vit"
```bash
# Use full path:
/path/to/vitruvyan-core/vit status

# Or add to PATH (see above)
```

### "ModuleNotFoundError"
```bash
# Ensure you're in the vitruvyan-core directory or have set PYTHONPATH:
export PYTHONPATH=/path/to/vitruvyan-core:${PYTHONPATH}
```

### Autocomplete not working
```bash
# Re-run setup:
vit completion install

# Or manually source:
source ~/.bashrc
```

---

## 📚 Full Documentation

- Update System Contract: `docs/contracts/platform/UPDATE_SYSTEM_CONTRACT_V1.md`
- Package Manager Contract: `docs/contracts/platform/PACKAGE_MANAGER_SYSTEM_CONTRACT_V1.md`
- Knowledge Base: http://localhost:9800/docs/knowledge_base/development/Update_Manager_System/

---

## 🎯 Design Philosophy

**Out-of-the-box usability**: The update system is an integral part of vitruvyan-core and must work immediately after git clone, without any additional installation steps.

**Zero external dependencies**: Uses only what's already installed with vitruvyan-core.

**Graceful degradation**: Autocomplete is optional; all functionality works without it.
