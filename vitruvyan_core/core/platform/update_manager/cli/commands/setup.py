"""
vit setup — Interactive first-run wizard

Usage:
    vit setup                   # interactive wizard
    vit setup --profile minimal # non-interactive with profile
    vit setup --check           # run prerequisite checks only
    vit setup --env-only        # generate .env file only
"""

import argparse
import sys
from pathlib import Path

from vitruvyan_core.core.platform.package_manager.bootstrap import (
    BootstrapReport,
    collect_env_interactive,
    find_repo_root,
    generate_env_file,
    read_existing_env,
    run_all_checks,
)
from vitruvyan_core.core.platform.package_manager.profiles import (
    CUSTOM,
    InstallProfile,
    get_profile,
    list_profiles,
)
from vitruvyan_core.core.platform.package_manager.registry import PackageRegistry
from vitruvyan_core.core.platform.package_manager.resolver import DependencyResolver
from vitruvyan_core.core.platform.package_manager.installer import PackageInstaller
from vitruvyan_core.core.platform.package_manager.state import PackageState


BANNER = r"""
  ╔══════════════════════════════════════════╗
  ║     Vitruvyan OS — Setup Wizard          ║
  ║     Epistemic Operating System           ║
  ╚══════════════════════════════════════════╝
"""


def cmd_setup(args: argparse.Namespace) -> int:
    """Entry point for 'vit setup'."""
    if args.check:
        return _run_checks_only()
    if args.env_only:
        return _env_only()
    if args.profile:
        profile = get_profile(args.profile)
        if not profile:
            print(f"  Unknown profile: {args.profile}")
            print(f"  Available: {', '.join(p.name for p in list_profiles())}")
            return 1
        return _run_with_profile(profile, skip_confirm=args.yes)
    return _interactive_wizard(skip_confirm=args.yes)


# ── Checks only ──────────────────────────────────────────────────

def _run_checks_only() -> int:
    """Run prerequisite checks and print report."""
    print("\n  Checking prerequisites...\n")
    report = run_all_checks()
    for line in report.summary_lines:
        print(line)
    if report.all_required_passed:
        print("\n  ✅ All required prerequisites met.")
        return 0
    print("\n  ❌ Some required prerequisites are missing.")
    return 1


# ── Env only ─────────────────────────────────────────────────────

def _env_only() -> int:
    """Generate .env file interactively."""
    repo_root = find_repo_root()
    if not repo_root:
        print("  Could not find vitruvyan-core repository root.")
        return 1
    env_path = repo_root / ".env"
    values = collect_env_interactive()
    generate_env_file(env_path, values)
    print(f"\n  ✅ Environment file written to {env_path}")
    return 0


# ── Interactive wizard ───────────────────────────────────────────

def _interactive_wizard(skip_confirm: bool = False) -> int:
    """Full interactive setup wizard."""
    print(BANNER)

    # Step 1: Prerequisites
    print("  Step 1/4 — Checking prerequisites\n")
    report = run_all_checks()
    for line in report.summary_lines:
        print(line)

    if not report.all_required_passed:
        print("\n  ❌ Required prerequisites are missing. Fix them and run 'vit setup' again.")
        return 1

    print("\n  ✅ Prerequisites OK\n")

    # Step 2: Profile selection
    print("  Step 2/4 — Choose installation profile\n")
    profiles = list_profiles()
    for i, p in enumerate(profiles, 1):
        print(f"    {i}) {p.summary}")

    profile = _prompt_profile(profiles)
    if profile is None:
        print("\n  Aborted.")
        return 1

    # If custom, let user pick packages
    if profile.name == "custom":
        profile = _custom_profile_selection()
        if profile is None:
            print("\n  Aborted.")
            return 1

    # Step 3: Environment configuration
    print(f"\n  Step 3/4 — Environment configuration\n")
    repo_root = find_repo_root()
    if not repo_root:
        print("  Could not find repository root.")
        return 1

    env_path = repo_root / ".env"
    existing_env = read_existing_env(env_path)

    # Check if required env vars are set
    missing_env = _check_profile_env(profile, existing_env)
    if missing_env:
        print(f"  The following env vars are needed for this profile:")
        for key in missing_env:
            print(f"    - {key}")
        print()
        values = collect_env_interactive()
        generate_env_file(env_path, values)
        print(f"\n  ✅ Environment file written to {env_path}\n")
    else:
        print(f"  ✅ Environment file already configured ({env_path})\n")

    # Step 4: Install packages
    return _run_with_profile(profile, skip_confirm=skip_confirm)


def _prompt_profile(profiles: list) -> InstallProfile | None:
    """Prompt user to select a profile."""
    try:
        raw = input(f"\n  Select profile [1-{len(profiles)}]: ").strip()
    except (EOFError, KeyboardInterrupt):
        return None

    try:
        idx = int(raw) - 1
        if 0 <= idx < len(profiles):
            return profiles[idx]
    except ValueError:
        # Try by name
        for p in profiles:
            if p.name == raw:
                return p
    print(f"  Invalid selection: {raw}")
    return None


def _custom_profile_selection() -> InstallProfile | None:
    """Let user pick individual packages for a custom profile."""
    registry = PackageRegistry()
    state = PackageState()
    all_manifests = registry.discover()

    # Only show installable (non-core) packages
    installable = [m for m in all_manifests if m.tier != "core"]
    if not installable:
        print("  No installable packages found.")
        return CUSTOM

    print(f"\n  Available packages (select with comma-separated numbers):\n")
    for i, m in enumerate(installable, 1):
        status_badge = f" [{m.status}]" if m.status != "stable" else ""
        print(f"    {i}) {m.short_name} v{m.package_version}{status_badge} — {m.description}")

    try:
        raw = input(f"\n  Select packages [e.g. 1,3]: ").strip()
    except (EOFError, KeyboardInterrupt):
        return None

    if not raw:
        return CUSTOM

    selected_names = []
    env_keys: list[str] = []
    for part in raw.split(","):
        part = part.strip()
        try:
            idx = int(part) - 1
            if 0 <= idx < len(installable):
                m = installable[idx]
                selected_names.append(m.cli_name)
                env_keys.extend(m.env_required)
        except ValueError:
            pass

    return InstallProfile(
        name="custom",
        label="Custom",
        description=f"Custom selection ({len(selected_names)} packages)",
        packages=selected_names,
        size_estimate="varies",
        env_keys=list(set(env_keys)),
    )


def _check_profile_env(profile: InstallProfile, existing: dict) -> list[str]:
    """Return env keys required by profile that are not yet set."""
    missing = []
    for key in profile.env_keys:
        val = existing.get(key, "")
        if not val:
            missing.append(key)
    return missing


# ── Non-interactive profile install ──────────────────────────────

def _run_with_profile(profile: InstallProfile, skip_confirm: bool = False) -> int:
    """Install packages from a profile."""
    if not profile.packages:
        print(f"\n  Profile '{profile.label}' — no extra packages to install.")
        print("  Core components are already available via 'vit upgrade'.")
        print("\n  ✅ Setup complete!")
        return 0

    registry = PackageRegistry()
    state = PackageState()
    resolver = DependencyResolver(registry, state)
    installer = PackageInstaller(state)

    # Resolve all packages
    print(f"\n  Step 4/4 — Installing profile '{profile.label}'\n")
    print(f"  Resolving {len(profile.packages)} package(s)...\n")

    plans = []
    for pkg_name in profile.packages:
        manifest = registry.get(pkg_name)
        if not manifest:
            print(f"  ⚠️  Package '{pkg_name}' not found — skipping")
            continue
        if state.is_installed(manifest.package_name):
            print(f"  ✓ {manifest.package_name} already installed")
            continue
        plan = resolver.resolve(pkg_name)
        if not plan.can_proceed:
            print(f"  ⚠️  {manifest.package_name}: {plan.block_reason}")
            continue
        plans.append((manifest, plan))

    if not plans:
        print("\n  Nothing to install — all packages already present or unavailable.")
        print("\n  ✅ Setup complete!")
        return 0

    # Show summary
    print(f"\n  Will install {len(plans)} package(s):")
    for manifest, plan in plans:
        deps_info = ""
        if plan.install_order and len(plan.install_order) > 1:
            deps_info = f" (+ {len(plan.install_order) - 1} deps)"
        print(f"    + {manifest.package_name} v{manifest.package_version}{deps_info}")

    # Confirm
    if not skip_confirm:
        try:
            confirm = input("\n  Proceed? [Y/n]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n  Aborted.")
            return 1
        if confirm and confirm not in ("y", "yes", ""):
            print("  Aborted.")
            return 1

    # Install
    success_count = 0
    fail_count = 0
    for i, (manifest, plan) in enumerate(plans, 1):
        print(f"\n  [{i}/{len(plans)}] Installing {manifest.package_name}...")
        ok = installer.install(manifest, interactive=False)
        if ok:
            print(f"  ✅ {manifest.package_name} installed successfully")
            success_count += 1
        else:
            print(f"  ❌ {manifest.package_name} installation failed")
            fail_count += 1

    # Summary
    print(f"\n  {'─' * 40}")
    print(f"  Setup complete: {success_count} installed, {fail_count} failed")
    if fail_count == 0:
        print("  ✅ All packages installed successfully!")
    else:
        print("  ⚠️  Some packages failed. Run 'vit status' for details.")

    return 1 if fail_count > 0 else 0


def register_setup_command(subparsers) -> None:
    """Register 'vit setup' subcommand."""
    parser = subparsers.add_parser(
        "setup",
        help="Interactive first-run setup wizard",
        description="Configure Vitruvyan OS: check prerequisites, set environment, install packages.",
    )
    parser.add_argument(
        "--profile",
        choices=["minimal", "standard", "finance", "full", "custom"],
        help="Installation profile (skip interactive selection)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run prerequisite checks only",
    )
    parser.add_argument(
        "--env-only",
        action="store_true",
        help="Generate .env file only",
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompts",
    )
    parser.set_defaults(func=cmd_setup)
