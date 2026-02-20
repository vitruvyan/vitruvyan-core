# 🚀 Vitruvyan CLI Quick Start

## Immediate Usage (No Installation Required)

The `vit` command works **out-of-the-box** without any installation:

```bash
cd /path/to/vitruvyan-core
./vit --help
```

### Add to PATH (Optional, Recommended)

To use `vit` from anywhere:

```bash
# Add this line to your ~/.bashrc or ~/.zshrc
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

## ⚡ Autocomplete Setup

The CLI will **automatically prompt you** to enable autocomplete on first run.

### Manual Setup (Bash)
```bash
# Add to ~/.bashrc:
source /path/to/vitruvyan-core/vitruvyan_core/core/platform/update_manager/cli/completion/vit-completion.bash

# Reload
source ~/.bashrc
```

### Manual Setup (Zsh)
```bash
# Add to ~/.zshrc:
autoload -U compinit && compinit
source /path/to/vitruvyan-core/vitruvyan_core/core/platform/update_manager/cli/completion/vit-completion.bash

# Reload
source ~/.zshrc
```

### Using the completion command
```bash
vit completion install    # Auto-install for current shell
vit completion uninstall  # Remove autocomplete
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
