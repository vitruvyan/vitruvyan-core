# VIT Tab Completion

> **Last updated**: Feb 20, 2026 10:30 UTC  
> **Status**: Implemented  
> **Shell Support**: Bash (Zsh coming soon)

## Features

The `vit` command supports intelligent tab completion for:

- **Commands**: `update`, `upgrade`, `plan`, `rollback`, `status`, `channel`, `install`, `remove`, `list`, `search`, `info`
- **Flags**: Command-specific options (e.g., `--channel`, `--target`, `--yes`)
- **Values**: Context-aware completion (e.g., `stable`/`beta` for `--channel`)
- **Package names**: Auto-discovered from manifests (for `install`/`info`) and installed packages (for `remove`)

## Installation

### Automatic (Recommended)

The completion script is automatically sourced when you install `vitruvyan-core`:

```bash
pip install -e .
```

The `pyproject.toml` entry point handles registration.

### Manual Installation

If automatic installation doesn't work:

**Option 1: Source in your shell config**

Add to `~/.bashrc`:

```bash
source /path/to/vitruvyan-core/vitruvyan_core/core/platform/update_manager/cli/completion/vit-completion.bash
```

**Option 2: System-wide installation**

```bash
sudo cp vitruvyan_core/core/platform/update_manager/cli/completion/vit-completion.bash \
         /etc/bash_completion.d/vit
```

**Option 3: User-level installation**

```bash
mkdir -p ~/.bash_completion.d
cp vitruvyan_core/core/platform/update_manager/cli/completion/vit-completion.bash \
   ~/.bash_completion.d/vit

# Add to ~/.bashrc:
for f in ~/.bash_completion.d/*; do source "$f"; done
```

### Verify Installation

```bash
# Reload shell
source ~/.bashrc

# Test completion
vit <TAB><TAB>
# Should show: update upgrade plan rollback status channel install remove list search info help

vit update --<TAB><TAB>
# Should show: --channel --json --help

vit install <TAB><TAB>
# Should show: babel_gardens neural_engine pattern_weavers ... (all available packages)
```

## Examples

### Command Completion

```bash
vit up<TAB>          →  vit update
vit upg<TAB>         →  vit upgrade
vit sta<TAB>         →  vit status
```

### Flag Completion

```bash
vit update --<TAB>
  --channel  --json  --help

vit upgrade --<TAB>
  --channel  --target  --yes  --json  --help
```

### Value Completion

```bash
vit update --channel <TAB>
  stable  beta

vit list --type <TAB>
  service  order  vertical  extension
```

### Package Name Completion

```bash
vit install <TAB>
  babel_gardens  neural_engine  pattern_weavers  orthodoxy_wardens  vault_keepers  memory_orders

vit install babel<TAB>   →  vit install babel_gardens

vit remove <TAB>
  service-babel-gardens  extension-mcp-tools  (shows only installed packages)
```

## Implementation Details

### Completion Logic

The completion script (`vit-completion.bash`) uses bash's programmable completion:

1. **Command detection**: Identifies current `vit` subcommand
2. **Context-aware suggestions**: Different completions per command
3. **Dynamic package discovery**:
   - `install`/`info`: Scans `packages/manifests/*.yaml`
   - `remove`: Reads `.vitruvyan/installed_packages.json`
4. **Flag completion**: Command-specific flags (e.g., `--channel` only for `update`/`upgrade`)

### Performance

- **Fast**: Caches package list on first TAB press
- **Minimal overhead**: No network calls (local manifest scan only)
- **Fallback**: Graceful degradation if manifest directory missing

### Zsh Support (Future)

Zsh completion planned for Phase 6:

```bash
# .zshrc
fpath=(~/.zsh/completion $fpath)
autoload -Uz compinit && compinit
```

File: `vit-completion.zsh` (uses `_arguments` and `_describe`)

## Troubleshooting

### Completion not working

**Check if completion loaded**:
```bash
complete -p vit
# Should output: complete -F _vit_completion vit
```

**If not loaded**:
```bash
source vitruvyan_core/core/platform/update_manager/cli/completion/vit-completion.bash
```

### Package names not completing

**Check manifest directory exists**:
```bash
ls vitruvyan_core/core/platform/update_manager/packages/manifests/
# Should show .yaml files (Phase 5+)
```

**Temporary workaround**: Hardcoded aliases work (e.g., `babel_gardens`, `neural_engine`)

### Installed packages not completing for `vit remove`

**Check registry file exists**:
```bash
cat .vitruvyan/installed_packages.json
```

If missing, completion falls back to empty list.

## Development

### Testing Completion

```bash
# Enable debug mode
set -x

# Test completion
vit up<TAB>

# Disable debug
set +x
```

### Adding New Commands

Edit `vit-completion.bash`:

1. Add command to `commands` variable:
   ```bash
   local commands="update upgrade ... newcommand"
   ```

2. Add command-specific flags:
   ```bash
   local newcommand_flags="--flag1 --flag2"
   ```

3. Add case in completion logic:
   ```bash
   newcommand)
       COMPREPLY=( $(compgen -W "${newcommand_flags}" -- "${cur}") )
       ;;
   ```

### Adding New Package Types

Edit `package_types` variable:
```bash
local package_types="service order vertical extension newtype"
```

## Future Enhancements

- [ ] Zsh completion script
- [ ] Fish shell completion
- [ ] PowerShell completion (Windows)
- [ ] Remote package name fetching (cache)
- [ ] Version number completion (fetch from GitHub Releases)
- [ ] Fuzzy matching for package names
- [ ] Colorized completion descriptions

## References

- [Bash Programmable Completion](https://www.gnu.org/software/bash/manual/html_node/Programmable-Completion.html)
- [bash-completion GitHub](https://github.com/scop/bash-completion)
- [Zsh Completion System](https://zsh.sourceforge.io/Doc/Release/Completion-System.html)
