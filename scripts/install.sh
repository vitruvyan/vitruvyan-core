#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
# Vitruvyan OS — On-Premise Installer
#
# One-liner installation for fresh Ubuntu/Debian VPS:
#
#   curl -fsSL https://raw.githubusercontent.com/dbaldoni/vitruvyan-core/main/scripts/install.sh | bash
#
# Or download and review first:
#
#   curl -fsSL https://raw.githubusercontent.com/dbaldoni/vitruvyan-core/main/scripts/install.sh -o install.sh
#   chmod +x install.sh
#   ./install.sh
#
# Options (env vars):
#   INSTALL_DIR    — where to clone (default: /opt/vitruvyan-core)
#   BRANCH         — git branch to clone (default: main)
#   SKIP_SETUP     — set to 1 to skip 'vit setup' after install
#   REPO_URL       — git repo URL (default: github.com/dbaldoni/vitruvyan-core)
# ═══════════════════════════════════════════════════════════════════

set -euo pipefail

# ── Configuration ──────────────────────────────────────────────
INSTALL_DIR="${INSTALL_DIR:-/opt/vitruvyan-core}"
BRANCH="${BRANCH:-main}"
SKIP_SETUP="${SKIP_SETUP:-0}"
REPO_URL="${REPO_URL:-https://github.com/dbaldoni/vitruvyan-core.git}"
VIT_LINK="/usr/local/bin/vit"

# ── Colors ─────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info()  { echo -e "${BLUE}[vitruvyan]${NC} $*"; }
ok()    { echo -e "${GREEN}[vitruvyan]${NC} $*"; }
warn()  { echo -e "${YELLOW}[vitruvyan]${NC} $*"; }
err()   { echo -e "${RED}[vitruvyan]${NC} $*" >&2; }

# ── Banner ─────────────────────────────────────────────────────
echo ""
echo -e "${BLUE}  ╔══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}  ║     Vitruvyan OS — On-Premise Installer  ║${NC}"
echo -e "${BLUE}  ║     Epistemic Operating System           ║${NC}"
echo -e "${BLUE}  ╚══════════════════════════════════════════╝${NC}"
echo ""

# ── Check: must be Linux ──────────────────────────────────────
if [[ "$(uname -s)" != "Linux" ]]; then
    err "This installer supports Linux only (detected: $(uname -s))."
    err "For macOS/Windows, clone the repo manually and run './vit setup'."
    exit 1
fi

# ── Check: root or sudo ──────────────────────────────────────
need_sudo() {
    if [[ "$(id -u)" -ne 0 ]]; then
        if command -v sudo &>/dev/null; then
            echo "sudo"
        else
            err "This script needs root privileges. Run as root or install sudo."
            exit 1
        fi
    fi
}

SUDO=$(need_sudo)

# ── Step 1: Install system prerequisites ──────────────────────
info "Step 1/4 — Installing system prerequisites"

$SUDO apt-get update -qq

PACKAGES_TO_INSTALL=""

if ! command -v git &>/dev/null; then
    PACKAGES_TO_INSTALL="$PACKAGES_TO_INSTALL git"
fi

if ! command -v curl &>/dev/null; then
    PACKAGES_TO_INSTALL="$PACKAGES_TO_INSTALL curl"
fi

if ! command -v python3 &>/dev/null; then
    PACKAGES_TO_INSTALL="$PACKAGES_TO_INSTALL python3"
fi

# pip3 is needed for Python package management
if ! command -v pip3 &>/dev/null; then
    PACKAGES_TO_INSTALL="$PACKAGES_TO_INSTALL python3-pip"
fi

if [[ -n "$PACKAGES_TO_INSTALL" ]]; then
    info "  Installing:$PACKAGES_TO_INSTALL"
    $SUDO apt-get install -y -qq $PACKAGES_TO_INSTALL
else
    ok "  All system prerequisites already installed"
fi

# Verify Python version >= 3.10
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [[ "$PYTHON_MAJOR" -lt 3 ]] || [[ "$PYTHON_MAJOR" -eq 3 && "$PYTHON_MINOR" -lt 10 ]]; then
    err "Python 3.10+ is required (found: $PYTHON_VERSION)."
    err "Install a newer Python version and retry."
    exit 1
fi

ok "  Python $PYTHON_VERSION ✓, git ✓, curl ✓"

# ── Step 2: Clone repository ─────────────────────────────────
info "Step 2/4 — Cloning Vitruvyan OS"

if [[ -d "$INSTALL_DIR" ]]; then
    if [[ -d "$INSTALL_DIR/.git" ]]; then
        warn "  Directory $INSTALL_DIR already exists — updating..."
        cd "$INSTALL_DIR"
        git fetch origin "$BRANCH" --quiet
        git checkout "$BRANCH" --quiet
        git pull origin "$BRANCH" --quiet
        ok "  Repository updated to latest $BRANCH"
    else
        err "  $INSTALL_DIR exists but is not a git repository."
        err "  Remove it or set INSTALL_DIR to a different path:"
        err "    INSTALL_DIR=/opt/my-vitruvyan curl -fsSL ... | bash"
        exit 1
    fi
else
    info "  Cloning to $INSTALL_DIR..."
    $SUDO mkdir -p "$(dirname "$INSTALL_DIR")"
    $SUDO git clone --branch "$BRANCH" --depth 1 "$REPO_URL" "$INSTALL_DIR"

    # If we cloned as root, fix ownership for the current user
    if [[ -n "$SUDO" ]] && [[ -n "${SUDO_USER:-}" ]]; then
        $SUDO chown -R "$SUDO_USER:$SUDO_USER" "$INSTALL_DIR"
    fi

    ok "  Cloned to $INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# ── Step 3: Create 'vit' command (symlink) ───────────────────
info "Step 3/4 — Setting up 'vit' command"

# Make vit executable
chmod +x "$INSTALL_DIR/vit"

# Create symlink in /usr/local/bin so 'vit' works from anywhere
if [[ -L "$VIT_LINK" ]]; then
    $SUDO rm "$VIT_LINK"
fi

$SUDO ln -s "$INSTALL_DIR/vit" "$VIT_LINK"
ok "  'vit' command available system-wide"

# ── Step 4: Run setup wizard ─────────────────────────────────
if [[ "$SKIP_SETUP" == "1" ]]; then
    info "Step 4/4 — Skipping setup wizard (SKIP_SETUP=1)"
    echo ""
    ok "Installation complete! Run 'vit setup' when ready."
else
    info "Step 4/4 — Launching setup wizard"
    echo ""
    echo "  ─────────────────────────────────────────"
    echo ""

    # Run vit setup interactively
    "$INSTALL_DIR/vit" setup
fi

# ── Done ──────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}  ╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}  ║     ✅ Vitruvyan OS installed!            ║${NC}"
echo -e "${GREEN}  ║                                          ║${NC}"
echo -e "${GREEN}  ║     vit status    — system overview       ║${NC}"
echo -e "${GREEN}  ║     vit setup     — re-run wizard         ║${NC}"
echo -e "${GREEN}  ║     vit upgrade   — update packages       ║${NC}"
echo -e "${GREEN}  ║     vit --help    — all commands           ║${NC}"
echo -e "${GREEN}  ╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${BLUE}Install directory${NC}: $INSTALL_DIR"
echo -e "  ${BLUE}Documentation${NC}:    https://dbaldoni.github.io/vitruvyan-core/"
echo ""
